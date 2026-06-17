"""
Fetch candidate research items from all configured sources.

Every fetcher is wrapped so one failing source never aborts the run.
Output: a list of normalized dicts (see normalize()).
"""
import hashlib
import re
import sys
import time
import warnings
from datetime import datetime, timezone

import feedparser
import requests

warnings.filterwarnings("ignore")

sys.path.insert(0, ".")
from scanner import config as C

HEADERS = {"User-Agent": C.UA}


def log(msg):
    print(f"  [fetch] {msg}", flush=True)


def clean(text):
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)          # strip HTML tags
    text = re.sub(r"\s+", " ", text)              # collapse whitespace
    return text.strip()


def make_id(url, title):
    return hashlib.sha1((url or title).encode("utf-8")).hexdigest()[:16]


def normalize(title, authors, abstract, url, published, source, source_type,
              doi=None, venue=None, default_topic=None):
    return {
        "id": make_id(url, title),
        "title": clean(title),
        "authors": authors or "",
        "abstract": clean(abstract),
        "url": url,
        "doi": doi,
        "published": published,        # ISO date string or None
        "source": source,             # e.g. "NBER", "arXiv", journal name
        "source_type": source_type,   # working_paper | preprint | journal | review | think_tank
        "venue": venue or source,
        "default_topic": default_topic,
    }


# ---------------------------------------------------------------------------
def fetch_arxiv():
    out = []
    cats = "+OR+".join(f"cat:{c}" for c in C.ARXIV_CATEGORIES)
    url = (f"http://export.arxiv.org/api/query?search_query={cats}"
           f"&sortBy=submittedDate&sortOrder=descending&max_results={C.ARXIV_MAX}")
    d = feedparser.parse(url, request_headers=HEADERS)
    for e in d.entries:
        authors = ", ".join(a.get("name", "") for a in e.get("authors", []))
        published = e.get("published", "")[:10] or None
        link = e.get("link", "")
        out.append(normalize(e.get("title"), authors, e.get("summary"),
                             link, published, "arXiv", "preprint"))
    log(f"arXiv: {len(out)}")
    return out


def fetch_nber():
    out = []
    d = feedparser.parse(C.NBER_FEED, request_headers=HEADERS)
    for e in d.entries:
        title = e.get("title", "")
        authors = ""
        # NBER titles look like "Paper Title -- by Author A, Author B"
        if " -- by " in title:
            title, authors = title.split(" -- by ", 1)
        published = None
        if e.get("published_parsed"):
            published = time.strftime("%Y-%m-%d", e.published_parsed)
        out.append(normalize(title, authors, e.get("description"),
                             e.get("link", ""), published, "NBER", "working_paper"))
    log(f"NBER: {len(out)}")
    return out


def fetch_crossref():
    out = []
    cutoff = (datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    for name, issn, topic in C.JOURNALS:
        try:
            url = (f"https://api.crossref.org/journals/{issn}/works"
                   f"?rows={C.CROSSREF_ROWS}&sort=published&order=desc"
                   f"&select=title,author,abstract,DOI,URL,published")
            r = requests.get(url, headers=HEADERS, timeout=30)
            items = r.json().get("message", {}).get("items", [])
            n = 0
            for it in items:
                title = (it.get("title") or [""])[0]
                if not title:
                    continue
                authors = ", ".join(
                    f"{a.get('given','')} {a.get('family','')}".strip()
                    for a in it.get("author", []) if a.get("family"))
                pub = it.get("published", {}).get("date-parts", [[None]])[0]
                published = "-".join(f"{p:02d}" if i else str(p)
                                     for i, p in enumerate(pub) if p) if pub and pub[0] else None
                doi = it.get("DOI")
                link = it.get("URL") or (f"https://doi.org/{doi}" if doi else "")
                out.append(normalize(title, authors, it.get("abstract"), link,
                                     published, name, "journal", doi=doi,
                                     venue=name, default_topic=topic))
                n += 1
            log(f"Crossref {name}: {n}")
            time.sleep(0.4)  # be polite to the public API
        except Exception as e:
            log(f"Crossref {name}: FAIL {e}")
    return out


def fetch_rss():
    out = []
    for name, url, stype in C.RSS_FEEDS:
        try:
            d = feedparser.parse(url, request_headers=HEADERS)
            n = 0
            for e in d.entries:
                authors = ", ".join(a.get("name", "") for a in e.get("authors", [])) \
                    if e.get("authors") else e.get("author", "")
                published = None
                if e.get("published_parsed"):
                    published = time.strftime("%Y-%m-%d", e.published_parsed)
                body = e.get("summary") or e.get("description") or ""
                out.append(normalize(e.get("title"), authors, body,
                                     e.get("link", ""), published, name, stype))
                n += 1
            log(f"RSS {name}: {n}")
        except Exception as e:
            log(f"RSS {name}: FAIL {e}")
    return out


def fetch_all():
    items = []
    for fn in (fetch_arxiv, fetch_nber, fetch_crossref, fetch_rss):
        try:
            items += fn()
        except Exception as e:
            log(f"{fn.__name__}: FAIL {e}")
    # dedupe by id
    seen, uniq = set(), []
    for it in items:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        uniq.append(it)
    log(f"TOTAL unique: {len(uniq)}")
    return uniq


if __name__ == "__main__":
    import json
    data = fetch_all()
    with open("data/raw.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {len(data)} items to data/raw.json")
