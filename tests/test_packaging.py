"""What actually reaches the deployed image.

Regression guard for a bug that cost a whole deployment: `.gcloudignore` uses gitignore
semantics, where a pattern without a leading slash matches at EVERY directory level. A bare
`tests/` therefore excluded `benchmarks/bugset/repos/pyshop/tests/` — the sample repo's own
suite, which the Tester agent exists to run — so every Python bug returned "0 tests" and
escalated on Cloud Run while passing locally. The JS repo survived only because its directory
happens to be named `test/`, singular, which is exactly what made the deployment look healthy.

A bare `runs.db*` / `traces/` likewise excluded `benchmarks/seed/`, the demo runs that stop a
cold instance's dashboard from being empty.
"""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _patterns(name: str) -> list[str]:
    text = (ROOT / name).read_text(encoding="utf-8")
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]


def _excluded(patterns: list[str], path: str) -> bool:
    """Approximate gitignore matching for the cases these files actually use."""
    parts = path.split("/")
    for pat in patterns:
        p = pat.rstrip("/")
        if p.startswith("/"):                      # anchored: must match from the root
            anchor = p.lstrip("/")
            if path == anchor or path.startswith(anchor + "/"):
                return True
            if fnmatch(parts[0], anchor):
                return True
        elif p.startswith("**/"):
            if p[3:] in parts:
                return True
        elif "/" not in p:                         # unanchored: matches at ANY level
            if any(fnmatch(seg, p) for seg in parts):
                return True
    return False


@pytest.mark.parametrize("ignore_file", [".gcloudignore", ".dockerignore"])
@pytest.mark.parametrize("needed", [
    "benchmarks/bugset/repos/pyshop/tests/test_pricing.py",   # the Tester runs this suite
    "benchmarks/bugset/repos/textkit/test/text.test.js",
    "benchmarks/bugset/bugs.yaml",
    "benchmarks/seed/runs.db",                                # dashboard demo data
    "benchmarks/seed/traces/x.jsonl",
    "config/models.yaml",
    "codefix/llm.py",
    "docs/graph.png",                                         # served by /api/graph
])
def test_files_the_image_needs_are_not_excluded(ignore_file, needed):
    assert not _excluded(_patterns(ignore_file), needed), (
        f"{ignore_file} excludes {needed}, which the deployed image needs"
    )


@pytest.mark.parametrize("ignore_file", [".gcloudignore", ".dockerignore"])
@pytest.mark.parametrize("secret", [
    ".env",
    ".venv/lib/python3.11/site-packages/x.py",
    "runs.db",
    "traces/20261115.jsonl",
    "tests/test_llm.py",          # our own suite stays out of the image
    "codefix/__pycache__/llm.cpython-311.pyc",
    "docs/report/CodeFix_AI_Final_Report.pdf",                # deliverables, not runtime
    "docs/slides/CodeFix_AI_Final_Presentation.pptx",
    "docs/slides/~$CodeFix_AI_Final_Presentation.pptx",       # Office lock file: gcloud crashed on it
])
def test_local_state_and_secrets_are_still_excluded(ignore_file, secret):
    assert _excluded(_patterns(ignore_file), secret), (
        f"{ignore_file} no longer excludes {secret}"
    )


def test_the_sample_repos_really_do_use_different_test_directory_names():
    """The asymmetry that hid the bug. If this ever changes, the guard above is less load-bearing
    than it looks — but the anchored patterns protect both spellings either way."""
    repos = ROOT / "benchmarks" / "bugset" / "repos"
    assert (repos / "pyshop" / "tests").is_dir()
    assert (repos / "textkit" / "test").is_dir()
