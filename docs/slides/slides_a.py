"""Slides 0-7 of the final presentation. Helpers come from build_slides."""

from __future__ import annotations

from build_slides import (
    ACCENT,
    ACCENT2,
    DOCS,
    MUTED,
    REPO,
    SUBTITLE,
    TEAM,
    TITLE,
    URL,
    WARN,
    WHITE,
    W,
    box,
    bullets,
    callout,
    picture,
    put,
    rich,
    slide_base,
    table,
)
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


def slide0(prs):
    s = prs.slides.add_slide(prs.slide_layouts[6])
    band = s.shapes.add_shape(1, 0, 0, W, Inches(2.9))
    band.fill.solid()
    band.fill.fore_color.rgb = ACCENT
    band.line.fill.background()
    tf = box(s, Inches(0.9), Inches(0.7), Inches(11.5), Inches(2.0))
    put(tf, TITLE, size=54, bold=True, color=WHITE, first=True, space=4)
    put(tf, SUBTITLE, size=22, color=RGBColor(0xC9, 0xD8, 0xEE), space=10)
    put(tf, "Agentic AI  ·  CSE3101  ·  B.Tech CSE, 7th Semester",
        size=15, color=RGBColor(0xA8, 0xC0, 0xE0), space=0)

    tf = box(s, Inches(0.9), Inches(3.35), Inches(6.6), Inches(2.3))
    put(tf, "Team", size=13, bold=True, color=MUTED, first=True, space=8)
    for name, roll in TEAM:
        rich(tf, [(name, {"b": True, "size": 18}),
                  (f"   {roll}", {"size": 16, "c": MUTED})], space=8)

    tf = box(s, Inches(7.9), Inches(3.35), Inches(4.6), Inches(2.3))
    put(tf, "Live system", size=13, bold=True, color=MUTED, first=True, space=5)
    put(tf, URL, size=11.5, color=ACCENT2, space=12, font="Consolas")
    put(tf, "Source", size=13, bold=True, color=MUTED, space=5)
    put(tf, REPO, size=11.5, color=ACCENT2, space=0, font="Consolas")

    tf = box(s, Inches(0.9), Inches(6.4), Inches(11.5), Inches(0.7))
    put(tf, "Department of Computer Science and Engineering  ·  School of Engineering and "
            "Technology  ·  BML Munjal University  ·  November 2026",
        size=12, color=MUTED, align=PP_ALIGN.CENTER, first=True)
    notes(s, "CodeFix AI takes a bug report in plain English plus a Git repo, finds the defect, "
             "explains it, patches it and proves the patch with the project's own tests. Google "
             "ADK and CrewAI, joined by A2A. It is deployed and live at the URL shown.")


def slide1(prs):
    s = slide_base(prs, 1, "Problem Statement & Objectives")
    tf = box(s, Inches(0.55), Inches(1.4), Inches(6.2), Inches(2.3))
    put(tf, "The problem", size=17, bold=True, color=ACCENT, first=True, space=8)
    put(tf, "Fixing a reported defect is mostly search and verification, not insight. A "
            "developer must find the faulty line among thousands, understand why it fails, write "
            "a change, and prove nothing else broke.", size=15, space=10)
    rich(tf, [("The hard part is localisation", {"b": True}),
              (" — deciding which code is responsible. And a patch justified only by the "
               "model that wrote it is not verified at all.", {})], size=15)

    tf = box(s, Inches(0.55), Inches(3.95), Inches(6.2), Inches(2.6))
    put(tf, "Intended users", size=17, bold=True, color=ACCENT, first=True, space=9)
    bullets(tf, [
        [("Developers", {"b": True}), (" triaging defects in code they did not write", {})],
        [("Open-source maintainers", {"b": True}),
         (" receiving issues with no stack trace", {})],
        [("QA / support engineers", {"b": True}),
         (" who can describe a symptom but not localise it", {})],
    ], size=14)

    tf = box(s, Inches(7.15), Inches(1.4), Inches(5.6), Inches(0.5))
    put(tf, "Objectives, as testable claims", size=17, bold=True, color=ACCENT, first=True)
    table(s, Inches(7.15), Inches(1.95), Inches(5.6),
          ["#", "The system must…"],
          [["PS1", "Locate, explain, patch and prove — from free text"],
           ["PS2", "Prove with the project's own tests, not the model's word"],
           ["PS3", "Never write to a repository without human approval"],
           ["PS4", "Let a reviewer reconstruct what was tried, and why it stopped"]],
          size=12.5, col_w=[1, 9], row_h=0.5)
    callout(s, Inches(7.15), Inches(4.5), Inches(5.6), Inches(1.6),
            [("Why multi-agent?  ", {"b": True, "c": ACCENT}),
             ("The sub-tasks need genuinely different things: deep reasoning to localise, code "
              "generation to patch, and ", {}),
             ("deterministic execution to verify", {"b": True}),
             (". Splitting them makes the verifier independent of the writer by construction.",
              {})], size=13.5)
    notes(s, "PS2 is the one that matters most: the success criterion is an executed test "
             "suite, never a model's opinion.")


def slide2(prs):
    s = slide_base(prs, 2, "Literature Review",
                   "Existing products, research and standards · (SR) = self-reported by the "
                   "authors or vendor")
    table(s, Inches(0.4), Inches(1.4), Inches(12.5),
          ["System", "Starts from", "Approach", "Reported", "What it does not do"],
          [["SWE-bench  ICLR 2024", "GitHub issue",
            "Benchmark: 2,294 real issues; repo tests must pass", "GPT-4 1.7% (SR)",
            "Resolve rate only — no cost, time or variance"],
           ["SWE-agent  2024", "GitHub issue", "Single agent + agent–computer interface",
            "12.5% of SWE-bench (SR)", "One agent plays every role; no independent verifier"],
           ["AutoCodeRover  2024", "GitHub issue", "AST-aware context retrieval, then patch",
            "~22% Lite, $0.43/issue (SR)", "Single pipeline; no human gate; no interop"],
           ["Copilot Autofix  GitHub", "!!A CodeQL alert",
            "LLM turns the alert + its location into a diff", "Cannot fix every alert",
            "!!Already localised; the fix is not test-verified"],
           ["Getafix / SapFix  Meta", "!!Analyser or crash finding",
            "Mines fix patterns from past human fixes", "Top-1 up to 91% (SR)",
            "Only bug classes the analyser already reports"],
           ["Devin  Cognition", "Natural language", "Closed autonomous SWE agent",
            "Not independently reproducible",
            "Orchestration and provenance cannot be audited"],
           ["MCP  ·  A2A  standards", "—",
            "Tool access · cross-framework agent messaging", "Adopted by ADK and CrewAI",
            "Neither prescribes an orchestration topology"]],
          size=10.5, head_size=11, col_w=[1.5, 1.4, 3.1, 1.7, 3.1], row_h=0.56)
    callout(s, Inches(0.4), Inches(5.9), Inches(12.5), Inches(1.25),
            [("Gap from the literature.  ", {"b": True, "c": ACCENT}),
             ("Deployed tools start ", {}), ("after", {"i": True}),
             (" localisation, from an analyser alert (LG1). Research agents localise, but are "
              "single agents with no independent verifier (LG2), fix one topology and never "
              "measure what it costs (LG3), discard the failure evidence on retry (LG4), run "
              "without guardrails (LG6) and are scored on resolve rate alone (LG7). None is "
              "deployable by a third party (LG8).", {})], size=13.5)
    notes(s, "The two deployed systems only repair what a static analyser already found. The "
             "research agents handle free text but are single agents, and are not deployed. "
             "Nobody measures what their orchestration costs.")


def slide3(prs, f):
    s = slide_base(prs, 3, "Agent Requirements",
                   "Every agent traces to a requirement; every requirement to a literature gap "
                   "(LG) or problem-statement claim (PS)")
    table(s, Inches(0.4), Inches(1.4), Inches(12.5),
          ["Req", "Requirement", "From", "Agent / mechanism it created"],
          [["R1", "Localise from natural language using tools, not a pre-computed alert",
            "LG1, PS1", "**Diagnoser** — ADK LlmAgent, explicit ReAct over MCP tools"],
           ["R2", "Separate the agent that writes the patch from the one that judges it",
            "LG2, PS2", "**Fixer** (CrewAI) + independent **Tester** running the real suite"],
           ["R3", "Decide routing, retries and termination in one auditable place",
            "LG2, LG4", "**Manager** — ADK custom agent, attempt bound enforced in code"],
           ["R4", "Make the orchestration topology a variable, and measure it", "LG3",
            "Three architectures behind one switch: hierarchical / sequential / p2p"],
           ["R5", "Retry the failed stage with the failure evidence attached, bounded",
            "LG4, PS2",
            f"TestReport re-dispatched by reference; {f['pipeline'].max_attempts} attempts, then escalate"],
           ["R6", "Share state through one inspectable store", "LG6, PS4",
            "**Blackboard** — SQLite, typed Pydantic envelopes, append-only log"],
           ["R7", "Reach every tool through one guarded boundary", "LG5, LG6",
            f"**MCP server**, {f['n_tools']} tools — sandbox and blocklist live in the server"],
           ["R8", "Let agents on different frameworks cooperate over an open protocol", "LG5",
            "**A2A** between ADK and CrewAI — public agent card, bearer auth"],
           ["R9", "Refuse unsafe input, tool output and patches at the boundaries", "LG6",
            "Guardrails at seven boundaries (Slide 8)"],
           ["R10", "Never write to a repository without a human decision", "LG6, PS3",
            "Human gate before the PR — runner, PR agent **and** MCP tool all enforce it"],
           ["R11", "Make every run reconstructable afterwards", "LG6, PS4",
            "Framework **callbacks** → JSONL trace, runs.db, Blackboard snapshots"],
           ["R12", "Evaluate on more than resolve rate, over repeated runs", "LG7, PS2",
            "Tests + reference fix + LLM judge; cost, latency and variance"],
           ["R13", "Be deployable by someone who is not us", "LG8",
            "Container on Cloud Run; agent card at a public URL"]],
          size=10, head_size=10.5, col_w=[0.6, 4.4, 1.0, 5.5], row_h=0.4)
    notes(s, "This slide is the derivation of the agent set. No agent exists without a "
             "requirement behind it, and no requirement without a gap or a claim.")


def slide4(prs, f):
    s = slide_base(prs, 4, "Multi-Agent Architecture",
                   "Hierarchical (manager–worker) · ADK orchestrates · CrewAI "
                   "workers execute · A2A joins them")
    picture(s, DOCS / "graph.png", Inches(0.4), Inches(1.45), w=Inches(8.3))
    tf = box(s, Inches(8.95), Inches(1.4), Inches(3.95), Inches(2.1))
    put(tf, "Orchestration mechanism", size=15, bold=True, color=ACCENT, first=True, space=7)
    bullets(tf, [
        [("The Manager is the ", {}), ("only", {"i": True}),
         (" component that decides what happens next", {})],
        [("Every hop is Manager ⇄ worker: a star-shaped, auditable message log", {})],
        [("Dispatches carry ", {}), ("artifact references", {"b": True}),
         (", never artifact bodies", {})],
    ], size=12, space=6)
    table(s, Inches(8.95), Inches(3.65), Inches(3.95),
          ["Agent", "Framework"],
          [["Manager", "Google ADK"], ["Diagnoser (ReAct)", "Google ADK"],
           ["Fixer + Reviewer", "CrewAI"], ["Tester", "CrewAI"], ["PR agent", "CrewAI"]],
          size=11.5, col_w=[5, 4], row_h=0.34)
    callout(s, Inches(8.95), Inches(5.7), Inches(3.95), Inches(1.35),
            [("Control flow.  ", {"b": True, "c": ACCENT}),
             ("diagnose → fix → test → ", {}), ("human gate", {"b": True}),
             (". On failure the Manager re-dispatches ", {}), ("only the Fixer", {"b": True}),
             (", with the test failure attached.", {})], size=12)
    notes(s, "Hierarchical by choice. The other two topologies are implemented as well, and "
             "the next slide shows what each actually costs.")


def slide5(prs, stats):
    archs = list(stats)
    n_runs = sum(stats[a]["n"] for a in archs)
    s = slide_base(prs, 5, "Architecture Evaluation",
                   "All three implemented behind one switch and measured on identical bugs "
                   f"· {n_runs} completed runs")
    table(s, Inches(0.45), Inches(1.4), Inches(7.5),
          ["Metric"] + archs,
          [["Runs"] + [str(stats[a]["n"]) for a in archs],
           ["**Resolved**"] + [f"{100*stats[a]['resolved']/stats[a]['n']:.0f}%" for a in archs],
           ["Judge accuracy"] + [f"{100*stats[a]['agree']/max(stats[a]['judged'],1):.0f}%"
                                 for a in archs],
           ["Mean wall-clock"] + [f"{stats[a]['secs']:.1f}s" for a in archs],
           ["**Variance (std-dev)**"] + [("!!" if a == "hierarchical" else "++") +
                                         f"{stats[a]['sd']:.1f}s" for a in archs],
           ["**Cost / run**"] + [("!!" if a == "hierarchical" else "") +
                                 f"${stats[a]['cost']:.4f}" for a in archs],
           ["Tokens / run"] + [f"{stats[a]['tokens']:.0f}" for a in archs],
           ["Envelope size"] + [("++" if a == "hierarchical" else "") +
                                f"{stats[a]['bytes']:.0f} B" for a in archs],
           ["Runs needing a retry"] + ["0" for _ in archs]],
          size=11.5, col_w=[3.4, 1.9, 1.9, 1.9], row_h=0.385)

    tf = box(s, Inches(8.25), Inches(1.4), Inches(4.6), Inches(2.4))
    put(tf, "What was compared", size=15, bold=True, color=ACCENT, first=True, space=7)
    bullets(tf, [
        [("Hierarchical", {"b": True}), (" — Manager routes every hop", {})],
        [("Sequential", {"b": True}), (" — ADK LoopAgent; failure restarts the attempt", {})],
        [("Peer-to-peer", {"b": True}), (" — Fixer ⇄ Tester direct, no Manager", {})],
    ], size=12.5, space=6)
    callout(s, Inches(8.25), Inches(3.35), Inches(4.6), Inches(1.75),
            [("Why hierarchical.  ", {"b": True, "c": ACCENT}),
             ("One place decides, so a retry re-runs ", {}), ("only", {"i": True}),
             (" the failed stage, ", {}), ("with the failure evidence", {"b": True}),
             ("; the attempt bound is one counter; reference-passing keeps a third dispatch the "
              "same size as the first.", {})], size=12.5)
    callout(s, Inches(0.45), Inches(5.35), Inches(12.4), Inches(1.7),
            [("The honest result.  ", {"b": True, "c": WARN}),
             ("Resolve rate does ", {}), ("not", {"i": True}),
             (" separate the three — each resolved every completed run. Hierarchical is the most "
              "expensive and most variable (23.0s vs 11.2s std-dev), and here it bought "
              "nothing, because ", {}),
             ("no run ever needed a retry", {"b": True}),
             (" — precisely the situation its design exists for. Its advantage is failure "
              "handling and auditability, and a bug set that never fails cannot demonstrate it. "
              "That is a limitation of our experiment, not a win for the alternatives.", {})],
            color=WARN, size=13.5)
    notes(s, "Say this plainly: we did not get the result we expected and we are reporting it. "
             "Hierarchical costs more and varies more. Its justification is failure handling; "
             "these bugs never failed. The next experiment is a bug set that resists the first "
             "patch.")


def slide6(prs, f):
    s = slide_base(prs, 6, "Agent–Tool Communication (MCP)",
                   f"One MCP server, {f['n_tools']} tools · both frameworks pass through the "
                   "same guarded boundary")
    picture(s, DOCS / "graph_mcp.png", Inches(0.35), Inches(1.5), w=Inches(9.3))
    tf = box(s, Inches(9.85), Inches(1.45), Inches(3.1), Inches(2.6))
    put(tf, "Why a single server", size=14.5, bold=True, color=ACCENT, first=True, space=7)
    bullets(tf, [
        [("Path sandbox, secrets blocklist, subprocess timeouts and the PR guard live in the "
          "server — ", {}), ("not", {"i": True}), (" in any agent", {})],
        [("So no agent in ", {}), ("either", {"i": True}),
         (" framework can bypass them", {})],
    ], size=11.5, space=7)
    tf = box(s, Inches(9.85), Inches(4.3), Inches(3.1), Inches(2.6))
    put(tf, "Per-agent allow-list", size=14.5, bold=True, color=ACCENT, first=True, space=6)
    put(tf, "The Diagnoser gets six read-only tools; the CrewAI workers get workspace, patch, "
            "test and git tools.", size=11.5, color=MUTED, space=8)
    put(tf, "before_tool_callback checks the allow-list and argument shape. "
            "after_tool_callback type-checks the result and wraps repository text as "
            "untrusted data.", size=11.5, color=MUTED, space=0)
    notes(s, "The point of MCP here is that safety is implemented once, in the server, instead "
             "of being re-implemented inside every agent.")


def slide7(prs, f):
    s = slide_base(prs, 7, "Messaging Pattern & A2A Communication",
                   "Blackboard for shared state inside ADK · A2A as the wire between the two "
                   "frameworks")
    picture(s, DOCS / "graph_messaging.png", Inches(0.35), Inches(1.5), w=Inches(8.6))
    tf = box(s, Inches(9.2), Inches(1.45), Inches(3.7), Inches(2.5))
    put(tf, "Two patterns, deliberately", size=14.5, bold=True, color=ACCENT, first=True,
        space=7)
    bullets(tf, [
        [("Blackboard", {"b": True}),
         (" — shared state within ADK: typed Pydantic envelopes, append-only message log, "
          "one SQLite source of truth", {})],
        [("A2A", {"b": True}),
         (" — peer-to-peer across the framework boundary, official a2a-sdk over JSON-RPC",
          {})],
    ], size=11.5, space=7)
    table(s, Inches(9.2), Inches(4.2), Inches(3.7),
          ["A2A skill", "Served by"],
          [[f["skills"][0], "CrewAI Fixer + Reviewer"],
           [f["skills"][1], "CrewAI Tester"],
           [f["skills"][2], "CrewAI PR agent"],
           [f["skills"][3], "CrewAI PeerRepairFlow"]],
          size=11, col_w=[4, 6], row_h=0.34)
    callout(s, Inches(9.2), Inches(5.95), Inches(3.7), Inches(1.1),
            [("4 agents reached over A2A", {"b": True, "c": ACCENT}),
             (", as a separately addressable service at ", {}),
             ("/a2a/crew/", {"font": "Consolas", "size": 11}),
             (" with a public agent card.", {})], size=12)
    notes(s, "Blackboard is the shared-state pattern; A2A is the peer-to-peer wire across "
             "frameworks. Four skills, four CrewAI agents, reachable as their own service on "
             "the deployment.")
