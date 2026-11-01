# daily-spark: architecture (v1)

A small daily loop for product builders: **Digest -> Think -> Build -> Recap**.
Inspired by [Morning Spark](https://github.com/tisu19021997/myThreads). Built for one person first, designed so anyone can copy it and fill in their own settings.

Status: agreed 2026-10-31. Nothing personal ever lives in this repo.

---

## 1. Requirements

- Loop every day: Digest -> Think -> Build -> Recap
- Under 5 minutes to start
- Actively pulls from the sources the user chooses
- Actively provokes thinking, and pushes the user to do something
- Personalized, but always fresh
- Works on any device (phone, laptop) as a web page; notifications only carry the link

## 2. The big picture

```
                    +-----------------------------------+
  06:12 local       |  WORKER (Claude scheduled task)   |
  ----------------> |  1. sync repos                    |
                    |  2. FETCH new items from sources  |
                    |  3. read user context             |
                    |  4. web search (Frontier only)    |
                    |  5. rank, write today's edition   |
                    |  6. build + save + publish        |
                    |  7. notify (push + email)         |
                    +--------+-----------------+--------+
                             |                 |
          +------------------v----+   +--------v------------------------+
          | daily-spark (PUBLIC)  |   | user's private repo             |
          | framework + runbook   |   | (for Ella: ella-second-brain/   |
          | public-safe editions  |   |  daily-spark/)                  |
          | GitHub Pages site     |   | profile, sources, settings,     |
          | Chrome new-tab ext.   |   | full editions, recaps, weekly,  |
          +-----------+-----------+   | knowledge base                  |
                      |               +---------------------------------+
                      | read by
        +-------------v-------------+        +----------------------------+
        | Web page / Chrome new tab | -----> | Supabase (write key only)  |
        | recap box, feedback, notes|        | recaps, feedback, picks,   |
        +---------------------------+        | notes                      |
                                             +-------------+--------------+
                                                           | read next morning (read key)
                                                           v
                                                         WORKER
```

## 3. Components

### 3.1 Config (private, per user)
Lives in the user's **private** repo. This repo ships only examples in `config/`.

| File | What it holds |
|---|---|
| `profile.yaml` | who I am, role, goals, interests, current focus, email, Supabase read key |
| `blocklist.txt` | company, product and client names that must never reach the public site (checked by `spark.py publish --blocklist`) |

Public settings live in this repo: `config/site.json` (owner, site_url, languages, Supabase URL and public key) and `config/sources.yaml`.

### 3.2 Fetch layer (`scripts/fetch.py`)
- Reads `sources.yaml`, pulls new items from RSS/Atom feeds (Substack, blogs, YouTube channel feeds, podcast feeds).
- Adaptive frequency (idea from NewsNow): busy sources every run, quiet ones less often.
- De-duplicates against the ledger of everything already sent.
- Output: `candidates.json` (~30 to 80 items with title, source, url, date, summary).
- Web search is used only for the **Frontier** section (big product/AI news).

### 3.3 Context layer (what the Worker knows about the user)
- `profile.yaml`
- Interest notes (for Ella: `ella@llm_wiki` only; personal notes are never read)
- The last 7 days of recaps (from Supabase)
- Thumbs up/down stats per source and topic (idea from NewsBlur)
- Personalize by similarity to the user's own library (idea from zotero-arxiv-daily)

### 3.4 Worker (Claude scheduled task)
- Runbook: `CLAUDE.md` in this repo. The scheduled task prompt only points to it.
- Fresh session each run. Memory = files + Supabase, never the chat.
- Final message = the notification text (push + email) with the link.

### 3.5 Edition format (same structure every day)

| # | Section | Rule | Public page |
|---|---|---|---|
| 1 | Frontier | Big picture + 2 to 4 product/AI stories. Smaller real stories when nothing big happened; never pad. | yes |
| 2 | From people you follow | Always. What followed builders published, plus the insight. | yes |
| 3 | Relevant to your work | Personalized from recaps. | **hidden** (private copy + email only) |
| 4 | Timeless | One lasting principle or strategy. | yes |
| 5 | Think | 2 to 3 questions; the user writes their own answer (writing as thinking). | yes |
| 6 | Exercises | 3 options every day: work, writing, build. User picks one. | yes |

Data: `editions/data/YYYY-MM-DD.json` is the source of truth; HTML, Markdown and `latest.json` are generated from it.

### 3.6 Outputs
- **Public site (GitHub Pages):** `index.html` (archive by date), `editions/YYYY-MM-DD.html`, `latest.json`. Phone-first, works on all devices.
- **Private copy:** full edition as Markdown (with section 3) in the user's private repo.
- **Chrome new tab (`extension/`):** small Chrome extension that shows the latest edition on every new tab, read from `latest.json`. Installed with "Load unpacked" (no store needed).

### 3.7 Interaction (Supabase, free tier)
- Tables: `recaps`, `feedback` (useful / knew / notme / deeper per item), `picks` (exercise picked), `notes` (her question on one item). Setup: `supabase/schema.sql`.
- Row Level Security: the page can only **insert**, and only with the write key (saved once per device in Menu > This device). Nobody can read through the public key.
- The Worker reads through the `ds_recent` function with the read key from `profile.yaml`.
- Without Supabase: reply to the morning email; the Worker reads replies as recaps.

### 3.8 Schedules
| Time (local) | Task |
|---|---|
| 05:40 daily | GitHub Actions fetch robot (`fetch.yml`), no Claude cost |
| 06:12 Monday to Saturday | Morning edition, notify by ~07:00. The email also carries the recap prompt (no separate evening task since 2026-11-01) |
| 07:41 Sunday | Weekly edition (replaces the daily): market overview + "what is really possible now" radar. Runbook: `WEEKLY.md` |

### 3.9 Design (design system v1, approved 2026-11-01)
- Source of truth: the "daily spark" Design System artifact (tokens, principles, logos). Every color, size, space and radius in the site, the new tab and the email comes from it; no one-off values.
- Themes: Light (page Petal `#e8d9ed`, cards Lace `#f7f4ed` and Bridal Blue `#e9f3ff`, accent Sapphire `#426bc2`, text Midnight `#0b1957`) and Dark (page Midnight `#0b1957`, cards `#17286f` and `#1b2f7c`, accent Lavender `#c7a9e3`, text Lace). The reader picks in Menu > Appearance: Auto (follows the device, default), Light, Dark; saved as `ds-theme`. Daily and weekly use the same theme; the weekly is marked by a "Weekly" tag, not by color.
- Type: Instrument Serif for headlines and quotes only; IBM Plex Sans for all text and numbers (lining, tabular). Six sizes 11 / 13 / 15 / 21 / 30 / 44, weights 400 and 600 only.
- Space on a 4px grid (4, 8, 12, 16, 24, 32, 48). Radius: 4 / 12 / 20 / pill. Two shadows (raised, overlay). Stamps have no shadow.
- Card layout: sections have no frame (title on the page); every point is its own stamp (perforated edge). Sections alternate card colors. No component uses the page background color.
- Navigation: two top-level tabs, Sparks (home) and Radar. Phone: bottom tab bar on those two screens only. Web: tabs in the header. Language (EN/VI) lives only in the Menu, never in a header.
- Menu (phone bottom sheet, web popover): Appearance, Reading (swipe / scroll), Language, feedback legend, This device, Other days.
- Dates: `30 Oct 2026` in content, `Sat 31 Oct 2026` in titles.
- Home (Sparks tab): greeting, Today stamp (chips, title, headlines, button), a "This week" row on Mon to Sat, previous sparks as one-line rows. Radar is not on Home.
- Edition page: translucent top bar (back, date, menu), translucent bottom bar with section dots.
- Content depth: Frontier = big picture + 3 to 4 stories (date, original source, type, key points, why it matters) + what to watch; People = 3 items with 4 key points + takeaway; key numbers only for standout items.
- Feedback per item: one row at the bottom of each stamp: Useful, Knew it (raise the bar), Not for me, Go deeper, then Note on the right.
- Chrome new tab (v3, 2026-11-01): the extension is a thin shell that frames `<site>/newtab/`, so design changes ship by pushing the site (no reinstall). Follows the site's Appearance and Language. Top: logo left; Gmail, Images, a Google apps grid and an Account circle on the right. Middle: every news item of the latest edition is an equal-size stamp, arranged in balanced rows (1 row up to 5, 2 rows up to 12, then 3; last row centered); a stamp turns accent once opened. Bottom: date, edition and "read" count left, headline middle, "Open daily spark" (home) and "Read this spark" (that edition) right. Daily: every frontier + people item. Weekly: shifts + mega/hype calls + radar changes. Data: `latest.json` `stamps`.
- Email: `templates/email.html`, light by default, dark colors for mail apps that support dark mode.
- Notes: a Note button after the 4 feedback icons opens a text box per item; saved to Supabase `notes` (private) and read by the next run as the strongest signal.

### 3.10 Weekly edition and radar (added 2026-10-31)
- Sunday only; the weekly replaces that day's daily. Edition number `W01`, `W02`...; `"type": "weekly"` in the JSON and in `editions/index.json`.
- Sections: market overview (big picture + 3 to 5 shifts with sources) · mega trend vs hype · radar changes · week in review (private, stripped like "work") · next week's bet.
- Design: same stamp layout and the reader's theme as the daily; marked by a "Weekly" tag and its W number.
- Home: a weekly shows as the Today card on Sunday; Monday to Saturday a "This week" card sits above Previous sparks; weekly rows carry a "Weekly" tag. A "Radar" link sits under the list.
- Knowledge base: every Sunday the weekly run ingests what she marked Useful / Go deeper that week, plus mega trends and radar moves, into her private wiki (`ella@llm_wiki`, its own schema). Recaps and work details never go in.
- Radar: `radar.json` (public), dashboard page `#radar`: stats, filter "only this week's changes", and a progress chart (one row per capability on an Early, Emerging, Ready line; hollow dot + line = where it was before its last move). Click a row: side panel (web) / bottom sheet (phone) at `#radar/<id>` with meaning, limits, evidence and history timeline. Each capability: area, maturity (ready / emerging / early), status (new / moved / stable), what it means for products, where it breaks, 1 to 4 dated sources. Validate with `spark.py radar`.

### 3.11 Source collection (updated 2026-10-31)
- Blogs/newsletters: RSS, fetched directly (25 feeds, most verified).
- YouTube: YouTube Data API (free key, ~20 quota units/day for 10 channels) as primary; YouTube RSS as fallback (it is often down for hours).
- Podcasts: podcast RSS feeds for show notes; public transcript archives where they exist (e.g. Lenny's Podcast transcripts on GitHub).
- Sites without feeds: read the page directly.

## 4. Repo layout

```
daily-spark/
├── ARCHITECTURE.md      <- this file
├── CLAUDE.md            <- Worker runbook
├── README.md            <- setup guide for anyone
├── config/              <- example profile / sources / settings
├── scripts/
│   ├── fetch.py         <- fetch layer
│   └── spark.py         <- ledger, validate, build pages
├── templates/           <- page layout
├── editions/            <- public-safe editions + data/
├── index.html, latest.json
├── extension/           <- Chrome new tab
└── supabase/            <- table + security setup (SQL)
```

Private side (Ella):
```
ella-second-brain/daily-spark/
├── profile.yaml, blocklist.txt
├── editions/            <- full editions (Markdown)
├── recaps/              <- daily recap archive
└── weekly/
ella@llm_wiki/            <- knowledge base, written by the weekly run
```

## 5. Privacy rules
1. Nothing personal in this repo: no profile, no recaps, no section 3.
2. Recaps and feedback go to Supabase (insert-only from the page) and are archived in the private repo.
   Public sections stay generic; `blocklist.txt` makes publishing fail if a private name slips in.
3. The Worker reads only the context paths listed in `profile.yaml`.
4. The site is public. Others follow it (read, new tab, feedback); running your own copy is optional.

## 6. Build plan
| Week | Ship |
|---|---|
| 1 | Framework, config, fetch layer, morning edition, Pages site, push + email, Chrome new tab |
| 2 | Supabase: recap box, feedback, notes, exercise picks |
| 3 | Weekly edition, radar, knowledge base |
| 4 | Polish for community: README, setup skill (`/daily-spark setup`) |

## 7. Success after 2 weeks
- Opened at least 4 days a week
- At least 1 post or build came from it

## 8. Inspiration
- Morning Spark (tisu19021997/myThreads): daily idea collisions, repo as memory, Pages output
- NewsBlur: train by thumbs up/down on sources and topics
- NewsNow: adaptive fetch frequency per source
- zotero-arxiv-daily: personalize from your own library; fork + config setup
- daily.dev: personalized feed as the browser new tab
- dkhamsing/news: clean card layouts for news on mobile
