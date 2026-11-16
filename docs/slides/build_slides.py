"""Build the 14-slide final presentation.

Run:  python docs/slides/build_slides.py

Slide order follows the brief exactly (Slide 0 Title ... Slide 14 References). Every number is
read from the run data at build time - the benchmark CSV, the cross-benchmark comparison, the
live model config, the MCP server and the A2A agent card - so the deck cannot disagree with the
report or with the system.
"""

from __future__ import annotations

import csv
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
DOCS = ROOT / "docs"
SHOTS = DOCS / "report" / "screenshots"
OUT = Path(__file__).resolve().parent / "CodeFix_AI_Final_Presentation.pptx"
BENCH_ID = "bench-20261115-180308"

W, H = Inches(13.333), Inches(7.5)
ACCENT = RGBColor(0x1F, 0x3B, 0x63)
ACCENT2 = RGBColor(0x2E, 0x6D, 0xB4)
INK = RGBColor(0x1A, 0x1A, 0x1A)
MUTED = RGBColor(0x5A, 0x5A, 0x5A)
GOOD = RGBColor(0x1B, 0x7F, 0x4B)
WARN = RGBColor(0xB3, 0x5C, 0x00)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xEE, 0xF2, 0xF8)
FONT = "Calibri"

TITLE = "CodeFix AI"
SUBTITLE = "Autonomous Multi-Agent Software Bug Resolution"
URL = "https://codefix-ai-324501187617.asia-south1.run.app"
REPO = "https://github.com/Abhiram12062005/AGAI"
TEAM = [("Singidi Satya Karthikeya", "220353"),
        ("Naman Agarwal", "230537"),
        ("Abhiram Putta", "230557")]


# ----------------------------------------------------------------- data


def rows() -> list[dict]:
    """Completed architecture runs. A row with no outcome was in flight when the process was
    killed; counting it scored an interrupted run as a sequential failure (see build_report)."""
    with (ROOT / "benchmarks" / "results" / BENCH_ID / "runs.csv").open(encoding="utf-8",
                                                                       newline="") as f:
        return [r for r in csv.DictReader(f) if (r.get("outcome") or "").strip()]


def study():
    """Study-wide totals, from the same source as the report so the two cannot disagree."""
    sys.path.insert(0, str(ROOT / "docs" / "report"))
    from build_report import study_totals

    return study_totals()


def num(r, k, d=0.0):
    v = r.get(k)
    try:
        return float(v) if v not in (None, "") else d
    except (TypeError, ValueError):
        return d


def arch_stats(rs):
    by = defaultdict(list)
    for r in rs:
        by[r["arch"]].append(r)
    out = {}
    for a, g in sorted(by.items()):
        n = len(g)
        durs = [num(r, "duration_ms") / 1000 for r in g if num(r, "duration_ms")]
        judged = [r for r in g if r.get("judge_verdict")]
        out[a] = {
            "n": n,
            "resolved": sum(1 for r in g if r.get("objective_pass") in ("1", "True", "true")),
            "agree": sum(1 for r in judged if r.get("agreement") in ("1", "True", "true")),
            "judged": len(judged),
            "secs": st.mean(durs) if durs else 0,
            "sd": st.pstdev(durs) if len(durs) > 1 else 0,
            "cost": st.mean([num(r, "pipeline_cost_usd") for r in g]),
            "tokens": st.mean([num(r, "tokens") for r in g]),
            "bytes": st.mean([num(r, "avg_msg_bytes") for r in g]),
            "diag": st.mean([num(r, "diagnoser_ms") / 1000 for r in g]),
            "fix": st.mean([num(r, "fixer_ms") / 1000 for r in g]),
            "test": st.mean([num(r, "tester_ms") / 1000 for r in g]),
            "pr": st.mean([num(r, "pr_ms") / 1000 for r in g]),
            "refx": sum(1 for r in g if r.get("ref_exact") in ("1", "True", "true")),
        }
    return out


def facts():
    from codefix import config
    from codefix.crew_side.a2a_server import agent_card
    from codefix.eval.bugset import load_bugs
    from mcp_server import server

    s = config.load_settings()
    tools = [n for n in dir(server) if not n.startswith("_")
             and callable(getattr(server, n, None))
             and getattr(getattr(server, n), "__module__", "") == server.__name__]
    return {"roles": {k: s.role(k) for k in ("manager", "diagnoser", "fixer", "judge")},
            "pipeline": s.pipeline, "n_tools": len(tools) - 2,
            "skills": [x.id for x in agent_card("http://x/").skills],
            "bugs": load_bugs()}


# ----------------------------------------------------------------- layout helpers


def box(slide, x, y, w, h):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tf


def put(tf, text, *, size=16, bold=False, color=INK, align=PP_ALIGN.LEFT, space=6,
        italic=False, first=False, font=FONT):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space)
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    r.font.name = font
    return p


def rich(tf, parts, *, size=16, space=6, first=False, align=PP_ALIGN.LEFT):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(space)
    for text, fmt in parts:
        r = p.add_run()
        r.text = text
        r.font.size = Pt(fmt.get("size", size))
        r.font.bold = fmt.get("b", False)
        r.font.italic = fmt.get("i", False)
        r.font.color.rgb = fmt.get("c", INK)
        r.font.name = fmt.get("font", FONT)
    return p


def slide_base(prs, n, title, subtitle=None):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    bar = s.shapes.add_shape(1, 0, 0, W, Inches(0.07))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()
    tf = box(s, Inches(0.55), Inches(0.3), Inches(11.4), Inches(0.9))
    put(tf, title, size=30, bold=True, color=ACCENT, first=True, space=2)
    if subtitle:
        put(tf, subtitle, size=14, color=MUTED, space=0)
    nf = box(s, Inches(12.1), Inches(0.34), Inches(0.9), Inches(0.4))
    put(nf, f"{n}", size=13, bold=True, color=MUTED, align=PP_ALIGN.RIGHT, first=True)
    return s


def bullets(tf, items, *, size=15, space=9, bullet="•  "):
    for it in items:
        parts = it if isinstance(it, list) else [(it, {})]
        rich(tf, [(bullet, {"c": ACCENT2, "b": True})] + parts, size=size, space=space)


def table(s, x, y, w, headers, data, *, size=11, head_size=11, col_w=None, row_h=0.32,
          highlight=None):
    r, c = len(data) + 1, len(headers)
    shape = s.shapes.add_table(r, c, x, y, w, Inches(row_h * r))
    t = shape.table
    if col_w:
        total = sum(col_w)
        for i, cw in enumerate(col_w):
            t.columns[i].width = Emu(int(w * cw / total))
    for j, h in enumerate(headers):
        cell = t.cell(0, j)
        cell.text = ""
        cell.fill.solid()
        cell.fill.fore_color.rgb = ACCENT
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        p = cell.text_frame.paragraphs[0]
        run = p.add_run()
        run.text = str(h)
        run.font.size = Pt(head_size)
        run.font.bold = True
        run.font.color.rgb = WHITE
        run.font.name = FONT
    for i, row in enumerate(data, start=1):
        for j, v in enumerate(row):
            cell = t.cell(i, j)
            cell.text = ""
            cell.fill.solid()
            cell.fill.fore_color.rgb = LIGHT if i % 2 == 0 else WHITE
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            txt = str(v)
            bold = txt.startswith("**") and txt.endswith("**")
            if bold:
                txt = txt[2:-2]
            col = INK
            if txt.startswith("++"):
                txt, col, bold = txt[2:], GOOD, True
            elif txt.startswith("!!"):
                txt, col, bold = txt[2:], WARN, True
            p = cell.text_frame.paragraphs[0]
            run = p.add_run()
            run.text = txt
            run.font.size = Pt(size)
            run.font.bold = bold or (highlight is not None and i - 1 == highlight)
            run.font.color.rgb = col
            run.font.name = FONT
    return t


def picture(s, path: Path, x, y, w=None, h=None):
    if not path.exists():
        put(box(s, x, y, Inches(5), Inches(0.4)), f"[missing: {path.name}]",
            size=12, italic=True, color=WARN, first=True)
        return None
    return s.shapes.add_picture(str(path), x, y, width=w, height=h)


def callout(s, x, y, w, h, text, *, color=ACCENT2, size=14):
    sh = s.shapes.add_shape(5, x, y, w, h)
    sh.fill.solid()
    sh.fill.fore_color.rgb = LIGHT
    sh.line.color.rgb = color
    sh.line.width = Pt(1.25)
    tf = sh.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.14)
    tf.margin_top = tf.margin_bottom = Inches(0.08)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    parts = text if isinstance(text, list) else [(text, {})]
    rich(tf, parts, size=size, first=True, space=0)
    return sh


def stat(s, x, y, w, value, label, *, color=ACCENT, vsize=30):
    sh = s.shapes.add_shape(5, x, y, w, Inches(1.05))
    sh.fill.solid()
    sh.fill.fore_color.rgb = LIGHT
    sh.line.color.rgb = color
    sh.line.width = Pt(1)
    tf = sh.text_frame
    tf.margin_top = Inches(0.07)
    tf.word_wrap = True
    put(tf, value, size=vsize, bold=True, color=color, align=PP_ALIGN.CENTER, first=True, space=0)
    put(tf, label, size=10.5, color=MUTED, align=PP_ALIGN.CENTER, space=0)
    return sh


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


# ----------------------------------------------------------------- driver


def main() -> None:
    import slides_a as A
    import slides_b as B

    rs = rows()
    stats = arch_stats(rs)
    f = facts()
    from codefix.eval.compare import _load, compare
    crows = _load()
    cmp_v, cmp_p, cmp_r = (compare(k, crows) for k in ("variant", "persona", "reporter"))
    total_cost = sum(num(r, "pipeline_cost_usd") for r in rs)
    st_ = study()

    prs = Presentation()
    prs.slide_width, prs.slide_height = W, H

    A.slide0(prs)
    A.slide1(prs)
    A.slide2(prs)
    A.slide3(prs, f)
    A.slide4(prs, f)
    A.slide5(prs, stats)
    A.slide6(prs, f)
    A.slide7(prs, f)
    B.slide8(prs)
    B.slide9(prs, cmp_v, cmp_p, cmp_r, st_)
    B.slide10(prs, stats, cmp_v, cmp_r, st_)
    B.slide11(prs)
    B.slide12(prs)
    B.slide13(prs, stats, total_cost, st_)
    B.slide14(prs)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(OUT)
    print(f"wrote {OUT}  ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    main()
