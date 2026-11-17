"""Build the Final Project Report (.docx -> .pdf) from the template in Final_Report_Format.pdf.

Run:  python docs/report/build_report.py [--pdf]

Everything quantitative is read from the repo at build time - the benchmark CSV, the live
`config/models.yaml`, the MCP server's tool list, the A2A agent card - so the report cannot
drift from the system it describes. Prose lives in `content.py`.
"""

from __future__ import annotations

import argparse
import csv
import re
import statistics as st
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
OUT_DIR = ROOT / "docs" / "report"
BENCH_ID = "bench-20261115-180308"

ACCENT = RGBColor(0x1F, 0x3B, 0x63)
MONO = "Consolas"


# --------------------------------------------------------------------------- data


def bench_rows() -> list[dict]:
    """Completed runs of the architecture experiment.

    A row with no outcome is a run that was still in flight when the benchmark process was
    killed (the session ended at run 140 of 144). It has no duration, no judge verdict and no
    re-test, so counting it would score an interrupted run as an agent failure - which is how
    "sequential: 46/47, one JS bug unresolved" crept into an earlier draft. It is excluded here
    and disclosed in the text instead.
    """
    p = ROOT / "benchmarks" / "results" / BENCH_ID / "runs.csv"
    with p.open(encoding="utf-8", newline="") as f:
        return [r for r in csv.DictReader(f) if (r.get("outcome") or "").strip()]


def interrupted_runs() -> int:
    p = ROOT / "benchmarks" / "results" / BENCH_ID / "runs.csv"
    with p.open(encoding="utf-8", newline="") as f:
        return sum(1 for r in csv.DictReader(f) if not (r.get("outcome") or "").strip())


def study_totals() -> dict:
    """Every live run across all five experiments, from runs.db - not just the architecture CSV.

    Categories are kept separate rather than folded into one percentage, because each means
    something different: a harness error is not an agent failure, and an ungraded demo run is
    not a resolved one.
    """
    import sqlite3

    from codefix import config

    con = sqlite3.connect(config.DB_PATH)
    try:
        q = lambda s: con.execute(s).fetchone()  # noqa: E731
        live = "r.llm_mode <> 'mock' AND r.outcome IS NOT NULL"
        recorded = q(f"SELECT COUNT(*) FROM runs r WHERE {live}")[0]
        harness_err = q(f"SELECT COUNT(*) FROM runs r WHERE {live} AND r.outcome = 'error'")[0]
        base = (f"FROM runs r LEFT JOIN evaluations e USING(task_id) "
                f"WHERE {live} AND r.outcome <> 'error'")
        agent_runs, graded, resolved, exact, agree, cost = q(
            "SELECT COUNT(*), SUM(e.verdict IS NOT NULL), SUM(e.objective_pass = 1),"
            f" SUM(e.ref_exact = 1), SUM(e.agreement = 1), SUM(r.cost_usd) {base}")
        bugs = q(f"SELECT COUNT(DISTINCT r.bug_id) {base} AND r.bug_id IS NOT NULL")[0]
        unresolved = con.execute(
            "SELECT r.bug_id, r.meta, e.objective_pass FROM runs r JOIN evaluations e "
            f"USING(task_id) WHERE {live} AND r.outcome <> 'error' AND e.objective_pass = 0"
        ).fetchall()
        by_bench = dict(con.execute(
            f"SELECT COALESCE(r.bench_id, ''), COUNT(*) FROM runs r WHERE {live} "
            "GROUP BY r.bench_id").fetchall())
    finally:
        con.close()
    # The five reported experiments, by benchmark id. Everything else is accounted for
    # explicitly as "other" rather than silently folded into a total that does not add up.
    experiments = {"architecture": BENCH_ID, "variant": "bench-20261116-171853",
                   "persona": "bench-20261116-174417", "reporter": "bench-20261116-175942",
                   "own_code": "bench-20261116-183335"}
    exp_counts = {k: by_bench.get(v, 0) for k, v in experiments.items()}
    other = {
        "pilot": by_bench.get("bench-20261115-180009", 0),          # live smoke test of bench
        "cancelled": by_bench.get("bench-20261116-163728", 0)       # partial runs from the
                     + by_bench.get("bench-20261116-164231", 0),    # oversized sweep, cancelled
        "demos": by_bench.get("", 0),                               # ad-hoc end-to-end demos
    }
    return {"recorded": recorded, "harness_errors": harness_err, "agent_runs": agent_runs,
            "graded": graded or 0, "ungraded": agent_runs - (graded or 0),
            "resolved": resolved or 0, "unresolved": len(unresolved),
            "exact": exact or 0, "agree": agree or 0, "cost": cost or 0.0, "bugs": bugs,
            "interrupted": interrupted_runs(), "experiments": exp_counts, "other": other}


def num(row: dict, key: str, default=0.0) -> float:
    v = row.get(key)
    try:
        return float(v) if v not in (None, "") else default
    except (TypeError, ValueError):
        return default


def by_arch(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        out[r["arch"]].append(r)
    return dict(sorted(out.items()))


def arch_stats(rows: list[dict]) -> dict[str, dict]:
    stats = {}
    for arch, rs in by_arch(rows).items():
        n = len(rs)
        durs = [num(r, "duration_ms") / 1000 for r in rs if num(r, "duration_ms")]
        judged = [r for r in rs if r.get("judge_verdict")]
        stats[arch] = {
            "n": n,
            "resolved": sum(1 for r in rs if r.get("objective_pass") in ("1", "True", "true")),
            "judge_pass": sum(1 for r in judged if r["judge_verdict"] == "pass"),
            "judged": len(judged),
            "agree": sum(1 for r in judged if r.get("agreement") in ("1", "True", "true")),
            "ref_exact": sum(1 for r in rs if r.get("ref_exact") in ("1", "True", "true")),
            "ref_sim": st.mean([num(r, "ref_similarity") for r in rs]) if n else 0,
            "secs": st.mean(durs) if durs else 0,
            "sd": st.pstdev(durs) if len(durs) > 1 else 0,
            "cost": sum(num(r, "pipeline_cost_usd") for r in rs),
            "tokens": st.mean([num(r, "tokens") for r in rs]) if n else 0,
            "calls": st.mean([num(r, "llm_calls") for r in rs]) if n else 0,
            "bytes": st.mean([num(r, "avg_msg_bytes") for r in rs]) if n else 0,
            "retried": sum(1 for r in rs if num(r, "attempts") > 1),
            "diag_s": st.mean([num(r, "diagnoser_ms") / 1000 for r in rs]) if n else 0,
            "fix_s": st.mean([num(r, "fixer_ms") / 1000 for r in rs]) if n else 0,
            "test_s": st.mean([num(r, "tester_ms") / 1000 for r in rs]) if n else 0,
            "pr_s": st.mean([num(r, "pr_ms") / 1000 for r in rs]) if n else 0,
        }
    return stats


def live_facts() -> dict:
    """Pull facts from the running code so the report cannot contradict it."""
    from codefix import config
    from codefix.agents.diagnoser import TOOLS as DIAG_TOOLS
    from codefix.crew_side.a2a_server import agent_card
    from mcp_server import server

    s = config.load_settings()
    tools = [n for n in dir(server)
             if not n.startswith("_") and callable(getattr(server, n, None))
             and getattr(getattr(server, n), "__module__", "") == server.__name__]
    return {
        "provider": s.provider,
        "roles": {k: s.role(k) for k in ("manager", "diagnoser", "fixer", "judge")},
        "pipeline": s.pipeline,
        "n_tools": len(tools) - 2,          # ctx, main
        "diag_tools": DIAG_TOOLS,
        "a2a_skills": [sk.id for sk in agent_card("http://x/").skills],
        "study": study_totals(),
    }


# --------------------------------------------------------------------------- docx helpers


def style_doc(doc: Document) -> None:
    n = doc.styles["Normal"]
    n.font.name = "Cambria"
    n.font.size = Pt(11)
    n.paragraph_format.space_after = Pt(6)
    n.paragraph_format.line_spacing = 1.15
    for i, size in ((1, 16), (2, 13), (3, 11.5)):
        h = doc.styles[f"Heading {i}"]
        h.font.name = "Cambria"
        h.font.size = Pt(size)
        h.font.color.rgb = ACCENT
        h.font.bold = True
        h.paragraph_format.space_before = Pt(14 if i == 1 else 10)
        h.paragraph_format.space_after = Pt(4)


# --------------------------------------------------------------------------- code links
#
# A claim in the prose is written  [[visible text|key]] . It renders as a hyperlink to the code
# that proves it, followed by a small grey "path:line" so the location is readable on paper too.
# The target depends on the build:
#   vscode  ->  vscode://file/<absolute path>:<line>:1   opens VS Code at the line (viva copy)
#   github  ->  https://github.com/<repo>/blob/<commit>/<path>#L<line>   (submission copy)

LINK_RE = re.compile(r"\[\[(.+?)\|([a-z0-9_]+)\]\]")
LINKS = {"mode": "vscode", "sha": None, "used": {}}       # used: key -> (path, line)
LINK_COLOR = RGBColor(0x1F, 0x5F, 0xB0)
LOC_COLOR = RGBColor(0x80, 0x80, 0x80)


def link_target(key: str) -> tuple[str, str, int]:
    from code_refs import resolve

    path, line = resolve(key, ROOT)
    LINKS["used"][key] = (path, line)
    if LINKS["mode"] == "github":
        url = f"https://github.com/Abhiram12062005/AGAI/blob/{LINKS['sha']}/{path}#L{line}"
    else:
        url = f"vscode://file/{(ROOT / path).as_posix()}:{line}:1"
    return url, path, line


def add_hyperlink(paragraph, url: str, text: str, *, size: float, bold=False, italic=False,
                  mono=False, color=LINK_COLOR, underline=True) -> None:
    from docx.opc.constants import RELATIONSHIP_TYPE as RT

    r_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    if mono:
        fonts = OxmlElement("w:rFonts")
        for a in ("w:ascii", "w:hAnsi", "w:cs"):
            fonts.set(qn(a), MONO)
        rpr.append(fonts)
    for flag, tag in ((bold, "w:b"), (italic, "w:i")):
        if flag:
            rpr.append(OxmlElement(tag))
    c = OxmlElement("w:color")
    c.set(qn("w:val"), f"{color[0]:02X}{color[1]:02X}{color[2]:02X}")
    rpr.append(c)
    if underline:
        u = OxmlElement("w:u")
        u.set(qn("w:val"), "single")
        rpr.append(u)
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), str(int(round(size * 2))))
    rpr.append(sz)
    run.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    run.append(t)
    link.append(run)
    paragraph._p.append(link)


def emit(p, text: str, *, size: float, bold=False, italic=False, mono=False, color=None) -> None:
    """Write `text` into paragraph `p`, turning [[text|key]] into a link to the code."""
    pos = 0
    for m in LINK_RE.finditer(text):
        if m.start() > pos:
            _plain(p, text[pos:m.start()], size=size, bold=bold, italic=italic, mono=mono,
                   color=color)
        url, path, line = link_target(m.group(2))
        add_hyperlink(p, url, m.group(1), size=size, bold=bold, italic=italic, mono=mono)
        add_hyperlink(p, url, f"  {path}:{line}", size=max(size - 3, 6.5), mono=True,
                      color=LOC_COLOR, underline=False)
        pos = m.end()
    if pos < len(text):
        _plain(p, text[pos:], size=size, bold=bold, italic=italic, mono=mono, color=color)


def _plain(p, text, *, size, bold, italic, mono, color):
    r = p.add_run(text)
    r.bold, r.italic = bold, italic
    r.font.size = Pt(size)
    if mono:
        r.font.name = MONO
    if color is not None:
        r.font.color.rgb = color


def para(doc, text="", *, size=11, bold=False, italic=False, align=None, space_after=6,
         style=None, mono=False):
    p = doc.add_paragraph(style=style)
    if text:
        emit(p, text, size=size, bold=bold, italic=italic, mono=mono)
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p


def rich(doc, parts, *, size=11, align=None, space_after=6):
    """parts: list of (text, {'b':bool,'i':bool,'mono':bool})"""
    p = doc.add_paragraph()
    for text, fmt in parts:
        mono = fmt.get("mono", False)
        emit(p, text, size=size - 1 if mono else size, bold=fmt.get("b", False),
             italic=fmt.get("i", False), mono=mono)
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    return p


def bullets(doc, items, *, size=11):
    for it in items:
        parts = it if isinstance(it, list) else [(it, {})]
        p = doc.add_paragraph(style="List Bullet")
        for text, fmt in parts:
            mono = fmt.get("mono", False)
            emit(p, text, size=size - 1 if mono else size, bold=fmt.get("b", False),
                 italic=fmt.get("i", False), mono=mono)
        p.paragraph_format.space_after = Pt(3)


def shade(cell, hex_colour: str) -> None:
    el = OxmlElement("w:shd")
    el.set(qn("w:fill"), hex_colour)
    cell._tc.get_or_add_tcPr().append(el)


def table(doc, headers, rows, *, widths=None, size=9.5, caption=None, header_fill="1F3B63"):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(str(h))
        r.bold = True
        r.font.size = Pt(size)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        c.paragraphs[0].paragraph_format.space_after = Pt(2)
        shade(c, header_fill)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            txt = str(v)
            bold = txt.startswith("**") and txt.endswith("**")
            if bold:
                txt = txt[2:-2]
            emit(cells[i].paragraphs[0], txt, size=size, bold=bold)
            cells[i].paragraphs[0].paragraph_format.space_after = Pt(2)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Inches(w)
    if caption:
        para(doc, caption, size=9, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
    return t


def figure(doc, path: Path, caption: str, width=6.3):
    if not path.exists():
        para(doc, f"[missing figure: {path.name}]", italic=True)
        return
    doc.add_picture(str(path), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    para(doc, caption, size=9, italic=True, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def add_page_numbers(doc) -> None:
    for section in doc.sections:
        p = section.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for instr in ("PAGE",):
            fld = OxmlElement("w:fldSimple")
            fld.set(qn("w:instr"), instr)
            p._p.append(fld)


def to_pdf(docx_path: Path) -> Path | None:
    """Convert with Microsoft Word via COM (Windows)."""
    pdf = docx_path.with_suffix(".pdf")
    ps = (
        "$w=New-Object -ComObject Word.Application; $w.Visible=$false; "
        f"$d=$w.Documents.Open('{docx_path}'); $d.ExportAsFixedFormat('{pdf}',17); "
        "$d.Close($false); $w.Quit()"
    )
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, text=True)
    if r.returncode != 0 or not pdf.exists():
        print("PDF conversion failed:", (r.stderr or r.stdout)[:500])
        return None
    return pdf


def code_index(doc) -> None:
    """Appendix D: every code reference the report makes, in one clickable table."""
    from code_refs import REFS

    if not LINKS["used"]:
        return
    page_break(doc)
    doc.add_heading("Appendix D  Code reference index", level=1)
    where = ("Each entry opens the file in VS Code at the line shown." if LINKS["mode"] == "vscode"
             else f"Each entry links to the line in the repository at commit "
                  f"{(LINKS['sha'] or '')[:10]}.")
    para(doc, "Every claim in this report that is linked to the code is listed here, in the "
              f"order the code is organised. {where} Line numbers are resolved from the source "
              "when the report is built, so they match the code it was built from.", size=10)
    order = {k: i for i, k in enumerate(REFS)}
    rows = [[f"[[{REFS[k][2]}|{k}]]"] for k in sorted(LINKS["used"], key=order.get)]
    table(doc, ["Claim, and where it is in the code"], rows, widths=[6.3], size=9)


def build_one(mode: str, out_name: str, pdf: bool) -> Path:
    from content import build  # noqa: PLC0415  (local module, after sys.path fix)

    LINKS["mode"], LINKS["used"] = mode, {}
    rows = bench_rows()
    doc = Document()
    style_doc(doc)
    build(doc, rows=rows, stats=arch_stats(rows), facts=live_facts(),
          helpers=dict(para=para, rich=rich, bullets=bullets, table=table, figure=figure,
                       page_break=page_break, Counter=Counter, num=num))
    code_index(doc)
    add_page_numbers(doc)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    docx = OUT_DIR / f"{out_name}.docx"
    doc.save(docx)
    print(f"wrote {docx}  ({len(LINKS['used'])} code references, {mode} links)")
    if pdf:
        p = to_pdf(docx)
        if p:
            print("wrote", p)
    return docx


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", action="store_true", help="also export a PDF via Word")
    ap.add_argument("--links", choices=("both", "vscode", "github"), default="both",
                    help="vscode: claims open VS Code at the line (viva copy, this machine only); "
                         "github: claims open the line on GitHub (submission copy)")
    args = ap.parse_args()

    if args.links in ("both", "github"):
        LINKS["sha"] = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                                      text=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "codefix", "mcp_server",
                                "web", "config", "deploy", "tests", "benchmarks/bugset"],
                               cwd=ROOT, capture_output=True, text=True).stdout.strip()
        if dirty:
            print("warning: code has uncommitted changes, so GitHub line numbers may not match "
                  f"commit {LINKS['sha'][:10]}. Commit first for exact links.")
        build_one("github", "CodeFix_AI_Final_Report", args.pdf)
    if args.links in ("both", "vscode"):
        build_one("vscode", "CodeFix_AI_Final_Report_VIVA", args.pdf)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
