"""Seed runs baked into the container image, so a cold instance is never a blank demo.

Cloud Run gives each instance a fresh `/tmp`, and that is where `runs.db` and the traces live
(`CODEFIX_DATA_DIR`). A cold start therefore shows an empty Runs list and an empty Dashboard —
fine for a service, bad in front of an examiner.

`export_seed` snapshots a chosen set of finished runs (every row that references them, plus
their JSONL traces) into `benchmarks/seed/`, which the Dockerfile already copies into the image.
`restore_seed` copies that into the data directory on startup *only when no database exists
yet*, so it can never overwrite real runs — including the ones made during the demo itself.
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from codefix import config

SEED_DIR = config.ROOT / "benchmarks" / "seed"
TABLES = ("runs", "artifacts", "messages", "llm_calls", "tool_calls", "evaluations")


def export_seed(task_ids: list[str], out_dir: Path | None = None, src_db: Path | None = None) -> dict:
    """Copy `task_ids` and everything referencing them from runs.db into a seed directory."""
    out = Path(out_dir or SEED_DIR)
    src = Path(src_db or config.DB_PATH)
    if not src.exists():
        raise FileNotFoundError(f"no database at {src}")
    if not task_ids:
        raise ValueError("refusing to build an empty seed")
    out.mkdir(parents=True, exist_ok=True)
    (out / "traces").mkdir(exist_ok=True)
    db = out / "runs.db"
    db.unlink(missing_ok=True)

    from codefix.blackboard.store import Blackboard

    Blackboard(db, out / "traces")  # create the schema (+ additive migrations) in the seed file
    counts: dict[str, int] = {}
    s, d = sqlite3.connect(src), sqlite3.connect(db)
    try:
        s.row_factory = sqlite3.Row
        marks = ",".join("?" * len(task_ids))
        for table in TABLES:
            rows = s.execute(f"SELECT * FROM {table} WHERE task_id IN ({marks})", task_ids).fetchall()
            if not rows:
                counts[table] = 0
                continue
            # only columns the seed schema also has, so an older source db still exports cleanly
            keep = [c for c in rows[0].keys()
                    if c in {r[1] for r in d.execute(f"PRAGMA table_info({table})")}]
            d.executemany(
                f"INSERT OR REPLACE INTO {table} ({','.join(keep)}) VALUES ({','.join('?' * len(keep))})",
                [tuple(r[c] for c in keep) for r in rows],
            )
            counts[table] = len(rows)
        d.commit()
        # The Blackboard runs in WAL mode, so these rows are still in runs.db-wal. The seed ships
        # as a single file copied with shutil, so fold the WAL back into the main database —
        # otherwise the seed arrives empty on the deployed instance.
        d.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        s.close()
        d.close()
    for stale in (db.with_name(db.name + "-wal"), db.with_name(db.name + "-shm")):
        stale.unlink(missing_ok=True)

    traces = 0
    for tid in task_ids:
        for f in config.TRACES_DIR.glob(f"{tid}*"):
            shutil.copy2(f, out / "traces" / f.name)
            traces += 1
    counts["traces"] = traces
    return counts


def restore_seed(data_dir: Path | None = None, seed_dir: Path | None = None) -> bool:
    """Install the seed into the data directory if it has no database yet. Returns True if it did."""
    data = Path(data_dir or config.DATA_DIR)
    seed = Path(seed_dir or SEED_DIR)
    db = data / "runs.db"
    if db.exists() or not (seed / "runs.db").exists():
        return False
    data.mkdir(parents=True, exist_ok=True)
    shutil.copy2(seed / "runs.db", db)
    if (seed / "traces").is_dir():
        dest = data / "traces"
        dest.mkdir(parents=True, exist_ok=True)
        for f in (seed / "traces").iterdir():
            if f.is_file():
                shutil.copy2(f, dest / f.name)
    return True


def pick_demo_runs(limit: int = 12, src_db: Path | None = None) -> list[str]:
    """A representative spread of finished live runs for the deployed dashboard.

    Three passes, so the dashboard shows variety *and* is actually full:
      1. retried / escalated runs first — the bounded self-correction loop is the point of the
         system, and a wall of first-attempt successes undersells it;
      2. one run per (architecture, outcome) so every architecture appears;
      3. fill the remaining slots, preferring bugs not already shown.
    """
    src = Path(src_db or config.DB_PATH)
    with sqlite3.connect(src) as c:
        c.row_factory = sqlite3.Row
        # outcome 'error' means the harness died (a killed process, a crashed sandbox), not
        # something the agents did. Seeding one shows a viewer a run with 0 attempts, 35 ms and
        # $0.00 against a repo path that does not exist in the container - it reads as a defect
        # in the system. 'escalated' is kept: that IS an agent outcome and worth showing.
        rows = c.execute(
            "SELECT task_id, arch, outcome, attempts, bug_id FROM runs "
            "WHERE llm_mode != 'mock' AND outcome IS NOT NULL AND outcome <> 'error' "
            "ORDER BY created_at DESC"
        ).fetchall()

    picked: list[str] = []
    taken: set[str] = set()

    def take(r) -> None:
        if r["task_id"] not in taken and len(picked) < limit:
            taken.add(r["task_id"])
            picked.append(r["task_id"])

    for r in rows:                                   # 1. interesting runs
        if (r["attempts"] or 1) > 1 or r["outcome"] != "passed":
            take(r)
    seen_keys: set[tuple] = set()
    for r in rows:                                   # 2. cover every architecture/outcome
        key = (r["arch"], r["outcome"])
        if key not in seen_keys:
            seen_keys.add(key)
            take(r)
    # 3. fill by round-robin over architectures, newest first, preferring bugs not yet shown.
    # Without the round-robin the fill just drains the most recent architecture and the dashboard
    # ends up looking like only one of them was ever run.
    by_arch: dict[str, list] = {}
    for r in rows:
        by_arch.setdefault(r["arch"], []).append(r)
    seen_bugs = {r["bug_id"] for r in rows if r["task_id"] in taken}
    for prefer_new_bug in (True, False):
        queues = {a: list(rs) for a, rs in by_arch.items()}
        while any(queues.values()) and len(picked) < limit:
            for arch in sorted(queues):
                while queues[arch]:
                    r = queues[arch].pop(0)
                    if prefer_new_bug and r["bug_id"] in seen_bugs:
                        continue
                    seen_bugs.add(r["bug_id"])
                    take(r)
                    break
    return picked[:limit]
