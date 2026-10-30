# Berlin Tour CBC Lab

A synthetic Choice-Based Conjoint (CBC) experiment on Spanish-language walking tours in Berlin, built as a classroom demonstration for HTW Berlin M9 Marketing Research in International Business (Prof. Dr. Holger Lütters).

**Live demo:** [open the interactive lab](https://mazapandi.github.io/berlin-cbc-lab/) *(update the URL after you enable GitHub Pages)*

## What this is

Ten invented Spanish-speaking traveller archetypes each face 12 booking decisions across six real tour products from my own Berlin tour business. A multinomial logit model with eight utility components decides each choice. The project exists to make the CBC method visible — the "ground truth" preferences are controlled, so the simulator can show that CBC recovers what was programmed into it.

**This is not a market study.** All preferences are invented. A real study would require ≥200 real respondents and incentive-aligned willingness-to-pay measurement.

## What's inside

```
berlin-cbc-lab/
├── docs/                      # GitHub Pages root
│   └── index.html             # the interactive Habbo-style classroom lab
├── handout/
│   └── index.html             # one-page printable A4 handout
├── src/
│   ├── simulator.py           # the CBC engine (pure Python stdlib)
│   └── generate_explanations.py  # produces in-character English explanations
├── data/
│   ├── respondents.csv        # 10 synthetic traveller archetypes
│   ├── products.csv           # 6 tour products
│   ├── choice_tasks.csv       # 12 choice-set configurations
│   ├── choice_results.csv     # 480 alternative-level records
│   ├── utility_components.csv # per-component utility breakdown
│   ├── explanations.json      # 120 in-character explanations
│   ├── model_config.json      # λ, q, seed, and other settings
│   └── summary_report.md      # auto-generated analysis
└── README.md
```

## How to reproduce the results

```bash
cd src
python3 simulator.py              # regenerates all CSVs and summary report
python3 generate_explanations.py  # regenerates explanations.json
```

Pure Python standard library — no `pip install` needed. Reproducible with `random_seed = 42` in `model_config.json`.

## The method, briefly

Each tour's utility for a respondent:

```
V_ij = T + D + P + R + C + F + G + U
```

- **T** theme fit (history / local life / art / custom)
- **D** duration preference (short vs. long)
- **P** price penalty (per €10 of payment)
- **R** private format bonus
- **C** customization bonus (private only)
- **F** fixed-price vs. tips preference
- **G** group tolerance (public tours only)
- **U** tip uncertainty penalty (tips tours)

Choice probability: `softmax(V / λ)` with the opt-out pinned at `V = 0`, `λ = 1.5`.

## Sources

- Green, P. E., & Srinivasan, V. (1978). Conjoint Analysis in Consumer Research: Issues and Outlook. *Journal of Consumer Research*, 5(2), 103–123.
- Louviere, J. J., & Woodworth, G. (1983). Design and Analysis of Simulated Consumer Choice or Allocation Experiments. *Journal of Marketing Research*, 20(4), 350–367.
- Orme, B. K. (2013). *Which Conjoint Method Should I Use?* Sawtooth Software Research Paper Series.

## AI disclosure

Implementation code and the classroom artifact were built with Claude as a coding assistant, following my specification. All methodological decisions — attributes, archetypes, utility structure, hypothesis, interpretation — are my own.

## License

MIT — see [LICENSE](LICENSE).

## Author

Carlos Maza · Berlin · [berlines.es](https://berlines.es)
