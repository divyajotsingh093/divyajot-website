#!/usr/bin/env python3
"""
generate_draft.py
Generates one draft post candidate per week based on recent real activity.
The output is a markdown file in drafts/ — it is NEVER auto-published.

You review, edit, and either copy into a Substack/LinkedIn post or discard.

Inputs:
  ANTHROPIC_API_KEY     required, GitHub secret
  data.json             the recent activity feeds populated by refresh_feeds.py

Output:
  drafts/YYYY-MM-DD-draft.md     markdown file you can iterate on

The prompt is intentionally narrow: the model is asked to draft a short
"pattern observation" or "field note" anchored to what actually happened
in your recent commits and posts. It is not asked to invent thought
leadership from nothing.
"""

import os
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data.json")
DRAFTS_DIR = os.path.join(ROOT, "drafts")

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-opus-4-7"  # via env override if needed


def call_anthropic(api_key, prompt, model=None):
    body = json.dumps({
        "model": model or MODEL,
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            # Concatenate any text blocks the model returned
            parts = []
            for block in data.get("content", []):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
            return "\n".join(parts).strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"  ! Anthropic API HTTP {e.code}: {body}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"  ! Anthropic API URL error: {e}", file=sys.stderr)
        return None


def summarise_activity(data):
    """Build a compact text summary of recent activity for the prompt."""
    lines = []
    feeds = data.get("feeds", {})

    gh = feeds.get("github_commits", [])
    if gh:
        lines.append("Recent GitHub activity:")
        for c in gh[:6]:
            repo = c.get("repo", "")
            title = c.get("title", "")
            lines.append(f"  - [{c.get('type', 'commit')}] {repo}: {title}")
        lines.append("")

    su = feeds.get("substack_posts", [])
    if su:
        lines.append("Recent Substack posts:")
        for p in su[:3]:
            lines.append(f"  - {p.get('title', '')}")
            if p.get("summary"):
                lines.append(f"    summary: {p['summary'][:160]}")
        lines.append("")

    li = feeds.get("linkedin_posts", [])
    if li:
        lines.append("Recent LinkedIn posts:")
        for p in li[:3]:
            lines.append(f"  - {p.get('title', '')[:200]}")
        lines.append("")

    xs = feeds.get("x_posts", [])
    if xs:
        lines.append("Recent X posts:")
        for p in xs[:5]:
            lines.append(f"  - {p.get('title', '')[:200]}")
        lines.append("")

    return "\n".join(lines).strip()


PROMPT_TEMPLATE = """You are helping Divyajot Singh draft a candidate post for his personal Substack/LinkedIn. He will edit it heavily before publishing. The goal is NOT to invent thought leadership — it is to give him a starting point grounded in what he actually did this week.

DIVYAJOT'S CONTEXT:
- Head of Product, AI Platform at Neutrinos (Singapore) — selling AI into tier-one insurers across APAC + MEA (Sun Life, Manulife, Prudential, Generali, Al Rajhi Takaful)
- Founder of Vortic (getvortic.com) — AI-native underwriting platform for MGAs/Lloyd's syndicates, in pilot
- Writes about: agentic systems, harness engineering, RLVR (Reinforcement Learning with Verifiable Rewards), eval-driven dev, applied LLM patterns in regulated industries
- His voice: direct, technical, no hype, no em-dashes, no "leveraging", no three-part lists, no "I am passionate about", contractions only where natural

THIS WEEK'S RAW ACTIVITY:
{activity}

YOUR TASK:
Draft ONE short post (300-450 words) for him to consider. Pick ONE specific thread from the activity above and turn it into a "field note" style post: an observation, a pattern, or a small lesson from real work. Concrete over abstract. Numbers and specifics over generalities.

REQUIREMENTS:
- Anchor the post to something specifically visible in the activity above. Do NOT invent facts.
- If activity is sparse or generic, draft a more reflective post on a pattern he has been working on (agentic systems, RLVR, IDP, harness engineering) but mark clearly where he needs to fill in specifics.
- Voice: direct, declarative, technical. No em-dashes. No "leveraging" or "passionate about". No "in this post I will discuss".
- Length: 300-450 words. Tight.
- Format: just the post body, no front-matter, no meta-commentary, no instructions to him.
- Title: include a working title on the first line as `# Title here`
- End with one short line tagged `<!-- needs your edit: ... -->` flagging the one thing you are least confident about, so he can verify or replace before publishing.

If the activity feed is empty or unusable, write a short note inside an HTML comment at the top explaining why, then produce a generic prompt-starter on one of his recurring topics that he can build from."""


def main():
    print(f"[draft] starting at {datetime.now(timezone.utc).isoformat()}")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("  ! ANTHROPIC_API_KEY not set, skipping draft generation.", file=sys.stderr)
        sys.exit(0)  # Exit cleanly so the workflow doesn't fail loudly

    if not os.path.exists(DATA_PATH):
        print(f"  ! data.json not found at {DATA_PATH}", file=sys.stderr)
        sys.exit(0)

    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    activity = summarise_activity(data)
    if not activity:
        activity = "(no recent activity found in feeds)"

    prompt = PROMPT_TEMPLATE.format(activity=activity)
    print(f"  prompt length: {len(prompt)} chars")

    model_override = os.environ.get("ANTHROPIC_MODEL", "").strip() or None
    text = call_anthropic(api_key, prompt, model=model_override)

    if not text:
        print("  ! No draft returned, skipping.", file=sys.stderr)
        sys.exit(0)

    os.makedirs(DRAFTS_DIR, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filename = f"{date_str}-draft.md"
    out_path = os.path.join(DRAFTS_DIR, filename)

    header = (
        f"<!-- DRAFT generated {datetime.now(timezone.utc).isoformat()} -->\n"
        f"<!-- This is NOT published. Review, edit, and decide what to do with it. -->\n\n"
    )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header + text + "\n")

    print(f"[draft] wrote {out_path}")


if __name__ == "__main__":
    main()
