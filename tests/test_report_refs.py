"""The report links its claims to the code (docs/report/code_refs.py). A link that lands on the
wrong line in front of an examiner is worse than no link, so every reference must resolve to
exactly one line - checked here, so a code change that breaks an anchor fails the suite instead
of silently producing a wrong link the next time the report is built."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "docs" / "report"))

from code_refs import REFS, RefError, resolve  # noqa: E402


@pytest.mark.parametrize("key", sorted(REFS))
def test_every_reference_resolves_to_exactly_one_line(key):
    path, line = resolve(key, ROOT)
    assert REFS[key][1] in (ROOT / path).read_text(encoding="utf-8").splitlines()[line - 1]


def test_every_link_in_the_report_names_a_known_reference():
    content = (ROOT / "docs" / "report" / "content.py").read_text(encoding="utf-8")
    used = set(re.findall(r"\[\[.+?\|([a-z0-9_]+)\]\]", content))
    assert used, "the report links no claims to code"
    unknown = used - set(REFS)
    assert not unknown, f"report links to undefined references: {sorted(unknown)}"


def test_an_ambiguous_anchor_is_refused(tmp_path, monkeypatch):
    (tmp_path / "f.py").write_text("x = 1\nx = 1\n", encoding="utf-8")
    monkeypatch.setitem(REFS, "_dup", ("f.py", "x = 1", "duplicate"))
    with pytest.raises(RefError, match="matches 2 lines"):
        resolve("_dup", tmp_path)
