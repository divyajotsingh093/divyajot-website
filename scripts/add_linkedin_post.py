#!/usr/bin/env python3
"""
add_linkedin_post.py
Add one LinkedIn post to data.json from just its URL.

    python scripts/add_linkedin_post.py --url "https://www.linkedin.com/posts/...-activity-7503302693537349632-MlTf"
    python scripts/add_linkedin_post.py --url "https://lnkd.in/gXXXX" --title "One-line summary"

What it does
  1. Resolves short links (lnkd.in) and parses the activity/share id out of any
     LinkedIn post URL shape (feed/update/urn:li:activity:ID, posts/…-activity-ID-xxx,
     urn:li:share:ID, urn:li:ugcPost:ID).
  2. Derives the post date from the id (LinkedIn ids carry a millisecond timestamp
     in their top bits), so no fetch is needed for the date.
  3. Fetches the public post page and lifts the post text (or og:title as a
     fallback) to build a one-line summary. --title overrides the fetched text.
  4. Merges the entry into data.json → feeds.linkedin_posts (newest first,
     deduplicated by activity id, capped), updates _meta.last_updated.

Exit codes: 0 = data.json changed, 3 = post already present (nothing to do),
1 = bad input / unrecoverable error.
"""

import argparse
import html as htmlmod
import json
import os
import re
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data.json")
CAP = 10
TITLE_MAX = 200

UAS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36",
    "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    "Mozilla/5.0 (compatible; bot)",
]

ID_PATTERNS = [
    re.compile(r"urn:li:(?:activity|share|ugcPost):(\d{15,})", re.I),
    re.compile(r"[-_](?:activity|share|ugcPost)[-:](\d{15,})", re.I),
    re.compile(r"activity[-:=](\d{15,})", re.I),
]


def fetch(url, timeout=20):
    """GET a URL trying a few user agents. Returns (final_url, text) or (None, None)."""
    for ua in UAS:
        req = Request(url, headers={"User-Agent": ua, "Accept-Language": "en"})
        try:
            with urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", "replace")
                return r.geturl(), body
        except (URLError, HTTPError, TimeoutError, ValueError) as e:
            print(f"  ! fetch failed ({ua[:24]}…): {e}", file=sys.stderr)
    return None, None


def resolve_short(url):
    """Follow lnkd.in / other redirectors to the real LinkedIn URL."""
    if "lnkd.in" not in url and "linkedin.com" in url:
        return url
    final, _ = fetch(url)
    return final or url


def extract_id(url):
    for pat in ID_PATTERNS:
        m = pat.search(url)
        if m:
            return m.group(1)
    return None


def id_to_iso(post_id):
    """LinkedIn activity ids are Snowflake-like: top bits are a ms epoch timestamp."""
    ms = int(post_id) >> 22
    d = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    return d.strftime("%Y-%m-%dT%H:%M:%SZ")


def clean(s):
    s = htmlmod.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()


def clip(s, n=TITLE_MAX):
    s = s.strip()
    if len(s) <= n:
        return s
    cut = s[:n]
    sp = cut.rfind(" ")
    if sp > n * 0.6:
        cut = cut[:sp]
    return cut.rstrip(" ,.;:—–-") + "…"


def summarise(text):
    """First sentence or two of the post, clipped to TITLE_MAX at a word boundary."""
    text = clean(text)
    if not text:
        return ""
    # Take whole sentences while they fit comfortably.
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = ""
    for p in parts:
        cand = (out + " " + p).strip()
        if len(cand) > TITLE_MAX * 0.85 and out:
            break
        out = cand
        if len(out) >= 90:
            break
    return clip(out or text)


def extract_text(page):
    """Post body from the public page; falls back to og:title / description."""
    if not page:
        return "", ""
    m = re.search(r'<p[^>]*attributed-text-segment-list__content[^>]*>(.*?)</p>', page, re.S)
    body = clean(m.group(1).replace("<br", " <br")) if m else ""
    og = re.search(r'<meta property="og:title" content="([^"]*)"', page)
    og_title = clean(og.group(1)) if og else ""
    og_title = re.sub(r"\s*\|\s*Divyajot Singh\s*$", "", og_title)
    og_title = re.sub(r"^Divyajot Singh on LinkedIn:\s*", "", og_title)
    return body, og_title


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True, help="LinkedIn post URL (any shape, lnkd.in ok)")
    ap.add_argument("--title", default="", help="Optional one-line summary; overrides fetched text")
    ap.add_argument("--force", action="store_true", help="Replace the entry if the post is already listed")
    ap.add_argument("--dry-run", action="store_true", help="Print the entry, don't write data.json")
    args = ap.parse_args()

    url = resolve_short(args.url.strip())
    post_id = extract_id(url)
    if not post_id:
        print(f"! could not find an activity id in: {url}", file=sys.stderr)
        sys.exit(1)

    canonical = f"https://www.linkedin.com/feed/update/urn:li:activity:{post_id}/"
    date_iso = id_to_iso(post_id)

    title = args.title.strip()
    if not title:
        _, page = fetch(canonical)
        body, og_title = extract_text(page)
        title = summarise(body) or clip(og_title) or ""
    if not title:
        title = f"New post on LinkedIn ({date_iso[:10]})"
        print("  ! could not read the post text; using a placeholder title", file=sys.stderr)

    entry = {"title": title, "url": canonical, "date": date_iso}
    print(json.dumps(entry, indent=2, ensure_ascii=False))
    if args.dry_run:
        return

    data = load_data()
    feeds = data.setdefault("feeds", {})
    posts = feeds.get("linkedin_posts") or []

    def pid(item):
        return extract_id(item.get("url", "")) or item.get("url", "")

    existing = [p for p in posts if pid(p) == post_id]
    if existing and not args.force:
        print("= already listed; nothing to do (use --force to replace)")
        sys.exit(3)

    posts = [p for p in posts if pid(p) != post_id]
    posts.append(entry)
    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    feeds["linkedin_posts"] = posts[:CAP]
    data.setdefault("_meta", {})["last_updated"] = datetime.now(timezone.utc).isoformat()
    save_data(data)
    print(f"+ added to data.json ({len(feeds['linkedin_posts'])} LinkedIn posts listed)")


if __name__ == "__main__":
    main()
