# Divyajot Singh

Static site with weekly auto-refreshed activity feeds + LLM-generated draft posts. Built for Vercel + GitHub Actions.

## What this is

- **`index.html`** — the one-page site. Reads `data.json` on load to populate the "Latest activity" section.
- **`data.json`** — dynamic content (social URLs + feed arrays). Auto-regenerated weekly by GitHub Actions. You can also edit it manually.
- **`scripts/refresh_feeds.py`** — pulls GitHub events, Substack RSS, LinkedIn RSS (via RSS.app), and X RSS (via RSS.app).
- **`scripts/generate_draft.py`** — generates one draft post per week using Anthropic API. Writes to `drafts/`. NEVER auto-publishes.
- **`.github/workflows/refresh-feed.yml`** — runs `refresh_feeds.py` weekly (Sun 00:00 SGT).
- **`.github/workflows/draft-post.yml`** — runs `generate_draft.py` weekly (Sun 00:30 SGT, 30 min after the feed refresh).

## Deploy in 3 steps

### 1. Push to GitHub

Create a public or private GitHub repo, push these files. Vercel works fine with private repos.

```bash
cd path/to/site
git init
git add .
git commit -m "initial commit"
git branch -M main
git remote add origin git@github.com:YOUR-USERNAME/divyajot-site.git
git push -u origin main
```

### 2. Connect to Vercel

Go to https://vercel.com/new, click "Import Git Repository", pick the repo, accept defaults, deploy. You will get a `*.vercel.app` URL in ~30 seconds.

Add a custom domain later: Vercel dashboard → your project → Settings → Domains.

### 3. Wire up the automation

Two things to configure inside your GitHub repo so the scheduled workflows actually do something.

#### Repository Variables (Settings → Secrets and variables → Actions → Variables tab)

Add these as **Variables**, not secrets. They are not sensitive.

| Variable | Example | What it is |
|---|---|---|
| `SITE_GITHUB_USERNAME` | `divyajot` | Your GitHub username (for the public events feed) |
| `SITE_SUBSTACK_URL` | `https://divyajot.substack.com` | Your Substack base URL |
| `SITE_LINKEDIN_RSS_URL` | `https://rss.app/feeds/abc123.xml` | RSS.app feed URL for your LinkedIn activity. See setup below. |
| `SITE_X_RSS_URL` | `https://rss.app/feeds/xyz456.xml` | RSS.app feed URL for your X posts. See setup below. |
| `ANTHROPIC_MODEL` *(optional)* | `claude-opus-4-7` | Override the default model used for drafts. |

If you leave any of these blank, that feed will just be empty in the rendered Latest section. The site still works.

#### Repository Secrets (Settings → Secrets and variables → Actions → Secrets tab)

| Secret | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | https://console.anthropic.com → Settings → API Keys |

This one IS sensitive. Use Secrets, not Variables.

#### Setting up RSS.app feeds for LinkedIn and X

LinkedIn and X don't expose RSS natively. RSS.app converts both into clean feeds.

1. Go to https://rss.app/new-rss-feed
2. Paste your LinkedIn profile URL (e.g. `https://www.linkedin.com/in/divyajot-singh-06b78559/`)
3. Click "Generate Feed"
4. Copy the RSS URL it gives you (ends in `.xml` or `.rss`)
5. Paste it into the `SITE_LINKEDIN_RSS_URL` variable in GitHub

Repeat for X (paste your X profile URL).

Free tier is 5 active feeds and refreshes hourly, which is more than enough. If you hit limits, the $9.99/month "Pro" tier is overkill but available.

Alternative for X: if RSS.app gives you trouble with X, you can also try Nitter instances (`nitter.net/yourusername/rss`) but they are flaky. RSS.app is more reliable.

### 4. Test the workflows

Once everything is configured, trigger each workflow manually to make sure they work:

1. Go to repo → Actions tab
2. Click "Refresh feeds" → "Run workflow" button on the right
3. Wait ~30 seconds, check the run log
4. If successful, you should see a new commit on `main` updating `data.json`
5. Repeat for "Draft post"
6. If successful, you should see a new file in `drafts/`

If anything fails, the run log shows exactly what went wrong (missing variable, RSS feed unreachable, API key issue, etc).

## Schedule

Both workflows run weekly on **Sunday 00:00 Singapore time (Saturday 16:00 UTC)**:
- 00:00 SGT — feed refresh
- 00:30 SGT — draft generation

To change the cadence, edit the `cron:` line in either workflow file. Cron syntax reference: https://crontab.guru

Examples:
- Every Monday and Friday at 9am SGT: `0 1 * * 1,5`
- Every weekday at 9am SGT: `0 1 * * 1-5`
- Twice a week (Sun + Wed): `0 16 * * 6,2`

## How the drafts work

Every Sunday, `generate_draft.py` looks at what's in `data.json` (your recent GitHub commits, Substack posts, LinkedIn activity, X posts) and asks Claude to draft ONE 300-450 word post anchored to that real activity.

The draft is written to `drafts/YYYY-MM-DD-draft.md` and committed to the repo.

**It is NOT published anywhere.** Drafts are for you to:
1. Open, read, and decide if there's a usable seed
2. Edit heavily into your own voice
3. Copy into Substack or LinkedIn (or discard)

The prompt explicitly tells the model NOT to invent thought leadership — only to surface a pattern from your actual work. If your activity feed is empty in a given week, the draft will be a generic prompt-starter you can build from.

To disable drafts entirely, just disable the workflow (Actions tab → Draft post → ⋯ → Disable workflow). The feed refresh still works.

## What to customize before going live

### Social URLs

Edit `data.json` directly. Update the `social` block:

```json
"social": {
  "x": "https://x.com/your-real-handle",
  "github": "https://github.com/your-real-username",
  "linkedin": "https://linkedin.com/in/your-real-profile",
  "substack": "https://your-real-substack.substack.com"
}
```

The site reads these at page load and updates the social link hrefs. The placeholders in `index.html` are fallbacks if `data.json` fails to load.

### Pinned work

The `pinned_work` array in `data.json` is preserved across feed refreshes. Use it to highlight 2-3 specific posts that you always want on the site, regardless of recency. (Not currently rendered in the UI — reserved for a future enhancement.)

### Static content in index.html

Everything else (hero, stats, work cards, repos, writing list, skills, contact) is hardcoded HTML in `index.html`. Edit directly when something changes.

## Cost

- **Vercel**: free (Hobby plan is fine for this)
- **GitHub Actions**: free (well under the 2,000 minutes/month limit for public repos)
- **RSS.app**: free (5-feed tier covers LinkedIn + X)
- **Anthropic API**: ~$0.10-0.50/month at weekly cadence

Total: under $1/month.

## File structure

```
.
├── index.html                          # the site
├── data.json                           # dynamic content (auto-updated)
├── vercel.json                         # Vercel config
├── README.md                           # this file
├── drafts/                             # LLM-generated drafts (review before publishing)
│   └── .gitkeep
├── scripts/
│   ├── refresh_feeds.py                # pulls GH + Substack + LinkedIn + X
│   └── generate_draft.py               # generates a weekly draft
└── .github/
    └── workflows/
        ├── refresh-feed.yml            # cron: weekly feed refresh
        └── draft-post.yml              # cron: weekly draft generation
```

## Local preview

```bash
# Python (easiest)
python3 -m http.server 8000

# Or Node
npx serve .
```

Open http://localhost:8000

## Troubleshooting

**Latest section is empty after the workflow runs.** Check the workflow logs in Actions tab. Most common causes: a variable is unset, an RSS.app feed URL is wrong, or your GitHub username has no public events (mostly private repo work). The script logs which feeds were pulled and how many items.

**No drafts being generated.** Check `ANTHROPIC_API_KEY` is set as a *Secret* (not Variable). Check the Draft post workflow logs. The script exits cleanly if the key is missing rather than failing loudly, so look for `ANTHROPIC_API_KEY not set` in the logs.

**Workflow doesn't trigger on schedule.** GitHub schedules can be delayed by up to ~30 minutes during high-traffic periods. They also pause if your repo has had no activity for 60 days. Push any commit to wake them back up.

**I want to disable everything and just have a static site.** Delete the `.github/workflows/` folder. The site keeps working as a pure static site. The Latest section will show whatever was last in `data.json` (or hide itself if `data.json` is removed).
