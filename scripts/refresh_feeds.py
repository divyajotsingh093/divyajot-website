#!/usr/bin/env python3
"""
refresh_feeds.py
Pulls latest activity from GitHub, Substack, LinkedIn (via RSS.app), and X (via RSS.app).
Writes the result into data.json. Run by GitHub Actions on a weekly schedule.

Reads config from environment variables:
  GITHUB_USERNAME       e.g. "divyajot"
  SUBSTACK_URL          e.g. "https://divyajot.substack.com"
  LINKEDIN_RSS_URL      RSS.app feed URL for your LinkedIn activity (set up at rss.app)
  X_RSS_URL             RSS.app feed URL for your X posts

Optional:
  GITHUB_LIMIT          default 5
  SUBSTACK_LIMIT        default 3
  LINKEDIN_LIMIT        default 3
  X_LIMIT               default 5

The script never invents content. If a feed is empty, unreachable, or misconfigured,
that feed's array stays empty and a warning is printed. The rest of the data file
is preserved (social URLs, pinned work).
"""

import os
import json
import sys
import time
from datetime import datetime, timezone
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data.json")


def fetch(url, headers=None, timeout=20):
    """Fetch a URL, return bytes. Returns None on failure (logged)."""
    req = Request(url, headers=headers or {"User-Agent": "divyajot-site-refresh/1.0"})
    try:
        with urlopen(req, timeout=timeout) as r:
            return r.read()
    except (URLError, HTTPError, TimeoutError) as e:
        print(f"  ! fetch failed for {url}: {e}", file=sys.stderr)
        return None


def parse_rss(xml_bytes, limit):
    """Parse an RSS/Atom feed, return list of {title, url, date, summary}."""
    if not xml_bytes:
        return []
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        print(f"  ! XML parse error: {e}", file=sys.stderr)
        return []

    items = []
    # Try RSS 2.0
    for item in root.iter("item"):
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "url": (item.findtext("link") or "").strip(),
            "date": (item.findtext("pubDate") or "").strip(),
            "summary": clean_html((item.findtext("description") or "").strip()),
        })
    # Atom fallback
    if not items:
        ns = {"a": "http://www.w3.org/2005/Atom"}
        for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
            link_el = entry.find("a:link", ns)
            href = link_el.get("href") if link_el is not None else ""
            items.append({
                "title": (entry.findtext("a:title", default="", namespaces=ns) or "").strip(),
                "url": href,
                "date": (entry.findtext("a:published", default="", namespaces=ns)
                         or entry.findtext("a:updated", default="", namespaces=ns) or "").strip(),
                "summary": clean_html(entry.findtext("a:summary", default="", namespaces=ns) or ""),
            })

    return [i for i in items if i["title"]][:limit]


def clean_html(s, max_len=200):
    """Strip tags and truncate. For RSS summaries which often contain HTML."""
    import re
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > max_len:
        s = s[:max_len].rsplit(" ", 1)[0] + "..."
    return s


def pull_github(username, limit):
    """GitHub events API. Public commits, PRs, issues from public repos."""
    if not username:
        return []
    url = f"https://api.github.com/users/{username}/events/public"
    raw = fetch(url, headers={
        "User-Agent": "divyajot-site-refresh/1.0",
        "Accept": "application/vnd.github+json",
    })
    if not raw:
        return []
    try:
        events = json.loads(raw)
    except json.JSONDecodeError:
        return []

    out = []
    for ev in events:
        if len(out) >= limit:
            break
        et = ev.get("type")
        repo = (ev.get("repo") or {}).get("name", "")
        created = ev.get("created_at", "")
        if et == "PushEvent":
            commits = (ev.get("payload") or {}).get("commits", [])
            for c in commits[:2]:
                if len(out) >= limit:
                    break
                msg = (c.get("message") or "").split("\n")[0]
                sha = c.get("sha", "")[:7]
                out.append({
                    "type": "commit",
                    "repo": repo,
                    "title": msg,
                    "url": f"https://github.com/{repo}/commit/{c.get('sha', '')}" if repo else "",
                    "date": created,
                    "sha": sha,
                })
        elif et == "PullRequestEvent":
            pr = (ev.get("payload") or {}).get("pull_request") or {}
            action = (ev.get("payload") or {}).get("action", "")
            out.append({
                "type": "pr",
                "repo": repo,
                "title": f"PR {action}: {pr.get('title', '')}",
                "url": pr.get("html_url", ""),
                "date": created,
            })
        elif et == "CreateEvent":
            ref_type = (ev.get("payload") or {}).get("ref_type", "")
            if ref_type == "repository":
                out.append({
                    "type": "repo_created",
                    "repo": repo,
                    "title": f"Created {repo}",
                    "url": f"https://github.com/{repo}",
                    "date": created,
                })
        elif et == "ReleaseEvent":
            rel = (ev.get("payload") or {}).get("release") or {}
            out.append({
                "type": "release",
                "repo": repo,
                "title": f"Released {rel.get('tag_name', '')}",
                "url": rel.get("html_url", ""),
                "date": created,
            })
    return out


def pull_substack(base_url, limit):
    """Substack publishes /feed for every blog."""
    if not base_url:
        return []
    base_url = base_url.rstrip("/")
    raw = fetch(f"{base_url}/feed")
    return parse_rss(raw, limit)


def pull_rss(url, limit):
    """Generic RSS pull (used for RSS.app feeds for LinkedIn and X)."""
    if not url:
        return []
    raw = fetch(url)
    return parse_rss(raw, limit)


def main():
    print(f"[refresh] starting at {datetime.now(timezone.utc).isoformat()}")

    if not os.path.exists(DATA_PATH):
        print(f"  ! data.json not found at {DATA_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    gh_user = os.environ.get("GITHUB_USERNAME", "").strip()
    substack = os.environ.get("SUBSTACK_URL", "").strip()
    li_rss = os.environ.get("LINKEDIN_RSS_URL", "").strip()
    x_rss = os.environ.get("X_RSS_URL", "").strip()

    gh_limit = int(os.environ.get("GITHUB_LIMIT", "5"))
    su_limit = int(os.environ.get("SUBSTACK_LIMIT", "3"))
    li_limit = int(os.environ.get("LINKEDIN_LIMIT", "3"))
    x_limit = int(os.environ.get("X_LIMIT", "5"))

    print(f"  github user: {gh_user or '(unset)'}")
    print(f"  substack:    {substack or '(unset)'}")
    print(f"  linkedin:    {'(rss configured)' if li_rss else '(unset)'}")
    print(f"  x/twitter:   {'(rss configured)' if x_rss else '(unset)'}")

    gh = pull_github(gh_user, gh_limit) if gh_user else []
    su = pull_substack(substack, su_limit) if substack else []
    li = pull_rss(li_rss, li_limit) if li_rss else []
    xs = pull_rss(x_rss, x_limit) if x_rss else []

    print(f"  pulled: gh={len(gh)} substack={len(su)} linkedin={len(li)} x={len(xs)}")

    data["feeds"]["github_commits"] = gh
    data["feeds"]["substack_posts"] = su
    data["feeds"]["linkedin_posts"] = li
    data["feeds"]["x_posts"] = xs
    data["_meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[refresh] wrote {DATA_PATH}")


if __name__ == "__main__":
    main()
