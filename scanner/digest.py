"""
Build and send the weekly digest of new high-scoring ideas to Josh via iMessage.

Delivery is direct osascript (no MCP needed) so it works from launchd/cron.
"Recent" = scored within RECENT_DAYS. Only causal-evidence, relevant items
above the score threshold make the digest.
"""
import json
import subprocess
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, ".")
from scanner import config as C

IMESSAGE_TO = "9175823254"   # per Josh's standing notification preference
SCORE_MIN = 60
STRONG = {"RCT", "strong quasi-experimental"}


def recent_winners():
    with open("data/papers.json") as f:
        papers = json.load(f).get("papers", [])
    cutoff = (datetime.utcnow() - timedelta(days=C.RECENT_DAYS)).strftime("%Y-%m-%d")
    picks = [p for p in papers
             if p.get("relevant")
             and p.get("causal_strength") in STRONG
             and p.get("score", 0) >= SCORE_MIN
             and (p.get("scored_at") or "") >= cutoff]
    picks.sort(key=lambda p: p.get("score", 0), reverse=True)
    return picks


def build_message(picks, site_url):
    if not picks:
        return None
    lines = [f"City Evidence Radar — {len(picks)} new vetted idea(s) this week:\n"]
    for p in picks[:8]:
        flag = "🚨 " if p.get("public_safety") else "• "
        lines.append(f"{flag}[{p['score']}] {p['title']}")
        if p.get("idea"):
            lines.append(f"   {p['idea']}")
        lines.append(f"   {p['causal_strength']} · {p['source']} · {p['url']}\n")
    if len(picks) > 8:
        lines.append(f"…and {len(picks)-8} more.\n")
    if site_url:
        lines.append(f"Browse all: {site_url}")
    return "\n".join(lines)


def send_imessage(body):
    script = f'''
    tell application "Messages"
        set targetService to 1st account whose service type = iMessage
        set targetBuddy to participant "{IMESSAGE_TO}" of targetService
        send "{body.replace('"', "'").replace(chr(92), "")}" to targetBuddy
    end tell'''
    subprocess.run(["osascript", "-e", script], check=True)


def main():
    site_url = sys.argv[1] if len(sys.argv) > 1 else ""
    picks = recent_winners()
    msg = build_message(picks, site_url)
    if not msg:
        print("  [digest] no new winners this week — no message sent")
        return
    # save a copy regardless
    with open(f"logs/digest_{time.strftime('%Y%m%d')}.txt", "w") as f:
        f.write(msg)
    try:
        send_imessage(msg)
        print(f"  [digest] sent {len(picks)} ideas to {IMESSAGE_TO}")
    except Exception as e:
        print(f"  [digest] iMessage send FAILED ({e}); digest saved to logs/")


if __name__ == "__main__":
    main()
