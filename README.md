# daily-spark

A small daily loop for product builders: **digest** the market, **think** for yourself, **build** something, **recap** what you learned.

Every morning a robot collects new posts and videos from the sources you choose, and Claude turns the best of them into one short edition:

| Section | What you get |
|---|---|
| Frontier | The big picture of the week + 2 to 4 important stories, each with date and original source |
| From people you follow | 3 items from your builders, with key points and a takeaway |
| Relevant to your work | Private: never published |
| Timeless | One lasting principle, how to apply it, an example |
| Think | 3 questions you answer in your own words |
| Exercises | Work, write, build: pick one |

Read it on any device, or as your Chrome new tab. English and Vietnamese.

## How it works
```
05:40  GitHub Actions  -> scripts/fetch.py  -> data/candidates/<date>.json
06:30  Claude (scheduled task, runbook in CLAUDE.md) -> editions/data/<date>.json
       -> GitHub Pages site + latest.json -> push notification + email
```
Details: [ARCHITECTURE.md](ARCHITECTURE.md). Design: [design/final.html](design/final.html).

## Repo layout
```
index.html              the site (home + daily pages), reads editions/
editions/index.json     list of editions (generated)
editions/data/*.json    one public edition per day (no private section)
latest.json             today's edition, compact, for the Chrome new tab
config/sources.yaml     your sources
scripts/fetch.py        collects new items (RSS + YouTube Data API)
scripts/spark.py        validates and publishes an edition
extension/              Chrome new tab
CLAUDE.md               the Worker's runbook
```

## Set up your own (about 20 minutes)
1. **Copy** this repo to your GitHub account and make it public.
2. **Sources:** edit `config/sources.yaml`.
3. **YouTube key (free):** Google Cloud Console → enable *YouTube Data API v3* → create an API key →
   in your repo: Settings → Secrets and variables → Actions → New secret `YOUTUBE_API_KEY`.
4. **Site:** Settings → Pages → Deploy from a branch → `main`, folder `/ (root)`.
5. **Private profile:** in a private repo, create `daily-spark/profile.yaml` (see CLAUDE.md for what the Worker reads).
6. **Morning run:** in Claude, create a scheduled task at 06:30 your time with the prompt:
   *"Run daily-spark for today. Follow CLAUDE.md in the daily-spark repo."*
7. **Chrome new tab (optional):** set `SITE` in `extension/newtab.js` to your Pages address, then
   Chrome → Extensions → Developer mode → Load unpacked → pick the `extension` folder.

A guided setup (`/daily-spark setup`) is planned for week 4.
