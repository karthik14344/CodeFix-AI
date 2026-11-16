"""Compare a factor's non-default levels against the main benchmark's baseline arm.

The architecture benchmark already contains, for every bug, the
`hierarchical / react / default / developer` arm. Re-running it inside every prompt or persona
sweep would be paying twice for the same measurement, so the sweeps vary one factor at a time
and this module joins them back to that baseline.

The comparison is **paired**: a level is only compared on bugs the baseline also covers, and the
baseline's repetitions are averaged per bug first, so one sweep run is compared against the mean
of three baseline runs for the same bug rather than against a single sample.
"""

from __future__ import annotations

import json
import sqlite3
import statistics as st
from collections import defaultdict
from pathlib import Path

from codefix import config

BASELINE = {"arch": "hierarchical", "variant": "react", "persona": "default",
            "reporter": "developer"}

SQL = """
SELECT r.task_id, r.bench_id, r.bug_id, r.arch, r.outcome, r.attempts, r.duration_ms,
       r.cost_usd, r.meta,
       (SELECT COALESCE(SUM(input_tokens+output_tokens),0) FROM llm_calls l
          WHERE l.task_id=r.task_id AND l.agent<>'judge') AS tokens,
       (SELECT COUNT(*) FROM llm_calls l WHERE l.task_id=r.task_id AND l.agent<>'judge') AS calls,
       (SELECT COALESCE(SUM(latency_ms),0) FROM messages m
          WHERE m.task_id=r.task_id AND m.sender='diagnoser' AND m.status IN ('success','failure'))
          AS diagnoser_ms,
       e.objective_pass, e.ref_exact, e.ref_similarity, e.ref_file_match, e.verdict, e.agreement
FROM runs r LEFT JOIN evaluations e ON e.task_id = r.task_id
WHERE r.llm_mode <> 'mock' AND r.outcome IS NOT NULL AND r.outcome <> 'error'
"""
# outcome 'error' is the harness dying (a killed process, a crashed tool server), not something
# the agents did. Counting one scored a cancelled run as a few-shot failure and pulled that
# variant's resolve rate from 90% to 82%.


def _load(db: Path | None = None) -> list[dict]:
    con = sqlite3.connect(db or config.DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        out = []
        for r in con.execute(SQL):
            d = dict(r)
            meta = json.loads(d.pop("meta") or "{}")
            d["variant"] = meta.get("variant", "react")
            d["persona"] = meta.get("persona", "default")
            d["reporter"] = meta.get("reporter", "developer")
            out.append(d)
        return out
    finally:
        con.close()


def _is_baseline(r: dict, factor: str) -> bool:
    """Baseline on every dimension, including the factor under test."""
    return all(r[k] == v for k, v in BASELINE.items())


def _cell(runs: list[dict]) -> dict:
    n = len(runs)
    if not n:
        return {}
    return {
        "n": n,
        "resolved": sum(1 for r in runs if r["objective_pass"]),
        "resolved_pct": 100 * sum(1 for r in runs if r["objective_pass"]) / n,
        "ref_exact_pct": 100 * sum(1 for r in runs if r["ref_exact"]) / n,
        "ref_sim": st.mean([r["ref_similarity"] or 0 for r in runs]),
        "right_file_pct": 100 * sum(1 for r in runs if r["ref_file_match"]) / n,
        "secs": st.mean([(r["duration_ms"] or 0) / 1000 for r in runs]),
        "diag_s": st.mean([(r["diagnoser_ms"] or 0) / 1000 for r in runs]),
        "cost": st.mean([r["cost_usd"] or 0 for r in runs]),
        "tokens": st.mean([r["tokens"] or 0 for r in runs]),
        "calls": st.mean([r["calls"] or 0 for r in runs]),
        "attempts": st.mean([r["attempts"] or 1 for r in runs]),
    }


def compare(factor: str, rows: list[dict] | None = None) -> dict:
    """Compare each level of `factor` ('variant' | 'persona' | 'reporter') to the baseline.

    Only bugs that the sweep covers are used, and only baseline runs for those same bugs, so
    every level is scored on an identical bug set.
    """
    rows = rows if rows is not None else _load()
    rows = [r for r in rows if r["arch"] == BASELINE["arch"]]

    levels: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        # a run belongs to a non-default level only if every OTHER factor is at baseline
        others = [k for k in BASELINE if k not in ("arch", factor)]
        if all(r[k] == BASELINE[k] for k in others):
            levels[r[factor]].append(r)

    base_level = BASELINE[factor]
    tested = {lv: rs for lv, rs in levels.items() if lv != base_level and rs}
    if not tested:
        return {"factor": factor, "levels": {}, "bugs": []}

    bugs = sorted({r["bug_id"] for rs in tested.values() for r in rs})
    baseline_runs = [r for r in levels.get(base_level, []) if r["bug_id"] in bugs]

    out = {"factor": factor, "bugs": bugs, "levels": {}}
    out["levels"][f"{base_level} (baseline)"] = _cell(baseline_runs)
    for lv, rs in sorted(tested.items()):
        out["levels"][lv] = _cell([r for r in rs if r["bug_id"] in bugs])
    return out


def markdown(cmp: dict) -> str:
    """Render one comparison as a Markdown table."""
    if not cmp["levels"]:
        return f"_No runs found for factor `{cmp['factor']}`._\n"
    levels = list(cmp["levels"])
    metrics = [
        ("Runs", lambda c: str(c["n"])),
        ("Resolved", lambda c: f"{c['resolved']}/{c['n']} ({c['resolved_pct']:.0f}%)"),
        ("Right file(s) changed", lambda c: f"{c['right_file_pct']:.0f}%"),
        ("Matches reference exactly", lambda c: f"{c['ref_exact_pct']:.0f}%"),
        ("Edit similarity (0-1)", lambda c: f"{c['ref_sim']:.2f}"),
        ("Mean wall-clock", lambda c: f"{c['secs']:.1f}s"),
        ("Diagnoser time", lambda c: f"{c['diag_s']:.1f}s"),
        ("Mean LLM calls", lambda c: f"{c['calls']:.1f}"),
        ("Mean tokens", lambda c: f"{c['tokens']:.0f}"),
        ("Mean cost / run", lambda c: f"${c['cost']:.4f}"),
    ]
    head = f"| Metric | {' | '.join(levels)} |\n|---|{'---|' * len(levels)}\n"
    body = "".join(
        f"| {name} | " + " | ".join(fn(cmp['levels'][lv]) for lv in levels) + " |\n"
        for name, fn in metrics)
    note = (f"\n_Paired on {len(cmp['bugs'])} bugs: "
            f"{', '.join(cmp['bugs'])}._\n")
    return head + body + note


def report(path: Path | None = None) -> str:
    rows = _load()
    parts = ["# Prompt variant and persona comparison\n",
             "Each level is compared against the `hierarchical / react / default / developer` "
             "baseline drawn from the main architecture benchmark, on the same bugs. Baseline "
             "repetitions are averaged per bug before comparison.\n"]
    for factor, title in (("variant", "Prompt variant"),
                          ("persona", "Agent persona"),
                          ("reporter", "Reporter persona (who filed the bug report)")):
        parts.append(f"\n## {title}\n")
        parts.append(markdown(compare(factor, rows)))
    text = "".join(parts)
    if path:
        Path(path).write_text(text, encoding="utf-8")
    return text
