"""Slides 8-14 of the final presentation."""

from __future__ import annotations

from build_slides import (
    ACCENT,
    DOCS,
    GOOD,
    MUTED,
    REPO,
    TEAM,
    URL,
    WARN,
    box,
    bullets,
    callout,
    picture,
    put,
    rich,
    slide_base,
    stat,
    table,
)
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


def slide8(prs):
    s = slide_base(prs, 8, "Securing the Multi-Agent System",
                   "Guardrails at seven boundaries · safeguards inside the tool server "
                   "· framework callbacks for provenance")
    table(s, Inches(0.4), Inches(1.4), Inches(8.5),
          ["Boundary", "Guardrail", "Mechanism"],
          [["User input", "Prompt injection, abusive language, empty/oversized reports",
            "screen_user_input — a blocked run calls no model at all"],
           ["Tool use", "Per-agent allow-list and argument shape",
            "ADK before_tool_callback"],
           ["Tool output", "Pydantic type check; repo text wrapped as untrusted data",
            "ADK after_tool_callback"],
           ["Agent output", "Patch must apply, must not touch tests, no shell/eval/network",
            "CrewAI Task guardrail — one retry with the reason"],
           ["Repository", "Never mutated: isolated clone per attempt; .env and keys blocklisted",
            "MCP server sandbox"],
           ["Pull request", "Human confirmation; only a codefix/* branch, never the default",
            "Runner, PR agent **and** MCP tool all enforce it"],
           ["A2A endpoint", "Bearer token on message/send; discovery deliberately public",
            "ASGI middleware on the JSON-RPC route"]],
          size=10.5, head_size=11, col_w=[1.5, 4.0, 4.3], row_h=0.5)

    tf = box(s, Inches(9.25), Inches(1.4), Inches(3.65), Inches(1.6))
    put(tf, "Callbacks (monitoring)", size=14.5, bold=True, color=ACCENT, first=True, space=6)
    put(tf, "The frameworks' own hooks, not wrappers: ADK before/after agent, model and tool, "
            "plus on_tool_error; CrewAI event bus with step and task callbacks. Each records "
            "framework, hook, agent and latency.", size=11.5, color=MUTED, space=0)
    callout(s, Inches(9.25), Inches(3.2), Inches(3.65), Inches(1.75),
            [("Live proof on the deployment\n\n", {"b": True, "c": ACCENT}),
             ("POST /a2a/crew/ (no token)\n", {"font": "Consolas", "size": 10.5}),
             ("   → 401 Unauthorized\n\n", {"font": "Consolas", "size": 10.5, "c": GOOD,
                                                 "b": True}),
             ("GET agent-card.json\n", {"font": "Consolas", "size": 10.5}),
             ("   → 200 OK", {"font": "Consolas", "size": 10.5, "c": GOOD, "b": True})],
            size=11.5)
    callout(s, Inches(9.25), Inches(5.15), Inches(3.65), Inches(1.9),
            [("A gate, not a prompt.  ", {"b": True, "c": ACCENT}),
             ("The MCP tool itself refuses to open a PR unless ", {}),
             ("confirmed=true", {"font": "Consolas", "size": 10.5}),
             (" and the branch is ", {}), ("codefix/*", {"font": "Consolas", "size": 10.5}),
             (". Three independent layers must agree before anything leaves the sandbox.", {})],
            size=11.5)
    notes(s, "Demo-able live: curl the A2A endpoint without a token and get 401; fetch the "
             "agent card and get 200. Discovery is public by design; acting requires the "
             "secret.")


def slide9(prs, cmp_v, cmp_p, cmp_r, study):
    ex, ot = study["experiments"], study["other"]
    s = slide_base(prs, 9, "Experimental Design for Validation",
                   f"{study['recorded']} live runs recorded · one factor varied at a time "
                   "· repetitions expose variance")
    table(s, Inches(0.4), Inches(1.35), Inches(7.7),
          ["Experiment", "Factor varied", "Levels", "Runs"],
          [["1  Architecture", "Orchestration topology",
            "hierarchical / sequential / p2p × 16 bugs × 3 reps",
            f"**{ex['architecture']}**"],
           ["2  Prompt variant", "How the Diagnoser is prompted",
            "fewshot, react-reflect × 8 bugs", str(ex["variant"])],
           ["3  Agent persona", "Persona in the agents' system prompts",
            "senior, novice, security × 4 bugs", str(ex["persona"])],
           ["4  Reporter persona", "Who filed it, and what they attached",
            "enduser — symptom only, no stack trace", str(ex["reporter"])],
           ["5  Own codebase", "Repository provenance",
            "3 bugs in the team's own MLOps project", str(ex["own_code"])],
           ["Other", "Not a reported experiment",
            f"pilot {ot['pilot']} · cancelled sweep {ot['cancelled']} · demos {ot['demos']}",
            str(sum(ot.values()))],
           ["", "", "**Total live runs recorded**", f"**{study['recorded']}**"]],
          size=10.5, col_w=[1.7, 2.3, 4.2, 0.8], row_h=0.37)

    stat(s, Inches(8.4), Inches(1.35), Inches(2.15), str(study["recorded"]), "live runs recorded")
    stat(s, Inches(10.75), Inches(1.35), Inches(2.15), str(study["bugs"]), "reproducible bugs")

    tf = box(s, Inches(8.4), Inches(2.65), Inches(4.5), Inches(1.5))
    put(tf, "Coverage", size=14, bold=True, color=ACCENT, first=True, space=6)
    put(tf, "3 repositories · 2 languages · 3 difficulty levels (6 easy, 8 medium, "
            "2 hard, plus 3 in our own code). Every bug is proven to fail when injected and "
            "pass when fixed.", size=11.5, color=MUTED, space=0)

    callout(s, Inches(0.4), Inches(4.85), Inches(7.7), Inches(1.0),
            [("Variance.  ", {"b": True, "c": ACCENT}),
             ("Models are sampled, not deterministic, so one run per configuration cannot tell "
              "a real difference from noise. Every (bug, architecture) pair is repeated ", {}),
             ("three times", {"b": True}),
             (", and the std-dev in Slide 5 is computed across those repetitions: 23.0s for "
              "hierarchical against 11.2s for sequential.", {})], size=11.5)
    callout(s, Inches(0.4), Inches(6.0), Inches(12.5), Inches(1.1),
            [("Efficient design.  ", {"b": True, "c": ACCENT}),
             ("Experiment 1 already contains the baseline arm (hierarchical / react / default / "
              "developer) for every bug, three times over. Sweeps 2-4 therefore run ", {}),
             ("only the non-baseline levels", {"b": True}),
             (" and are compared back to it ", {}), ("pairwise on the same bugs", {"b": True}),
             (" — 36 extra runs instead of 112, and a paired comparison rather than one "
              "across different bug sets.", {})], size=11.5)
    notes(s, "Two persona dimensions: agent personas change the system prompts; reporter "
             "personas change who filed the report. The end-user persona withholds the stack "
             "trace entirely, which is the real test of localisation.")


def slide10(prs, stats, cmp_v, cmp_r, study):
    s = slide_base(prs, 10, "Validating the Multi-Agent System",
                   f"Graded three ways, two of them model-free · all {study['graded']} "
                   "graded runs across the five experiments")
    archs = list(stats)
    # headline figures are study-wide; the latency table below is the architecture experiment
    tot_n, tot_res = study["graded"], study["resolved"]
    tot_ag, tot_j, tot_rx = study["agree"], study["graded"], study["exact"]

    stat(s, Inches(0.45), Inches(1.3), Inches(2.9), f"{100*tot_res/tot_n:.1f}%",
         f"resolved — {tot_res}/{tot_n} runs, fresh-clone suite green", color=GOOD)
    stat(s, Inches(3.5), Inches(1.3), Inches(2.9), f"{100*tot_ag/max(tot_j,1):.0f}%",
         "judge agrees with the tests (judge never sees them)")
    stat(s, Inches(6.55), Inches(1.3), Inches(2.9), f"{100*tot_rx/tot_n:.0f}%",
         "patches byte-identical to the reference fix")
    stat(s, Inches(9.6), Inches(1.3), Inches(3.3), str(study["unresolved"]),
         "unresolved — both caught only by the fresh-clone re-test", color=WARN)

    tf = box(s, Inches(0.45), Inches(2.6), Inches(6.0), Inches(0.4))
    put(tf, "Response time — the system and each agent", size=15, bold=True, color=ACCENT,
        first=True)
    table(s, Inches(0.45), Inches(3.05), Inches(6.0),
          ["Agent"] + archs,
          [["Diagnoser"] + [f"!!{stats[a]['diag']:.1f}s" for a in archs],
           ["Fixer"] + [f"{stats[a]['fix']:.1f}s" for a in archs],
           ["Tester"] + [f"{stats[a]['test']:.1f}s" for a in archs],
           ["PR agent"] + [f"{stats[a]['pr']:.1f}s" for a in archs],
           ["**Whole system**"] + [f"**{stats[a]['secs']:.1f}s**" for a in archs]],
          size=11.5, col_w=[3, 2, 2, 2], row_h=0.37)
    callout(s, Inches(0.45), Inches(5.3), Inches(6.0), Inches(1.75),
            [("The Diagnoser is the bottleneck", {"b": True, "c": ACCENT}),
             (" in every architecture — about half of each run. That is the right place for "
              "the time to go: it is the only agent doing multi-step reasoning with tools, and "
              "localisation is the hard part. The Tester runs a whole suite in ~2s because it "
              "calls no model at all.", {})], size=12.5)

    tf = box(s, Inches(6.75), Inches(2.6), Inches(6.15), Inches(0.4))
    put(tf, "Reference text and LLM-as-judge", size=15, bold=True, color=ACCENT, first=True)
    table(s, Inches(6.75), Inches(3.05), Inches(6.15),
          ["Method", "Model-free?", "Result"],
          [["Objective re-test in a fresh clone", "Yes", f"++{tot_res}/{tot_n} resolved"],
           ["Reference-fix comparison", "Yes",
            f"{100*tot_rx/tot_n:.0f}% exact, 0.95 similarity"],
           ["LLM-as-judge (verdict + score)", "No",
            f"{100*tot_ag/max(tot_j,1):.0f}% agreement with tests"]],
          size=11, col_w=[4.6, 1.8, 3.6], row_h=0.44)
    callout(s, Inches(6.75), Inches(4.85), Inches(6.15), Inches(2.2),
            [("Why all three — the case that proves it.  ", {"b": True, "c": WARN}),
             ("In both unresolved runs (hard bug py11) the ", {}),
             ("Tester", {"b": True}), (" passed the patch in its own workspace and the ", {}),
             ("judge", {"b": True}), (" rated it a pass at 0.95–0.97. Only the ", {}),
             ("fresh-clone re-test", {"b": True}),
             (" caught that the recorded patch did not apply. Two of three graders were wrong; "
              "the model-free one was right.", {})], size=12.5)
    notes(s, "Lead with the failures, they are the best evidence for the design. Tester said "
             "green, judge said pass, fresh clone said the patch does not even apply. That is "
             "why the fresh-clone re-test exists. Also: the judge model must differ from both "
             "generating models, enforced when the config loads.")


def slide11(prs):
    s = slide_base(prs, 11, "Team Responsibility / Self-Contribution Matrix")
    names = [f"{n.split()[-1] if n.startswith('Singidi') else n.split()[0]} ({r})"
             for n, r in TEAM]
    names = [f"Karthikeya ({TEAM[0][1]})", f"Naman ({TEAM[1][1]})", f"Abhiram ({TEAM[2][1]})"]
    L, C, D = "Lead", "Contributed", "—"
    table(s, Inches(1.3), Inches(1.4), Inches(10.7),
          ["Activity"] + names,
          [["Agent design / multi-agent architecture", L, C, C],
           ["Agent orchestration (Manager, retry policy)", C, L, D],
           ["State management (Blackboard, envelopes)", D, C, L],
           ["MCP design (server, 16 tools, sandbox)", C, D, L],
           ["A2A communication (ADK ⇄ CrewAI)", D, C, L],
           ["Guardrails / callbacks", C, L, C],
           ["Observability (tracing, live run view)", D, L, C],
           ["Diagnoser (ReAct) and Fixer agents", L, D, C],
           ["Tester and PR agents", D, C, L],
           ["RAG: vector store, retrieval, citations", L, D, D],
           ["Code search and static-analysis tooling", L, D, C],
           ["Integration and testing", C, C, C],
           ["Evaluation and documentation", C, L, C],
           ["Presentation / interface UI", C, L, D],
           ["Deployment (Docker, Cloud Run, secrets)", C, D, L],
           ["End-to-end evaluation (time and cost)", C, L, C]],
          size=11, head_size=11.5, col_w=[5.0, 1.9, 1.9, 1.9], row_h=0.325)
    tf = box(s, Inches(1.3), Inches(6.95), Inches(10.7), Inches(0.4))
    put(tf, "Lead = primary responsibility for design and implementation   ·   "
            "Contributed = substantive work on the item",
        size=11, color=MUTED, align=PP_ALIGN.CENTER, first=True)
    notes(s, "Three members. Karthikeya: Diagnoser, Fixer, RAG and code search. Naman: "
             "orchestration, observability and evaluation. Abhiram: MCP, Blackboard, A2A, "
             "Tester/PR and deployment.")


def slide12(prs):
    s = slide_base(prs, 12, "Demonstration", f"Live at  {URL}")
    # figures/ holds slide-sized crops; the report's full-page captures are far too tall here
    fig = DOCS / "slides" / "figures"
    picture(s, fig / "run_live.png", Inches(0.4), Inches(1.45), w=Inches(6.15))
    picture(s, fig / "dashboard.png", Inches(6.8), Inches(1.45), w=Inches(6.15))
    tf = box(s, Inches(0.4), Inches(5.75), Inches(6.15), Inches(1.2))
    put(tf, "Live run view", size=13, bold=True, color=ACCENT, first=True, space=3)
    put(tf, "Pipeline state per agent, the ReAct transcript, A2A exchanges, guardrail "
            "decisions, the patch and the test output — and the run holding at the human "
            "PR gate.", size=11.5, color=MUTED, space=0)
    tf = box(s, Inches(6.8), Inches(5.75), Inches(6.15), Inches(1.2))
    put(tf, "Dashboard", size=13, bold=True, color=ACCENT, first=True, space=3)
    put(tf, "Per-agent latency with the bottleneck flagged, attempts, cost and judge accuracy "
            "across every seeded run — including three bugs in our own MLOps project.",
        size=11.5, color=MUTED, space=0)
    notes(s, "Demo script: pick ml01-alerts-limit-wrong-end (a bug in our own MLOps project), "
             "live LLM, hierarchical. ~60s, ~$0.02. Watch the ReAct steps, the A2A hand-offs to "
             "CrewAI, and the run stopping at the human PR gate. Then open the Dashboard.")


def slide13(prs, stats, total_cost, study):
    s = slide_base(prs, 13, "Conclusions")
    tf = box(s, Inches(0.5), Inches(1.3), Inches(12.4), Inches(0.9))
    rich(tf, [("CodeFix AI resolves defects end to end from a natural-language report, using "
               "five role-specialised agents across ", {"size": 16}),
              ("two frameworks joined by an open protocol", {"b": True, "size": 16}),
              (f". Across {study['recorded']} live runs on {study['bugs']} reproducible bugs in "
               f"three repositories it resolved {study['resolved']} of {study['graded']} graded "
               f"({100*study['resolved']/study['graded']:.1f}%), where “resolved” means "
               "the patch was re-applied to a clean clone and the entire suite passed.",
               {"size": 16})], first=True, size=16)

    tf = box(s, Inches(0.5), Inches(2.45), Inches(6.1), Inches(4.2))
    put(tf, "What we found", size=16, bold=True, color=ACCENT, first=True, space=8)
    bullets(tf, [
        [("The agent set is derived, not assumed.", {"b": True}),
         (" Each agent traces to a requirement, and each requirement to a gap or a claim.", {})],
        [("Model-free verification earned its place.", {"b": True}),
         (" In both failures the Tester and the judge passed a patch that the fresh-clone "
          "re-test showed would not even apply.", {})],
        [("Architecture did not change whether bugs were fixed.", {"b": True}),
         (" All three resolved every completed run; they differ in cost, latency and "
          "variance.", {})],
        [("Localisation is where the time goes.", {"b": True}),
         (" The Diagnoser takes about half of every run.", {})],
        [("Plain ReAct was the most reliable prompt.", {"b": True}),
         (" It resolved every run; few-shot and Reflection each lost one, on the same hard "
          "bug, at half and ~67% more the cost.", {})],
        [("A stack trace turned out to be unnecessary.", {"b": True}),
         (" The end-user persona, given symptoms only, still resolved every run.", {})],
    ], size=12.5, space=8)

    tf = box(s, Inches(6.9), Inches(2.45), Inches(6.0), Inches(4.2))
    put(tf, "Limitations, honestly", size=16, bold=True, color=WARN, first=True, space=8)
    bullets(tf, [
        [("The bug set is seeded and single-file.", {"b": True}),
         (" Defects spanning modules, or needing a design change, are not represented.", {})],
        [("The architecture runs never needed a retry,", {"b": True}),
         (" so the topologies could not be compared on recovery. The loop ran live once "
          "elsewhere and worked; escalation never ran live.", {})],
        [("Agent personas showed no measurable effect", {"b": True}),
         (" on defects this well-specified. Reported as a negative result.", {})],
        [("Deployed run data is not durable;", {"b": True}),
         (" a cold instance restores a seeded snapshot rather than accumulating history.", {})],
    ], size=12.5, space=8)
    put(tf, "Next: a deliberately harder bug set that resists the first patch — that is "
            "what would actually test the orchestration.", size=12.5, italic=True,
        color=ACCENT, space=0)

    callout(s, Inches(0.5), Inches(6.75), Inches(12.4), Inches(0.55),
            [("Deployed, public and reproducible:  ", {"b": True, "c": ACCENT}),
             (URL, {"font": "Consolas", "size": 11.5}),
             (f"      ·      {study['recorded']} runs for ${study['cost']:.2f}      ·      "
              "155 automated tests, no API key required", {})], size=12)
    notes(s, "Lead with the honest findings. The architecture result and the persona result are "
             "both negative, and reporting them is the point: we measured instead of assuming.")


def slide14(prs):
    s = slide_base(prs, 14, "References")
    refs = [
        ("[1]", "C. E. Jimenez, J. Yang, A. Wettig, S. Yao, K. Pei, O. Press, K. Narasimhan. "
                "SWE-bench: Can Language Models Resolve Real-World GitHub Issues? ICLR 2024. "
                "arXiv:2310.06770"),
        ("[2]", "J. Yang, C. E. Jimenez, A. Wettig, K. Lieret, S. Yao, K. Narasimhan, O. Press. "
                "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering. "
                "2024. arXiv:2405.15793"),
        ("[3]", "Y. Zhang, H. Ruan, Z. Fan, A. Roychoudhury (NUS). AutoCodeRover: Autonomous "
                "Program Improvement. 2024. arXiv:2404.05427"),
        ("[4]", "GitHub. Copilot Autofix for code scanning — product documentation. "
                "docs.github.com/en/code-security"),
        ("[5]", "J. Bader, A. Scott, M. Pradel, S. Chandra. Getafix: Learning to Fix Bugs "
                "Automatically. OOPSLA 2019. arXiv:1902.06111"),
        ("[6]", "Cognition. Devin. cognition.ai"),
        ("[7]", "Anthropic. Model Context Protocol specification. modelcontextprotocol.io"),
        ("[8]", "Agent2Agent (A2A) protocol. a2a-protocol.org · github.com/a2aproject/A2A"),
        ("[9]", "Google. Agent Development Kit (ADK) documentation. google.github.io/adk-docs"),
        ("[10]", "CrewAI. CrewAI documentation. docs.crewai.com"),
        ("[11]", "Z.AI. GLM API documentation and pricing. docs.z.ai"),
    ]
    tf = box(s, Inches(0.7), Inches(1.45), Inches(11.9), Inches(5.0))
    first = True
    for tag, text in refs:
        rich(tf, [(f"{tag}  ", {"b": True, "c": ACCENT}), (text, {})],
             size=12.5, space=7, first=first)
        first = False
    callout(s, Inches(0.7), Inches(6.35), Inches(11.9), Inches(0.7),
            [("Project artefacts:  ", {"b": True, "c": ACCENT}),
             (f"{URL}   ·   {REPO}", {"font": "Consolas", "size": 11})], size=12)
    notes(s, "Primary sources throughout: arXiv papers, official specifications and vendor "
             "documentation. Vendor and self-reported figures are marked as such in Slide 2.")
