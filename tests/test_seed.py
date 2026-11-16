"""Seed runs baked into the image for cold deployed instances (codefix/eval/seed.py).

The safety property that matters: restoring a seed must never destroy real run data.
"""

from __future__ import annotations

import sqlite3

import pytest

from codefix.eval.seed import export_seed, restore_seed


def _db_with_runs(path, task_ids, traces_dir=None):
    from codefix.blackboard.store import Blackboard

    bb = Blackboard(path, traces_dir or path.parent / "traces")
    for tid in task_ids:
        bb.create_run(tid, bug_report=f"report {tid}", repo="/repo", arch="hierarchical",
                      max_attempts=3, llm_mode="live")
        bb.update_run(tid, status="done", outcome="passed")
        if traces_dir:
            traces_dir.mkdir(parents=True, exist_ok=True)
            (traces_dir / f"{tid}.jsonl").write_text('{"event":"run_start"}\n', encoding="utf-8")
    return bb


def test_export_then_restore_round_trips(tmp_path, monkeypatch):
    from codefix import config

    src = tmp_path / "src"
    src.mkdir()
    monkeypatch.setattr(config, "TRACES_DIR", src / "traces")
    _db_with_runs(src / "runs.db", ["t1", "t2"], src / "traces")

    seed = tmp_path / "seed"
    counts = export_seed(["t1", "t2"], out_dir=seed, src_db=src / "runs.db")
    assert counts["runs"] == 2 and counts["traces"] == 2

    data = tmp_path / "data"
    assert restore_seed(data_dir=data, seed_dir=seed) is True
    with sqlite3.connect(data / "runs.db") as c:
        assert {r[0] for r in c.execute("SELECT task_id FROM runs")} == {"t1", "t2"}
    assert (data / "traces" / "t1.jsonl").exists()


def test_restore_refuses_to_overwrite_an_existing_database(tmp_path, monkeypatch):
    """The demo's own runs must survive. A seed only installs into an empty data directory."""
    from codefix import config

    src = tmp_path / "src"
    src.mkdir()
    monkeypatch.setattr(config, "TRACES_DIR", src / "traces")
    _db_with_runs(src / "runs.db", ["seeded"], src / "traces")
    seed = tmp_path / "seed"
    export_seed(["seeded"], out_dir=seed, src_db=src / "runs.db")

    data = tmp_path / "data"
    data.mkdir()
    _db_with_runs(data / "runs.db", ["real-run-from-the-demo"])

    assert restore_seed(data_dir=data, seed_dir=seed) is False
    with sqlite3.connect(data / "runs.db") as c:
        ids = {r[0] for r in c.execute("SELECT task_id FROM runs")}
    assert ids == {"real-run-from-the-demo"}, "restoring a seed destroyed real runs"


def test_restore_is_a_no_op_without_a_seed(tmp_path):
    assert restore_seed(data_dir=tmp_path / "data", seed_dir=tmp_path / "missing") is False


def test_export_refuses_an_empty_seed(tmp_path, monkeypatch):
    from codefix import config

    src = tmp_path / "src"
    src.mkdir()
    monkeypatch.setattr(config, "TRACES_DIR", src / "traces")
    _db_with_runs(src / "runs.db", ["t1"], src / "traces")

    with pytest.raises(ValueError, match="empty seed"):
        export_seed([], out_dir=tmp_path / "seed", src_db=src / "runs.db")


def test_export_only_takes_the_requested_runs(tmp_path, monkeypatch):
    from codefix import config

    src = tmp_path / "src"
    src.mkdir()
    monkeypatch.setattr(config, "TRACES_DIR", src / "traces")
    _db_with_runs(src / "runs.db", ["keep", "drop"], src / "traces")

    seed = tmp_path / "seed"
    export_seed(["keep"], out_dir=seed, src_db=src / "runs.db")

    with sqlite3.connect(seed / "runs.db") as c:
        assert {r[0] for r in c.execute("SELECT task_id FROM runs")} == {"keep"}
    assert not (seed / "traces" / "drop.jsonl").exists()


def test_harness_errors_are_never_seeded(tmp_path, monkeypatch):
    """outcome 'error' means the harness died, not something the agents did.

    A seeded error run shows a viewer 0 attempts, ~35ms, $0.00 and a repo path that does not
    exist in the container - it reads as a defect in the system. 'escalated' is a real agent
    outcome and must still be seeded.
    """
    from codefix import config
    from codefix.blackboard.store import Blackboard
    from codefix.eval.seed import pick_demo_runs

    src = tmp_path / "src"
    src.mkdir()
    monkeypatch.setattr(config, "TRACES_DIR", src / "traces")
    bb = Blackboard(src / "runs.db", src / "traces")
    for tid, outcome in (("ok", "passed"), ("boom", "error"), ("gaveup", "escalated")):
        bb.create_run(tid, bug_report="r", repo="/repo", arch="hierarchical",
                      max_attempts=3, llm_mode="live")
        bb.update_run(tid, status="done", outcome=outcome)

    picked = pick_demo_runs(limit=10, src_db=src / "runs.db")

    assert "boom" not in picked, "a harness error was seeded as demo data"
    assert {"ok", "gaveup"} <= set(picked), "escalated runs should still be seeded"
