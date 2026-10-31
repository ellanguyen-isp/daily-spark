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
  06:30 local       |  WORKER (Claude scheduled task)   |
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
        | Web page / Chrome new tab | -----> | Supabase (insert-only)     |
        | recap box + thumbs up/down|        | recaps, feedback, exercise |
        +---------------------------+        +-------------+--------------+
                                                           | read next morning
                                                           v
                                                         WORKER
```

## 3. Components

### 3.1 Config (private, per user)
Lives in the user's **private** repo. This repo ships only examples in `config/`.

| File | What it holds |
|---|---|
| `profile.yaml` | who I am, role, goals, interests, current focus, context paths (notes to learn interests from) |
| `sources.yaml` | sources with type (`rss`, `youtube`, `podcast`, `web`), url, tags, priority, check frequency |
| `settings.yaml` | timezone, schedule, language, notification channels, public site on/off, Supabase project |

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
| 1 | Frontier | Big product/AI news relevant to the user. Max 1 to 2. Skip if nothing. | yes |
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
- Tables: `recaps`, `feedback` (item thumbs up/down), `exercise_log` (which exercise was picked/done).
- Row Level Security: the page can **insert only**; nobody can read through the public key. The Worker reads with the service connection.
- A personal key saved once in the user's browser marks their entries; entries without it are ignored.
- Community default without Supabase: reply to the email.

### 3.8 Schedules
| Time (local) | Task |
|---|---|
| 06:30 daily | Morning edition, notify by ~07:00 |
| 20:00 daily | Recap reminder (push + email) linking to the recap box |
| Sunday morning | Weekly edition: market overview + "what is really possible now" radar |

## 3.9 Design (agreed 2026-10-31)
- Mood: calm minimal (Morning Spark-like), no personal branding, neutral for the community.
- Palette: Midnight `#0b1957`, Sapphire `#426bc2`, Petal `#e8d9ed`, Lace `#f7f4ed`, Lavender `#d2b3db`, Bridal Blue `#e9f3ff`.
- Reading: swipeable cards by default (one section per card); a toggle at the top switches to one long scroll.
- Language toggle EN / VI at the top.
- Chrome new tab: compact card (Frontier headline + today's question + 3 exercise buttons) with "Read full edition".

## 3.10 Source collection (updated 2026-10-31)
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
├── profile.yaml, sources.yaml, settings.yaml
├── editions/            <- full editions (Markdown)
├── recaps/              <- daily recap archive
├── weekly/
└── kb/ (radar.md, ideas.md, index.md)
```

## 5. Privacy rules
1. Nothing personal in this repo: no profile, no recaps, no section 3.
2. Recaps and feedback go to Supabase (insert-only from the page) and are archived in the private repo.
3. The Worker reads only the context paths listed in `profile.yaml`.
4. The public site is unlisted until the user decides to share it.

## 6. Build plan
| Week | Ship |
|---|---|
| 1 | Framework, config, fetch layer, morning edition, Pages site, push + email, Chrome new tab |
| 2 | Supabase: recap box, thumbs up/down, exercise log; 20:00 recap task |
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
