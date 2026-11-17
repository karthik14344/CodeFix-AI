"""LLM-as-judge + objective verification.

The judge model (config role `judge`) is required to differ from the Diagnoser and Fixer
models (self-preference bias). It sees the bug report, the pre-patch source of the touched
files and the final diff — NOT the test results — so judge-vs-tests agreement is a genuine
measure of the judge rather than an echo of the Tester.

The objective signal is recomputed independently of the Tester: the final patch is applied
to a fresh clone and the bug's previously-failing test plus the full suite are run.
"""

from __future__ import annotations

import difflib
from pathlib import Path

from codefix.agents.base import JudgeVerdict
from codefix.blackboard import Blackboard
from codefix.eval.bugset import Bug
from codefix.llm import BaseLLM, LLMError
from mcp_server import testrunner
from mcp_server.sandbox import WorkspaceManager, run

SYSTEM = """You are an impartial senior engineer judging an automated bug fix.
Decide whether the patch actually resolves the reported bug without breaking intended behaviour.
You are NOT shown test results; reason from the bug report, the original code and the diff.

verdict: "pass" (resolves the bug correctly), "partial" (addresses it incompletely or with a
side effect), "fail" (does not fix it, wrong place, or no patch). score: 0.0-1.0.
Reply as JSON {verdict, reasoning, score}. Keep reasoning under 120 words.
"""


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n") if p.exists() else ""


def _changed_lines(before: str, after: str) -> str:
    """The lines a change removes and adds (the 'edit text'), in order, for similarity scoring."""
    out = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, before.splitlines(), after.splitlines()).get_opcodes():
        if tag != "equal":
            out += ["-" + x.strip() for x in before.splitlines()[i1:i2]]
            out += ["+" + x.strip() for x in after.splitlines()[j1:j2]]
    return "\n".join(out)


def reference_compare(repo: Path, ws: Path, bug: Bug) -> dict:
    """Reference-text evaluation: compare the agent's patched files with the known-good fix.

    * ref_exact       - every buggy file is byte-identical (modulo whitespace) to the reference fix
    * ref_similarity  - difflib ratio between the agent's edit text and the reference edit text (0-1)
    * ref_file_match  - the agent changed exactly the file(s) the reference fix changes
    """
    from codefix.agents.patching import apply_edits_in_memory

    originals = {f: _read(repo / f) for f in bug.files}
    reference = apply_edits_in_memory(originals, [dict(e) for e in bug.fix_edits])
    exact, sims = True, []
    for f in bug.files:
        cand = _read(ws / f)
        exact &= " ".join(cand.split()) == " ".join(reference[f].split())
        ref_edit, cand_edit = _changed_lines(originals[f], reference[f]), _changed_lines(originals[f], cand)
        sims.append(difflib.SequenceMatcher(None, ref_edit, cand_edit).ratio() if cand_edit else 0.0)
    changed = {c for c in (x.strip() for x in run(["git", "diff", "--name-only", "HEAD"], cwd=ws).stdout.splitlines())
               if c}
    return {"ref_exact": int(exact), "ref_similarity": round(sum(sims) / len(sims), 3) if sims else 0.0,
            "ref_file_match": int(changed == set(bug.files))}


def objective_check(repo: Path, sandbox: Path, diff: str, bug: Bug | None, name: str) -> dict:
    empty_ref = {"ref_exact": 0 if bug else None, "ref_similarity": 0.0 if bug else None,
                 "ref_file_match": 0 if bug else None}
    if not diff.strip():
        return {"objective_pass": False, "target_test_pass": False, "note": "no patch", **empty_ref}
    wm = WorkspaceManager(repo, sandbox)
    ws = wm.create(name)
    try:
        pf = ws / ".git" / "judge.patch"
        pf.write_text(diff if diff.endswith("\n") else diff + "\n", encoding="utf-8", newline="\n")
        # Same apply policy as the Tester's apply_patch tool: strict first, then tolerant of
        # CRLF/whitespace drift in context lines. Without the fallback, a multi-file patch touching
        # a CRLF file on a Windows checkout was graded "does not apply" although it was correct.
        flags = ["--recount", "--whitespace=nowarn"]
        if run(["git", "apply", "--check", *flags, str(pf)], cwd=ws).returncode != 0:
            flags.append("--ignore-whitespace")
        if run(["git", "apply", *flags, str(pf)], cwd=ws).returncode != 0:
            return {"objective_pass": False, "target_test_pass": False, "note": "patch does not apply", **empty_ref}
        ref = reference_compare(repo, ws, bug) if bug else empty_ref
        target = testrunner.run_tests(ws, selector=bug.failing_test) if bug else {"passed": None}
        full = testrunner.run_tests(ws)
        return {"objective_pass": bool(full["passed"]), "target_test_pass": target["passed"],
                "note": f"{full['total']} tests, {full['failed']} failed", **ref}
    finally:
        wm.discard(name)


def judge_run(llm: BaseLLM, bb: Blackboard, task_id: str, bug: Bug | None = None,
              sandbox: Path | None = None) -> dict:
    snap = bb.snapshot(task_id)
    run_row = snap["run"]
    patches = bb.artifacts(task_id, "patch")
    final_patch = patches[-1]["body"] if patches else {"diff": "", "rationale": ""}
    tr = snap["test_report"] or {}
    if tr.get("passed") and tr.get("patch_artifact_id"):  # the verified patch, if any
        final_patch = next((p["body"] for p in patches if p["id"] == tr["patch_artifact_id"]), final_patch)
    diff = final_patch.get("diff", "")

    repo = Path(run_row["repo"])
    obj = objective_check(repo, sandbox or repo.parent / "_judge_ws", diff, bug, f"judge-{task_id}"[:100])

    originals = []
    for f in final_patch.get("files_touched", [])[:4]:
        p = repo / f
        if p.exists():
            originals.append(f"--- {f}\n{p.read_text(encoding='utf-8', errors='replace')[:8000]}")
    prompt = (f"BUG REPORT:\n{run_row['bug_report']}\n\nORIGINAL SOURCE OF TOUCHED FILES:\n"
              f"{chr(10).join(originals) or '(none)'}\n\nFINAL PATCH:\n{diff or '(no patch was produced)'}\n\n"
              f"FIXER RATIONALE:\n{final_patch.get('rationale', '')}")
    verdict, reasoning, score, cost = "fail", "no patch", 0.0, 0.0
    if diff.strip():
        try:
            res = llm.structured(role="judge", system=SYSTEM, messages=[{"role": "user", "content": prompt}],
                                 schema=JudgeVerdict, task_id=task_id, agent="judge")
            v: JudgeVerdict = res.parsed
            verdict, reasoning, score, cost = v.verdict, v.reasoning, v.score, res.cost_usd
        except LLMError as e:
            verdict, reasoning = "error", str(e)[:500]
    judged_pass = verdict == "pass"
    agreement = None if verdict == "error" else int(judged_pass == obj["objective_pass"])
    row = {"judge_model": llm.role("judge").model if llm.mode != "mock" else "mock", "verdict": verdict,
           "score": score, "reasoning": reasoning, "objective_pass": int(obj["objective_pass"]),
           "target_test_pass": None if obj["target_test_pass"] is None else int(obj["target_test_pass"]),
           "agreement": agreement, "cost_usd": cost,
           "ref_exact": obj.get("ref_exact"), "ref_similarity": obj.get("ref_similarity"),
           "ref_file_match": obj.get("ref_file_match")}
    bb.record_evaluation(task_id, **row)
    bb.trace.emit(task_id, "evaluation", **row, objective_note=obj["note"])
    return row
