"""
Score each candidate with Claude (Haiku) on the four dimensions Josh chose:
  - causal strength (causal-evidence-only bar)
  - scalability + cost-effectiveness flags
  - NYC applicability
  - public-safety weighting

Only UNSEEN items are sent to the API; previously scored items are reused from
data/papers.json. This keeps ongoing cost to pennies per weekly run.
"""
import json
import os
import re
import subprocess
import sys
import time

import requests

sys.path.insert(0, ".")
from scanner import config as C

MODEL = "claude-haiku-4-5-20251001"
API_URL = "https://api.anthropic.com/v1/messages"

# Feeds broad enough to need a relevance keyword gate before spending API calls.
GATE_SOURCES = {"arXiv", "NBER", "Urban Institute", "World Bank", "SocArXiv"}
GATE_TERMS = [
    "crime", "police", "polic", "violence", "violent", "gun", "shooting", "homicide",
    "safety", "victim", "incarcerat", "prison", "jail", "recidivism", "reentry", "reoffend",
    "city", "cities", "urban", "neighborhood", "neighbourhood", "housing", "homeless",
    "eviction", "rent", "tenant", "transit", "transport", "commut", "traffic", "pedestrian",
    "school", "student", "education", "youth", "health", "mental", "overdose", "addiction",
    "poverty", "welfare", "cash transfer", "employment", "job", "wage", "social", "community",
    "lighting", "blight", "vacant", "311", "emergency", "fire", "ems", "trash", "sanitation",
    "court", "diversion", "probation", "parole", "deterrence", "nuisance", "disorder",
]

TOPICS = ["public safety", "housing", "transit/mobility", "health", "education",
          "economic mobility", "governance/services", "environment", "other"]
CAUSAL = ["RCT", "strong quasi-experimental", "observational", "descriptive", "non-empirical"]

PROMPT = """You are an evidence analyst for a New York City civic-journalism outlet. \
You triage research for ideas that could practically improve the lives of people who \
live in cities, with special weight on PUBLIC SAFETY, but also housing, transit, health, \
education, economic mobility, city services, and environment.

Read this item (you only have title + abstract; judge accordingly):

TITLE: {title}
VENUE: {venue} ({source_type})
AUTHORS: {authors}
ABSTRACT: {abstract}

Return ONLY a JSON object (no prose, no markdown fence) with these keys:
- "relevant": true/false. True ONLY if it identifies a concrete, potentially actionable \
intervention, policy, program, or practice that a city could plausibly adopt to improve \
residents' lives. False for pure theory, methods papers, forecasts with no lever, or \
topics with no city-policy hook.
- "topic": one of {topics}
- "public_safety": true/false (does the idea bear on crime, violence, policing, justice, \
emergency response, or community safety?)
- "idea": one sentence stating the actionable idea/intervention.
- "summary": 2-3 sentences on what the study actually found.
- "effect_size": the magnitude AND direction of the study's MAIN finding as a short phrase \
with the number (e.g. "15% fewer parole violations", "0.18 SD higher test scores", \
"34% drop in nighttime crime", "no statistically significant effect"). If the abstract \
gives no quantified effect, return "Not quantified in abstract".
- "reach": how many people/units the study covered, as a short phrase with the number and \
unit (e.g. "1,156 parolees", "~30,000 court cases", "12 cities over 6 years", \
"8 RCTs, 11,000 students"). If not stated, return "Not stated in abstract".
- "method": one sentence on how it was conducted (design, data, setting, sample size if stated).
- "causal_strength": one of {causal}. Use "RCT" only for randomized experiments; \
"strong quasi-experimental" for credible diff-in-diff / RD / IV / natural experiments; \
"observational" for controlled correlational; "descriptive" for descriptive/measurement; \
"non-empirical" for theory/review-of-others (note: a rigorous systematic review/meta-analysis \
of experiments counts as "strong quasi-experimental").
- "effect_magnitude": integer 1-5 for how LARGE and PROMISING the demonstrated effect is. \
1 = null / no significant effect / negligible; 2 = small; 3 = moderate; 4 = large; \
5 = very large and robust. A rigorously evaluated study that found NO effect must get 1-2.
- "effect_magnitude_note": short phrase justifying the rating.
- "scalability": integer 1-5 (5 = easily scaled city- or nationwide).
- "scalability_note": short phrase why.
- "cost": integer 1-5 (5 = very cheap / highly cost-effective per person helped).
- "cost_note": short phrase; include a per-unit cost if the abstract gives one.
- "nyc_applicability": integer 1-5 (5 = directly implementable in NYC given its agencies/programs).
- "nyc_note": short phrase why.
- "underused": integer 1-5 for the GAP between the strength of the evidence and how much \
this idea is actually deployed or invested in, especially in large US cities like New York. \
1 = already mainstream and widely adopted (e.g. hot-spot policing, focused deterrence, body \
cameras); 5 = strong or promising evidence but rarely tried or underfunded. Weight toward \
ideas a city is NOT already doing.
- "underused_note": short phrase why.
- "novelty": integer 1-5 for how fresh or counterintuitive the framing is for public-safety \
or urban policy. 1 = conventional/well-worn; 5 = a genuinely new way of thinking about the problem.
- "novelty_note": short phrase why.
- "theme": the SINGLE best-fit editorial theme key from this list: {themes}. Use "other" \
only if none fit.
- "confidence": "low"/"medium"/"high" — your confidence given only the abstract.
"""


def get_api_key():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return os.environ["ANTHROPIC_API_KEY"]
    return subprocess.check_output(
        ["security", "find-generic-password", "-s", "ANTHROPIC_API_KEY", "-w"]
    ).decode().strip()


def gated_out(item):
    """True if a broad-feed item clearly isn't on-topic (skip to save API spend)."""
    if item["source"] not in GATE_SOURCES:
        return False
    blob = (item["title"] + " " + item["abstract"]).lower()
    return not any(t in blob for t in GATE_TERMS)


def call_claude(key, item):
    body = {
        "model": MODEL,
        "max_tokens": 900,
        "messages": [{
            "role": "user",
            "content": PROMPT.format(
                title=item["title"], venue=item["venue"],
                source_type=item["source_type"], authors=item["authors"][:300],
                abstract=(item["abstract"] or "(no abstract available)")[:4000],
                topics=TOPICS, causal=CAUSAL, themes=C.THEME_KEYS),
        }],
    }
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01",
               "content-type": "application/json"}
    r = requests.post(API_URL, headers=headers, json=body, timeout=60)
    r.raise_for_status()
    text = r.json()["content"][0]["text"].strip()
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # model appended prose after the object — extract the first balanced {...}
        start = text.find("{")
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    parsed = json.loads(text[start:i + 1])
                    break
        else:
            raise
    return parsed, r.json().get("usage", {})


def compute_score(s):
    """0-100 overall (balanced weighting).

    Effect magnitude is the single largest factor, so rigorously-evaluated nulls
    rank below high-promise findings. Rigor and feasibility still dominate;
    underused + novelty are meaningful but secondary. Public-safety nudge on top.
    Max from dimensions = 100: effect 26 + causal 20 + scalability 13 + cost 13
    + NYC 12 + underused 9 + novelty 7.
    """
    causal_bonus = {"RCT": 20, "strong quasi-experimental": 14,
                    "observational": 6, "descriptive": 1, "non-empirical": 0}
    n = lambda k: max(1, min(5, s.get(k, 1) or 1))
    score = (n("effect_magnitude") / 5) * 26
    score += causal_bonus.get(s.get("causal_strength"), 0)
    score += (n("scalability") / 5) * 13
    score += (n("cost") / 5) * 13
    score += (n("nyc_applicability") / 5) * 12
    score += (n("underused") / 5) * 9
    score += (n("novelty") / 5) * 7
    if s.get("public_safety"):
        score += 8  # public-safety emphasis
    if s.get("confidence") == "low":
        score -= 5
    return round(max(0, min(100, score)))


def main():
    with open("data/raw.json") as f:
        raw = json.load(f)

    archive = {}
    if os.path.exists("data/papers.json"):
        with open("data/papers.json") as f:
            for p in json.load(f).get("papers", []):
                archive[p["id"]] = p

    key = get_api_key()
    new, gated, errs, in_tok, out_tok = 0, 0, 0, 0, 0

    for item in raw:
        if item["id"] in archive:
            continue
        if gated_out(item):
            gated += 1
            continue
        try:
            s, usage = call_claude(key, item)
            in_tok += usage.get("input_tokens", 0)
            out_tok += usage.get("output_tokens", 0)

            def txt(k):
                return (s.get(k) or "").strip()

            def num(k):
                try:
                    return max(1, min(5, int(s.get(k) or 1)))
                except (TypeError, ValueError):
                    return 1

            rec = dict(item)
            rec.update({
                "relevant": bool(s.get("relevant")),
                "topic": txt("topic") or "other",
                "public_safety": bool(s.get("public_safety")),
                "idea": txt("idea"),
                "summary": txt("summary"),
                "effect_size": txt("effect_size"),
                "reach": txt("reach"),
                "method": txt("method"),
                "causal_strength": txt("causal_strength") or "non-empirical",
                "effect_magnitude": num("effect_magnitude"),
                "effect_magnitude_note": txt("effect_magnitude_note"),
                "scalability": num("scalability"),
                "scalability_note": txt("scalability_note"),
                "cost": num("cost"),
                "cost_note": txt("cost_note"),
                "nyc_applicability": num("nyc_applicability"),
                "nyc_note": txt("nyc_note"),
                "underused": num("underused"),
                "underused_note": txt("underused_note"),
                "novelty": num("novelty"),
                "novelty_note": txt("novelty_note"),
                "theme": (txt("theme") or "other") if (txt("theme") or "other") in C.THEME_KEYS else "other",
                "confidence": txt("confidence") or "low",
                "scored_at": time.strftime("%Y-%m-%d"),
            })
            rec["score"] = compute_score(rec)
            archive[item["id"]] = rec
            new += 1
            if new % 25 == 0:
                print(f"  [score] {new} scored...", flush=True)
        except Exception as e:
            errs += 1
            print(f"  [score] ERR {item['id']} {str(e)[:120]}", flush=True)
        time.sleep(0.2)

    papers = sorted(archive.values(),
                    key=lambda p: (p.get("score", 0), p.get("published") or ""),
                    reverse=True)
    out = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "count": len(papers),
        "sources": C.SOURCE_SUMMARY,
        "known_gaps": C.KNOWN_GAPS,
        "themes": [{"key": k, "label": l, "blurb": b} for k, l, b in C.THEMES],
        "papers": papers,
    }
    with open("data/papers.json", "w") as f:
        json.dump(out, f, indent=2)

    # rough cost estimate (Haiku 4.5: ~$1 / Mtok in, ~$5 / Mtok out)
    cost = in_tok / 1e6 * 1.0 + out_tok / 1e6 * 5.0
    print(f"\n  [score] new={new} gated={gated} errors={errs} total_archive={len(papers)}")
    print(f"  [score] tokens in={in_tok} out={out_tok}  est_cost=${cost:.3f}")


if __name__ == "__main__":
    main()
