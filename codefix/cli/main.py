"""codefix CLI: fix | demo | index | bench | trace | runs | pr | serve | crew-serve | graph."""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from codefix import config

app = typer.Typer(add_completion=False, help="CodeFix AI — autonomous multi-agent bug resolution.")
con = Console()

ARCH_HELP = "hierarchical (default) | sequential | p2p"
VARIANT_HELP = "Prompt variant: react (default) | fewshot | react-reflect"
PERSONA_HELP = "Persona: default | senior | novice | security"
AGENT_STYLE = {"manager": "magenta", "diagnoser": "cyan", "fixer": "yellow", "tester": "green", "pr": "blue",
               "system": "dim", "human": "bold white"}


def _follow(task_id_box: list, stop: threading.Event) -> None:
    """Tail the run's JSONL trace and print a live, compact timeline."""
    from codefix.graph.runner import blackboard

    offset = 0
    while True:
        done = stop.is_set()  # read once more after the run finishes so nothing is dropped
        if task_id_box:
            for ev in blackboard().trace.read(task_id_box[0], offset):
                offset += 1
                _print_event(ev)
        if done:
            break
        time.sleep(0.3)


def _print_event(ev: dict) -> None:
    t = ev["type"]
    if t == "envelope":
        e = ev["envelope"]
        p = e["payload"]
        s = AGENT_STYLE.get(e["sender"], "white")
        detail = {"dispatch": p.get("instruction", ""), "diagnosis": p.get("root_cause", "")[:110],
                  "patch": p.get("rationale", "")[:110] or p.get("generation_error", ""),
                  "test_report": f"passed={p.get('passed')} {p.get('total')} tests, {p.get('failed')} failed"
                                 + (f" [{p.get('failure_stage')}]" if p.get("failure_stage") else ""),
                  "escalation": p.get("reason", ""), "pr_result": p.get("note", "")}.get(p["kind"], "")
        lat = f" {e['latency_ms'] / 1000:.1f}s" if e.get("latency_ms") else ""
        con.print(f"[{s}]{e['sender']:>9}[/] → {e['target_agent']:<9} [bold]{e['status']:<11}[/] "
                  f"{p['kind']:<11}{lat}  {detail}")
    elif t == "react_step":
        con.print(f"[dim]          ReAct {ev['step']}: [/][cyan]{ev['action']}[/] [dim]{ev['action_input'][:70]}[/]"
                  f"\n[dim]            thought: {ev['thought'][:150]}[/]")
    elif t == "manager_decision":
        con.print(f"[magenta]   manager[/] decides [bold]{ev['decision']}[/] [dim]({ev['reason'][:100]})[/]")
    elif t == "llm_call":
        con.print(f"[dim]          llm {ev['agent']} {ev.get('served_model') or ev['model']} "
                  f"in={ev['input_tokens']} out={ev['output_tokens']} ${ev['cost_usd']:.4f} {ev['latency_ms']}ms[/]")
    elif t == "a2a_request":
        con.print(f"[blue]       A2A[/] adk → codefix-crew [bold]{ev['skill']}[/] [dim]({ev['transport']}, "
                  f"{ev['bytes']} bytes)[/]")
    elif t == "a2a_response" and not ev.get("ok"):
        con.print(f"[red]       A2A {ev['skill']} failed: {ev.get('error')}[/]")
    elif t == "guardrail" and (not ev.get("allowed") or ev.get("category") != "ok"):
        con.print(f"[red]  guardrail[/] {ev.get('stage')}: [bold]{ev.get('category')}[/] "
                  f"[dim]{'; '.join(ev.get('reasons', []))[:160]}[/]")
    elif t == "reflection":
        con.print(f"[yellow]  reviewer[/] approved={ev.get('approved')} [dim]{'; '.join(ev.get('issues') or [])[:140]}[/]")
    elif t in ("run_error",):
        con.print(f"[red]run error: {ev['error']}[/]")
    elif t == "index":
        con.print(f"[dim]   RAG index: {ev.get('files_changed')} files changed, {ev.get('code_chunks')} code chunks, "
                  f"{ev.get('doc_chunks')} doc chunks ({ev.get('embedder')})[/]")


def _show_result(snap: dict) -> None:
    run = snap["run"]
    color = {"passed": "green", "escalated": "yellow"}.get(run["outcome"], "red")
    if snap["diagnosis"]:
        d = snap["diagnosis"]
        con.print(Panel(f"{d['root_cause']}\n\n[dim]files: {', '.join(d['implicated_files'])} · confidence "
                        f"{d['confidence']:.2f} · cites: {', '.join(d['citations']) or '-'}[/]", title="Diagnosis"))
    if snap["patch"] and snap["patch"]["diff"]:
        con.print(Panel(Syntax(snap["patch"]["diff"], "diff", word_wrap=True), title=f"Patch (attempt {snap['patch']['attempt_no']})"))
    if snap["escalation"]:
        con.print(Panel(snap["escalation"]["summary"] + "\n\n" + "\n".join(snap["escalation"]["tried"]),
                        title="Escalated to human", border_style="yellow"))
    con.print(f"\n[bold {color}]{run['outcome'] or run['status']}[/] · task [bold]{run['task_id']}[/] · "
              f"attempts {run['attempts']}/{run['max_attempts']} · {(run['duration_ms'] or 0) / 1000:.1f}s · "
              f"${run['cost_usd']:.4f} · trace: traces/{run['task_id']}.jsonl")


def _execute(bug_report: str, repo: Path, arch: str, max_attempts: int | None, llm: str, stack_trace: str,
             handler=None, extra=None) -> dict:
    from codefix.graph import runner

    box: list = []
    stop = threading.Event()
    result: dict = {}

    def work():
        from codefix.blackboard import new_task_id

        tid = new_task_id()
        box.append(tid)
        result["snap"] = runner.run_pipeline(bug_report, repo, arch=arch, max_attempts=max_attempts, llm_mode=llm,
                                             stack_trace=stack_trace, task_id=tid, mock_handler=handler, extra=extra)

    th = threading.Thread(target=work, daemon=True)
    th.start()
    follower = threading.Thread(target=_follow, args=(box, stop), daemon=True)
    follower.start()
    th.join()
    stop.set()
    follower.join(timeout=3)
    return result["snap"]


def _offer_pr(snap: dict, yes: bool) -> None:
    from codefix.graph import runner

    run = snap["run"]
    if run["status"] != "awaiting_approval":
        return
    con.print(f"\n[green]Tests passed.[/] The fix is committed on branch [bold]codefix/{run['task_id']}[/] "
              "in an isolated workspace. Nothing has been pushed.")
    if yes or typer.confirm("Push the branch and open a Pull Request?", default=False):
        out = runner.resolve_pr(run["task_id"], confirmed=True)
        pr = out["pr"] or {}
        con.print(f"[blue]PR:[/] {pr.get('url') or '(not opened)'} — {pr.get('note', '')}")
    else:
        con.print(f"Not opened. Later: [bold]codefix pr {run['task_id']}[/]")


@app.command()
def fix(bug_report: str = typer.Argument(..., help="Bug report text (or @file.txt)"),
        repo: Path = typer.Option(..., "--repo", "-r", help="Path to the target git repo"),
        arch: str = typer.Option("hierarchical", help=ARCH_HELP),
        max_attempts: int | None = typer.Option(None, help="Fixer attempts before escalation (default from YAML)"),
        trace: Path | None = typer.Option(None, "--stack-trace", "-t", help="File containing a stack trace"),
        llm: str = typer.Option("live", help="live | mock (mock only for bugset repos; use `codefix demo`)"),
        variant: str | None = typer.Option(None, help=VARIANT_HELP),
        persona: str | None = typer.Option(None, help=PERSONA_HELP),
        yes_pr: bool = typer.Option(False, "--yes-pr", help="Skip the PR confirmation prompt (still explicit)")):
    """Locate, explain, patch and verify a bug; then offer to open a PR."""
    if bug_report.startswith("@"):
        bug_report = Path(bug_report[1:]).read_text(encoding="utf-8")
    stack = trace.read_text(encoding="utf-8") if trace else ""
    if llm == "mock":
        raise typer.BadParameter("mock mode needs ground truth: use `codefix demo <bug-id> --llm mock`")
    snap = _execute(bug_report, repo, arch, max_attempts, llm, stack, extra=_variant_extra(variant, persona))
    _show_result(snap)
    _offer_pr(snap, yes_pr)


def _variant_extra(variant: str | None, persona: str | None) -> dict:
    from codefix import prompts

    extra = {k: v for k, v in (("variant", variant), ("persona", persona)) if v}
    try:
        prompts.check(extra.get("variant", "react"), extra.get("persona", "default"))
    except ValueError as e:
        raise typer.BadParameter(str(e)) from e
    return extra


@app.command()
def demo(bug_id: str = typer.Argument("py05-region-case", help="Bug id from benchmarks/bugset/bugs.yaml"),
         arch: str = typer.Option("hierarchical", help=ARCH_HELP),
         llm: str = typer.Option("live", help="live (Z.AI GLM API, billed) | mock (offline oracle, shows a retry)"),
         max_attempts: int | None = typer.Option(None),
         variant: str | None = typer.Option(None, help=VARIANT_HELP),
         persona: str | None = typer.Option(None, help=PERSONA_HELP)):
    """Materialise a seeded bug into a fresh repo and fix it end-to-end (the live-demo path)."""
    from codefix.eval.bugset import failing_output, load_bugs, materialize, trace_text
    from codefix.eval.oracle import OracleMock

    bugs = load_bugs([bug_id])
    if not bugs:
        raise typer.BadParameter(f"unknown bug {bug_id}")
    bug = bugs[0]
    repo = materialize(bug, config.DATA_DIR / ".codefix" / "demo" / bug.id)
    stack = trace_text(failing_output(bug, repo)) if bug.with_trace else ""
    con.print(Panel(f"{bug.report}\n\n[dim]repo: {repo}[/]" + (f"\n[dim]failing test output attached ({len(stack)} chars)[/]" if stack else ""),
                    title=f"Bug report · {bug.id} · {arch} · llm={llm}"))
    snap = _execute(bug.report, repo, arch, max_attempts, llm, stack,
                    handler=OracleMock(bug) if llm == "mock" else None, extra=_variant_extra(variant, persona))
    _show_result(snap)
    _offer_pr(snap, False)


@app.command()
def index(repo: Path = typer.Argument(..., help="Repo to index"), force: bool = typer.Option(False, "--force")):
    """Build/refresh the RAG index (incremental on file mtime)."""
    from codefix.mcp_client import get_toolbox

    stats = get_toolbox(repo).call("index_repo", {"force": force})
    t = Table(title=f"RAG index · {repo}")
    for k, v in stats.items():
        t.add_row(k, str(v))
    con.print(t)


@app.command()
def bench(arch: str = typer.Option("all", help="all | comma list of " + ARCH_HELP),
          runs: int = typer.Option(1, help="Repetitions per bug x architecture"),
          bugs: str | None = typer.Option(None, help="Comma list of bug ids/prefixes (default: all)"),
          llm: str = typer.Option("live", help="live | mock"),
          judge: bool = typer.Option(True, help="Run the LLM judge"),
          max_attempts: int | None = typer.Option(None),
          variants: str = typer.Option("react", help="Comma list of prompt variants: react,fewshot,react-reflect"),
          personas: str = typer.Option("default", help="Comma list of personas: default,senior,novice,security"),
          reporters: str = typer.Option("developer", help="Comma list of user personas filing the report: developer,enduser"),
          verify_bugset: bool = typer.Option(False, "--verify-bugset", help="Only check every bug is reproducible")):
    """Benchmark architectures on the seeded bug set -> CSV + markdown report."""
    from codefix.eval.bugset import load_bugs, verify

    if verify_bugset:
        work = config.DATA_DIR / ".codefix" / "verify"
        t = Table("bug", "fails injected", "target green after fix", "suite green after fix")
        ok = True
        for b in load_bugs(bugs.split(",") if bugs else None):
            r = verify(b, work)
            ok &= r["ok"]
            t.add_row(b.id, *("✅" if r[k] else "❌" for k in ("fails_when_injected", "target_passes_after_fix",
                                                              "suite_passes_after_fix")))
        con.print(t)
        raise typer.Exit(0 if ok else 1)
    from codefix.eval.bench import run_bench
    from codefix.graph.runner import ARCHS

    archs = list(ARCHS) if arch == "all" else [a.strip() for a in arch.split(",")]
    vs, ps = [v.strip() for v in variants.split(",")], [p.strip() for p in personas.split(",")]
    for v in vs:
        for p in ps:
            _variant_extra(v, p)
    out = run_bench(archs, runs=runs, bug_ids=bugs.split(",") if bugs else None, llm_mode=llm, judge=judge,
                    max_attempts=max_attempts, variants=vs, personas=ps, progress=con.print,
                    reporters=[u.strip() for u in reporters.split(",")])
    con.print(Path(out["report"]).read_text(encoding="utf-8"))


@app.command()
def report(bench_id: str):
    """Regenerate the CSV + markdown report for an existing benchmark id."""
    from codefix.eval.bench import RESULTS_DIR, export_csv
    from codefix.eval.report import write_report

    export_csv(bench_id, RESULTS_DIR / bench_id / "runs.csv")
    con.print(write_report(bench_id, RESULTS_DIR / bench_id / "report.md").read_text(encoding="utf-8"))


@app.command()
def trace(task_id: str, as_json: bool = typer.Option(False, "--json", help="Dump the full Blackboard snapshot"),
          react: bool = typer.Option(False, "--react", help="Print the ReAct transcript")):
    """Replay a run's trace (or dump its full pipeline state)."""
    from codefix.graph.runner import blackboard

    bb = blackboard()
    if as_json:
        con.print_json(json.dumps(bb.snapshot(task_id), default=str))
        return
    if react:
        p = config.TRACES_DIR / f"{task_id}.react.md"
        con.print(p.read_text(encoding="utf-8") if p.exists() else "(no ReAct transcript)")
        return
    for ev in bb.trace.read(task_id):
        _print_event(ev)
    _show_result(bb.snapshot(task_id))


@app.command()
def runs(limit: int = 20, outcome: str | None = None):
    """List recent runs."""
    from codefix.graph.runner import blackboard

    t = Table("task_id", "arch", "llm", "outcome", "attempts", "time", "cost", "bug / report")
    for r in blackboard().list_runs(outcome=outcome, limit=limit):
        t.add_row(r["task_id"], r["arch"], r["llm_mode"], r["outcome"] or r["status"], str(r["attempts"]),
                  f"{(r['duration_ms'] or 0) / 1000:.0f}s", f"${r['cost_usd']:.3f}",
                  r["bug_id"] or r["bug_report"][:50])
    con.print(t)


@app.command()
def pr(task_id: str, yes: bool = typer.Option(False, "--yes", help="Confirm without prompting")):
    """Push the codefix/<task_id> branch and open the PR for a passing run (asks for confirmation)."""
    from codefix.graph import runner

    run = runner.blackboard().get_run(task_id)
    if not run:
        raise typer.BadParameter("unknown task")
    if not (yes or typer.confirm(f"Push codefix/{task_id} to {run['repo']}'s origin and open a PR?", default=False)):
        runner.resolve_pr(task_id, confirmed=False)
        con.print("Declined.")
        return
    out = runner.resolve_pr(task_id, confirmed=True)
    con.print(out["pr"])


@app.command()
def serve(host: str = "127.0.0.1", port: int = 8000):
    """Start the web app (new fix, live run view, dashboard, runs)."""
    import uvicorn

    con.print(f"CodeFix AI web app → [bold]http://{host}:{port}[/]")
    uvicorn.run("web.api.app:app", host=host, port=port, log_level="warning")


@app.command("crew-serve")
def crew_serve(host: str = "127.0.0.1", port: int = 8100):
    """Run the CrewAI worker agents as a standalone A2A service (point CODEFIX_CREW_A2A_URL at it)."""
    import uvicorn

    from codefix.crew_side.a2a_server import build_app

    url = f"http://{host}:{port}/"
    con.print(f"CodeFix CrewAI A2A service → [bold]{url}[/] (agent card: {url}.well-known/agent-card.json)")
    uvicorn.run(build_app(url), host=host, port=port, log_level="warning")


#: PRAGMA user_version on runs.db. 1 = cached prompt tokens have been split out of input_tokens.
DB_SCHEMA_VERSION = 1


@app.command("compare")
def compare_cmd(out: Path = typer.Option(None, help="Also write the Markdown to this path")):
    """Compare prompt variants and personas against the main benchmark's baseline arm.

    The sweeps vary one factor at a time; this joins them back to the
    hierarchical/react/default/developer runs from the architecture benchmark, paired on the
    same bugs, so no measurement is paid for twice.
    """
    from codefix.eval.compare import report

    text = report(out)
    con.print(text)
    if out:
        con.print(f"[dim]written to {out}[/]")


@app.command("recost")
def recost(apply: bool = typer.Option(False, "--apply", help="Write the corrected costs (default: dry run)"),
           split_cached: bool = typer.Option(
               False, "--split-cached-input",
               help="One-time migration: subtract cached tokens from input_tokens on old rows")):
    """Recompute llm_calls.cost_usd from stored token counts and the current price table.

    Use after a pricing correction so historical runs do not have to be re-executed. Token
    counts are facts recorded at call time; only the money is recomputed.

    `--split-cached-input` additionally repairs rows written before the OpenAI-dialect usage
    fix, where `input_tokens` was stored as the provider's `prompt_tokens` - which *includes*
    the cached prefix - so cached tokens were billed at the full input rate and then charged the
    cache-read fee on top. It is guarded by PRAGMA user_version so it can never run twice.
    """
    import sqlite3

    from codefix.observability.pricing import Usage, cost_usd

    pricing = config.settings().pricing
    db = sqlite3.connect(config.DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        version = db.execute("PRAGMA user_version").fetchone()[0]
        migrate = split_cached and version < DB_SCHEMA_VERSION
        if split_cached and not migrate:
            con.print(f"[yellow]cached-input split already applied (user_version={version});"
                      " skipping it[/]")

        rows = db.execute(
            "SELECT id, served_model, model, input_tokens, output_tokens,"
            " cache_read_tokens, cache_write_tokens, cost_usd FROM llm_calls").fetchall()
        changes, before, after, split = [], 0.0, 0.0, 0
        for r in rows:
            cached = r["cache_read_tokens"] or 0
            inp = r["input_tokens"] or 0
            if migrate and cached and inp >= cached:
                inp -= cached
                split += 1
            new = cost_usd(r["served_model"] or r["model"],
                           Usage(inp, r["output_tokens"] or 0, cached,
                                 r["cache_write_tokens"] or 0), pricing)
            before += r["cost_usd"] or 0
            after += new
            if abs(new - (r["cost_usd"] or 0)) > 1e-9 or (migrate and inp != (r["input_tokens"] or 0)):
                changes.append((inp, new, r["id"]))
        # runs.cost_usd is a running total incremented per call (Blackboard.record_llm_call),
        # so correcting llm_calls alone leaves the per-run figure - the one the dashboard and
        # the benchmark report show - stale. Rebuild it from its calls.
        run_delta = db.execute(
            "SELECT COUNT(*) FROM runs r WHERE ABS(COALESCE(r.cost_usd,0) -"
            " (SELECT COALESCE(SUM(l.cost_usd),0) FROM llm_calls l WHERE l.task_id=r.task_id))"
            " > 1e-9").fetchone()[0]
        if apply:
            if changes:
                db.executemany("UPDATE llm_calls SET input_tokens=?, cost_usd=? WHERE id=?", changes)
            db.execute(
                "UPDATE runs SET cost_usd = COALESCE("
                "  (SELECT SUM(l.cost_usd) FROM llm_calls l WHERE l.task_id = runs.task_id), 0)")
            if migrate:
                db.execute(f"PRAGMA user_version = {DB_SCHEMA_VERSION}")
            db.commit()
    finally:
        db.close()

    verb = "Updated" if apply else "Would update"
    con.print(f"{verb} {len(changes)} of {len(rows)} llm_calls: "
              f"${before:.4f} -> ${after:.4f} ({after - before:+.4f})")
    if migrate:
        con.print(f"  cached-input split applied to {split} rows")
    con.print(f"  {verb.lower()} runs.cost_usd on {run_delta} runs (rebuilt from their calls)")
    if not apply:
        con.print("[dim]dry run - pass --apply to write[/]")


@app.command("seed")
def seed(task_ids: str = typer.Option("", help="Comma list of task ids; default: pick a spread automatically"),
         bench_id: str = typer.Option("", "--bench-id", help="Seed every run of this benchmark"),
         limit: int = typer.Option(12, help="How many runs to seed when picking automatically")):
    """Bake finished runs into benchmarks/seed/ so a cold deployed instance is never blank.

    The Dockerfile copies benchmarks/ into the image, and the web app installs the seed on
    startup when the data directory has no database yet.
    """
    import sqlite3

    from codefix.eval.seed import SEED_DIR, export_seed, pick_demo_runs

    ids = [t.strip() for t in task_ids.split(",") if t.strip()]
    if not ids and bench_id:
        with sqlite3.connect(config.DB_PATH) as c:
            # same exclusion as pick_demo_runs: a harness error is not an agent outcome
            ids = [r[0] for r in c.execute(
                "SELECT task_id FROM runs WHERE bench_id=? AND outcome IS NOT NULL"
                " AND outcome <> 'error' ORDER BY created_at", (bench_id,))]
        if not ids:
            con.print(f"[red]No runs found for bench_id {bench_id!r}[/]")
            raise typer.Exit(1)
    ids = ids or pick_demo_runs(limit)
    if not ids:
        con.print("[red]No finished non-mock runs to seed. Run `codefix demo` or `codefix bench` first.[/]")
        raise typer.Exit(1)
    counts = export_seed(ids)
    con.print(f"Seeded {len(ids)} runs -> {SEED_DIR}")
    for k, v in counts.items():
        con.print(f"  {k:12} {v}")


@app.command()
def graph(out: Path = typer.Option(config.ROOT / "docs")):
    """Export the architecture diagrams (docs/graph.png + per-architecture, Mermaid source)."""
    from codefix.graph.runner import export_graph_images

    for arch, p in export_graph_images(out).items():
        con.print(f"{arch}: {p}")


def main():  # pragma: no cover
    import sys

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    app()


if __name__ == "__main__":  # pragma: no cover
    main()
