# CodeFix AI benchmark — `bench-20261116-175942`

8 runs · 8 bugs · architectures: hierarchical

## Headline comparison

| Metric | hierarchical |
|---|---|
| Resolved (fresh-clone full suite green) | 8/8 (100%) |
| Previously-failing test green | 8/8 |
| Judge verdict = pass | 8/8 (100%) |
| Judge verdict = partial | 0 |
| **Judge accuracy** (agrees with tests) | 100% |
| Mean Fixer attempts | 1.00 |
| Runs needing a retry | 0 |
| Escalated to human | 0 |
| Errors | 0 |
| Reference fix: exact match | 5/8 (62%) |
| Reference fix: edit similarity (0-1) | 0.95 |
| Reference fix: same file(s) changed | 8/8 |
| Mean wall-clock / run | 61.8s |
| Wall-clock std-dev | 14.7s |
| Mean pipeline cost / run | $0.0210 |
| Total pipeline cost | $0.168 |
| Mean LLM calls / run | 4.1 |
| Mean tokens / run | 8734 |
| Mean envelope size (bytes) | 398 |

## Per-agent mean latency (seconds per run)

| Agent | hierarchical |
|---|---|
| Diagnoser | 29.6 |
| Fixer | 10.5 |
| Tester | 1.8 |
| PR agent | 0.5 |
| Manager (LLM time) | 0.0 |

Bottleneck agent per architecture: **hierarchical** → diagnoser

## Failure-stage breakdown (non-passing runs)

_No failures._

## Judge vs objective tests (all architectures)

| Judge \ Tests | green | red |
|---|---|---|
| pass | 8 | 0 |

## Per-bug outcomes (✅ resolved · ❌ not resolved · attempts)

| Bug | difficulty | hierarchical |
|---|---|---|
| js01-slugify-global | easy | ✅1 |
| js03-template-falsy | medium | ✅1 |
| py01-subtotal-skips-last | easy | ✅1 |
| py03-rounding-truncates | medium | ✅1 |
| py05-region-case | medium | ✅1 |
| py08-mutable-default | hard | ✅1 |
| py09-snapshot-aliasing | medium | ✅1 |
| py11-sku-dashes | hard | ✅1 |

## By difficulty (resolved / runs)

| Difficulty | hierarchical |
|---|---|
| easy | 2/2 |
| medium | 4/4 |
| hard | 2/2 |

## Cost and running time

- **8 runs** in **8.2 min** of wall-clock (mean 61.8s/run)
- **Pipeline cost $0.168** ($0.0210/run); LLM-as-judge a further $0.002
- Tokens: 50,833 fresh in / 50,112 cached in / 19,035 out

Same token volume, every agent on one model (list prices, cached input charged at each model's cache-read rate):

| If all agents ran on | Estimated cost | vs actual |
|---|---|---|
| glm-5.3 (all agents) | $0.168 | 1.00x |
| glm-5.3-flash (all agents) | $0.019 | 0.11x |
| **actual (per-role mix)** | **$0.168** | 1.00x |
