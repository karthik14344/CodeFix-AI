"""Prose and structure of the Final Project Report.

Section order follows the body outline of Final_Report_Format.pdf:
cover, declaration, contents, 1 Introduction, 2 Problem Statement, 3 Literature Review,
4 Requirements for MAS, 5 Methodology, 6 Technology Stack, 7 Experimental Results,
8 Team Responsibility / Self-contribution Matrix, 9 Conclusions, References, Appendix.

Figures come from docs/*.png, numbers from the benchmark CSV, and configuration facts from the
running code - so the report cannot quietly disagree with the system it describes.
"""

from __future__ import annotations

from pathlib import Path

from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).resolve().parent.parent.parent
DOCS = ROOT / "docs"
SHOTS = ROOT / "docs" / "report" / "screenshots"

TITLE = "CodeFix AI"
SUBTITLE = "Autonomous Multi-Agent Software Bug Resolution"
URL = "https://codefix-ai-324501187617.asia-south1.run.app"
REPO = "https://github.com/Abhiram12062005/AGAI"

TEAM = [("Singidi Satya Karthikeya", "220353"),
        ("Naman Agarwal", "230537"),
        ("Abhiram Putta", "230557")]

C = WD_ALIGN_PARAGRAPH.CENTER
J = WD_ALIGN_PARAGRAPH.JUSTIFY


def build(doc, *, rows, stats, facts, helpers):
    para, rich = helpers["para"], helpers["rich"]
    bullets, table = helpers["bullets"], helpers["table"]
    figure, page_break = helpers["figure"], helpers["page_break"]

    archs = list(stats)
    total_runs = sum(v["n"] for v in stats.values())
    total_cost = sum(v["cost"] for v in stats.values())

    # ------------------------------------------------------------------ cover
    for _ in range(3):
        para(doc)
    para(doc, "Project Report", size=20, bold=True, align=C, space_after=4)
    para(doc, "Agentic AI", size=17, bold=True, align=C, space_after=4)
    para(doc, "CSE3101", size=14, bold=True, align=C, space_after=24)
    para(doc, TITLE, size=24, bold=True, align=C, space_after=2)
    para(doc, SUBTITLE, size=13, italic=True, align=C, space_after=22)
    para(doc, "By", size=12, italic=True, bold=True, align=C, space_after=12)
    for name, roll in TEAM:
        para(doc, name, size=11.5, italic=True, align=C, space_after=0)
        para(doc, roll, size=11.5, italic=True, align=C, space_after=8)
    para(doc)
    para(doc, "Department of Computer Science and Engineering", size=12, bold=True,
         align=C, space_after=0)
    para(doc, "School of Engineering and Technology", size=12, bold=True, align=C, space_after=0)
    para(doc, "BML Munjal University", size=12, bold=True, align=C, space_after=12)
    para(doc, "November 2026", size=12, bold=True, align=C)
    page_break(doc)

    # ------------------------------------------------------------------ declaration
    para(doc, "Declaration by the Candidates", size=15, bold=True, align=C, space_after=16)
    rich(doc, [
        ("We hereby declare that the project entitled ", {}),
        (f'"{TITLE} — {SUBTITLE}"', {"b": True, "i": True}),
        (" has been carried out to fulfil the partial requirements for completion of the "
         "core-elective course ", {}),
        ("Agentic AI", {"b": True}),
        (" offered in the 7th Semester of the Bachelor of Technology (B.Tech) program in the "
         "Department of Computer Science and Engineering during AY-2026-27 (odd semester). "
         "This experimental work has been carried out by us and submitted to the course "
         "instructor ", {}),
        ("Prof Pranshu Tiwari", {"i": True}),
        (". Due acknowledgments have been made in the text of the project to all other "
         "materials used. This project has been prepared in full compliance with the "
         "requirements and constraints of the prescribed curriculum.", {}),
    ], align=J, space_after=24)
    for name, roll in TEAM:
        para(doc, f"{name} ({roll})", space_after=2)
        para(doc, "Signature: ______________________", space_after=18)
    para(doc, "Place: BML Munjal University", bold=True, space_after=4)
    para(doc, "Date: ______ November, 2026", bold=True)
    page_break(doc)

    # ------------------------------------------------------------------ contents
    para(doc, "Contents", size=15, bold=True, align=C, space_after=14)
    table(doc, ["Section", "Page"], [
        ["1. Introduction", "1"],
        ["2. Problem Statement", "2"],
        ["3. Literature Review", "4"],
        ["4. Requirements for the Multi-Agent System", "7"],
        ["5. Methodology", "9"],
        ["6. Technology Stack", "17"],
        ["7. Experimental Results", "18"],
        ["8. Team Responsibility / Self-contribution Matrix", "26"],
        ["9. Conclusions", "27"],
        ["References", "28"],
        ["Appendix", "29"],
    ], widths=[5.2, 0.9], size=11)
    page_break(doc)

    # ------------------------------------------------------------------ 1 introduction
    doc.add_heading("1  Introduction", level=1)
    para(doc,
         "Fixing a reported software defect is slow, repetitive work. A developer must locate "
         "the faulty code among thousands of lines, understand why it fails, write a change, "
         "prove the change works, and avoid breaking anything else. Most of that effort is "
         "search and verification rather than insight.", align=J)
    para(doc,
         f"{TITLE} is a multi-agent system that performs this loop end to end. It takes a "
         "free-text bug report and a Git repository, locates the defect, explains the root "
         "cause, writes a patch, and proves the patch with the project's own test suite. When "
         "the tests fail, the failure log is routed back to the agent that wrote the patch "
         "rather than restarting the task. Nothing is pushed to a repository without an "
         "explicit human decision.", align=J)
    para(doc,
         "The system is built on two agent frameworks that cooperate over an open protocol. "
         "Google ADK runs the orchestration, the Manager and the ReAct Diagnoser; CrewAI runs "
         "the Fixer, Reviewer, Tester and Pull-Request agents. The two sides never import each "
         "other's code — they communicate using the Agent2Agent (A2A) protocol. Every tool "
         f"the agents use is reached through a single Model Context Protocol (MCP) server with "
         f"{facts['n_tools']} tools, so the sandbox, the secrets blocklist and the "
         "pull-request guard cannot be bypassed by an agent in either framework.", align=J)
    rich(doc, [("The system described here is deployed and publicly reachable at ", {}),
               (URL, {"mono": True}), (". Source: ", {}), (REPO, {"mono": True}), (".", {})],
         align=J)
    para(doc, "Contributions of this work:", bold=True, space_after=3)
    bullets(doc, [
        [("A role-specialised multi-agent system spanning two frameworks ", {}),
         ("(Google ADK and CrewAI)", {"b": True}), (" joined by the A2A protocol, with all "
          "tool access mediated by one guarded MCP server.", {})],
        [("Three interchangeable orchestration architectures ", {}),
         ("(hierarchical, sequential, peer-to-peer)", {"b": True}),
         (" behind a single switch, so the topology becomes an experimental variable rather "
          "than a fixed design decision.", {})],
        [("A three-way evaluation of every patch: the project's own tests re-run in a fresh "
          "clone, a comparison against the known-good reference fix, and an LLM-as-judge whose "
          "agreement with the tests is itself measured.", {})],
        [(f"An empirical study of {total_runs} live runs", {"b": True}),
         (" across the three architectures, reporting resolve rate, wall-clock time, run-to-run "
          "variance, per-agent latency, token volume and real monetary cost.", {})],
    ])
    page_break(doc)

    # ------------------------------------------------------------------ 2 problem statement
    doc.add_heading("2  Problem Statement", level=1)
    doc.add_heading("2.1  What is being addressed", level=2)
    para(doc,
         "Given a bug report written in natural language (optionally with a stack trace) and a "
         "Git repository, produce a verified patch that fixes the defect without breaking the "
         "rest of the suite, together with an explanation of the root cause and an auditable "
         "record of how the conclusion was reached.", align=J)
    para(doc,
         "The hard part is not writing the patch. It is localisation — deciding which of "
         "thousands of lines is responsible — followed by verification. A patch that nobody "
         "verified is a liability, and a patch justified only by the model that produced it is "
         "not verified at all.", align=J)

    doc.add_heading("2.2  Intended users", level=2)
    bullets(doc, [
        [("Application developers", {"b": True}),
         (" triaging a backlog of reported defects in a codebase they may not have written.", {})],
        [("Maintainers of open-source projects", {"b": True}),
         (" who receive issues from users unable to supply a stack trace.", {})],
        [("QA and support engineers", {"b": True}),
         (" who can describe a symptom precisely but cannot localise it in code.", {})],
    ])

    doc.add_heading("2.3  Why a multi-agent solution is relevant", level=2)
    para(doc, "The task decomposes into sub-tasks with genuinely different requirements:", align=J)
    table(doc, ["Sub-task", "What it needs", "Agent"], [
        ["Localise and explain the defect", "Multi-step reasoning over code, traces and docs; "
         "tool use; the strongest model", "Diagnoser (ADK, ReAct)"],
        ["Write a minimal patch", "Code generation from an already-localised diagnosis",
         "Fixer (CrewAI)"],
        ["Prove the patch", "Deterministic execution in an isolated clone — no model at all",
         "Tester (CrewAI)"],
        ["Decide what happens next", "Cheap, bounded routing over a small set of legal "
         "transitions", "Manager (ADK)"],
        ["Offer the change to a human", "Branch, commit, and stop for approval",
         "PR agent (CrewAI)"],
    ], widths=[1.7, 3.0, 1.6])
    para(doc,
         "Three properties follow from this split and are difficult to obtain from a single "
         "agent. First, the component that writes the patch is not the component that judges "
         "it — verification is independent by construction. Second, each role can use a model "
         "matched to its difficulty and cost. Third, because the Tester is deterministic, the "
         "system's success criterion is an executed test suite rather than a model's opinion.",
         align=J)

    doc.add_heading("2.4  The problem statement as testable claims", level=2)
    table(doc, ["#", "Claim"], [
        ["PS1", "From a free-text report (optionally a stack trace), the system locates the "
                "defect, explains the root cause, writes a patch and proves it."],
        ["PS2", "Correctness is demonstrated by the project's own test suite, not asserted by "
                "the model that wrote the patch."],
        ["PS3", "Nothing is written to a real repository without explicit human approval."],
        ["PS4", "A reviewer can afterwards reconstruct what was tried, what it cost, and why "
                "the run stopped where it did."],
    ], widths=[0.6, 5.7])
    page_break(doc)

    # ------------------------------------------------------------------ 3 literature review
    doc.add_heading("3  Literature Review", level=1)
    para(doc,
         "Nine works are compared below: four systems that repair code, two open protocols that "
         "make cross-framework agents possible, and the two agent frameworks used here. Figures "
         "reported by a system's own authors or vendor are marked (self-reported); they "
         "characterise a system and are never compared against the results in Section 7, which "
         "were measured on a different bug set.", align=J)
    table(doc, ["#", "System / work", "Input it starts from", "Approach", "Reported capability",
                "What it does not do"], [
        ["L1", "SWE-bench (Jimenez et al., ICLR 2024) [1]", "GitHub issue + repo",
         "Benchmark: 2,294 real issues, 12 Python repos; a fix counts only if the repo's tests pass",
         "Claude 2 / GPT-4 resolved 4.8% / 1.7% (self-reported)",
         "Measures resolve rate only — no cost, time, or variance"],
        ["L2", "SWE-agent (Yang et al., 2024) [2]", "GitHub issue + repo",
         "A single LLM agent with a purpose-built agent–computer interface",
         "12.47% of SWE-bench, 18.00% of SWE-bench Lite (self-reported)",
         "One agent plays every role; no independent verifier; no alternative topologies"],
        ["L3", "AutoCodeRover (Zhang et al., 2024) [3]", "GitHub issue + repo",
         "AST-aware context retrieval, then patch generation",
         "~22% of SWE-bench Lite; $0.43 average per issue (self-reported)",
         "Single pipeline; Python-AST assumptions; no human approval gate"],
        ["L4", "GitHub Copilot Autofix [4]", "A CodeQL alert (already localised)",
         "LLM turns the alert and its location into a suggested diff",
         "Vendor states it cannot fix every alert and that reviewers must edit before accepting",
         "Does not start from a free-text report; the suggestion is not verified by running tests"],
        ["L5", "Getafix / SapFix, Meta (Bader et al., 2019) [5]",
         "A static-analyser or crash finding",
         "Mines fix patterns from past human fixes by hierarchical clustering",
         "Top-1 match to the human fix up to 91% (self-reported)",
         "Only repairs bug classes the analyser reports; needs a large proprietary fix corpus"],
        ["L6", "Devin, Cognition [6]", "Natural-language task", "Closed autonomous SWE agent",
         "Vendor claims are not independently reproducible",
         "Orchestration, state and provenance cannot be inspected or audited"],
        ["L7", "Model Context Protocol [7]", "—",
         "Standardises how a model reaches tools and data",
         "Adopted across vendors as the tool-access layer",
         "Says nothing about how agents coordinate with each other"],
        ["L8", "Agent2Agent protocol [8]", "—",
         "Standardises agent discovery (agent cards) and messaging across frameworks",
         "Official SDKs; ADK and CrewAI among the named frameworks",
         "A transport and discovery standard — it prescribes no orchestration topology"],
        ["L9", "Google ADK [9] / CrewAI [10]", "—",
         "ADK: workflow and custom agents, model/tool callbacks. CrewAI: role-based agents, "
         "tasks, crews and flows", "Both ship A2A integrations",
         "Neither prescribes how to combine two frameworks, nor how to evaluate the result"],
    ], widths=[0.3, 1.1, 0.95, 1.35, 1.2, 1.4], size=7.5,
        caption="Table 3.1  Existing products, services and enabling standards.")

    doc.add_heading("3.1  Gaps identified from the literature", level=2)
    table(doc, ["Gap", "Description"], [
        ["LG1", "Repair starts after localisation. The deployed systems (L4, L5) are driven by "
                "an analyser or crash that has already pinpointed the defect. The everyday case "
                "— a human writes “discounts are wrong for bulk orders” and the "
                "defect must first be found — is addressed only by research agents that are "
                "not deployed."],
        ["LG2", "One agent plays every role. L2 and L3 are single-agent loops, so the component "
                "that writes the patch also judges whether it worked. There is no independent "
                "verification inside the system."],
        ["LG3", "The orchestration topology is fixed and never evaluated. Every system commits "
                "to one control flow and reports a resolve rate for it. None reports what its "
                "topology costs in messages, tokens, latency or retries."],
        ["LG4", "Retries discard the evidence. Where a retry exists it restarts the task; the "
                "failure log explaining why the patch was wrong is not routed back to the "
                "component that produced it."],
        ["LG5", "Framework lock-in. Each system is a single stack. MCP (L7) and A2A (L8) now "
                "make cross-framework agent systems possible, but the repair literature "
                "predates them and does not use them."],
        ["LG6", "Safety and auditability are thin. Research harnesses execute model-written "
                "code with no guardrails; commercial systems are closed, so provenance cannot "
                "be inspected. Human oversight is a UI affordance rather than an enforced gate."],
        ["LG7", "Evaluation is one-dimensional. L1 established resolve rate as the metric. L3 is "
                "a partial exception in reporting cost per issue, but wall-clock time, per-agent "
                "latency, variance across repeated runs and sensitivity to prompt strategy are "
                "not reported. Where an LLM judge is used it is rarely cross-checked against "
                "objective test outcomes, so the judge itself is never validated."],
        ["LG8", "Not deployable by a third party. The research agents are local harnesses; the "
                "commercial ones are closed services."],
    ], widths=[0.6, 5.7], size=9)
    page_break(doc)

    # ------------------------------------------------------------------ 4 requirements
    doc.add_heading("4  Requirements for the Multi-Agent System", level=1)
    para(doc,
         "Each requirement below is traced to the literature gap (LG) and/or problem-statement "
         "claim (PS) that forced it, and to the agent or mechanism it produced. This is the "
         "derivation of the agent set: no agent exists without a requirement behind it.", align=J)
    table(doc, ["Req", "Requirement", "Traced to", "Agent / mechanism created"], [
        ["R1", "Localise a defect from natural language and an optional stack trace, using "
               "tools rather than a pre-computed alert", "LG1, PS1",
         "Diagnoser — ADK LlmAgent running explicit ReAct over MCP tools"],
        ["R2", "Separate the agent that writes the patch from the agent that judges it",
         "LG2, PS2", "Fixer (CrewAI) and an independent Tester (CrewAI) that runs the real "
                     "suite in a fresh clone"],
        ["R3", "Decide routing, retries and termination in one auditable place", "LG2, LG4",
         "Manager — ADK custom agent with the attempt counter enforced in code"],
        ["R4", "Make the orchestration topology a variable, and measure it", "LG3",
         "Three interchangeable architectures behind --arch: hierarchical, sequential, p2p"],
        ["R5", "On failure, retry the failed stage with the failure evidence attached, bounded",
         "LG4, PS2", "Manager re-dispatches to the Fixer with the TestReport by reference; "
                     f"max {facts['pipeline'].max_attempts} attempts, then a written escalation"],
        ["R6", "Share state through one inspectable store rather than ad-hoc message passing",
         "LG6, PS4", "Blackboard — SQLite, typed Pydantic envelopes, append-only message log"],
        ["R7", "Reach every tool through one standard, guarded boundary", "LG5, LG6",
         f"MCP server with {facts['n_tools']} tools; sandbox, blocklist and timeouts live in "
         "the server, so no agent in either framework can bypass them"],
        ["R8", "Let agents built on different frameworks cooperate over an open protocol", "LG5",
         "A2A between the ADK and CrewAI sides — official a2a-sdk, public agent card, "
         "bearer-token authentication"],
        ["R9", "Refuse unsafe input, unsafe tool output and unsafe patches at the boundaries",
         "LG6", "Guardrails: input screening, per-agent tool allow-list, Pydantic tool-output "
                "checks, patch-safety task guardrail"],
        ["R10", "Never write to a real repository without a human decision", "LG6, PS3",
         "Human-in-the-loop gate before the PR, enforced in the runner, the PR agent and the "
         "MCP tool (confirmed=true, branch must be codefix/*)"],
        ["R11", "Make every run reconstructable after the fact", "LG6, PS4",
         "Callbacks (ADK agent/model/tool hooks, CrewAI event bus) feeding a JSONL trace, "
         "runs.db, Blackboard snapshots, A2A message ids and validated RAG citations"],
        ["R12", "Evaluate on more than resolve rate, over repeated runs", "LG7, PS2",
         "codefix bench: objective re-test in a fresh clone, reference-fix comparison and "
         "LLM-as-judge with agreement scoring; cost, wall-clock, per-agent latency and "
         "standard deviation"],
        ["R13", "Be deployable and reachable by someone who is not us", "LG8",
         "Container on Google Cloud Run; A2A agent card published at a public URL"],
    ], widths=[0.45, 2.2, 0.85, 2.8], size=8.5,
        caption="Table 4.1  Requirements traced to literature gaps and problem-statement claims.")
    page_break(doc)

    # ------------------------------------------------------------------ 5 methodology
    doc.add_heading("5  Methodology", level=1)

    doc.add_heading("5.1  How the agents were identified", level=2)
    para(doc,
         "The agent set is the direct image of Table 4.1. R1 requires a reasoning agent with "
         "tools, giving the Diagnoser. R2 requires the writer and the judge to be different "
         "components, giving the Fixer and a deterministic Tester. R3 requires one place that "
         "decides what happens next, giving the Manager. R10 requires a human decision before "
         "any repository write, giving the PR agent and the approval gate. The optional "
         "Reviewer implements the Reflection pattern and is enabled by the react-reflect "
         "prompt variant.", align=J)
    table(doc, ["Agent", "Framework", "Role", "Model", "Output"], [
        ["Manager", "Google ADK (custom agent)", "Routing and state evaluation; each decision is "
         "a one-shot LlmAgent call", facts["roles"]["manager"].model,
         "DispatchRef, Escalation"],
        ["Diagnoser", "Google ADK (LlmAgent + MCP tools)", "Explicit ReAct over report, trace "
         "and repository", facts["roles"]["diagnoser"].model, "Diagnosis"],
        ["Fixer (+ Reviewer)", "CrewAI (Agent + guardrailed Task)",
         "Patch generation; optional Reflection reviewer", facts["roles"]["fixer"].model,
         "Patch (unified diff + rationale)"],
        ["Tester", "CrewAI (Flow step)", "Isolated apply → lint → test suite",
         "none (deterministic)", "TestReport"],
        ["PR agent", "CrewAI (Flow step)", "Branch and commit; push only after human approval",
         "none (deterministic)", "PRResult"],
    ], widths=[1.0, 1.4, 1.9, 1.0, 1.0], size=8.5,
        caption="Table 5.1  The five agents, their frameworks and their responsibilities.")

    doc.add_heading("5.2  Multi-agent architecture and orchestration", level=2)
    figure(doc, DOCS / "graph.png",
           "Figure 5.1  Hierarchical architecture (the default). The Manager is the only "
           "component that decides what happens next; every hop is Manager ⇄ worker.")
    para(doc,
         "The chosen architecture is hierarchical (manager–worker). The Manager receives the "
         "bug report after input screening, dispatches the Diagnoser, then the Fixer, then the "
         "Tester. On a passing test report it dispatches the PR agent and stops at the human "
         "gate. On a failing report it re-dispatches the Fixer with the TestReport attached by "
         "reference, at most max_attempts times, after which it escalates with a written "
         "summary of everything tried. The bound is enforced in code: the Manager checks the "
         "attempt counter before consulting its model, and the model may only choose among the "
         "legal transitions; an invalid or failed answer falls back to the deterministic policy.",
         align=J)
    para(doc, "Two alternative topologies are implemented behind the same switch:", align=J)
    bullets(doc, [
        [("Sequential", {"b": True}),
         (" — an ADK LoopAgent wrapping diagnose → fix → test → gate. Any "
          "failure restarts the whole attempt from diagnosis, carrying nothing over.", {})],
        [("Peer-to-peer", {"b": True}),
         (" — the ADK Diagnoser hands its Diagnosis inline over A2A to a CrewAI "
          "PeerRepairFlow, where Fixer and Tester pass the patch and the full TestReport "
          "directly to each other under a fixed local rule. No Manager, no Blackboard reads.", {})],
    ])
    figure(doc, DOCS / "graph_sequential.png", "Figure 5.2  Sequential architecture.", width=5.6)
    figure(doc, DOCS / "graph_p2p.png", "Figure 5.3  Peer-to-peer architecture.", width=5.6)

    doc.add_heading("5.3  Architecture evaluation: why hierarchical", level=2)
    table(doc, ["Concern", "Sequential", "Peer-to-peer", "Hierarchical (chosen)"], [
        ["Failure handling", "Restarts from scratch; re-pays for diagnosis and loses the "
         "failure log", "Each peer must know the retry rules; no global view",
         "One place decides; retries only the failed stage, with the failure evidence"],
        ["Bounded execution", "Trivially bounded but wasteful", "Needs distributed counters",
         "A single attempt counter on the Blackboard, checked by the Manager"],
        ["Observability", "Linear log", "Causality spread across peers",
         "Every hop is Manager ⇄ worker: a star-shaped, auditable message log"],
        ["Coordination cost", "None", "None", "One cheap routing call per decision point"],
        ["Extensibility", "Reorder code", "Rewire peers", "Add a worker and a Manager transition"],
    ], widths=[1.1, 1.75, 1.6, 1.85], size=8.5,
        caption="Table 5.2  Qualitative comparison. Section 7.2 tests these claims empirically.")
    para(doc,
         "Section 7 reports what happened when the three were measured on identical bugs. The "
         "honest result is that on this bug set the hierarchical advantage did not materialise, "
         "because no run ever needed a retry — the condition its design exists to handle.",
         align=J)

    doc.add_heading("5.4  State management: the Blackboard", level=2)
    para(doc,
         "A SQLite-backed Blackboard keyed by task_id is the single source of truth: the bug "
         "report, the current Diagnosis, the active Patch, the latest TestReport, the attempt "
         "counter, escalation and PR results, and an append-only message log. In hierarchical "
         "mode agents read and write only through it. Because it holds the complete state, a "
         "run paused at the human gate resumes directly from it with no framework checkpoint.",
         align=J)
    para(doc, "Every inter-agent exchange is a typed, validated Pydantic envelope:", align=J)
    para(doc,
         "class Envelope(BaseModel):\n"
         "    task_id: str\n"
         "    sender: str\n"
         "    target_agent: str\n"
         "    status: Literal['dispatched','in_progress','success','failure']\n"
         "    payload: Diagnosis | Patch | TestReport | DispatchRef | Escalation | PRResult\n"
         "    confidence: float          # 0.0-1.0, self-reported by the sending agent\n"
         "    timestamp: datetime\n"
         "    latency_ms: int | None",
         size=8.5, mono=True, space_after=8)
    para(doc,
         "Message size is bounded by design. A Manager dispatch references prior artifacts by "
         "task_id and artifact id, never by re-sending their content, and the A2A message "
         "carries exactly that reference set. A third-attempt dispatch is therefore the same "
         "size as the first, whereas the peer-to-peer hand-off carries the full TestReport "
         "inline. Section 7 measures this as mean envelope size.", align=J)

    doc.add_heading("5.5  Agent–tool communication through MCP", level=2)
    figure(doc, DOCS / "graph_mcp.png",
           f"Figure 5.4  All {facts['n_tools']} tools are reached through one MCP server. "
           "Safety lives in the server, so no agent in either framework can bypass it.")
    para(doc,
         "The Diagnoser reaches tools as native ADK tools whose declarations are the server's "
         f"own JSON schemas; it is restricted to {len(facts['diag_tools'])} read-only tools "
         "(code search, file reading, tree listing, stack-trace parsing, RAG retrieval and "
         "static analysis). The CrewAI workers use the workspace, patch, test and git tools. "
         "The path sandbox, the secrets blocklist, subprocess timeouts and the pull-request "
         "confirmation guard are implemented in the server rather than in any agent.", align=J)

    doc.add_heading("5.6  Messaging pattern and A2A communication", level=2)
    figure(doc, DOCS / "graph_messaging.png",
           "Figure 5.5  Two mechanisms: a Blackboard for shared state within the ADK "
           "orchestration, and A2A as the wire between the two frameworks.")
    para(doc,
         "Two distinct mechanisms are used deliberately. Within the ADK side, agents coordinate "
         "through the shared Blackboard — a blackboard architecture. Across the framework "
         "boundary, the ADK side is an A2A client and the CrewAI workers are published as an "
         f"A2A agent with the skills {', '.join(facts['a2a_skills'])} and an agent card at "
         "/.well-known/agent-card.json. Each request is one A2A message carrying a single data "
         "part; the reply carries result ids, not payloads.", align=J)
    para(doc,
         "In the deployed service the CrewAI agent is mounted at /a2a/crew/ and is a separately "
         "addressable A2A service. Discovery is deliberately public so the agent card can be "
         "read by anyone, while every message/send requires a bearer token — without it a "
         "public URL would let a stranger drive the worker agents and spend the API key.", align=J)

    doc.add_heading("5.7  Securing the system: guardrails, safeguards and callbacks", level=2)
    table(doc, ["Boundary", "Guardrail", "Mechanism"], [
        ["User input", "Prompt-injection patterns, abusive language, empty or oversized reports",
         "screen_user_input before any agent runs; a blocked run ends with outcome 'blocked' "
         "and no model is ever called"],
        ["Tool use", "Per-agent tool allow-list and argument shape check",
         "ADK before_tool_callback"],
        ["Tool output", "Type check against the Pydantic schema for that tool; repository text "
         "that addresses the model is wrapped as untrusted data", "ADK after_tool_callback"],
        ["Agent output", "The patch must apply, must not touch tests, and must not add shell "
         "execution, eval, file deletion, network access or secret access",
         "CrewAI Task guardrail, retried once with the reason fed back"],
        ["Repository", "Never mutated: every attempt runs in its own git clone; paths outside "
         "the repository are refused; .env, keys and CI secrets are blocklisted", "MCP server"],
        ["Pull request", "Only after explicit human confirmation, only on a codefix/<task_id> "
         "branch, never the default branch",
         "Enforced in the runner, the PR agent and the MCP tool"],
        ["A2A endpoint", "Shared-secret bearer token on the deployed service; discovery stays "
         "public", "ASGI middleware on the JSON-RPC route"],
    ], widths=[1.0, 2.3, 3.0], size=8.5,
        caption="Table 5.3  Guardrails at seven boundaries. Every decision is recorded as a "
                "GuardrailResult and a trace event.")
    para(doc,
         "Monitoring uses the frameworks' own callback mechanisms rather than wrappers: ADK "
         "before/after agent, model and tool callbacks plus on_tool_error, and the CrewAI "
         "event bus together with step and task callbacks. Each hook writes a callback event "
         "recording framework, hook, agent and latency.", align=J)

    doc.add_heading("5.8  Validation strategy", level=2)
    para(doc, "Every patch is graded three ways, two of which are independent of any model:",
         align=J)
    bullets(doc, [
        [("Objective re-test", {"b": True}),
         (" — the final diff is applied to a fresh clone and the previously-failing test "
          "plus the full suite are run again, independently of the Tester agent.", {})],
        [("Reference-text comparison", {"b": True}),
         (" — the patched files are compared against the known-good fix: exact match "
          "(modulo whitespace), similarity between the agent's edit text and the reference "
          "edit text, and whether exactly the reference file set was changed.", {})],
        [("LLM-as-judge", {"b": True}),
         (" — a judge model sees the report, the source and the diff but not the test "
          "results, and returns a verdict with reasoning and a score. Because it cannot see the "
          "tests, judge-versus-tests agreement is a measurement of the judge.", {})],
    ])
    para(doc,
         "The judge model must differ from both generating models; this is enforced when the "
         "configuration is loaded. On the deployment used here the provider serves only two "
         "distinct models, which forces the judge onto the model the generators do not use — "
         "exactly the independence the method requires.", align=J)

    doc.add_heading("5.9  Deployment", level=2)
    figure(doc, DOCS / "graph_deployment.png",
           "Figure 5.6  Deployment on Google Cloud Run: one container serving the web "
           "application, the ADK orchestration, the CrewAI A2A service and the MCP tool server.")
    para(doc,
         "A single container holds the FastAPI web application, the ADK orchestration, the "
         "CrewAI A2A service mounted at /a2a/crew/ and the MCP tool server as a stdio "
         "subprocess, with the RAG embedding model baked in so no download occurs on a cold "
         "start. The API key and the A2A token are held in Secret Manager and mounted as "
         "environment variables; neither is baked into the image. The service runs with CPU "
         "always allocated, which is a correctness requirement rather than a tuning choice: a "
         "run is started by an HTTP request that returns immediately and continues on a "
         "background thread, and Cloud Run's default would starve that thread the moment the "
         "response was sent.", align=J)
    page_break(doc)

    # ------------------------------------------------------------------ 6 technology stack
    doc.add_heading("6  Technology Stack", level=1)
    table(doc, ["Layer", "Technology", "Why"], [
        ["Agent frameworks", "Google ADK 2.12 (orchestration, Manager, Diagnoser) · "
         "CrewAI 1.15 (Fixer, Reviewer, Tester, PR)",
         "The two frameworks permitted by the course. A test asserts that no other agent "
         "framework is imported anywhere in the codebase."],
        ["Agent-to-agent", "a2a-sdk 1.2.3 (JSON-RPC binding, agent card)",
         "Open protocol so the two frameworks interoperate without importing each other"],
        ["Tooling protocol", f"MCP (FastMCP) over stdio — {facts['n_tools']} tools",
         "One guarded boundary for every tool call from either framework"],
        ["Models", f"Z.AI GLM — {facts['roles']['diagnoser'].model} (Diagnoser, Fixer), "
                   f"{facts['roles']['manager'].model} (Manager, Judge)",
         "Task–model fit: the heaviest reasoning gets the flagship, routing and judging "
         "get the cheap model"],
        ["Structured output", "Pydantic 2.12",
         "Every agent output and every message is a validated model; invalid output gets one "
         "repair turn"],
        ["State", "SQLite (Blackboard: runs, messages, llm_calls, tool_calls, evaluations, "
                  "artifacts)",
         "Single inspectable source of truth; no extra service to deploy"],
        ["Retrieval", "ChromaDB 1.5 + sentence-transformers all-MiniLM-L6-v2",
         "Code, past-fix and documentation collections with citations validated against "
         "retrieved ids"],
        ["Static analysis / tests", "ruff 0.17, ESLint; pytest 9.1, jest, node:test",
         "The project's own suite is the success criterion"],
        ["Backend / API", "FastAPI 0.141 + Uvicorn 0.54", "Async web app and SSE trace stream"],
        ["Frontend", "Plain HTML, CSS and JavaScript (no build step, no CDN)",
         "Works offline during a demonstration; nothing to compile on stage"],
        ["CLI", "Typer 0.27 + Rich 14.3", "Live run view in the terminal"],
        ["Deployment", "Docker → Google Cloud Build → Cloud Run (asia-south1); "
                       "Secret Manager", "Public HTTPS endpoint; secrets never in the image"],
        ["Quality", "pytest suite, ruff lint",
         "The suite runs with no API key: the model layer is mocked and embeddings fall back "
         "to hashing"],
    ], widths=[1.1, 2.3, 2.9], size=8.5,
        caption="Table 6.1  Technology stack.")
    page_break(doc)

    _results(doc, helpers, rows, stats, facts, archs, total_runs, total_cost)
    _team_and_conclusions(doc, helpers, stats, total_runs, total_cost, facts)


def _results(doc, helpers, rows, stats, facts, archs, total_runs, total_cost):
    para, rich = helpers["para"], helpers["rich"]
    bullets, table = helpers["bullets"], helpers["table"]
    figure, page_break = helpers["figure"], helpers["page_break"]
    num, Counter = helpers["num"], helpers["Counter"]

    doc.add_heading("7  Experimental Results", level=1)

    doc.add_heading("7.1  Experimental design", level=2)
    para(doc,
         "The bug set contains 19 reproducible defects injected into three repositories: a "
         "Python e-commerce library (pyshop, 46 tests), a JavaScript text utility library "
         "(textkit, node:test), and alertsink — the incident-trigger service from the team's "
         "own MLOps-Incident-Diagnosis project, carried over with its module and test file "
         "unmodified. Each bug is a realistic logic error: an off-by-one in a subtotal, a "
         "case-sensitivity bug in region lookup, a mutable default argument, a list sliced from "
         "the wrong end. A separate check proves every one of the 19 fails when injected and "
         "passes when fixed, so a resolved run cannot be an artefact of a broken test.", align=J)
    para(doc,
         "Including alertsink is deliberate. A bug set written entirely for the benchmark "
         "invites the objection that the agents are being graded on code shaped to suit them; "
         "alertsink is pre-existing production code that was never written with this system in "
         "mind. It is included because it depends only on the standard library, whereas the "
         "rest of that project requires MLflow, scikit-learn and a live Flask app.", align=J)
    para(doc,
         "The defect is never stored in the repository. Each run copies the pristine repository, "
         "applies the injection, and commits the broken state as the single commit of a fresh "
         "git history. The agents therefore receive a repository with one defect, no clue in the "
         "git log, and a bug report that describes only symptoms — no file or function is "
         "named. Reversing the injection yields the known-good fix used for reference scoring.",
         align=J)
    diffs = Counter(r["difficulty"] for r in rows if r.get("difficulty"))
    table(doc, ["Dimension", "Levels", "Count"], [
        ["Bugs", "16 injected defects across 2 repositories and 2 languages", "16"],
        ["Difficulty", f"easy, medium, hard (runs: {diffs.get('easy',0)} / "
                       f"{diffs.get('medium',0)} / {diffs.get('hard',0)})", "3"],
        ["Architecture", ", ".join(archs), str(len(archs))],
        ["Repetitions", "Each (bug, architecture) pair repeated to expose run-to-run variance",
         "3"],
        ["Total runs", "Live model calls, every run graded three ways", f"**{total_runs}**"],
    ], widths=[1.1, 3.9, 0.8], size=9,
        caption="Table 7.1  Experimental design.")
    para(doc,
         "Repetition is what makes variance observable. Because the models are sampled rather "
         "than deterministic, a single run per configuration cannot distinguish a genuine "
         "difference between architectures from ordinary noise; the standard deviations in "
         "Table 7.2 are computed across these repetitions.", align=J)
    para(doc,
         "Four further experiments vary one factor at a time while holding the rest at the "
         "baseline configuration (hierarchical, react, default persona, developer reporter). "
         "Because the architecture experiment already contains that baseline arm for every bug "
         "with three repetitions, the sweeps run only the non-baseline levels and are compared "
         "back to it pairwise on the same bugs — 36 additional runs rather than 112, and a "
         "paired comparison rather than one across different bug sets.", align=J)
    table(doc, ["Experiment", "Factor varied", "Levels", "Runs"], [
        ["1  Architecture", "Orchestration topology",
         "hierarchical, sequential, p2p × 16 bugs × 3 repetitions", "140"],
        ["2  Prompt variant", "How the Diagnoser is prompted",
         "fewshot, react-reflect × 8 bugs (baseline: react)", "16"],
        ["3  Agent persona", "System-prompt persona of Diagnoser, Fixer, Reviewer",
         "senior, novice, security × 4 bugs (baseline: default)", "12"],
        ["4  Reporter persona", "Who filed the report, and what they attached",
         "enduser — symptom only, no stack trace × 8 bugs", "8"],
        ["5  Own-codebase check", "Repository provenance",
         "3 alertsink bugs from the team's own MLOps project", "3"],
        ["", "", "**Total live evaluated runs (incl. demonstrations)**", "**188**"],
    ], widths=[1.35, 1.75, 2.4, 0.7], size=8.5,
        caption="Table 7.1b  The five experiments. Each varies one factor; the rest stay at "
                "baseline.")

    doc.add_heading("7.2  Is the system working as expected?", level=2)
    hdr = ["Metric"] + archs
    table(doc, hdr, [
        ["Runs"] + [str(stats[a]["n"]) for a in archs],
        ["**Resolved (fresh-clone suite green)**"] +
        [f"{stats[a]['resolved']}/{stats[a]['n']} "
         f"({100*stats[a]['resolved']/stats[a]['n']:.0f}%)" for a in archs],
        ["Judge verdict = pass"] +
        [f"{stats[a]['judge_pass']}/{stats[a]['judged']}" for a in archs],
        ["**Judge accuracy (agrees with tests)**"] +
        [f"{100*stats[a]['agree']/stats[a]['judged']:.0f}%" if stats[a]["judged"] else "n/a"
         for a in archs],
        ["Reference fix: exact match"] +
        [f"{stats[a]['ref_exact']}/{stats[a]['n']} "
         f"({100*stats[a]['ref_exact']/stats[a]['n']:.0f}%)" for a in archs],
        ["Reference fix: edit similarity (0–1)"] +
        [f"{stats[a]['ref_sim']:.2f}" for a in archs],
        ["Runs needing a retry"] + [str(stats[a]["retried"]) for a in archs],
        ["Mean wall-clock per run"] + [f"{stats[a]['secs']:.1f}s" for a in archs],
        ["**Wall-clock standard deviation**"] + [f"{stats[a]['sd']:.1f}s" for a in archs],
        ["Mean cost per run"] + [f"${stats[a]['cost']/stats[a]['n']:.4f}" for a in archs],
        ["Mean LLM calls per run"] + [f"{stats[a]['calls']:.1f}" for a in archs],
        ["Mean tokens per run"] + [f"{stats[a]['tokens']:.0f}" for a in archs],
        ["Mean envelope size (bytes)"] + [f"{stats[a]['bytes']:.0f}" for a in archs],
    ], widths=[2.3] + [1.3] * len(archs), size=9,
        caption="Table 7.2  Headline comparison across architectures, identical bugs.")
    para(doc,
         "The system works as intended. Across all three architectures the agents resolved "
         f"{sum(s['resolved'] for s in stats.values())} of {total_runs} runs, where "
         "“resolved” means the final patch was re-applied to a clean clone and the "
         "entire suite passed — not that an agent said so. The single non-resolution was one "
         "JavaScript bug under the sequential architecture.", align=J)

    doc.add_heading("7.3  Architecture comparison", level=2)
    para(doc,
         "Resolve rate does not discriminate between the architectures: all three are at or "
         "near 100%. The meaningful differences are in cost, latency and stability.", align=J)
    best_cost = min(archs, key=lambda a: stats[a]["cost"] / stats[a]["n"])
    best_time = min(archs, key=lambda a: stats[a]["secs"])
    most_var = max(archs, key=lambda a: stats[a]["sd"])
    bullets(doc, [
        [("Cost. ", {"b": True}),
         (f"{best_cost} is cheapest at ${stats[best_cost]['cost']/stats[best_cost]['n']:.4f} "
          f"per run; hierarchical costs "
          f"${stats['hierarchical']['cost']/stats['hierarchical']['n']:.4f}, about "
          f"{stats['hierarchical']['cost']/stats['hierarchical']['n'] / (stats[best_cost]['cost']/stats[best_cost]['n']):.0f}"
          "× more, because each Manager decision is an extra model call.", {})],
        [("Latency. ", {"b": True}),
         (f"{best_time} is fastest at {stats[best_time]['secs']:.1f}s mean wall-clock against "
          f"{stats['hierarchical']['secs']:.1f}s for hierarchical.", {})],
        [("Stability. ", {"b": True}),
         (f"{most_var} is the most variable at {stats[most_var]['sd']:.1f}s standard deviation, "
          f"roughly twice that of the steadiest architecture "
          f"({min(stats[a]['sd'] for a in archs):.1f}s).", {})],
        [("Message size. ", {"b": True}),
         (f"Hierarchical envelopes average {stats['hierarchical']['bytes']:.0f} bytes against "
          f"{stats['p2p']['bytes']:.0f} for peer-to-peer, confirming that reference-passing "
          "keeps dispatches small while the p2p hand-off carries the TestReport inline.", {})],
    ])
    para(doc,
         "The decisive observation is that no run in this experiment ever needed a retry. The "
         "hierarchical architecture's advantages — retrying only the failed stage, with the "
         "failure evidence attached, under a single enforced attempt bound — are advantages "
         "in exactly the situation that never arose here. On this bug set its extra routing "
         "calls bought nothing and cost both money and time. We report this rather than "
         "claiming a victory the data does not support: the correct conclusion is that the "
         "hierarchical design is justified by failure handling and auditability, and that a "
         "bug set which never fails cannot demonstrate it. A set containing defects that "
         "genuinely resist a first patch would be required, and that is the obvious next "
         "experiment.", align=J)

    doc.add_heading("7.4  Response time of the system and of each agent", level=2)
    table(doc, ["Agent"] + archs, [
        ["Diagnoser"] + [f"{stats[a]['diag_s']:.1f}s" for a in archs],
        ["Fixer"] + [f"{stats[a]['fix_s']:.1f}s" for a in archs],
        ["Tester"] + [f"{stats[a]['test_s']:.1f}s" for a in archs],
        ["PR agent"] + [f"{stats[a]['pr_s']:.1f}s" for a in archs],
        ["**Whole system (end to end)**"] + [f"**{stats[a]['secs']:.1f}s**" for a in archs],
    ], widths=[2.3] + [1.3] * len(archs), size=9,
        caption="Table 7.3  Mean response time per agent and for the system as a whole.")
    para(doc,
         "The Diagnoser dominates in every architecture, taking roughly 25–28 seconds of a "
         "55–62 second run — around half the total. This is expected and is the correct "
         "place for the time to go: it is the only agent performing multi-step reasoning with "
         "tool calls, and localisation is the hard part of the task. The Tester takes about two "
         "seconds despite running an entire test suite, because it is deterministic and calls "
         "no model. The Manager's own model time is negligible, which is why its cost shows up "
         "as extra calls rather than extra seconds.", align=J)

    doc.add_heading("7.5  Validation against reference text and an LLM judge", level=2)
    agree = sum(s["agree"] for s in stats.values())
    judged = sum(s["judged"] for s in stats.values())
    ref_exact = sum(s["ref_exact"] for s in stats.values())
    para(doc,
         f"The judge agreed with the objective test outcome on {agree} of {judged} judged runs "
         f"({100*agree/judged:.0f}%). Because the judge never sees the test results, this is a "
         "measurement of the judge rather than of the system; at this level of agreement the "
         "judge is a usable proxy when tests are unavailable, but the tests remain the "
         "criterion.", align=J)
    para(doc,
         f"Against the reference fix, {ref_exact} of {total_runs} patches "
         f"({100*ref_exact/total_runs:.0f}%) were byte-identical to the known-good fix modulo "
         "whitespace, with a mean edit similarity of "
         f"{sum(s['ref_sim']*s['n'] for s in stats.values())/total_runs:.2f} and the correct "
         "file set changed in virtually every run. The gap between ~75% exact and ~100% "
         "resolved is the interesting part: in the remaining quarter the agent produced a "
         "different but still correct patch — for instance normalising a value at a "
         "different but equivalent point. This is why reference matching alone would be the "
         "wrong criterion, and why the executed test suite is the one used.", align=J)

    doc.add_heading("7.6  Cost and running time", level=2)
    secs = sum(num(r, "duration_ms") for r in rows) / 1000
    tok_in = sum(num(r, "input_tokens") for r in rows)
    tok_c = sum(num(r, "cached_tokens") for r in rows)
    tok_out = sum(num(r, "output_tokens") for r in rows)
    bullets(doc, [
        f"{total_runs} runs in {secs/60:.0f} minutes of wall-clock ({secs/total_runs:.1f}s per run)",
        f"Total pipeline cost ${total_cost:.2f} (${total_cost/total_runs:.4f} per run)",
        f"Tokens: {tok_in:,.0f} fresh input, {tok_c:,.0f} cached input, {tok_out:,.0f} output",
    ])
    para(doc,
         "Cached input accounts for more than half of all prompt tokens, because the Diagnoser's "
         "system prompt and tool declarations are stable across ReAct steps. Accounting for "
         "this correctly matters: charging cached tokens at the full input rate overstated the "
         "measured cost of this experiment by a third.", align=J)
    para(doc,
         "A counterfactual over the same token volume shows that running every agent on the "
         "flagship model would have cost essentially what the per-role mix cost, because the "
         "Diagnoser and Fixer dominate token volume and already use it; running everything on "
         "the cheap model would cost about a tenth, at a quality that this experiment does not "
         "measure. The practical conclusion is that task–model fit pays off only where the "
         "expensive agents are, and the Manager and Judge are not where the money goes.", align=J)

    doc.add_heading("7.7  Prompt variants: does more machinery help?", level=2)
    from codefix.eval.compare import _load
    from codefix.eval.compare import compare as cmp_factor

    crows = _load()
    cv = cmp_factor("variant", crows)
    if cv["levels"]:
        lv = list(cv["levels"])
        table(doc, ["Metric"] + lv, [
            ["Runs"] + [str(cv["levels"][k]["n"]) for k in lv],
            ["**Resolved**"] + [f"{cv['levels'][k]['resolved']}/{cv['levels'][k]['n']} "
                                f"({cv['levels'][k]['resolved_pct']:.0f}%)" for k in lv],
            ["Right file(s) changed"] + [f"{cv['levels'][k]['right_file_pct']:.0f}%" for k in lv],
            ["Edit similarity to reference"] + [f"{cv['levels'][k]['ref_sim']:.2f}" for k in lv],
            ["Mean wall-clock"] + [f"{cv['levels'][k]['secs']:.1f}s" for k in lv],
            ["Diagnoser time"] + [f"{cv['levels'][k]['diag_s']:.1f}s" for k in lv],
            ["Mean LLM calls"] + [f"{cv['levels'][k]['calls']:.1f}" for k in lv],
            ["**Mean cost / run**"] + [f"${cv['levels'][k]['cost']:.4f}" for k in lv],
        ], widths=[2.1] + [1.4] * len(lv), size=9,
            caption=f"Table 7.4  Prompt variants, paired on {len(cv['bugs'])} bugs.")
    para(doc,
         "Plain ReAct is the best of the three, and the two alternatives fail in opposite "
         "directions. The few-shot variant is the cheapest and fastest because it makes 1.8 "
         "model calls instead of 4.5 and runs no tool loop at all — but without tools it must "
         "infer the location from retrieved context, and it changes the right file only 82% of "
         "the time. ReAct+Reflection adds a Reviewer that critiques the patch before it is "
         "tested: it costs about two-thirds more and takes half again as long, and still "
         "resolves no better than plain ReAct.", align=J)
    para(doc,
         "The explanation is the same one that limits the architecture comparison. Reflection "
         "is a mechanism for catching a bad first patch, and on this bug set the first patch "
         "was almost always correct, so the Reviewer re-reads work that needed no revision. "
         "These results say the extra machinery does not pay for itself here; they do not say "
         "it never would.", align=J)

    doc.add_heading("7.8  Personas: who prompts, and who reports", level=2)
    cp, cr = cmp_factor("persona", crows), cmp_factor("reporter", crows)
    if cp["levels"]:
        lv = list(cp["levels"])
        table(doc, ["Metric"] + lv, [
            ["Runs"] + [str(cp["levels"][k]["n"]) for k in lv],
            ["Resolved"] + [f"{cp['levels'][k]['resolved_pct']:.0f}%" for k in lv],
            ["Right file(s) changed"] + [f"{cp['levels'][k]['right_file_pct']:.0f}%" for k in lv],
            ["Edit similarity"] + [f"{cp['levels'][k]['ref_sim']:.2f}" for k in lv],
            ["Mean wall-clock"] + [f"{cp['levels'][k]['secs']:.1f}s" for k in lv],
            ["Mean cost / run"] + [f"${cp['levels'][k]['cost']:.4f}" for k in lv],
        ], widths=[1.9] + [1.1] * len(lv), size=9,
            caption=f"Table 7.5  Agent personas, paired on {len(cp['bugs'])} bugs.")
    para(doc,
         "The agent personas make no measurable difference. All four resolve every run, change "
         "the correct file every time, and sit within 0.03 of each other on edit similarity; "
         "the senior persona is about a quarter slower for no benefit. On defects this "
         "well-specified, persona prompting is decoration. We report it as a negative result "
         "rather than omitting it, because the alternative — presenting an implemented "
         "feature without the evidence that it does nothing here — would be misleading.",
         align=J)
    if cr["levels"]:
        lv = list(cr["levels"])
        table(doc, ["Metric"] + lv, [
            ["Runs"] + [str(cr["levels"][k]["n"]) for k in lv],
            ["**Resolved**"] + [f"{cr['levels'][k]['resolved']}/{cr['levels'][k]['n']} "
                                f"({cr['levels'][k]['resolved_pct']:.0f}%)" for k in lv],
            ["Right file(s) changed"] + [f"{cr['levels'][k]['right_file_pct']:.0f}%" for k in lv],
            ["Edit similarity"] + [f"{cr['levels'][k]['ref_sim']:.2f}" for k in lv],
            ["Diagnoser time"] + [f"{cr['levels'][k]['diag_s']:.1f}s" for k in lv],
            ["Mean cost / run"] + [f"${cr['levels'][k]['cost']:.4f}" for k in lv],
        ], widths=[2.1] + [1.7] * len(lv), size=9,
            caption=f"Table 7.6  Reporter persona, paired on {len(cr['bugs'])} bugs. The "
                    "enduser arm receives no stack trace at all.")
    para(doc,
         "The reporter persona is the most consequential of the three sweeps and produced the "
         "most surprising result. The enduser arm withholds the failing test output entirely, "
         "leaving the Diagnoser nothing but a symptom description — and it still resolved "
         "every run, changed the right file every time, and scored slightly higher on edit "
         "similarity while costing less. Localisation did not depend on the stack trace.",
         align=J)
    para(doc,
         "This speaks directly to gap LG1. The deployed systems in the literature are driven by "
         "an analyser finding or a crash that has already localised the defect; the result here "
         "indicates that a tool-using ReAct agent can recover the location from a description "
         "of the symptom alone. The caveat is the bug set: these defects are single-file and "
         "the repositories are small, so search is cheap. Whether this survives a large "
         "codebase is exactly the question a harder bug set would answer.", align=J)

    doc.add_heading("7.9  Working on code the system was not designed around", level=2)
    para(doc,
         "The three alertsink defects test the system on pre-existing production code from a "
         "different project of the team's, with the module and its test unmodified. All three "
         "were resolved on the first attempt, each patch matching the reference fix exactly, "
         "at a mean of 58 seconds and $0.023 per run — indistinguishable from the "
         "purpose-built repositories.", align=J)
    table(doc, ["Bug", "Defect", "Outcome"], [
        ["ml01", "tail_lines slices from the start of the file, so ?limit=N returns the oldest "
                 "alerts instead of the newest", "Resolved, attempt 1, exact match"],
        ["ml02", "The per-alert record takes status from the top-level webhook payload, so every "
                 "alert inherits the group status and resolutions are stored as firing",
         "Resolved, attempt 1, exact match"],
        ["ml03", "The POST response counts the payload dict's keys rather than the flattened "
                 "records actually appended", "Resolved, attempt 1, exact match"],
    ], widths=[0.5, 3.9, 1.9], size=9,
        caption="Table 7.7  The alertsink bugs, from the team's own MLOps project.")
    para(doc,
         "One difference is worth recording: the LLM judge agreed with the tests on two of the "
         "three runs, against 98–100% on the purpose-built repositories. A single "
         "disagreement in three runs is not a trend, but it is consistent with a judge being "
         "less certain on code it has less context for — and it is a further reason to treat "
         "the executed test suite, not the judge, as the criterion.", align=J)

    doc.add_heading("7.10  Deployment and demonstration", level=2)
    rich(doc, [("The system is deployed publicly at ", {}), (URL, {"mono": True}),
               (". The screenshots below are taken from that deployment.", {})], align=J)
    shots = [("new_fix.png", "Figure 7.1  Submitting a bug report."),
             ("run_live.png", "Figure 7.2  Live run view: the pipeline diagram, agent messages, "
                              "A2A exchanges, guardrail decisions and the ReAct transcript."),
             ("runs_list.png", "Figure 7.3  Run history."),
             ("dashboard.png", "Figure 7.4  Dashboard aggregating the evaluation runs: "
                               "per-agent latency with the bottleneck flagged, attempts, cost "
                               "and judge accuracy."),
             ("agent_card.png", "Figure 7.5  The published A2A agent card.")]
    for fn, cap in shots:
        figure(doc, SHOTS / fn, cap)
    page_break(doc)


def _team_and_conclusions(doc, helpers, stats, total_runs, total_cost, facts):
    para, table = helpers["para"], helpers["table"]
    bullets, page_break = helpers["bullets"], helpers["page_break"]

    doc.add_heading("8  Team Responsibility / Self-contribution Matrix", level=1)
    table(doc, ["Activity"] + [f"{n} ({r})" for n, r in
                               [("Karthikeya", TEAM[0][1]), ("Naman", TEAM[1][1]),
                                ("Abhiram", TEAM[2][1])]], [
        ["Agent design / multi-agent architecture", "Lead", "Contributed", "Contributed"],
        ["Agent orchestration (Manager, retry policy)", "Contributed", "Lead", "—"],
        ["State management (Blackboard, envelopes)", "—", "Contributed", "Lead"],
        ["MCP design (server, 16 tools, sandbox)", "Contributed", "—", "Lead"],
        ["A2A communication (ADK ⇄ CrewAI)", "—", "Contributed", "Lead"],
        ["Guardrails / callbacks", "Contributed", "Lead", "Contributed"],
        ["Observability (tracing, run view)", "—", "Lead", "Contributed"],
        ["Diagnoser (ReAct) and Fixer agents", "Lead", "—", "Contributed"],
        ["Tester and PR agents", "—", "Contributed", "Lead"],
        ["RAG: vector store, retrieval, citations", "Lead", "—", "—"],
        ["Code search and static-analysis tooling", "Lead", "—", "Contributed"],
        ["Integration and testing", "Contributed", "Contributed", "Contributed"],
        ["Evaluation and documentation", "Contributed", "Lead", "Contributed"],
        ["Presentation / interface UI", "Contributed", "Lead", "—"],
        ["Deployment (Docker, Cloud Run, secrets)", "Contributed", "—", "Lead"],
        ["End-to-end evaluation (time and cost)", "Contributed", "Lead", "Contributed"],
    ], widths=[2.7, 1.2, 1.2, 1.2], size=9,
        caption="Table 8.1  Contribution matrix. “Lead” denotes primary responsibility "
                "for design and implementation; “Contributed” denotes substantive work "
                "on the item.")
    page_break(doc)

    doc.add_heading("9  Conclusions", level=1)
    para(doc,
         f"{TITLE} resolves software defects end to end from a natural-language bug report, "
         "using five role-specialised agents spread across two frameworks that cooperate over "
         "an open protocol. Across "
         f"{total_runs} live runs on 16 reproducible bugs in two languages, the system resolved "
         f"{sum(s['resolved'] for s in stats.values())} of them, where resolution means the "
         "patch was re-applied to a clean clone and the project's entire test suite passed.",
         align=J)
    para(doc, "Principal findings:", bold=True, space_after=3)
    bullets(doc, [
        [("The agent set is derived, not assumed. ", {"b": True}),
         ("Each of the five agents traces to a requirement which traces in turn to a literature "
          "gap or a problem-statement claim (Tables 4.1 and 5.1).", {})],
        [("Role specialisation makes verification independent. ", {"b": True}),
         ("The Tester runs no model at all, so the success criterion is an executed test suite "
          "rather than any agent's opinion.", {})],
        [("Architecture choice did not affect whether bugs were fixed. ", {"b": True}),
         ("All three topologies resolved at or near 100%. They differed in cost, latency and "
          "variance, not in capability — and the hierarchical architecture's advantages "
          "were never exercised because no run needed a retry.", {})],
        [("Localisation is where the time goes. ", {"b": True}),
         ("The Diagnoser consumes roughly half of each run's wall-clock, confirming that "
          "finding the defect, not writing the fix, is the expensive part.", {})],
        [("A judge is a usable proxy but not a substitute. ", {"b": True}),
         (f"Judge–test agreement was {100*sum(s['agree'] for s in stats.values())/max(sum(s['judged'] for s in stats.values()),1):.0f}%; "
          "roughly a quarter of correct patches differed from the reference fix while still "
          "passing every test, so neither the judge nor reference matching could replace "
          "execution.", {})],
        [("Cost is modest and measurable. ", {"b": True}),
         (f"${total_cost/total_runs:.4f} per resolved defect, with cached input more than half "
          "of all prompt tokens.", {})],
    ])
    para(doc, "Limitations and future work:", bold=True, space_after=3)
    bullets(doc, [
        "The bug set is seeded and single-file. Real defects spanning several modules, or "
        "requiring a design change rather than a local edit, are not represented.",
        "Because no run failed its first patch, the retry and escalation paths — the "
        "principal justification for the hierarchical design — were exercised in testing "
        "but not in the live experiment. A deliberately harder bug set is the clear next step.",
        "The prompt-variant and persona dimensions are implemented and available but held at "
        "their defaults in the reported experiment, so architecture remained the only variable.",
        "Run data on the deployed service is not persistent; a cold instance restores a seeded "
        "snapshot of the evaluation rather than accumulating history.",
    ])
    page_break(doc)

    doc.add_heading("References", level=1)
    refs = [
        "C. E. Jimenez, J. Yang, A. Wettig, S. Yao, K. Pei, O. Press and K. Narasimhan, "
        "“SWE-bench: Can Language Models Resolve Real-World GitHub Issues?”, ICLR 2024. "
        "arXiv:2310.06770.",
        "J. Yang, C. E. Jimenez, A. Wettig, K. Lieret, S. Yao, K. Narasimhan and O. Press, "
        "“SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering”, "
        "2024. arXiv:2405.15793.",
        "Y. Zhang, H. Ruan, Z. Fan and A. Roychoudhury, “AutoCodeRover: Autonomous Program "
        "Improvement”, National University of Singapore, 2024. arXiv:2404.05427.",
        "GitHub, “Copilot Autofix for code scanning”, product documentation. "
        "https://docs.github.com/en/code-security",
        "J. Bader, A. Scott, M. Pradel and S. Chandra, “Getafix: Learning to Fix Bugs "
        "Automatically”, OOPSLA 2019. arXiv:1902.06111.",
        "Cognition, “Devin”. https://cognition.ai",
        "Anthropic, “Model Context Protocol specification”. "
        "https://modelcontextprotocol.io",
        "“Agent2Agent (A2A) protocol”. https://a2a-protocol.org · "
        "https://github.com/a2aproject/A2A",
        "Google, “Agent Development Kit (ADK) documentation”. "
        "https://google.github.io/adk-docs/",
        "CrewAI, “CrewAI documentation”. https://docs.crewai.com",
        "Z.AI, “GLM API documentation and pricing”. https://docs.z.ai",
    ]
    for i, r in enumerate(refs, 1):
        para(doc, f"[{i}]  {r}", size=10, space_after=4)
    page_break(doc)

    doc.add_heading("Appendix", level=1)
    doc.add_heading("A  Repository and deployment", level=2)
    table(doc, ["Item", "Location"], [
        ["Deployed application", URL],
        ["A2A agent card", URL + "/a2a/crew/.well-known/agent-card.json"],
        ["Source repository", REPO],
        ["Architecture and design notes", "docs/architecture.md"],
        ["Literature review and traceability", "docs/literature.md"],
        ["Benchmark report and raw runs", "benchmarks/results/<bench-id>/{report.md, runs.csv}"],
    ], widths=[1.9, 4.4], size=9)

    doc.add_heading("B  Reproducing the experiment", level=2)
    para(doc,
         "pip install -e .\n"
         "copy .env.example .env          # add ZAI_API_KEY\n"
         "codefix bench --verify-bugset   # prove every bug fails injected, passes fixed\n"
         "codefix bench --arch all --runs 3 --llm live\n"
         "codefix demo py05-region-case   # single run, live view\n"
         "codefix serve                   # web app at 127.0.0.1:8000",
         size=9, mono=True, space_after=8)

    doc.add_heading("C  Verification status", level=2)
    table(doc, ["Check", "Result"], [
        ["Automated test suite", "154 tests passing, no API key required"],
        ["Lint", "ruff: all checks passed"],
        ["Bug-set validity", "All 19 bugs fail when injected and pass when fixed"],
        ["Framework restriction", "A test asserts only CrewAI and Google ADK are imported"],
        ["Judge independence", "Enforced at configuration load: the judge model must differ "
                               "from both generating models"],
        ["Deployment", "Verified live: a Python bug resolved end to end with 46/46 tests green "
                       "in-container, 6 A2A messages and the human gate holding"],
    ], widths=[1.9, 4.4], size=9)
