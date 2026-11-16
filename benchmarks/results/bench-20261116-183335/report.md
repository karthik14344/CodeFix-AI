# CodeFix AI benchmark — `bench-20261116-183335`

3 runs · 3 bugs · architectures: hierarchical

## Headline comparison

| Metric | hierarchical |
|---|---|
| Resolved (fresh-clone full suite green) | 3/3 (100%) |
| Previously-failing test green | 3/3 |
| Judge verdict = pass | 2/3 (67%) |
| Judge verdict = partial | 1 |
| **Judge accuracy** (agrees with tests) | 67% |
| Mean Fixer attempts | 1.00 |
| Runs needing a retry | 0 |
| Escalated to human | 0 |
| Errors | 0 |
| Reference fix: exact match | 3/3 (100%) |
| Reference fix: edit similarity (0-1) | 1.00 |
| Reference fix: same file(s) changed | 3/3 |
| Mean wall-clock / run | 57.4s |
| Wall-clock std-dev | 5.3s |
| Mean pipeline cost / run | $0.0225 |
| Total pipeline cost | $0.067 |
| Mean LLM calls / run | 4.0 |
| Mean tokens / run | 10208 |
| Mean envelope size (bytes) | 426 |

## Per-agent mean latency (seconds per run)

| Agent | hierarchical |
|---|---|
| Diagnoser | 24.9 |
| Fixer | 11.0 |
| Tester | 2.4 |
| PR agent | 0.5 |
| Manager (LLM time) | 0.0 |

Bottleneck agent per architecture: **hierarchical** → diagnoser

## Failure-stage breakdown (non-passing runs)

_No failures._

## Judge vs objective tests (all architectures)

| Judge \ Tests | green | red |
|---|---|---|
| pass | 2 | 0 |
| partial | 1 | 0 |

## Per-bug outcomes (✅ resolved · ❌ not resolved · attempts)

| Bug | difficulty | hierarchical |
|---|---|---|
| ml01-alerts-limit-wrong-end | medium | ✅1 |
| ml02-alert-status-from-payload | medium | ✅1 |
| ml03-stored-count-counts-payload | easy | ✅1 |

## By difficulty (resolved / runs)

| Difficulty | hierarchical |
|---|---|
| easy | 1/1 |
| medium | 2/2 |

## Cost and running time

- **3 runs** in **2.9 min** of wall-clock (mean 57.4s/run)
- **Pipeline cost $0.067** ($0.0225/run); LLM-as-judge a further $0.001
- Tokens: 24,524 fresh in / 24,128 cached in / 6,101 out

Same token volume, every agent on one model (list prices, cached input charged at each model's cache-read rate):

| If all agents ran on | Estimated cost | vs actual |
|---|---|---|
| glm-5.3 (all agents) | $0.067 | 1.00x |
| glm-5.3-flash (all agents) | $0.007 | 0.11x |
| **actual (per-role mix)** | **$0.067** | 1.00x |
