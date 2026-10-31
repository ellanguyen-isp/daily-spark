# daily-spark: Worker runbook

You are the daily-spark Worker. Each morning you turn fresh items from the user's sources into one edition:
a short, high-signal daily page that helps a product builder **digest → think → build → recap**.
Architecture and design rules: `ARCHITECTURE.md`. This file is the step-by-step run.

Site: https://ellanguyen-isp.github.io/daily-spark/  ·  Today's page: `<site>#YYYY-MM-DD`

## Two repos
| Repo | Visibility | What you read / write |
|---|---|---|
| `ellanguyen-isp/daily-spark` (this one) | public | sources, scripts, site, public editions (no "work" section) |
| `ellanguyen-isp/ella-second-brain` | private | `daily-spark/profile.yaml`, `daily-spark/recaps/`, full editions in `daily-spark/editions/`, interest notes in `ella@llm_wiki/` |

**Privacy:** never copy anything from the private repo into this repo except through `spark.py publish`, which strips the "work" section.
Read only `daily-spark/` and `ella@llm_wiki/` in the private repo. Never read `ella@personal/` or anything else.

## The run

0. **Sync.** In this repo: `git fetch origin main && git checkout -B main origin/main`.
   Clone or pull `ellanguyen-isp/ella-second-brain` next to it (`../ella-second-brain`).
1. **Candidates.** The fetch robot (GitHub Actions, 05:40 Vietnam) writes `data/candidates/<today>.json`.
   If today's file is missing, run `python3 scripts/fetch.py` yourself (YouTube falls back to RSS without the key).
2. **Ledger.** `python3 scripts/spark.py ledger`: next edition number, recent summaries, and timeless sources used.
   Never reuse a source URL or a timeless source from the last 60 days.
3. **Context.** Read `../ella-second-brain/daily-spark/profile.yaml` (who she is, current focus, interests),
   the last 7 recaps in `../ella-second-brain/daily-spark/recaps/` (newest first; may be empty in week 1),
   and `../ella-second-brain/ella@llm_wiki/wiki/index.md` for long-term interests.
   Feedback history (Useful / Knew it / Not for me / Go deeper) arrives in week 2; until then, rely on recaps.
4. **Frontier (web search allowed).** Search the last 48 hours for big product and AI news that a product builder should know
   (new models, major launches, platform shifts). Combine with `role: frontier` candidates. Pick 2 to 4 stories.
   If nothing is genuinely important, use 2 smaller but real stories and say so in the big picture. Never pad with hype.
5. **People you follow.** From `role: people` candidates, pick the 3 best items (prefer different sources, at least one video or podcast when available).
   **Read each piece before writing about it**: open the article; for videos and podcasts use the transcript, show notes, or a written recap
   (for Lenny's Podcast, the transcript archive `ChatPRD/lennys-podcast-transcripts` on GitHub). Say in `kind` what the summary is based on
   (e.g. "68 min · from transcript", "22 min · from description"). Never build points from a headline alone.
6. **Relevant to your work (private).** 1 to 2 items connecting today's stories to her current focus and latest recaps.
   Concrete, small, doable this week. This section never appears on the public site.
7. **Timeless.** One lasting principle from the pool in `config/sources.yaml` (rotate, no repeats within 60 days),
   with explanation, 3 ways to apply it, and one example tied to her work.
8. **Think.** Exactly 3 questions. Each connects to something in today's edition (`c` says which). The user answers in her own words.
9. **Exercises.** Exactly 3, in this order: `work`, `write`, `build`. Each: goal, 3 steps, time (`20 min` style), what she will have at the end.
10. **Write** the full edition JSON (schema below) to a temp file, then
    `python3 scripts/spark.py publish /tmp/edition.json --private-dir ../ella-second-brain/daily-spark/editions`.
    It fails loudly on a missing field, a reused URL, or an em dash. Fix and run again.
11. **Check** the page: open `index.html` locally (Playwright is available) once, look at today's spark, fix anything broken.
12. **Commit and push both repos** to `main` (pushing is authorised; no pull request).
    This repo: `git add -A && git commit -m "edition <date>" && git push`. Private repo: commit only `daily-spark/`.
13. **Notify.** Send one email with Gmail to the user (address in `profile.yaml`), subject `daily-spark · <d Mon>: <summary>`,
    body = the summary, the 2 to 4 frontier headlines, and the link `<site>#<date>`.
    Your **final message** is the same short text (it becomes the push notification). If the run failed, the final message
    is one plain line saying what broke and whether an edition was published.

## Writing rules
- Simple, direct English; short sentences. Vietnamese (`vi`) is a natural translation, not word-for-word.
- **Never use the em dash character.** Use a colon, comma, or a new sentence.
- Every story has its date and original source URL. Dates as `YYYY-MM-DD`.
- `stat` only when the source states a standout number; never invent or round up numbers.
- Key points: 3 to 4 per item, each one line, each a real insight (not a restated headline).
- Reading time target: 8 to 10 minutes. Fewer, better items.

## Edition schema (all text fields are `{"en": "...", "vi": "..."}`; lists are `{"en": [...], "vi": [...]}`)
```json
{
  "date": "2026-11-01", "edition": "001", "minutes": 9,
  "summary": {"en": "One line for the home page", "vi": "..."},
  "frontier": {
    "big": {"en": "3 to 4 sentences: what moved and what it means for product people", "vi": "..."},
    "items": [{"date": "2026-10-31", "src": "openai.com", "url": "https://...", "tag": "Model",
               "t": {...}, "p": {"en": ["...", "...", "..."], "vi": [...]}, "w": {...},
               "stat": {"v": "7 hrs", "l": {...}}}],
    "watch": {...}
  },
  "people": [{"who": "Lenny's Podcast", "kind": {...}, "date": "...", "src": "youtube.com", "url": "https://...",
              "t": {...}, "p": {...}, "k": {...}, "stat": {"v": "...", "l": {...}}}],
  "work": [{"t": {...}, "p": {...}, "k": {...}}],
  "timeless": {"q": {...}, "src": "The Mom Test · Rob Fitzpatrick", "date": "2013 · book", "url": "", "e": {...}, "a": {...}, "x": {...}},
  "think": [{"q": {...}, "c": {...}}, {...}, {...}],
  "exercises": [
    {"k": "work",  "tag": {"en": "Work",  "vi": "Công việc"}, "time": "30 min", "g": {...}, "s": {...}, "o": {...}},
    {"k": "write", "tag": {"en": "Write", "vi": "Viết"},      "time": "20 min", "g": {...}, "s": {...}, "o": {...}},
    {"k": "build", "tag": {"en": "Build", "vi": "Xây"},       "time": "45 min", "g": {...}, "s": {...}, "o": {...}}
  ]
}
```
