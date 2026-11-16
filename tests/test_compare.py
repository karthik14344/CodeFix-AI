"""Cross-benchmark comparison of prompt variants and personas (codefix/eval/compare.py).

The property that matters: a level must only ever be compared against baseline runs on the
SAME bugs. An unpaired comparison would silently attribute a difficulty difference between bug
sets to the prompt variant.
"""

from __future__ import annotations

from codefix.eval.compare import compare, markdown


def _run(bug, *, variant="react", persona="default", reporter="developer",
         arch="hierarchical", resolved=True, secs=60.0, cost=0.02, ref_exact=1):
    return {
        "task_id": f"{bug}-{variant}-{persona}-{reporter}-{secs}", "bench_id": "b",
        "bug_id": bug, "arch": arch, "outcome": "passed" if resolved else "escalated",
        "attempts": 1, "duration_ms": secs * 1000, "cost_usd": cost,
        "tokens": 9000, "calls": 4, "diagnoser_ms": 25000,
        "objective_pass": 1 if resolved else 0, "ref_exact": ref_exact,
        "ref_similarity": 0.95, "ref_file_match": 1, "verdict": "pass", "agreement": 1,
        "variant": variant, "persona": persona, "reporter": reporter,
    }


def test_levels_are_paired_on_the_same_bugs():
    """Baseline covers 3 bugs; the swept level covers 2. Only those 2 may be compared."""
    rows = [_run("bugA"), _run("bugB"), _run("bugC", secs=999.0)]          # baseline, 3 bugs
    rows += [_run("bugA", variant="fewshot"), _run("bugB", variant="fewshot")]

    out = compare("variant", rows)

    assert out["bugs"] == ["bugA", "bugB"]
    assert out["levels"]["react (baseline)"]["n"] == 2, "bugC must be excluded from the baseline"
    assert out["levels"]["fewshot"]["n"] == 2
    # the 999s outlier belongs to the excluded bug, so it must not reach the baseline mean
    assert out["levels"]["react (baseline)"]["secs"] == 60.0


def test_baseline_repetitions_are_all_counted():
    rows = [_run("bugA", secs=50.0), _run("bugA", secs=70.0),          # two baseline reps
            _run("bugA", variant="fewshot", secs=100.0)]

    out = compare("variant", rows)

    assert out["levels"]["react (baseline)"]["n"] == 2
    assert out["levels"]["react (baseline)"]["secs"] == 60.0
    assert out["levels"]["fewshot"]["secs"] == 100.0


def test_a_level_needs_every_other_factor_at_baseline():
    """A fewshot run that ALSO changed persona says nothing about fewshot alone."""
    rows = [_run("bugA"), _run("bugA", variant="fewshot", persona="senior")]

    out = compare("variant", rows)

    assert out["levels"] == {} or "fewshot" not in out["levels"]


def test_persona_and_reporter_factors_are_isolated():
    rows = [_run("bugA"), _run("bugA", persona="senior"), _run("bugA", reporter="enduser")]

    assert "senior" in compare("persona", rows)["levels"]
    assert "enduser" in compare("reporter", rows)["levels"]
    # varying persona must not show up as a reporter level, or vice versa
    assert "senior" not in compare("reporter", rows)["levels"]
    assert "enduser" not in compare("persona", rows)["levels"]


def test_other_architectures_are_excluded():
    rows = [_run("bugA"), _run("bugA", variant="fewshot"),
            _run("bugA", variant="fewshot", arch="p2p", secs=999.0)]

    out = compare("variant", rows)

    assert out["levels"]["fewshot"]["n"] == 1
    assert out["levels"]["fewshot"]["secs"] == 60.0


def test_markdown_renders_without_runs():
    assert "No runs found" in markdown({"factor": "variant", "levels": {}, "bugs": []})


def test_markdown_includes_every_level_and_the_paired_bug_list():
    rows = [_run("bugA"), _run("bugA", variant="fewshot"),
            _run("bugA", variant="react-reflect")]

    md = markdown(compare("variant", rows))

    assert "react (baseline)" in md and "fewshot" in md and "react-reflect" in md
    assert "bugA" in md and "Resolved" in md


def test_harness_errors_are_excluded_by_the_loader(tmp_path, monkeypatch):
    """A run killed mid-flight (outcome 'error') is not an agent failure and must not lower a
    level's resolve rate. Regression: one cancelled run scored few-shot at 82% instead of 90%."""
    from codefix.blackboard.store import Blackboard
    from codefix.eval.compare import _load

    bb = Blackboard(tmp_path / "runs.db", tmp_path / "traces")
    for tid, outcome in (("done", "passed"), ("killed", "error")):
        bb.create_run(tid, bug_report="r", repo="/repo", arch="hierarchical", max_attempts=3,
                      llm_mode="live", meta={"variant": "fewshot"})
        bb.update_run(tid, status="done", outcome=outcome)

    ids = {r["task_id"] for r in _load(tmp_path / "runs.db")}

    assert "killed" not in ids
    assert "done" in ids
