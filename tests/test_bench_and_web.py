"""Benchmark harness, judge/objective check and the web API — all with the offline oracle mock."""

import time

import pytest

pytestmark = pytest.mark.usefixtures("isolated")


def test_bugset_loads_and_fix_reverses_injection():
    from codefix.eval.bugset import REPOS_DIR, load_bugs

    bugs = load_bugs()
    assert len(bugs) >= 14 and len({b.id for b in bugs}) == len(bugs)
    # every bug names a repository that actually exists, and every injected file is in it.
    # (Asserting a fixed set of repo names instead would just need editing each time a repo is
    # added, without checking anything the loader could get wrong.)
    for b in bugs:
        assert (REPOS_DIR / b.repo).is_dir(), f"{b.id} names missing repo {b.repo}"
        for f in b.files:
            assert (REPOS_DIR / b.repo / f).is_file(), f"{b.id} injects into missing file {f}"
    b = load_bugs(["py08"])[0]
    assert b.fix_edits[0]["find"] == b.inject[-1]["replace"]


def test_bench_end_to_end_mock(isolated, monkeypatch):
    from codefix.eval import bench

    monkeypatch.setattr(bench, "BENCH_DIR", isolated / "bench")
    monkeypatch.setattr(bench, "RESULTS_DIR", isolated / "results")
    out = bench.run_bench(["hierarchical", "sequential"], bug_ids=["py04"], llm_mode="mock", progress=lambda m: None)
    rows = bench.bench_rows(out["bench_id"])
    assert len(rows) == 2 and all(r["llm_mode"] == "mock" for r in rows)
    hier = next(r for r in rows if r["arch"] == "hierarchical")
    assert hier["outcome"] == "passed" and hier["attempts"] == 2  # oracle fails first, Manager retries
    assert hier["objective_pass"] == 1 and hier["target_test_pass"] == 1 and hier["agreement"] == 1
    seq = next(r for r in rows if r["arch"] == "sequential")
    assert seq["attempts"] == 2  # restarted from scratch, then passed
    report = open(out["report"], encoding="utf-8").read()
    assert "MOCK RUN" in report and "Judge accuracy" in report
    assert open(out["csv"], encoding="utf-8").readline().startswith("bench_id,task_id")


def test_objective_check_detects_bad_patch(isolated):
    from codefix.eval.bugset import known_fix_diff, load_bugs, materialize
    from codefix.eval.judge import objective_check

    bug = load_bugs(["py10"])[0]
    repo = materialize(bug, isolated / "repo")
    good = objective_check(repo, isolated / "sb", known_fix_diff(bug, repo), bug, "ok1")
    assert good["objective_pass"] and good["target_test_pass"]
    # reference-text evaluation: the known-good fix matches the reference exactly
    assert good["ref_exact"] == 1 and good["ref_similarity"] == 1.0 and good["ref_file_match"] == 1
    bad = objective_check(repo, isolated / "sb", "", bug, "bad1")
    assert not bad["objective_pass"] and bad["ref_exact"] == 0 and bad["ref_similarity"] == 0.0


def test_a2a_bearer_token_required(monkeypatch):
    from fastapi.testclient import TestClient

    from codefix.crew_side.a2a_server import build_app

    monkeypatch.setenv("CODEFIX_A2A_TOKEN", "s3cret")
    c = TestClient(build_app("http://x/"))
    assert c.get("/.well-known/agent-card.json").status_code == 200  # discovery stays public
    assert c.post("/", json={"jsonrpc": "2.0", "id": 1, "method": "SendMessage", "params": {}}).status_code == 401
    ok = c.post("/", json={"jsonrpc": "2.0", "id": 1, "method": "SendMessage", "params": {}},
                headers={"Authorization": "Bearer s3cret"})
    assert ok.status_code != 401


def test_web_api_flow():
    from fastapi.testclient import TestClient

    from web.api.app import app

    c = TestClient(app)
    cfg = c.get("/api/config").json()
    assert "hierarchical" in cfg["archs"] and cfg["models"]["judge"]["model"]
    assert c.post("/api/runs", json={"bug_report": "x", "repo": ".", "llm": "mock"}).status_code == 400
    tid = c.post("/api/runs", json={"bug_id": "js02-truncate-length", "llm": "mock", "arch": "p2p"}).json()["task_id"]
    for _ in range(240):
        run = c.get(f"/api/runs/{tid}").json()
        if run["run"]["status"] != "running":
            break
        time.sleep(0.5)
    assert run["run"]["status"] == "awaiting_approval", run["run"]
    assert run["spans"] and run["react"] and len(run["patches"]) == 2
    events = c.get(f"/api/runs/{tid}/events").text
    assert "run_finished" in events and "event: done" in events
    src = c.get(f"/api/runs/{tid}/source", params={"path": "src/text.js", "start": 1, "end": 5}).json()
    assert len(src["lines"]) == 5
    assert c.get(f"/api/runs/{tid}/source", params={"path": "../../etc/passwd"}).status_code == 400
    assert c.post(f"/api/runs/{tid}/pr", json={"confirm": False}).json()["status"] == "done"
    assert c.post(f"/api/runs/{tid}/pr", json={"confirm": True}).status_code == 409  # already resolved
    dash = c.get("/api/dashboard", params={"llm_mode": "mock"}).json()
    assert dash["runs"] and dash["localisation"]["p2p"]["hit"] == 1
    assert any(r["task_id"] == tid for r in c.get("/api/runs").json())
