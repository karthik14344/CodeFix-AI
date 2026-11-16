# CodeFix AI benchmark — `bench-20261116-171853`

16 runs · 8 bugs · architectures: fewshot, react-reflect

## Headline comparison

| Metric | fewshot | react-reflect |
|---|---|---|
| Resolved (fresh-clone full suite green) | 7/8 (88%) | 7/8 (88%) |
| Previously-failing test green | 7/8 | 7/8 |
| Judge verdict = pass | 8/8 (100%) | 8/8 (100%) |
| Judge verdict = partial | 0 | 0 |
| **Judge accuracy** (agrees with tests) | 88% | 88% |
| Mean Fixer attempts | 1.00 | 1.12 |
| Runs needing a retry | 0 | 1 |
| Escalated to human | 0 | 0 |
| Errors | 0 | 0 |
| Reference fix: exact match | 4/8 (50%) | 4/8 (50%) |
| Reference fix: edit similarity (0-1) | 0.81 | 0.77 |
| Reference fix: same file(s) changed | 7/8 | 7/8 |
| Mean wall-clock / run | 60.8s | 110.8s |
| Wall-clock std-dev | 27.6s | 72.6s |
| Mean pipeline cost / run | $0.0147 | $0.0441 |
| Total pipeline cost | $0.118 | $0.353 |
| Mean LLM calls / run | 2.0 | 5.6 |
| Mean tokens / run | 6141 | 17076 |
| Mean envelope size (bytes) | 376 | 431 |

## Per-agent mean latency (seconds per run)

| Agent | fewshot | react-reflect |
|---|---|---|
| Diagnoser | 13.5 | 47.7 |
| Fixer | 16.7 | 34.1 |
| Tester | 2.1 | 2.9 |
| PR agent | 0.5 | 0.6 |
| Manager (LLM time) | 0.0 | 0.2 |

Bottleneck agent per architecture: **fewshot** → fixer, **react-reflect** → diagnoser

## Failure-stage breakdown (non-passing runs)

_No failures._

## Judge vs objective tests (all architectures)

| Judge \ Tests | green | red |
|---|---|---|
| pass | 14 | 2 |

## Per-bug outcomes (✅ resolved · ❌ not resolved · attempts)

| Bug | difficulty | fewshot | react-reflect |
|---|---|---|---|
| js01-slugify-global | easy | ✅1 | ✅1 |
| js03-template-falsy | medium | ✅1 | ✅1 |
| py01-subtotal-skips-last | easy | ✅1 | ✅1 |
| py03-rounding-truncates | medium | ✅1 | ✅1 |
| py05-region-case | medium | ✅1 | ✅1 |
| py08-mutable-default | hard | ✅1 | ✅1 |
| py09-snapshot-aliasing | medium | ✅1 | ✅2 |
| py11-sku-dashes | hard | ❌1 | ❌1 |

## By difficulty (resolved / runs)

| Difficulty | fewshot | react-reflect |
|---|---|---|
| easy | 2/2 | 2/2 |
| medium | 4/4 | 4/4 |
| hard | 1/2 | 1/2 |

## Cost and running time

- **16 runs** in **22.9 min** of wall-clock (mean 85.8s/run)
- **Pipeline cost $0.471** ($0.0294/run); LLM-as-judge a further $0.003
- Tokens: 121,150 fresh in / 71,808 cached in / 64,592 out

Same token volume, every agent on one model (list prices, cached input charged at each model's cache-read rate):

| If all agents ran on | Estimated cost | vs actual |
|---|---|---|
| glm-5.3 (all agents) | $0.472 | 1.00x |
| glm-5.3-flash (all agents) | $0.053 | 0.11x |
| **actual (per-role mix)** | **$0.471** | 1.00x |
