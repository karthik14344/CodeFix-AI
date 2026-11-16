# Prompt variant and persona comparison
Each level is compared against the `hierarchical / react / default / developer` baseline drawn from the main architecture benchmark, on the same bugs. Baseline repetitions are averaged per bug before comparison.

## Prompt variant
| Metric | react (baseline) | fewshot | react-reflect |
|---|---|---|---|
| Runs | 27 | 10 | 10 |
| Resolved | 27/27 (100%) | 9/10 (90%) | 9/10 (90%) |
| Right file(s) changed | 100% | 90% | 90% |
| Matches reference exactly | 59% | 60% | 60% |
| Edit similarity (0-1) | 0.91 | 0.84 | 0.81 |
| Mean wall-clock | 65.6s | 59.4s | 101.3s |
| Diagnoser time | 31.1s | 13.6s | 42.7s |
| Mean LLM calls | 4.5 | 2.0 | 5.3 |
| Mean tokens | 9604 | 5878 | 15528 |
| Mean cost / run | $0.0238 | $0.0142 | $0.0398 |

_Paired on 8 bugs: js01-slugify-global, js03-template-falsy, py01-subtotal-skips-last, py03-rounding-truncates, py05-region-case, py08-mutable-default, py09-snapshot-aliasing, py11-sku-dashes._

## Agent persona
| Metric | default (baseline) | novice | security | senior |
|---|---|---|---|---|
| Runs | 14 | 4 | 4 | 4 |
| Resolved | 14/14 (100%) | 4/4 (100%) | 4/4 (100%) | 4/4 (100%) |
| Right file(s) changed | 100% | 100% | 100% | 100% |
| Matches reference exactly | 71% | 75% | 75% | 75% |
| Edit similarity (0-1) | 0.97 | 0.96 | 0.94 | 0.96 |
| Mean wall-clock | 60.1s | 68.8s | 59.7s | 74.8s |
| Diagnoser time | 26.6s | 29.5s | 27.9s | 33.0s |
| Mean LLM calls | 3.9 | 3.2 | 3.8 | 3.8 |
| Mean tokens | 8128 | 8247 | 8392 | 9193 |
| Mean cost / run | $0.0208 | $0.0229 | $0.0206 | $0.0243 |

_Paired on 4 bugs: js01-slugify-global, js03-template-falsy, py05-region-case, py08-mutable-default._

## Reporter persona (who filed the bug report)
| Metric | developer (baseline) | enduser |
|---|---|---|
| Runs | 27 | 8 |
| Resolved | 27/27 (100%) | 8/8 (100%) |
| Right file(s) changed | 100% | 100% |
| Matches reference exactly | 59% | 62% |
| Edit similarity (0-1) | 0.91 | 0.95 |
| Mean wall-clock | 65.6s | 61.8s |
| Diagnoser time | 31.1s | 29.6s |
| Mean LLM calls | 4.5 | 4.1 |
| Mean tokens | 9604 | 8734 |
| Mean cost / run | $0.0238 | $0.0212 |

_Paired on 8 bugs: js01-slugify-global, js03-template-falsy, py01-subtotal-skips-last, py03-rounding-truncates, py05-region-case, py08-mutable-default, py09-snapshot-aliasing, py11-sku-dashes._
