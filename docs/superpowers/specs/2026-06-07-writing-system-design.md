# Writing System + Reliable Feed Auto-Update — Design

**Date:** 2026-06-07
**Status:** Approved

## Goal

1. Give the site a first-class home for long-form thought leadership (essays, whitepapers) that DJ writes — hosted on-site, SEO-friendly, easy to add to.
2. Make the activity feeds (GitHub, Substack, LinkedIn, X) keep updating reliably.

## Part 1 — On-site writing system (static, markdown-sourced)

Matches the repo's existing "Python script generates a committed artifact" pattern (like `refresh_feeds.py` → `data.json`).

### Components

- **`content/posts/<slug>.md`** — source of truth per post. YAML-style frontmatter + markdown body.
  - Frontmatter: `title`, `subtitle`, `date` (ISO), `type` (`essay` | `whitepaper`), `tags` (list), `canonical` (optional external URL), `diagrams` (optional list of svg filenames in order they appear via `[[diagram:n]]` placeholders).
- **`content/posts/<slug>.crossposts.md`** — optional companion holding LinkedIn / X adaptations for manual cross-posting. Not published as a page.
- **`scripts/build_posts.py`** — reads every `content/posts/*.md` (excluding `*.crossposts.md`), renders each to a site-styled standalone page at **`writing/<slug>.html`**, builds a **`writing/index.html`** listing page, and writes **`posts.json`** (the index consumed by the home page).
  - Self-contained markdown converter (no pip dependency) covering: headings, bold, italic, inline code, links, ordered/unordered lists, blockquotes, horizontal rules, images, and `[[diagram:n]]` → inline `<img>` of the matching SVG.
- **`writing/assets/post.css`** — article reading styles, reusing the site's color tokens and fonts.
- **`writing/assets/*.svg`** — diagrams.
- **Home page Writing section** ([index.html](../../../index.html)) — replaces the 3 dead-`href="#"` placeholders with entries rendered from `posts.json`, linking to on-site `/writing/<slug>` pages. Posts without an on-site page (pure external) may still be listed with their external URL.
- **`.github/workflows/build-posts.yml`** — on push touching `content/**` or `scripts/build_posts.py`, rebuild and commit `writing/` + `posts.json`.

### Data flow

`content/posts/*.md` → `build_posts.py` → `writing/<slug>.html` + `writing/index.html` + `posts.json` → committed → Vercel serves static → home page Writing section fetches `posts.json`.

### URLs

Clean URLs via existing `vercel.json` `cleanUrls: true`: `/writing/system-of-action` serves `writing/system-of-action.html`. `/writing` serves `writing/index.html`.

## Part 2 — Feed auto-update hardening

- **GitHub** — already working via `refresh_feeds.py` cron.
- **Substack** — Cloudflare blocks GitHub Actions runner IPs (confirmed: pull returns 0 from CI, 200 locally). Add a reader-proxy fallback: if the direct feed fetch fails or yields nothing, retry through a public reader proxy. Combined with the existing preserve-on-empty logic, Substack updates from CI without wiping on failure.
- **X / LinkedIn** — no native feed. The `SITE_X_RSS_URL` / `SITE_LINKEDIN_RSS_URL` workflow variables are already wired; they become live the moment DJ creates RSS.app feeds. Until then: X empty (account has 0 posts), LinkedIn hand-curated in `data.json` (preserved across refreshes).
- **Cadence** — keep weekly (Sunday 00:00 SGT).

## First post

`content/posts/system-of-action.md` — "The System of Action: Why 'Close the Books' Is Harder Than Any Model" (long-form essay). `canonical` → the Substack original. Two generated SVG diagrams: the coordination funnel (business verbs → real systems) and the blocked-close demo flow. LinkedIn + X thread variants saved in `system-of-action.crossposts.md`.

## Out of scope (YAGNI)

- Tag/type filtering UI on the writing index.
- Rendering cross-post variants as on-site pages.
- A CMS or admin UI — publishing is `git commit` of a markdown file.
