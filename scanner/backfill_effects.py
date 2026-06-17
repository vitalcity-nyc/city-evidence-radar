"""
One-time backfill: add effect_size + reach to existing scored papers without
re-deriving the other fields. Uses a small focused prompt (cheap). Idempotent:
skips papers that already have a non-empty effect_size.
"""
import json
import re
import sys
import time

import requests

sys.path.insert(0, ".")
from scanner import score as S

PROMPT = """From this study's title and abstract, extract two facts. Return ONLY a JSON \
object with keys "effect_size" and "reach".

- "effect_size": magnitude AND direction of the MAIN finding as a short phrase with the \
number (e.g. "15% fewer parole violations", "0.18 SD higher test scores", "no significant \
effect"). If no quantified effect is given, return "Not quantified in abstract".
- "reach": how many people/units the study covered, with the number and unit (e.g. \
"1,156 parolees", "~30,000 court cases", "12 cities over 6 years"). If not stated, return \
"Not stated in abstract".

TITLE: {title}
ABSTRACT: {abstract}"""


def extract(key, item):
    body = {
        "model": S.MODEL,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": PROMPT.format(
            title=item["title"], abstract=(item["abstract"] or "(no abstract)")[:4000])}],
    }
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01",
               "content-type": "application/json"}
    r = requests.post(S.API_URL, headers=headers, json=body, timeout=60)
    r.raise_for_status()
    text = r.json()["content"][0]["text"].strip()
    text = re.sub(r"^```(json)?|```$", "", text, flags=re.MULTILINE).strip()
    start = text.find("{")
    return json.loads(text[start:text.rfind("}") + 1]), r.json().get("usage", {})


def main():
    with open("data/papers.json") as f:
        blob = json.load(f)
    papers = blob["papers"]
    key = S.get_api_key()
    done, skip, err, itok, otok = 0, 0, 0, 0, 0
    for p in papers:
        if p.get("effect_size"):
            skip += 1
            continue
        try:
            s, usage = extract(key, p)
            itok += usage.get("input_tokens", 0)
            otok += usage.get("output_tokens", 0)
            p["effect_size"] = (s.get("effect_size") or "").strip()
            p["reach"] = (s.get("reach") or "").strip()
            done += 1
            if done % 50 == 0:
                print(f"  [backfill] {done} done...", flush=True)
        except Exception as e:
            err += 1
            print(f"  [backfill] ERR {p['id']} {str(e)[:90]}", flush=True)
        time.sleep(0.15)
    with open("data/papers.json", "w") as f:
        json.dump(blob, f, indent=2)
    cost = itok / 1e6 * 1.0 + otok / 1e6 * 5.0
    print(f"\n  [backfill] done={done} skip={skip} err={err}  est_cost=${cost:.3f}")


if __name__ == "__main__":
    main()
