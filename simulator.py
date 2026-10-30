"""
Berlin Walking Tour CBC — Synthetic Classroom Demonstration
============================================================

Author: Carlos Maza
Course: M9 Marketing Research in International Business, Prof. Dr. Holger Luetters
Scope:  10 synthetic Spanish-speaking respondents x 12 CBC choice tasks each,
        for a classroom demonstration of Choice-Based Conjoint analysis.

This script is NOT evidence of real consumer preferences. All respondents
and their utility coefficients are invented archetypes designed to illustrate
how preferences drive choices under a multinomial-logit model.

Decisions locked in:
  - lambda (logit scale)      = 1.5   (softens choices without erasing preferences)
  - q (tip uncertainty level) = 1.0   (uncertainty penalty = lambda_i * q)
  - private tour per-head     = group_price / party_size

Run:
    python3 simulator.py

Outputs (written next to this script):
    respondents.csv
    products.csv
    choice_tasks.csv
    model_config.json
    choice_results.csv
    utility_components.csv
    summary_report.md
"""

import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path


# -------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------

CONFIG = {
    "experiment_name": "Berlin Walking Tour CBC",
    "version": "1.0",
    "respondents": 10,
    "tasks_per_respondent": 12,
    "include_opt_out": True,
    "opt_out_utility": 0.0,
    "choice_model": "multinomial_logit",
    "random_seed": 42,
    "duration_reference_hours": 2,
    "price_scale_euros": 10,
    "tip_uncertainty_level_q": 1.0,
    "logit_scale_lambda": 1.5,
    "expected_tip_fixed_across_history_durations": True,
    "llm_controls_choice": False,
    "synthetic_data_only": True,
}


# -------------------------------------------------------------------
# Product catalogue
# -------------------------------------------------------------------

PRODUCTS = {
    "H2":   {"theme": "history",            "duration": 2.0, "payment": "tips",
             "price_per_person": 0,  "price_per_group": 0,   "arrangement": "public",  "customizable": 0},
    "H3.5": {"theme": "history",            "duration": 3.5, "payment": "tips",
             "price_per_person": 0,  "price_per_group": 0,   "arrangement": "public",  "customizable": 0},
    "L":    {"theme": "local_life",         "duration": 3.5, "payment": "fixed",
             "price_per_person": 18, "price_per_group": 0,   "arrangement": "public",  "customizable": 0},
    "AB":   {"theme": "alternative_berlin", "duration": 3.5, "payment": "fixed",
             "price_per_person": 18, "price_per_group": 0,   "arrangement": "public",  "customizable": 0},
    "P2":   {"theme": "customizable",       "duration": 2.0, "payment": "fixed",
             "price_per_person": 0,  "price_per_group": 175, "arrangement": "private", "customizable": 1},
    "P3.5": {"theme": "customizable",       "duration": 3.5, "payment": "fixed",
             "price_per_person": 0,  "price_per_group": 250, "arrangement": "private", "customizable": 1},
}


# -------------------------------------------------------------------
# Respondent archetypes (all invented, for demonstration only)
# -------------------------------------------------------------------

RESPONDENT_FIELDS = [
    "respondent_id", "archetype", "party_size", "available_time_hours",
    "history_interest", "local_life_interest", "art_architecture_interest",
    "price_sensitivity", "duration_preference", "private_preference",
    "customization_preference", "fixed_price_preference", "group_size_tolerance",
    "expected_tip_per_person", "tip_uncertainty_aversion",
]

RESPONDENTS_RAW = [
    ("R01", "Time-Constrained Explorer",       1, 3.0,  2.0,  0.0,  0.0, 0.65, -0.9, -0.5, 0.0,  1.0,  0.0, 10, 1.0),
    ("R02", "Berlin Lifestyle Seeker",         2, 5.0, -1.0,  2.0,  1.0, 0.30, -0.3,  0.5, 1.0,  0.5,  0.5, 15, 0.3),
    ("R03", "Alternative Culture Enthusiast",  3, 5.0, -1.5,  0.8,  2.0, 0.15,  0.2,  0.2, 1.0, -0.5,  1.0, 18, 0.2),
    ("R04", "History Enthusiast",              1, 6.0,  2.0,  0.2,  0.0, 0.15,  0.9, -0.5, 0.0, -0.5,  0.5, 20, 0.1),
    ("R05", "Budget-Conscious Friends",        4, 3.0,  0.3,  0.3,  0.3, 0.80, -0.8, -0.8, 0.0,  0.5,  0.5,  8, 0.8),
    ("R06", "Family Organizer",                4, 4.0,  0.3,  0.3,  0.3, 0.65, -0.9,  1.0, 1.5,  1.0, -0.5, 12, 0.8),
    ("R07", "Comfort-Oriented Couple",         2, 6.0,  0.2,  0.8,  0.3, 0.15,  0.2,  2.0, 2.0,  0.5, -0.5, 18, 0.2),
    ("R08", "Independent Urban Explorer",      1, 6.0, -0.5,  1.0,  1.5, 0.35, -0.3, -1.0, 0.0, -0.5,  1.0, 12, 0.5),
    ("R09", "Curious Generalist",              2, 5.0,  1.0,  1.0,  1.0, 0.35,  0.2,  0.3, 1.0,  0.0,  0.5, 15, 0.4),
    ("R10", "Spontaneous Culture Seeker",      2, 3.0,  0.0,  0.8,  2.0, 0.35, -0.7,  0.2, 1.0,  0.0,  0.5, 14, 0.4),
]


# -------------------------------------------------------------------
# Choice tasks (12 tasks, three alternatives each + opt-out)
# -------------------------------------------------------------------

CHOICE_TASKS = [
    (1,  "H2",   "L",    "P3.5"),
    (2,  "H3.5", "AB",   "P2"),
    (3,  "H2",   "AB",   "P2"),
    (4,  "H3.5", "L",    "P3.5"),
    (5,  "H2",   "H3.5", "L"),
    (6,  "H2",   "H3.5", "AB"),
    (7,  "H2",   "H3.5", "P2"),
    (8,  "H2",   "H3.5", "P3.5"),
    (9,  "L",    "AB",   "P2"),
    (10, "L",    "AB",   "P3.5"),
    (11, "H3.5", "L",    "P2"),
    (12, "H2",   "AB",   "P3.5"),
]


# -------------------------------------------------------------------
# Utility model
# -------------------------------------------------------------------

def resolve_theme_fit(respondent, product_code):
    """
    T_ij — theme fit.

    For public tours, the respondent's interest in the theme carried by that tour.
    For customizable private tours, the respondent picks their favourite theme,
    so T = max over all three thematic interests.
    """
    product = PRODUCTS[product_code]
    theme = product["theme"]
    if theme == "history":
        return respondent["history_interest"]
    if theme == "local_life":
        return respondent["local_life_interest"]
    if theme == "alternative_berlin":
        return respondent["art_architecture_interest"]
    if theme == "customizable":
        return max(
            respondent["history_interest"],
            respondent["local_life_interest"],
            respondent["art_architecture_interest"],
        )
    return 0.0


def effective_price(respondent, product_code):
    """
    Returns the per-person price seen by this respondent for this product.
      - Tips tours: the respondent's expected tip per person.
      - Fixed public: EUR 18.
      - Private: group price divided by party size.
    """
    product = PRODUCTS[product_code]
    if product["payment"] == "tips":
        return respondent["expected_tip_per_person"]
    if product["arrangement"] == "private":
        return product["price_per_group"] / respondent["party_size"]
    return product["price_per_person"]


def systematic_utility(respondent, product_code, q):
    """
    V_ij = T + D + P + R + C + F + G, plus tip-uncertainty penalty U for tips tours.
    Returns the component breakdown so the simulator can log and audit it.
    """
    product = PRODUCTS[product_code]

    # Theme fit
    T = resolve_theme_fit(respondent, product_code)

    # Duration (reference level = 2h, so D = 0 for H2/P2)
    D = respondent["duration_preference"] if product["duration"] == 3.5 else 0.0

    # Payment utility: -beta_price * price / 10
    price = effective_price(respondent, product_code)
    P = -respondent["price_sensitivity"] * (price / CONFIG["price_scale_euros"])

    # Private format
    R = respondent["private_preference"] if product["arrangement"] == "private" else 0.0

    # Customization
    C = respondent["customization_preference"] if product["customizable"] == 1 else 0.0

    # Fixed-price preference (positive = prefers fixed, negative = prefers tips).
    # Encoded on fixed-price tours; tips tours get 0 (equivalent in relative utility).
    F = respondent["fixed_price_preference"] if product["payment"] == "fixed" else 0.0

    # Group arrangement: public tours carry the respondent's group tolerance;
    # private tours have no shared-group risk.
    G = respondent["group_size_tolerance"] if product["arrangement"] == "public" else 0.0

    # Tip uncertainty penalty (only applies to tips tours)
    U_tip = -respondent["tip_uncertainty_aversion"] * q if product["payment"] == "tips" else 0.0

    V_total = T + D + P + R + C + F + G + U_tip

    return {
        "T_theme": T,
        "D_duration": D,
        "P_payment": P,
        "R_private": R,
        "C_customization": C,
        "F_fixed_price": F,
        "G_group": G,
        "U_tip_uncertainty": U_tip,
        "V_total": V_total,
        "effective_price_eur": price,
    }


def softmax(utilities, scale):
    """
    Softmax with temperature. Dividing by scale > 1 flattens the distribution.
    Numerically stable: subtract the max before exponentiating.
    """
    scaled = [u / scale for u in utilities]
    m = max(scaled)
    exps = [math.exp(u - m) for u in scaled]
    s = sum(exps)
    return [e / s for e in exps]


# -------------------------------------------------------------------
# Simulation
# -------------------------------------------------------------------

def build_respondents():
    return [dict(zip(RESPONDENT_FIELDS, row)) for row in RESPONDENTS_RAW]


def run_simulation(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    respondents = build_respondents()
    q = CONFIG["tip_uncertainty_level_q"]
    scale = CONFIG["logit_scale_lambda"]
    rng = random.Random(CONFIG["random_seed"])

    # ---------- Write inputs ----------

    with open(out_dir / "respondents.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=RESPONDENT_FIELDS)
        w.writeheader()
        w.writerows(respondents)

    product_fields = ["product_code", "theme", "duration_hours", "payment_type",
                      "price_per_person", "price_per_group", "arrangement", "customizable"]
    with open(out_dir / "products.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(product_fields)
        for code, p in PRODUCTS.items():
            w.writerow([code, p["theme"], p["duration"], p["payment"],
                        p["price_per_person"], p["price_per_group"],
                        p["arrangement"], p["customizable"]])

    with open(out_dir / "choice_tasks.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "alternative_a", "alternative_b", "alternative_c"])
        for row in CHOICE_TASKS:
            w.writerow(row)

    with open(out_dir / "model_config.json", "w") as f:
        json.dump(CONFIG, f, indent=2)

    # ---------- Run choice simulation ----------

    results_rows = []
    components_rows = []

    for r in respondents:
        for task_id, a, b, c in CHOICE_TASKS:
            alternatives = [a, b, c, "NONE"]

            utilities = []
            comp_cache = {}
            for alt in alternatives:
                if alt == "NONE":
                    utilities.append(CONFIG["opt_out_utility"])
                    comp_cache[alt] = {
                        "T_theme": 0.0, "D_duration": 0.0, "P_payment": 0.0,
                        "R_private": 0.0, "C_customization": 0.0, "F_fixed_price": 0.0,
                        "G_group": 0.0, "U_tip_uncertainty": 0.0,
                        "V_total": CONFIG["opt_out_utility"], "effective_price_eur": 0.0,
                    }
                else:
                    comp = systematic_utility(r, alt, q=q)
                    utilities.append(comp["V_total"])
                    comp_cache[alt] = comp

            probs = softmax(utilities, scale=scale)

            # Draw choice using inverse CDF with the seeded RNG
            draw = rng.random()
            cumulative = 0.0
            chosen_idx = len(alternatives) - 1
            for i, prob in enumerate(probs):
                cumulative += prob
                if draw <= cumulative:
                    chosen_idx = i
                    break
            chosen_alt = alternatives[chosen_idx]

            for i, alt in enumerate(alternatives):
                comp = comp_cache[alt]
                results_rows.append({
                    "respondent_id": r["respondent_id"],
                    "task_id": task_id,
                    "alternative_id": alt,
                    "utility_score": round(utilities[i], 4),
                    "choice_probability": round(probs[i], 4),
                    "chosen": 1 if alt == chosen_alt else 0,
                })

                comp_row = {
                    "respondent_id": r["respondent_id"],
                    "task_id": task_id,
                    "alternative_id": alt,
                }
                for key, val in comp.items():
                    comp_row[key] = round(val, 4)
                components_rows.append(comp_row)

    # ---------- Write outputs ----------

    with open(out_dir / "choice_results.csv", "w", newline="") as f:
        fields = ["respondent_id", "task_id", "alternative_id",
                  "utility_score", "choice_probability", "chosen"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(results_rows)

    with open(out_dir / "utility_components.csv", "w", newline="") as f:
        fields = ["respondent_id", "task_id", "alternative_id",
                  "T_theme", "D_duration", "P_payment", "R_private",
                  "C_customization", "F_fixed_price", "G_group",
                  "U_tip_uncertainty", "V_total", "effective_price_eur"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(components_rows)

    return respondents, results_rows, components_rows


# -------------------------------------------------------------------
# Validation
# -------------------------------------------------------------------

def validate(out_dir):
    out_dir = Path(out_dir)
    issues = []

    with open(out_dir / "choice_results.csv") as f:
        rows = list(csv.DictReader(f))

    # Row count: 10 respondents * 12 tasks * 4 alternatives = 480
    if len(rows) != 480:
        issues.append(f"Row count: expected 480, got {len(rows)}")

    # Probabilities sum to 1 per (respondent, task), and exactly one 'chosen' per task
    task_groups = defaultdict(list)
    chosen_counts = defaultdict(int)
    for row in rows:
        key = (row["respondent_id"], row["task_id"])
        task_groups[key].append(float(row["choice_probability"]))
        if row["chosen"] == "1":
            chosen_counts[key] += 1

    for key, probs in task_groups.items():
        total = sum(probs)
        if not (0.999 <= total <= 1.001):
            issues.append(f"{key}: probabilities sum to {total:.4f}, not 1")

    for key, cnt in chosen_counts.items():
        if cnt != 1:
            issues.append(f"{key}: {cnt} chosen, expected exactly 1")

    # Confirm H2 and H3.5 have identical payment+uncertainty utility within a respondent
    with open(out_dir / "utility_components.csv") as f:
        comp_rows = list(csv.DictReader(f))

    for rid in sorted({c["respondent_id"] for c in comp_rows}):
        h2 = next((c for c in comp_rows if c["respondent_id"] == rid and c["alternative_id"] == "H2"), None)
        h35 = next((c for c in comp_rows if c["respondent_id"] == rid and c["alternative_id"] == "H3.5"), None)
        if h2 and h35:
            p_h2 = float(h2["P_payment"]) + float(h2["U_tip_uncertainty"])
            p_h35 = float(h35["P_payment"]) + float(h35["U_tip_uncertainty"])
            if abs(p_h2 - p_h35) > 1e-6:
                issues.append(f"{rid}: H2/H3.5 payment+uncertainty differ ({p_h2} vs {p_h35})")

    # Confirm private per-head price = group_price / party_size
    with open(out_dir / "respondents.csv") as f:
        respondents_check = {r["respondent_id"]: r for r in csv.DictReader(f)}
    for c in comp_rows:
        if c["alternative_id"] in {"P2", "P3.5"}:
            group_price = 175 if c["alternative_id"] == "P2" else 250
            expected = group_price / int(respondents_check[c["respondent_id"]]["party_size"])
            # Allow for the 4-decimal rounding the CSV uses
            if abs(float(c["effective_price_eur"]) - expected) > 5e-4:
                issues.append(
                    f"{c['respondent_id']} {c['alternative_id']}: "
                    f"per-head price {c['effective_price_eur']}, expected {expected}"
                )
                break  # one message per issue type is enough

    return issues


# -------------------------------------------------------------------
# Summary
# -------------------------------------------------------------------

def summarize(out_dir):
    out_dir = Path(out_dir)

    with open(out_dir / "choice_results.csv") as f:
        rows = list(csv.DictReader(f))

    with open(out_dir / "respondents.csv") as f:
        respondents = {r["respondent_id"]: r for r in csv.DictReader(f)}

    total_tasks = 10 * 12
    chosen_counts = defaultdict(int)
    for row in rows:
        if row["chosen"] == "1":
            chosen_counts[row["alternative_id"]] += 1

    # Head-to-head H2 vs H3.5 within tasks 5-8
    h2_wins = h35_wins = other_wins = none_wins = 0
    for row in rows:
        if row["chosen"] == "1" and row["task_id"] in {"5", "6", "7", "8"}:
            if row["alternative_id"] == "H2":
                h2_wins += 1
            elif row["alternative_id"] == "H3.5":
                h35_wins += 1
            elif row["alternative_id"] == "NONE":
                none_wins += 1
            else:
                other_wins += 1

    # Opt-out and modal choice per respondent
    opt_out_by_resp = defaultdict(int)
    chosen_by_resp = defaultdict(lambda: defaultdict(int))
    for row in rows:
        if row["chosen"] == "1":
            if row["alternative_id"] == "NONE":
                opt_out_by_resp[row["respondent_id"]] += 1
            chosen_by_resp[row["respondent_id"]][row["alternative_id"]] += 1

    def modal(d):
        return max(d.items(), key=lambda kv: kv[1])

    # ---------- Report ----------

    lines = []
    lines.append("# Berlin Walking Tour CBC — Simulation Summary\n")
    lines.append("**Synthetic classroom demonstration — not real consumer data.**\n")
    lines.append(f"- Respondents: {CONFIG['respondents']}")
    lines.append(f"- Choice tasks per respondent: {CONFIG['tasks_per_respondent']}")
    lines.append(f"- Alternatives per task: 3 tours + opt-out")
    lines.append(f"- Total decisions: {total_tasks}")
    lines.append(f"- Logit scale lambda: {CONFIG['logit_scale_lambda']}")
    lines.append(f"- Tip uncertainty level q: {CONFIG['tip_uncertainty_level_q']}")
    lines.append(f"- Random seed: {CONFIG['random_seed']}\n")

    lines.append("## Aggregate choice share\n")
    lines.append("| Alternative | Chosen | Share |")
    lines.append("|---|---:|---:|")
    for alt in ["H2", "H3.5", "L", "AB", "P2", "P3.5", "NONE"]:
        cnt = chosen_counts.get(alt, 0)
        lines.append(f"| {alt} | {cnt} | {cnt/total_tasks:.1%} |")
    lines.append("")

    lines.append("## Central hypothesis — H2 vs H3.5 head-to-head (tasks 5-8)\n")
    lines.append("All four of these tasks place H2 and H3.5 together; the third alternative varies.\n")
    lines.append(f"- H2 chosen: {h2_wins} / 40 ({h2_wins/40:.1%})")
    lines.append(f"- H3.5 chosen: {h35_wins} / 40 ({h35_wins/40:.1%})")
    lines.append(f"- Other alternative chosen: {other_wins} / 40 ({other_wins/40:.1%})")
    lines.append(f"- Opt-out chosen: {none_wins} / 40 ({none_wins/40:.1%})\n")
    if h2_wins > h35_wins:
        verdict = ("Under the modelled preferences, the 2-hour public history tour "
                   "is chosen more often than the 3.5-hour format in these head-to-head tasks. "
                   "This supports the shorter-tour hypothesis within the model's assumptions.")
    elif h2_wins == h35_wins:
        verdict = "H2 and H3.5 are chosen equally often; the model is inconclusive."
    else:
        verdict = ("Under the modelled preferences, the 3.5-hour format is chosen more often "
                   "than the 2-hour format. The simulation does NOT support the shorter-tour hypothesis.")
    lines.append(verdict + "\n")

    lines.append("## Per-respondent choice pattern\n")
    lines.append("The archetype column states the preference baked in; the modal choice is what the model picked most often across 12 tasks. Alignment is the preference-recovery check.\n")
    lines.append("| Respondent | Archetype | Party | Opt-outs | Modal choice (count) |")
    lines.append("|---|---|---:|---:|---|")
    for rid in sorted(respondents.keys()):
        archetype = respondents[rid]["archetype"]
        party = respondents[rid]["party_size"]
        opts = opt_out_by_resp.get(rid, 0)
        if chosen_by_resp[rid]:
            top_alt, top_cnt = modal(chosen_by_resp[rid])
            modal_str = f"{top_alt} ({top_cnt})"
        else:
            modal_str = "n/a"
        lines.append(f"| {rid} | {archetype} | {party} | {opts} | {modal_str} |")
    lines.append("")

    lines.append("## Interpretation notes\n")
    lines.append("- Opt-outs cluster among respondents whose best available alternative has large negative price utility or weak theme fit. A high opt-out rate means the current product mix fails that archetype.")
    lines.append("- Private tours (P2, P3.5) win choice share mainly for respondents with large parties (price / party_size is small) and positive private_preference. Solo travellers with high price sensitivity reject private.")
    lines.append("- Fixed-price public tours (L, AB) win when the respondent has strong theme fit and positive fixed_price_preference.")
    lines.append("- Tips tours (H2, H3.5) win when expected tip is low and tip_uncertainty_aversion is low enough that the uncertainty penalty does not outweigh the price advantage.")
    lines.append("")

    lines.append("## Limitations\n")
    lines.append("- 10 synthetic respondents; the frequencies in this file do not estimate real population shares.")
    lines.append("- Preference coefficients are assigned, not estimated. The simulator demonstrates how choices follow from preferences; it cannot test whether the chosen preferences match reality.")
    lines.append("- Expected tip is held constant across H2 and H3.5. The head-to-head duration comparison isolates duration_preference by construction.")
    lines.append("- Tip uncertainty q = 1 applies equally to both tips tours; the uncertainty structure is a simplification, not a measured risk premium.")
    lines.append("- The 12-task design emphasises the H2/H3.5 contrast (4 of 12 tasks). It is not a statistically balanced design optimised for every attribute effect.")
    lines.append("")

    report = "\n".join(lines)
    with open(out_dir / "summary_report.md", "w") as f:
        f.write(report)
    return report


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

if __name__ == "__main__":
    out_dir = Path(__file__).parent
    print(f"Writing outputs to {out_dir}")

    respondents, results, components = run_simulation(out_dir)
    print(f"Generated {len(results)} alternative-level records "
          f"({len(results)//4} tasks x 4 alternatives).")

    issues = validate(out_dir)
    if issues:
        print("\nValidation issues:")
        for i in issues:
            print(f"  - {i}")
    else:
        print("Validation: all checks passed.")

    print()
    print(summarize(out_dir))
