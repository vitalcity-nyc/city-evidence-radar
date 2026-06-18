"""
One-time enrichment: add effect_magnitude, underused, novelty and theme to every
already-scored paper, then recompute the overall score with the new balanced
formula. Non-destructive to existing fields (idea, summary, effect_size, reach,
the 1-5 feasibility ratings). Idempotent: skips papers that already have a theme.
"""
import json
import re
import sys
import time

import requests

sys.path.insert(0, ".")
from scanner import config as C
from scanner import score as S

PROMPT = """You are an evidence analyst for a New York City civic-journalism outlet that \
wants to surface UNDERUSED, high-promise ideas for improving city life, with a public-safety \
emphasis. For this study (title + abstract, plus the one-line idea already extracted), return \
ONLY a JSON object with these keys:

- "effect_magnitude": integer 1-5 for how LARGE and PROMISING the demonstrated effect is. \
1 = null / no significant effect / negligible; 2 = small; 3 = moderate; 4 = large; 5 = very \
large and robust. A rigorously evaluated study that found NO effect must get 1-2.
- "effect_magnitude_note": short phrase justifying it.
- "underused": integer 1-5 for the GAP between the strength of the evidence and how much this \
idea is actually deployed or invested in, especially in large US cities like New York. \
1 = already mainstream/widely adopted (hot-spot policing, focused deterrence, body cameras); \
5 = strong or promising evidence but rarely tried or underfunded.
- "underused_note": short phrase why.
- "novelty": integer 1-5 for how fresh or counterintuitive the framing is. 1 = conventional; \
5 = a genuinely new way of thinking about the problem.
- "novelty_note": short phrase why.
- "theme": the SINGLE best-fit theme key from: {themes}. Use "other" only if none fit.

TITLE: {title}
IDEA: {idea}
ABSTRACT: {abstract}"""


def enrich_one(key, p):
    body = {
        "model": S.MODEL,
        "max_tokens": 350,
        "messages": [{"role": "user", "content": PROMPT.format(
            themes=C.THEME_KEYS, title=p["title"], idea=p.get("idea", ""),
            abstract=(p["abstract"] or "(no abstract)")[:4000])}],
    }
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01",
               "content-type": "application/json"}
    r = requests.post(S.API_URL, headers=headers, json=body, timeout=60)
    r.raise_for_status()
    t = r.json()["content"][0]["text"].strip()
    t = re.sub(r"^```(json)?|```$", "", t, flags=re.MULTILINE).strip()
    return json.loads(t[t.find("{"):t.rfind("}") + 1]), r.json().get("usage", {})


def main():
    with open("data/papers.json") as f:
        blob = json.load(f)
    papers = blob["papers"]
    key = S.get_api_key()
    done = skip = err = itok = otok = 0
    for p in papers:
        if p.get("theme"):
            skip += 1
            continue
        try:
            s, usage = enrich_one(key, p)
            itok += usage.get("input_tokens", 0)
            otok += usage.get("output_tokens", 0)
            num = lambda k: max(1, min(5, int(s.get(k) or 1)))
            theme = (s.get("theme") or "other").strip()
            p["effect_magnitude"] = num("effect_magnitude")
            p["effect_magnitude_note"] = (s.get("effect_magnitude_note") or "").strip()
            p["underused"] = num("underused")
            p["underused_note"] = (s.get("underused_note") or "").strip()
            p["novelty"] = num("novelty")
            p["novelty_note"] = (s.get("novelty_note") or "").strip()
            p["theme"] = theme if theme in C.THEME_KEYS else "other"
            done += 1
            if done % 50 == 0:
                print(f"  [enrich] {done} done...", flush=True)
        except Exception as e:
            err += 1
            print(f"  [enrich] ERR {p['id']} {str(e)[:90]}", flush=True)
        time.sleep(0.15)

    # recompute every score with the new balanced formula
    for p in papers:
        p["score"] = S.compute_score(p)
    papers.sort(key=lambda p: (p.get("score", 0), p.get("published") or ""), reverse=True)

    blob["themes"] = [{"key": k, "label": l, "blurb": b} for k, l, b in C.THEMES]
    blob["sources"] = C.SOURCE_SUMMARY
    blob["known_gaps"] = C.KNOWN_GAPS
    with open("data/papers.json", "w") as f:
        json.dump(blob, f, indent=2)
    cost = itok / 1e6 * 1.0 + otok / 1e6 * 5.0
    print(f"\n  [enrich] done={done} skip={skip} err={err}  est_cost=${cost:.3f}")


if __name__ == "__main__":
    main()
