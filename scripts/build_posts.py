#!/usr/bin/env python3
"""
build_posts.py
Builds the on-site writing system from markdown sources.

Reads:   content/posts/*.md   (excluding *.crossposts.md)
Writes:  writing/<slug>.html   one styled page per post
         writing/index.html    the writing index
         posts.json            index consumed by the home page Writing section

No third-party dependencies — a small, purpose-built markdown converter handles
the subset of markdown used by the posts (headings, bold, italic, inline code,
links, ordered/unordered lists, blockquotes, rules, and [[diagram:n]] refs).
"""

import os
import re
import json
import html
import glob
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(ROOT, "content", "posts")
OUT_DIR = os.path.join(ROOT, "writing")
POSTS_JSON = os.path.join(ROOT, "posts.json")


# ----------------------------- frontmatter -----------------------------

def parse_front_matter(text):
    """Return (meta dict, body str). Frontmatter is a leading --- ... --- block."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    meta = {}
    for line in raw.splitlines():
        if not line.strip() or ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip()
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip() for v in val[1:-1].split(",") if v.strip()]
            meta[key] = items
        else:
            meta[key] = val
    return meta, body


# ----------------------------- inline markdown -----------------------------

def render_inline(text):
    """Escape HTML then apply inline markdown: code, links, bold, italic."""
    text = html.escape(text, quote=False)
    # inline code first so its contents aren't touched by other rules
    code_spans = []

    def _stash_code(m):
        code_spans.append(m.group(1))
        return f"\x00{len(code_spans) - 1}\x00"

    text = re.sub(r"`([^`]+)`", _stash_code, text)
    # links [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)\s]+)\)",
                  r'<a href="\2" target="_blank" rel="noopener">\1</a>', text)
    # bold then italic
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # restore code
    text = re.sub(r"\x00(\d+)\x00",
                  lambda m: f"<code>{html.escape(code_spans[int(m.group(1))], quote=False)}</code>",
                  text)
    return text


# ----------------------------- block markdown -----------------------------

def render_markdown(body, diagrams):
    """Convert a markdown body into HTML. `diagrams` maps index->svg filename."""
    blocks = re.split(r"\n\s*\n", body.strip())
    out = []
    for block in blocks:
        block = block.strip("\n")
        if not block.strip():
            continue

        # diagram placeholder, e.g. [[diagram:1]]
        m = re.fullmatch(r"\[\[diagram:(\d+)\]\]", block.strip())
        if m:
            idx = int(m.group(1))
            svg = diagrams.get(idx)
            if svg:
                out.append(
                    f'<figure><img src="assets/{html.escape(svg)}" alt="Diagram {idx}" loading="lazy"></figure>'
                )
            continue

        if block.startswith("### "):
            out.append(f"<h3>{render_inline(block[4:].strip())}</h3>")
            continue
        if block.startswith("## "):
            out.append(f"<h2>{render_inline(block[3:].strip())}</h2>")
            continue
        if re.fullmatch(r"-{3,}", block.strip()):
            out.append("<hr>")
            continue

        lines = block.split("\n")

        # ordered list
        if all(re.match(r"\d+\.\s+", ln) for ln in lines):
            stripped = [re.sub(r"^\d+\.\s+", "", ln) for ln in lines]
            items = "".join("<li>" + render_inline(s) + "</li>" for s in stripped)
            out.append(f"<ol>{items}</ol>")
            continue
        # unordered list
        if all(re.match(r"[-*]\s+", ln) for ln in lines):
            stripped = [re.sub(r"^[-*]\s+", "", ln) for ln in lines]
            items = "".join("<li>" + render_inline(s) + "</li>" for s in stripped)
            out.append(f"<ul>{items}</ul>")
            continue
        # blockquote
        if all(ln.startswith(">") for ln in lines):
            inner = " ".join(ln.lstrip("> ").rstrip() for ln in lines)
            out.append(f"<blockquote>{render_inline(inner)}</blockquote>")
            continue

        # paragraph
        out.append(f"<p>{render_inline(' '.join(ln.strip() for ln in lines))}</p>")
    return "\n".join(out)


# ----------------------------- page templates -----------------------------

def post_page(meta, content_html):
    title = html.escape(meta.get("title", "Untitled"))
    subtitle = html.escape(meta.get("subtitle", ""))
    date_disp = format_date(meta.get("date", ""))
    ptype = html.escape(meta.get("type", "essay")).upper()
    tags = meta.get("tags", [])
    tags_html = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in tags)
    canonical = meta.get("canonical", "")
    canonical_html = (
        f'<a class="canonical" href="{html.escape(canonical)}" target="_blank" rel="noopener">Originally on Substack ↗</a>'
        if canonical else ""
    )
    desc = subtitle or title
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<title>{title} — Divyajot Singh</title>
<meta name="description" content="{desc}" />
<meta property="og:title" content="{title}" />
<meta property="og:description" content="{desc}" />
<meta property="og:type" content="article" />
{f'<link rel="canonical" href="{html.escape(canonical)}" />' if canonical else ''}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/post.css" />
</head>
<body>
<header class="topbar">
  <a class="brand" href="/">divyajot<b>.</b>singh</a>
  <nav>
    <a href="/writing">Writing</a>
    <a href="/#work">Work</a>
    <a href="/#contact">Contact</a>
  </nav>
</header>

<article class="article">
  <div class="eyebrow"><span class="type">{ptype}</span> · {date_disp}</div>
  <h1>{title}</h1>
  <p class="subtitle">{subtitle}</p>
  <div class="byline">
    <div class="tags">{tags_html}</div>
    {canonical_html}
  </div>
  <div class="content">
{content_html}
  </div>
</article>

<footer>
  <div>Divyajot Singh · Singapore · 2026</div>
  <div><a href="/writing">← All writing</a></div>
</footer>
</body>
</html>
"""


def index_page(posts):
    rows = ""
    for p in posts:
        rows += f"""
    <div class="post-row">
      <div class="date">{format_date(p['date'])}</div>
      <div>
        <div class="type">{html.escape(p['type'])}</div>
        <h2><a href="{html.escape(p['url'])}">{html.escape(p['title'])}</a></h2>
        <div class="summary">{html.escape(p.get('subtitle',''))}</div>
      </div>
      <div class="type" style="text-align:right">→</div>
    </div>"""
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<title>Writing — Divyajot Singh</title>
<meta name="description" content="Essays and whitepapers on applied AI, agentic systems, and enterprise coordination." />
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Geist:wght@300;400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/post.css" />
</head>
<body>
<header class="topbar">
  <a class="brand" href="/">divyajot<b>.</b>singh</a>
  <nav>
    <a href="/#work">Work</a>
    <a href="/#contact">Contact</a>
  </nav>
</header>

<div class="index-head">
  <div class="num">04 / Writing</div>
  <h1>Notes from the <em style="font-style:italic;color:var(--coral-soft)">field</em>.</h1>
</div>
<div class="post-list">{rows}
</div>

<footer>
  <div>Divyajot Singh · Singapore · 2026</div>
  <div><a href="/">← Home</a></div>
</footer>
</body>
</html>
"""


def format_date(value):
    """Accept ISO date/datetime, return e.g. 'Jun 2026'."""
    if not value:
        return ""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).strftime("%b %Y")
        except ValueError:
            continue
    return value


# ----------------------------- main -----------------------------

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sources = sorted(
        p for p in glob.glob(os.path.join(POSTS_DIR, "*.md"))
        if not p.endswith(".crossposts.md")
    )

    posts = []
    for path in sources:
        slug = os.path.splitext(os.path.basename(path))[0]
        with open(path, "r", encoding="utf-8") as f:
            meta, body = parse_front_matter(f.read())
        diagrams = {i + 1: name for i, name in enumerate(meta.get("diagrams", []))}
        content_html = render_markdown(body, diagrams)

        with open(os.path.join(OUT_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
            f.write(post_page(meta, content_html))

        posts.append({
            "slug": slug,
            "title": meta.get("title", slug),
            "subtitle": meta.get("subtitle", ""),
            "date": meta.get("date", ""),
            "type": meta.get("type", "essay"),
            "tags": meta.get("tags", []),
            "url": f"/writing/{slug}",
            "canonical": meta.get("canonical", ""),
        })
        print(f"  built writing/{slug}.html")

    posts.sort(key=lambda p: p["date"], reverse=True)

    with open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_page(posts))
    print("  built writing/index.html")

    with open(POSTS_JSON, "w", encoding="utf-8") as f:
        json.dump(
            {"_meta": {"generated": datetime.now(timezone.utc).isoformat()}, "posts": posts},
            f, indent=2, ensure_ascii=False,
        )
    print(f"  wrote posts.json ({len(posts)} post{'s' if len(posts) != 1 else ''})")


if __name__ == "__main__":
    main()
