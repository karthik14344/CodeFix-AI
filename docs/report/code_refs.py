"""Claims in the report, mapped to the code that proves them.

Each entry is (path, anchor): the anchor is a piece of text that occurs EXACTLY ONCE in that
file. The line number is looked up at build time, never written down, because line numbers drift
every time the code changes and a link that lands on the wrong line in front of an examiner is
worse than no link. If an anchor is missing or matches more than one line, the build fails.

In content.py a claim is marked up as  [[visible text|key]] .
"""

from __future__ import annotations

from pathlib import Path

REFS: dict[str, tuple[str, str, str]] = {
    # key: (path, anchor, short description for the index)

    # --- agents and orchestration ------------------------------------------------------------
    "manager": ("codefix/adk_side/pipelines.py", "class ManagerAgent",
                "Manager - ADK custom agent"),
    "attempt_bound": ("codefix/adk_side/pipelines.py", "if attempts >= max_attempts:",
                      "Attempt bound checked before the Manager's model is consulted"),
    "arch_switch": ("codefix/adk_side/pipelines.py", "def build(arch: str, max_attempts: int)",
                    "The architecture switch: hierarchical / sequential / p2p"),
    "loop_agent": ("codefix/adk_side/pipelines.py", 'LoopAgent(name="restart_loop"',
                   "Sequential architecture - ADK LoopAgent"),
    "p2p_flow": ("codefix/crew_side/flows.py", "class PeerRepairFlow",
                 "Peer-to-peer architecture - CrewAI Flow"),
    "diagnoser": ("codefix/agents/diagnoser.py", "ReAct Diagnoser over MCP tools",
                  "Diagnoser - ADK LlmAgent running ReAct"),
    "diagnoser_tools": ("codefix/agents/diagnoser.py", "TOOLS = [",
                        "The Diagnoser's read-only tool allow-list"),
    "react_cap": ("codefix/agents/diagnoser.py", "max_iter = cfg.react_max_iterations",
                  "ReAct iteration cap"),
    "react_step": ("codefix/agents/base.py", "class ReActStep",
                   "ReAct step schema: thought / action / action_input / final_answer"),
    "fixer": ("codefix/agents/fixer.py", "guardrail=",
              "Fixer - CrewAI Task with a patch-safety guardrail"),
    "patching": ("codefix/agents/patching.py", "def build_diff",
                 "Unified diff derived deterministically from find/replace edits"),
    "tester": ("codefix/agents/tester.py", "def run(ctx: RunContext, patch: Patch",
               "Tester - deterministic: apply, lint, run the suite"),
    "pr_prepare": ("codefix/agents/pr_agent.py", "def prepare(",
                   "PR agent - branch and commit in the sandbox"),

    # --- state and messaging -----------------------------------------------------------------
    "envelope": ("codefix/blackboard/schemas.py", "class Envelope",
                 "Typed Pydantic message envelope"),
    "dispatch_ref": ("codefix/blackboard/schemas.py", "class DispatchRef",
                     "Dispatch by artifact reference, never by body"),
    "blackboard": ("codefix/blackboard/store.py", "class Blackboard",
                   "Blackboard - SQLite shared state"),
    "snapshot": ("codefix/blackboard/store.py", "def snapshot",
                 "Full pipeline state at any instant"),
    "a2a_card": ("codefix/crew_side/a2a_server.py", "def agent_card",
                 "A2A agent card and its four skills"),
    "a2a_auth": ("codefix/crew_side/a2a_server.py", "class A2AAuthMiddleware",
                 "A2A bearer-token authentication"),
    "a2a_client": ("codefix/a2a_link.py", "async def call_crew",
                   "ADK side as A2A client of the CrewAI service"),

    # --- tools ---------------------------------------------------------------------------------
    "mcp_server": ("mcp_server/server.py", "FastMCP(",
                   "The MCP tool server"),
    "mcp_to_adk": ("codefix/adk_side/tools.py", "def mcp_tools",
                   "MCP tools exposed to ADK as native tools"),
    "sandbox_clone": ("mcp_server/sandbox.py", '"git", "clone", "-q", "--no-hardlinks"',
                      "Isolated git clone per attempt"),
    "blocklist": ("mcp_server/sandbox.py", "BLOCKED_PATTERNS = [",
                  "Secrets blocklist (.env, keys, CI secrets)"),
    "path_jail": ("mcp_server/sandbox.py", "def safe_path",
                  "Paths outside the repository are refused"),
    "pr_confirm": ("mcp_server/tools.py", "requires explicit human confirmation",
                   "PR tool refuses without confirmed=true"),
    "pr_no_default": ("mcp_server/tools.py", "refusing to push to the default branch",
                      "PR tool never pushes to the default branch"),

    # --- guardrails and callbacks --------------------------------------------------------------
    "screen_input": ("codefix/guardrails.py", "def screen_user_input",
                     "Input guardrail: prompt injection, abuse, size"),
    "screen_input_call": ("codefix/graph/runner.py", "screen_user_input",
                          "Input screened before any agent runs"),
    "untrusted": ("codefix/guardrails.py", "def screen_untrusted",
                  "Repository text addressing the model is wrapped as untrusted"),
    "tool_output": ("codefix/guardrails.py", "def validate_tool_output",
                    "Tool-output type check"),
    "patch_safety": ("codefix/guardrails.py", "def patch_safety",
                     "Patch-safety guardrail"),
    "adk_callbacks": ("codefix/observability/callbacks.py", "def adk_callbacks",
                      "ADK agent / model / tool callbacks"),
    "tool_allowlist": ("codefix/observability/callbacks.py", "tool.name not in allowed_tools",
                       "Per-agent tool allow-list enforced in before_tool_callback"),
    "crew_callbacks": ("codefix/observability/callbacks.py", "def crew_callbacks",
                       "CrewAI step / task callbacks"),
    "citations": ("codefix/agents/diagnoser.py", 'ctx.event("citation_dropped"',
                  "RAG citations validated against the ids actually retrieved"),

    # --- models and configuration --------------------------------------------------------------
    "models_yaml": ("config/models.yaml", "roles:",
                    "Per-role model selection"),
    "judge_independent": ("codefix/config.py", "self-preference bias",
                          "Judge must differ from both generating models"),
    "zai": ("codefix/llm.py", "class ZaiLLM",
            "Z.AI GLM client"),
    "effort": ("codefix/llm.py", "def normalize_effort",
               "Reasoning effort mapped to what each model accepts"),
    "alias_warn": ("codefix/llm.py", "def _check_alias",
                   "Warning when the provider serves a different model"),
    "cached_tokens": ("codefix/llm.py", "Normalise to Anthropic's convention",
                      "Cached prompt tokens not billed twice"),
    "backoff": ("codefix/llm.py", "def _post_with_backoff",
                "Rate-limit backoff"),

    # --- evaluation ----------------------------------------------------------------------------
    "materialize": ("codefix/eval/bugset.py", "def materialize",
                    "Pristine repo copied, bug injected, committed as the only commit"),
    "verify_bugset": ("codefix/eval/bugset.py", "def verify",
                      "Every bug fails injected and passes fixed"),
    "eol_fix": ("codefix/eval/bugset.py", "def _normalize_eol",
                "Bug repositories committed with LF line endings (the py11 grading fix)"),
    "grader_apply": ("codefix/eval/judge.py", "Same apply policy as the Tester's apply_patch tool",
                     "Grader applies patches with the Tester's tolerant fallback"),
    "bug_ml01": ("benchmarks/bugset/bugs.yaml", "id: ml01-alerts-limit-wrong-end",
                 "A seeded bug on the team's own MLOps code"),
    "run_bench": ("codefix/eval/bench.py", "def run_bench",
                  "The benchmark harness"),
    "reporters": ("codefix/eval/bench.py", "REPORTERS: dict",
                  "Reporter personas: developer vs end user"),
    "objective_check": ("codefix/eval/judge.py", "def objective_check",
                        "Objective re-test in a fresh clone"),
    "reference_compare": ("codefix/eval/judge.py", "def reference_compare",
                          "Comparison against the known-good fix"),
    "judge_run": ("codefix/eval/judge.py", "def judge_run",
                  "LLM-as-judge, blind to the test results"),
    "compare": ("codefix/eval/compare.py", "def compare(",
                "Paired comparison of variants and personas against the baseline"),
    "cost_estimate": ("codefix/eval/report.py", "def _cost_and_time",
                      "Cost and running-time counterfactual"),
    "seed": ("codefix/eval/seed.py", "def restore_seed",
             "Seed restored only into an empty data directory"),
    "dashboard_resolved": ("web/ui/dashboard.html", "const isResolved",
                           "Dashboard counts resolved by the fresh-clone re-test"),
    "frameworks_test": ("tests/test_frameworks.py",
                        "def test_only_crewai_and_adk_agent_frameworks",
                        "Test asserting only CrewAI and ADK are used"),

    # --- deployment ----------------------------------------------------------------------------
    "deploy_cpu": ("deploy/deploy_cloudrun.ps1", '"--no-cpu-throttling"',
                   "Cloud Run deploy with always-allocated CPU"),
    "data_dir": ("Dockerfile", "CODEFIX_DATA_DIR=/tmp/codefix",
                 "Container data directory"),
}


class RefError(ValueError):
    pass


def resolve(key: str, root: Path) -> tuple[str, int]:
    """(relative path, 1-based line) for a reference key. Strict: exactly one match."""
    if key not in REFS:
        raise RefError(f"unknown code reference '{key}' - add it to code_refs.REFS")
    path, anchor, _ = REFS[key]
    f = root / path
    if not f.exists():
        raise RefError(f"[{key}] file not found: {path}")
    hits = [i + 1 for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace")
                                           .splitlines()) if anchor in line]
    if len(hits) != 1:
        raise RefError(f"[{key}] anchor {anchor!r} matches {len(hits)} lines in {path} "
                       f"(must be exactly 1): {hits[:6]}")
    return path, hits[0]
