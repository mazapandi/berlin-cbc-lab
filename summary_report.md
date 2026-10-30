# Berlin Walking Tour CBC — Simulation Summary

**Synthetic classroom demonstration — not real consumer data.**

- Respondents: 10
- Choice tasks per respondent: 12
- Alternatives per task: 3 tours + opt-out
- Total decisions: 120
- Logit scale lambda: 1.5
- Tip uncertainty level q: 1.0
- Random seed: 42

## Aggregate choice share

| Alternative | Chosen | Share |
|---|---:|---:|
| H2 | 14 | 11.7% |
| H3.5 | 13 | 10.8% |
| L | 16 | 13.3% |
| AB | 26 | 21.7% |
| P2 | 15 | 12.5% |
| P3.5 | 7 | 5.8% |
| NONE | 29 | 24.2% |

## Central hypothesis — H2 vs H3.5 head-to-head (tasks 5-8)

All four of these tasks place H2 and H3.5 together; the third alternative varies.

- H2 chosen: 10 / 40 (25.0%)
- H3.5 chosen: 4 / 40 (10.0%)
- Other alternative chosen: 13 / 40 (32.5%)
- Opt-out chosen: 13 / 40 (32.5%)

Under the modelled preferences, the 2-hour public history tour is chosen more often than the 3.5-hour format in these head-to-head tasks. This supports the shorter-tour hypothesis within the model's assumptions.

## Per-respondent choice pattern

The archetype column states the preference baked in; the modal choice is what the model picked most often across 12 tasks. Alignment is the preference-recovery check.

| Respondent | Archetype | Party | Opt-outs | Modal choice (count) |
|---|---|---:|---:|---|
| R01 | Time-Constrained Explorer | 1 | 3 | NONE (3) |
| R02 | Berlin Lifestyle Seeker | 2 | 1 | AB (4) |
| R03 | Alternative Culture Enthusiast | 3 | 3 | AB (5) |
| R04 | History Enthusiast | 1 | 1 | H3.5 (4) |
| R05 | Budget-Conscious Friends | 4 | 5 | NONE (5) |
| R06 | Family Organizer | 4 | 5 | NONE (5) |
| R07 | Comfort-Oriented Couple | 2 | 1 | P3.5 (5) |
| R08 | Independent Urban Explorer | 1 | 3 | AB (3) |
| R09 | Curious Generalist | 2 | 3 | AB (4) |
| R10 | Spontaneous Culture Seeker | 2 | 4 | NONE (4) |

## Interpretation notes

- Opt-outs cluster among respondents whose best available alternative has large negative price utility or weak theme fit. A high opt-out rate means the current product mix fails that archetype.
- Private tours (P2, P3.5) win choice share mainly for respondents with large parties (price / party_size is small) and positive private_preference. Solo travellers with high price sensitivity reject private.
- Fixed-price public tours (L, AB) win when the respondent has strong theme fit and positive fixed_price_preference.
- Tips tours (H2, H3.5) win when expected tip is low and tip_uncertainty_aversion is low enough that the uncertainty penalty does not outweigh the price advantage.

## Limitations

- 10 synthetic respondents; the frequencies in this file do not estimate real population shares.
- Preference coefficients are assigned, not estimated. The simulator demonstrates how choices follow from preferences; it cannot test whether the chosen preferences match reality.
- Expected tip is held constant across H2 and H3.5. The head-to-head duration comparison isolates duration_preference by construction.
- Tip uncertainty q = 1 applies equally to both tips tours; the uncertainty structure is a simplification, not a measured risk premium.
- The 12-task design emphasises the H2/H3.5 contrast (4 of 12 tasks). It is not a statistically balanced design optimised for every attribute effect.
