"""
Generate in-character English explanations for every (respondent x task) choice.

Reads the simulator outputs and writes explanations.json, consumed by the
Habbo-style classroom artifact. Explanations are deterministic — produced by
templates driven by the actual utility components, not an LLM call — so the
output is reproducible and ships inside the static site.
"""

import csv
import json
from collections import defaultdict
from pathlib import Path


HERE = Path(__file__).parent


# -------------------------------------------------------------------
# Archetype voices
# -------------------------------------------------------------------

# Each respondent has a "voice" dictionary with phrase fragments the
# templates stitch together. Keeping these per-archetype gives each
# character a recognisable tone across their 12 tasks.
VOICES = {
    "R01": {
        "hook": ["I've only got three hours before my train", "Time is tight today",
                 "Three hours in Berlin and that's it", "Short visit, no time to waste"],
        "wants_short": "I need something that fits a tight schedule",
        "hates_waste": "I'm not spending my only free afternoon on something that drags",
    },
    "R02": {
        "hook": ["I didn't come to Berlin for the museums", "I want the real neighbourhoods",
                 "I'm after Kreuzberg, not Checkpoint Charlie", "Give me the lived-in city"],
        "wants_local": "I want somewhere locals actually go",
        "hates_tourist": "I'll pass on the standard tourist loop",
    },
    "R03": {
        "hook": ["I came for the murals and the squats", "Give me the alternative stuff",
                 "I'm here for the street art", "RAW-Gelände is more my scene than Museum Island"],
        "wants_art": "the art and the alternative culture pull me in",
        "hates_history": "the Cold War tour isn't what I came for",
    },
    "R04": {
        "hook": ["I came specifically for the history", "Berlin is a history book you can walk through",
                 "I've read about this city for years", "I want the full story, not a highlight reel"],
        "wants_depth": "I want the long version, every layer",
        "hates_rush": "a quick overview won't do it",
    },
    "R05": {
        "hook": ["My budget is tight", "We're four friends travelling cheap",
                 "Every euro counts on this trip", "Hostel beds and supermarket dinners this week"],
        "wants_cheap": "I'll walk, not pay",
        "hates_premium": "I'm not dropping that kind of money on a walking tour",
    },
    "R06": {
        "hook": ["Travelling with the family — two kids in tow", "I need something manageable for the group",
                 "Four of us, including the kids", "I'm the one organising this for everyone"],
        "wants_private": "I'd rather have us together, not mixed with strangers",
        "hates_crowd": "a big group tour with my kids is a nightmare",
    },
    "R07": {
        "hook": ["It's just the two of us", "We're happy to pay for comfort",
                 "I'd rather spend more and get the private treatment", "This is a romantic trip, not a group outing"],
        "wants_private": "I want a private experience, tailored to us",
        "hates_strangers": "I'm not sharing our afternoon with twenty strangers",
    },
    "R08": {
        "hook": ["I prefer to explore on my own terms", "I'll pick depth over breadth",
                 "I want something a bit off the standard route", "I'm not into packed tourist groups"],
        "wants_alt": "the alternative Berlin angle is what pulls me",
        "hates_mass": "mass tourism isn't my thing",
    },
    "R09": {
        "hook": ["I'm open to most things", "I like a bit of everything",
                 "Hard to say what I want most, honestly", "I'll go with whatever looks solid"],
        "wants_variety": "I'm curious about several of these",
        "hates_nothing_strong": "nothing jumps out as a dealbreaker",
    },
    "R10": {
        "hook": ["I only have an afternoon free", "I'm here for a day and want colour, not textbooks",
                 "I want the vibrant, visual side of Berlin", "Street art and life on the streets, that's what I'm after"],
        "wants_short_art": "something quick and visual works best",
        "hates_long": "I don't have energy for a long walking day",
    },
}


# Readable tour names and labels used in explanations
TOUR_NAMES = {
    "H2":   "the 2-hour history tour",
    "H3.5": "the 3.5-hour history tour",
    "L":    "the local life tour",
    "AB":   "the alternative Berlin tour",
    "P2":   "the 2-hour private tour",
    "P3.5": "the 3.5-hour private tour",
}

TOUR_SHORT = {
    "H2": "H2", "H3.5": "H3.5", "L": "L", "AB": "AB",
    "P2": "P2 (private)", "P3.5": "P3.5 (private)",
}


def top_drivers(components, chosen_alt):
    """Return the sorted list of (component_name, value) for the chosen alt,
    highest positive first, with the single biggest cost (most negative) too."""
    c = components[chosen_alt]
    comps = [
        ("theme fit", c["T_theme"]),
        ("duration preference", c["D_duration"]),
        ("price", c["P_payment"]),
        ("private format", c["R_private"]),
        ("customization", c["C_customization"]),
        ("fixed-price preference", c["F_fixed_price"]),
        ("group tolerance", c["G_group"]),
        ("tip uncertainty", c["U_tip_uncertainty"]),
    ]
    positives = sorted([(n, v) for n, v in comps if v > 0.1], key=lambda x: -x[1])
    negatives = sorted([(n, v) for n, v in comps if v < -0.1], key=lambda x: x[1])
    return positives, negatives


def opt_out_reason(respondent, components, alternatives):
    """Explain why none of these worked."""
    arch_id = respondent["respondent_id"]
    voice = VOICES[arch_id]
    hook = voice["hook"][0]

    shown = [a for a in alternatives if a != "NONE"]
    all_public = all(a in {"H2", "H3.5", "L", "AB"} for a in shown)
    all_private = all(a in {"P2", "P3.5"} for a in shown)
    all_long = all(components[a]["D_duration"] != 0 for a in shown)
    all_tips = all(a in {"H2", "H3.5"} for a in shown)

    if arch_id == "R01":
        return f"{hook}, and nothing here fits. The private tours are out of reach solo and I can't risk ending up with a huge tip bill. I'll skip."
    if arch_id == "R02":
        if all_tips:
            return f"{hook}, so public history isn't what I want. The private isn't on offer either. I'll skip and head to Kreuzberg myself."
        return f"{hook}. None of these pull me in — I'll explore on my own."
    if arch_id == "R03":
        return f"{hook}. The alternative scene isn't on offer in this set — I'll skip."
    if arch_id == "R04":
        return f"{hook}, and nothing in this set is history-focused enough for what I want. I'll pass."
    if arch_id == "R05":
        return f"{hook} — these are all too expensive for four of us on a budget. I'd rather use a free walking tour and tip what I can."
    if arch_id == "R06":
        if all_public:
            return f"{hook}. Public group tours with the kids are a non-starter and there's no private option here. I'll ask the hotel for family-friendly ideas instead."
        return f"{hook}. Nothing here works — public with the kids is tough, and the private option is still a big spend. I'll look elsewhere."
    if arch_id == "R07":
        if all_public:
            return f"{hook}, and all three options here are public group tours. We'd rather pay for the private tour and have the day to ourselves. Pass."
        return f"{hook}. None of these feels right — I'll wait for a trip where the private option is on the menu."
    if arch_id == "R08":
        return f"{hook}. Nothing here is alternative enough — I'll explore my own route."
    if arch_id == "R09":
        return f"{hook}. Nothing jumps out as worth booking this time — I'll pass."
    if arch_id == "R10":
        if all_long:
            return f"{hook}, and all three options eat the whole afternoon. Not today — I'll wander with my phone instead."
        return f"{hook}. None of these hits the mark — I'll just walk around and look at street art myself."
    return f"{hook}. Nothing in this trio quite works — I'll pass and look around on my own."


def craft_explanation(respondent, chosen_alt, components, alternatives):
    """Build the English, first-person speech-bubble explanation."""
    arch_id = respondent["respondent_id"]
    voice = VOICES[arch_id]

    if chosen_alt == "NONE":
        return opt_out_reason(respondent, components, alternatives)

    name = TOUR_NAMES[chosen_alt]
    name_cap = name[0].upper() + name[1:]
    positives, negatives = top_drivers(components, chosen_alt)
    hook = voice["hook"][int(abs(components[chosen_alt]["V_total"]) * 10) % len(voice["hook"])]

    # Per-respondent crafted explanations by chosen type
    is_private = chosen_alt in {"P2", "P3.5"}
    is_tips = chosen_alt in {"H2", "H3.5"}
    is_fixed_public = chosen_alt in {"L", "AB"}

    # R01 Time-Constrained
    if arch_id == "R01":
        if chosen_alt == "H2":
            return f"{hook}. I'll take the 2-hour history tour — short, covers what I came for, and the tip is bearable."
        if chosen_alt == "H3.5":
            return f"{hook}. The 3.5-hour history tour is longer than I'd like, but it's the only history on the menu and I came for that."
        if is_private:
            return f"{hook}. Private is out of my range as a solo traveller, but I'd take {name} over nothing — I can afford it just about."
        if is_fixed_public:
            return f"{hook}, so I'll take {name}. The fixed price means no surprise about what I owe at the end."

    # R02 Berlin Lifestyle Seeker
    if arch_id == "R02":
        if chosen_alt == "L":
            return f"{hook} — {name} is exactly what I came for. Shared group is fine, €18 is fine, local neighbourhoods are the point."
        if chosen_alt == "AB":
            return f"{hook}. The alternative Berlin tour hits the lived-in angle too, and I like that it's fixed-price."
        if is_private:
            return f"{hook}, and {name} means we get to shape the route around what my partner and I actually want to see."
        if chosen_alt in {"H2", "H3.5"}:
            return f"Not my first choice, but {name} is the best of what's offered here. I'd rather do local life, but history will do."

    # R03 Alternative Culture Enthusiast
    if arch_id == "R03":
        if chosen_alt == "AB":
            return f"{hook}. {name_cap} is why I came to Berlin — street art, alternative scene, the stuff that doesn't fit the Cold War narrative."
        if chosen_alt == "L":
            return f"{hook}. Local life is close enough to the alternative scene for me — I'll take it over the history tours."
        if is_private:
            return f"{hook}, and {name} means I can tell the guide 'show me the murals and the squats' and that's what I get."
        if chosen_alt in {"H2", "H3.5"}:
            return f"History isn't my thing but {name} is the best of a weak menu here."

    # R04 History Enthusiast
    if arch_id == "R04":
        if chosen_alt == "H3.5":
            return f"{hook}. I'll take the long history tour every time — more time, more context, more layers of the story."
        if chosen_alt == "H2":
            return f"{hook}. The 2-hour version is shorter than I'd like, but history is what I came for and the longer one isn't on this menu."
        if is_private:
            return f"{hook}. I'd customise {name} to be a deep history walk — happy to pay for the guide's full attention."
        if is_fixed_public:
            return f"Not what I came for, but {name} is the best option in this set."

    # R05 Budget-Conscious Friends
    if arch_id == "R05":
        if chosen_alt in {"H2", "H3.5"}:
            return f"{hook} — {name} is tips-based, so I can pay what I can afford. That's the plan."
        if is_fixed_public:
            return f"€18 is at the top of what I'll pay for a walking tour, but {name} looks worth it for four of us."
        if is_private:
            return f"{hook}, but splitting {name} across four of us keeps the per-head cost down — it's borderline but worth it."

    # R06 Family Organizer
    if arch_id == "R06":
        if chosen_alt == "P2":
            return f"{hook}. The 2-hour private tour is perfect — just us four, kids can set the pace, €43 each is manageable."
        if chosen_alt == "P3.5":
            return f"{hook}. Private is the way, even if 3.5 hours is a stretch for the kids. We'll make it work."
        if is_fixed_public:
            return f"If private isn't on offer, {name} is a safe second — fixed price, I know what I'm paying for four of us."
        if is_tips:
            return f"{hook}. {name_cap} is my fallback — short enough for the kids, and the tip is manageable even for four."

    # R07 Comfort-Oriented Couple
    if arch_id == "R07":
        if chosen_alt == "P3.5":
            return f"{hook}. {name_cap} is exactly what we want — just the two of us, tailored to our interests, worth every euro."
        if chosen_alt == "P2":
            return f"{hook}. The 2-hour private tour is a bit short, but better than sharing a sidewalk with 20 strangers."
        if chosen_alt == "AB":
            return f"If private isn't on the menu, {name} is a decent fallback — I'd still rather pay for the private, but this works."
        if is_tips:
            return f"Not ideal — I'd rather pay a fixed price and get a private tour. {name_cap} is the best of what's offered."

    # R08 Independent Urban Explorer
    if arch_id == "R08":
        if chosen_alt == "AB":
            return f"{hook}. {name_cap} fits — alternative, art-forward, not the standard tourist loop."
        if chosen_alt == "L":
            return f"{hook}. Local life works for me — proper neighbourhoods, not the Brandenburg Gate parade."
        if chosen_alt == "H2":
            return f"If I have to do history, the 2-hour version is enough. {hook}."
        if is_private:
            return f"Solo private is expensive, but {name} lets me shape the walk to the alternative side of the city."

    # R09 Curious Generalist
    if arch_id == "R09":
        if chosen_alt == "AB":
            return f"{hook}. {name_cap} looks interesting — I'll go with the alternative angle today."
        if chosen_alt == "L":
            return f"{hook}. Local life sounds good — fixed price, nice length, varied content."
        if chosen_alt == "H3.5":
            return f"{hook}, and {name} gives me the most depth for the time. I'll take it."
        if is_private:
            return f"{hook}, and splitting {name} between the two of us is manageable. Private sounds nice for a change."

    # R10 Spontaneous Culture Seeker
    if arch_id == "R10":
        if chosen_alt == "AB":
            return f"{hook}. {name_cap} is the visual, vibrant side of Berlin — exactly my scene, even if it's a bit long."
        if chosen_alt == "L":
            return f"{hook}. Local life gives me the colour I want without the heavy history angle."
        if is_private:
            return f"{hook}, and splitting {name} between the two of us means we can request the street-art route."
        if is_tips:
            return f"History isn't my thing but {name} is the best option here."

    # Fallback — generic
    return f"I'll take {name}. It's the best fit from what's on offer in this set."


# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------

def main():
    # Load required inputs
    with open(HERE / "respondents.csv") as f:
        respondents = {r["respondent_id"]: r for r in csv.DictReader(f)}

    with open(HERE / "choice_tasks.csv") as f:
        tasks = {r["task_id"]: (r["alternative_a"], r["alternative_b"], r["alternative_c"], "NONE")
                 for r in csv.DictReader(f)}

    with open(HERE / "choice_results.csv") as f:
        results = list(csv.DictReader(f))

    with open(HERE / "utility_components.csv") as f:
        comp_rows = list(csv.DictReader(f))

    # Index utility components by (resp, task, alt)
    comps_by = defaultdict(dict)
    for row in comp_rows:
        key = (row["respondent_id"], row["task_id"])
        comps_by[key][row["alternative_id"]] = {
            k: float(row[k]) for k in [
                "T_theme", "D_duration", "P_payment", "R_private",
                "C_customization", "F_fixed_price", "G_group",
                "U_tip_uncertainty", "V_total", "effective_price_eur",
            ]
        }

    # Index chosen alternative by (resp, task)
    chosen_by = {}
    for row in results:
        if row["chosen"] == "1":
            chosen_by[(row["respondent_id"], row["task_id"])] = row["alternative_id"]

    # Build explanations
    explanations = []
    for rid in sorted(respondents.keys()):
        for tid in sorted(tasks.keys(), key=int):
            key = (rid, tid)
            chosen = chosen_by[key]
            components = comps_by[key]
            alternatives = list(tasks[tid])
            text = craft_explanation(respondents[rid], chosen, components, alternatives)
            explanations.append({
                "respondent_id": rid,
                "task_id": int(tid),
                "chosen_alternative": chosen,
                "explanation": text,
            })

    out_path = HERE / "explanations.json"
    with open(out_path, "w") as f:
        json.dump(explanations, f, indent=2)
    print(f"Wrote {len(explanations)} explanations to {out_path}")

    # Preview a few
    print("\nSample explanations:")
    for ex in [explanations[6*12 + 0], explanations[6*12 + 4], explanations[0]]:
        print(f"\n{ex['respondent_id']} task {ex['task_id']} chose {ex['chosen_alternative']}:")
        print(f"  \"{ex['explanation']}\"")


if __name__ == "__main__":
    main()
