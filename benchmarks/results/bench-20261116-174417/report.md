# CodeFix AI benchmark — `bench-20261116-174417`

12 runs · 4 bugs · architectures: novice, security, senior

## Headline comparison

| Metric | novice | security | senior |
|---|---|---|---|
| Resolved (fresh-clone full suite green) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) |
| Previously-failing test green | 4/4 | 4/4 | 4/4 |
| Judge verdict = pass | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) |
| Judge verdict = partial | 0 | 0 | 0 |
| **Judge accuracy** (agrees with tests) | 100% | 100% | 100% |
| Mean Fixer attempts | 1.00 | 1.00 | 1.00 |
| Runs needing a retry | 0 | 0 | 0 |
| Escalated to human | 0 | 0 | 0 |
| Errors | 0 | 0 | 0 |
| Reference fix: exact match | 3/4 (75%) | 3/4 (75%) | 3/4 (75%) |
| Reference fix: edit similarity (0-1) | 0.96 | 0.94 | 0.96 |
| Reference fix: same file(s) changed | 4/4 | 4/4 | 4/4 |
| Mean wall-clock / run | 68.8s | 59.7s | 74.8s |
| Wall-clock std-dev | 1.7s | 4.3s | 7.9s |
| Mean pipeline cost / run | $0.0227 | $0.0205 | $0.0241 |
| Total pipeline cost | $0.091 | $0.082 | $0.096 |
| Mean LLM calls / run | 3.2 | 3.8 | 3.8 |
| Mean tokens / run | 8247 | 8392 | 9193 |
| Mean envelope size (bytes) | 399 | 444 | 419 |

## Per-agent mean latency (seconds per run)

| Agent | novice | security | senior |
|---|---|---|---|
| Diagnoser | 29.5 | 27.9 | 33.0 |
| Fixer | 18.2 | 10.4 | 19.7 |
| Tester | 1.6 | 1.5 | 1.6 |
| PR agent | 0.6 | 0.5 | 0.5 |
| Manager (LLM time) | 0.0 | 0.0 | 0.0 |

Bottleneck agent per architecture: **novice** → diagnoser, **security** → diagnoser, **senior** → diagnoser

## Failure-stage breakdown (non-passing runs)

_No failures._

## Judge vs objective tests (all architectures)

| Judge \ Tests | green | red |
|---|---|---|
| pass | 12 | 0 |

## Per-bug outcomes (✅ resolved · ❌ not resolved · attempts)

| Bug | difficulty | novice | security | senior |
|---|---|---|---|---|
| js01-slugify-global | easy | ✅1 | ✅1 | ✅1 |
| js03-template-falsy | medium | ✅1 | ✅1 | ✅1 |
| py05-region-case | medium | ✅1 | ✅1 | ✅1 |
| py08-mutable-default | hard | ✅1 | ✅1 | ✅1 |

## By difficulty (resolved / runs)

| Difficulty | novice | security | senior |
|---|---|---|---|
| easy | 1/1 | 1/1 | 1/1 |
| medium | 2/2 | 2/2 | 2/2 |
| hard | 1/1 | 1/1 | 1/1 |

## Cost and running time

- **12 runs** in **13.6 min** of wall-clock (mean 67.8s/run)
- **Pipeline cost $0.269** ($0.0224/run); LLM-as-judge a further $0.002
- Tokens: 67,311 fresh in / 63,232 cached in / 36,018 out

Same token volume, every agent on one model (list prices, cached input charged at each model's cache-read rate):

| If all agents ran on | Estimated cost | vs actual |
|---|---|---|
| glm-5.3 (all agents) | $0.269 | 1.00x |
| glm-5.3-flash (all agents) | $0.030 | 0.11x |
| **actual (per-role mix)** | **$0.269** | 1.00x |
