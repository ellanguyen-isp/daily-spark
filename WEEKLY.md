# daily-spark: Weekly runbook (Sundays)

The weekly edition replaces the Sunday daily. It zooms out: what moved in the market this week, what is a real trend vs hype,
what AI can really do now (the radar), what you did this week (private), and one bet for next week.
Shared rules (two repos, privacy, writing rules, no em dash) are in `CLAUDE.md`. Design: `ARCHITECTURE.md` 3.11.

## The weekly run

0. **Sync.** Same as `CLAUDE.md` step 0 (both repos, `main`).
1. **The week.** `python3 scripts/spark.py ledger` gives the next weekly number (`W01`, `W02`...).
   Read this week's editions (Monday to Saturday) in `editions/data/` and the candidate files in `data/candidates/` for the same days.
2. **Context.** Same as `CLAUDE.md` step 3: profile, recaps, Supabase recaps/feedback/picks for the last **7** days (ignore test data before `2026-10-31T09:30:00Z`),
   email recap replies. Archive new recaps. Feedback tells you which topics to weigh up or down.
3. **Market overview (web search allowed).** Search the last 7 days for the biggest product and AI moves. Combine with the week's frontier stories.
   Write `market.big` (3 to 4 sentences: what changed this week and what it means for product builders) and 3 to 5 `shifts`.
   A shift is a change in the market, not a single headline: group related news under one shift and link the best original source.
   You may reuse URLs from this week's dailies. Read each source before writing about it.
4. **Mega trend vs hype.** 2 to 4 calls. `mega` = a long-term change with evidence from more than one company or dataset.
   `hype` = loud this week but weak evidence, or a demo that will not survive real users. Say why in `e`, plainly. Add `url`, `src`, `date` when one source carries the call.
5. **Radar.** Open `radar.json`. Update it from this week's evidence:
   - add a capability that became real (`status: new`), move maturity when evidence changes (`status: moved`), and set every other entry to `status: stable` (except entries whose `since` is today: they stay `new`);
   - add the new source to `evidence` (newest first, keep at most 4); set `updated` to today;
   - every new or moved entry gets one line appended to its `history`: `{"date": today, "maturity": <new maturity>, "note": {en, vi} why}` (oldest first; never delete history);
   - never upgrade maturity on one vendor's claim alone; "ready" needs real users or independent proof.
   Run `python3 scripts/spark.py radar` until it passes. In the edition, `radar.note` says in 1 to 2 sentences what changed, and `radar.changes` lists the new and moved entries (`id`, `status`, `e`).
6. **Week in review (private).** From this week's recaps, picks and feedback: 2 to 4 `wins`, 2 to 4 `stuck` points, and one `pattern`
   (what keeps happening, said kindly and honestly). If there were no recaps this week, say so in `pattern` and keep wins/stuck to what the data shows. Never invent.
7. **Next week's bet** (public: keep it generic, no company, product or market names; see `CLAUDE.md` writing rules). One concrete thing to build, test or write next week, tied to her current focus and this week's market.
   `t` (the bet), `why`, `s` (3 steps), `o` (what she will have), `time` (e.g. `2 hrs`). Small enough to finish in the week.
8. **Write and publish.** Write the JSON (schema below) to `/tmp/weekly.json`, then
   `python3 scripts/spark.py publish /tmp/weekly.json --private-dir ../ella-second-brain/daily-spark/weekly --blocklist ../ella-second-brain/daily-spark/blocklist.txt`.
   It strips `review` from the public copy. Fix any error and run again.
9. **Check** the page once with Playwright: home (Today card is the weekly), `#<date>`, and `#radar`.
10. **Knowledge base (private wiki).** Save the week's best into `../ella-second-brain/ella@llm_wiki/`, following that folder's own `CLAUDE.md` (its schema, section 5 ingest workflow, index and log formats) exactly.
    - **What:** only items she marked `useful` or `deeper` or wrote a note on this week (a note's question goes into the raw file as "her question") (Supabase feedback after the test cutoff; item ids map to editions: `f0` = `frontier.items[0]`, `p1` = `people[1]`, `t0` = `timeless`, `m0` = weekly `market.shifts[0]`, `h0` = weekly `trend[0]`), plus this weekly's `mega` trends and radar new/moved entries.
    - **How:** for each marked item, read the original source again, write it as a new raw file `raw/daily-spark/<date>-<slug>.md` (title, url, date, source, the key points, and why she marked it), then ingest it: source page, create or update concept and entity pages, `wiki/index.md`. Mega trends and radar moves update one overview page, `wiki/overviews/ai-capability-radar.md` (create it the first time).
    - Write **one** log entry for the batch: `## [<date>] ingest | daily spark <edition>: N sources`. If nothing was marked, ingest only the overview and say so in the log.
    - **Never** put recaps, the week in review, or anything about her job, company or products in the wiki. Never edit existing files in `raw/`.
11. **Commit and push both repos** to `main`: this repo `git add -A && git commit -m "weekly <date>" && git push`; private repo: only `daily-spark/` and `ella@llm_wiki/`.
12. **Notify.** One Gmail email to the user (address in `profile.yaml`), subject `daily spark · weekly <d Mon>: <headline>`.
    Body: the week in one line, one line per shift, the bet, and the link `<site>#<date>` plus `<site>#radar`. Plain and short.
    Your **final message** is the same short text. If the run failed, one plain line saying what broke and whether an edition was published.

## Weekly schema (text fields are `{"en", "vi"}`; lists are `{"en": [...], "vi": [...]}`)
```json
{
  "type": "weekly", "date": "2026-11-08", "edition": "W02", "minutes": 10,
  "summary": {"en": "Headline: one line for the whole week", "vi": "..."},
  "week": {"from": "2026-11-02", "to": "2026-11-07"},
  "market": {
    "big": {...},
    "shifts": [{"date": "2026-11-04", "src": "openai.com", "url": "https://...", "tag": "Platform",
                "t": {...}, "p": {"en": ["...", "..."], "vi": [...]}, "w": {...}, "stat": {"v": "...", "l": {...}}}]
  },
  "trend": [{"k": "mega", "t": {...}, "e": {...}}, {"k": "hype", "t": {...}, "e": {...}, "url": "https://...", "src": "...", "date": "..."}],
  "radar": {"note": {...}, "changes": [{"id": "computer-use", "status": "moved", "e": {...}}]},
  "review": {"wins": {"en": [...], "vi": [...]}, "stuck": {...}, "pattern": {...}},
  "bet": {"time": "2 hrs", "t": {...}, "why": {...}, "s": {"en": ["...", "...", "..."], "vi": [...]}, "o": {...}}
}
```
