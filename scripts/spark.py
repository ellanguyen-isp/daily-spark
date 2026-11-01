#!/usr/bin/env python3
"""daily-spark build tool (standard library only).

  python3 scripts/spark.py ledger
      What was already sent: recent dates, used source URLs, timeless sources.

  python3 scripts/spark.py publish EDITION.json [--private-dir DIR]
      Validate a full edition (daily, or "type": "weekly"), then:
        - write the public copy (no private "work" / "review" sections) to editions/data/<date>.json
        - rebuild editions/index.json and latest.json
        - if --private-dir is given, write the full edition as Markdown there

  python3 scripts/spark.py radar
      Validate radar.json (the "what's really possible now" page).
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "editions" / "data"
LANGS = ("en", "vi")
FORBIDDEN = "—"  # em dash: house style says never use it
PRIVATE = ("work", "review")  # sections that never reach the public repo
RADAR = ROOT / "radar.json"
MATURITY = ("ready", "emerging", "early")
STATUS = ("new", "moved", "stable")


def kind(E):
    return E.get("type", "daily")


class Invalid(Exception):
    pass


def need(cond, msg):
    if not cond:
        raise Invalid(msg)


def bi(v, where, is_list=False):
    """A bilingual field: {"en": ..., "vi": ...}."""
    need(isinstance(v, dict), f"{where}: must be {{en, vi}}")
    for l in LANGS:
        need(l in v and v[l], f"{where}.{l}: missing")
        if is_list:
            need(isinstance(v[l], list) and len(v[l]) >= 2, f"{where}.{l}: needs a list of at least 2 points")


def walk_text(o, path="$"):
    if isinstance(o, str):
        yield path, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from walk_text(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk_text(v, f"{path}[{i}]")


def used_urls(exclude_date=None):
    urls = {}
    for f in sorted(DATA.glob("*.json")):
        if f.stem == exclude_date:
            continue
        for u in re.findall(r'"url":\s*"([^"]+)"', f.read_text()):
            urls[u] = f.stem
    return urls


def no_dash(o):
    for path, text in walk_text(o):
        need(FORBIDDEN not in text, f"{path}: contains an em dash; rewrite the sentence")


def validate_radar(R):
    need(re.fullmatch(r"\d{4}-\d{2}-\d{2}", R.get("updated", "")), "radar.updated: YYYY-MM-DD")
    bi(R.get("intro"), "radar.intro")
    ids = set()
    need(6 <= len(R.get("entries", [])) <= 24, "radar.entries: 6 to 24 capabilities")
    for i, x in enumerate(R["entries"]):
        w = f"radar.entries[{i}]"
        need(re.fullmatch(r"[a-z0-9-]+", x.get("id", "")), w + ".id: short-kebab-id")
        need(x["id"] not in ids, w + ".id: duplicate"); ids.add(x["id"])
        need(x.get("maturity") in MATURITY, w + ".maturity: " + "/".join(MATURITY))
        need(x.get("status") in STATUS, w + ".status: " + "/".join(STATUS))
        need(re.fullmatch(r"\d{4}-\d{2}-\d{2}", x.get("since", "")), w + ".since: YYYY-MM-DD")
        need(x.get("area"), w + ".area: required")
        for k in ("cap", "means", "limit"):
            bi(x.get(k), f"{w}.{k}")
        need(1 <= len(x.get("evidence", [])) <= 4, w + ".evidence: 1 to 4 sources")
        for j, ev in enumerate(x["evidence"]):
            need(ev.get("url", "").startswith("http") and re.fullmatch(r"\d{4}-\d{2}-\d{2}", ev.get("date", "")),
                 f"{w}.evidence[{j}]: url and YYYY-MM-DD date required")
            bi(ev.get("note"), f"{w}.evidence[{j}].note")
        for j, h in enumerate(x.get("history", [])):
            need(re.fullmatch(r"\d{4}-\d{2}-\d{2}", h.get("date", "")) and h.get("maturity") in MATURITY,
                 f"{w}.history[{j}]: date (YYYY-MM-DD) and maturity required")
            bi(h.get("note"), f"{w}.history[{j}].note")
    no_dash(R)
    return ids


def validate_weekly(E):
    need(re.fullmatch(r"\d{4}-\d{2}-\d{2}", E.get("date", "")), "date: YYYY-MM-DD")
    need(isinstance(E.get("edition"), str) and re.fullmatch(r"W\d{2}", E["edition"]), 'edition: weekly number like "W01"')
    need(isinstance(E.get("minutes"), int), "minutes: integer")
    bi(E.get("summary"), "summary")
    wk = E.get("week", {})
    need(re.fullmatch(r"\d{4}-\d{2}-\d{2}", wk.get("from", "")) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", wk.get("to", "")),
         "week: {from, to} as YYYY-MM-DD")
    M = E.get("market")
    need(isinstance(M, dict), "market: missing")
    bi(M.get("big"), "market.big")
    need(3 <= len(M.get("shifts", [])) <= 5, "market.shifts: 3 to 5 shifts")
    for i, it in enumerate(M["shifts"]):
        w = f"market.shifts[{i}]"
        need(it.get("url", "").startswith("http") and it.get("date"), f"{w}: url and date required")
        bi(it.get("t"), w + ".t"); bi(it.get("p"), w + ".p", True); bi(it.get("w"), w + ".w")
    T = E.get("trend", [])
    need(2 <= len(T) <= 6, "trend: 2 to 6 calls")
    need({x.get("k") for x in T} == {"mega", "hype"}, 'trend: at least one "mega" and one "hype"')
    for i, x in enumerate(T):
        bi(x.get("t"), f"trend[{i}].t"); bi(x.get("e"), f"trend[{i}].e")
    R = E.get("radar")
    need(isinstance(R, dict), "radar: missing")
    bi(R.get("note"), "radar.note")
    ids = validate_radar(json.loads(RADAR.read_text())) if RADAR.exists() else set()
    for i, c in enumerate(R.get("changes", [])):
        need(c.get("id") in ids, f"radar.changes[{i}].id: not in radar.json")
        need(c.get("status") in STATUS, f"radar.changes[{i}].status")
        bi(c.get("e"), f"radar.changes[{i}].e")
    if E.get("review"):
        V = E["review"]
        bi(V.get("wins"), "review.wins", True); bi(V.get("stuck"), "review.stuck", True); bi(V.get("pattern"), "review.pattern")
    B = E.get("bet")
    need(isinstance(B, dict) and B.get("time"), "bet: missing (with time)")
    bi(B.get("t"), "bet.t"); bi(B.get("why"), "bet.why"); bi(B.get("s"), "bet.s", True); bi(B.get("o"), "bet.o")
    no_dash(E)


def validate(E):
    if kind(E) == "weekly":
        return validate_weekly(E)
    need(re.fullmatch(r"\d{4}-\d{2}-\d{2}", E.get("date", "")), "date: YYYY-MM-DD")
    need(isinstance(E.get("edition"), str) and re.fullmatch(r"\d{3}", E["edition"]), 'edition: 3-digit string like "001"')
    bi(E.get("summary"), "summary")
    need(isinstance(E.get("minutes"), int), "minutes: integer")

    F = E.get("frontier")
    need(isinstance(F, dict), "frontier: missing")
    bi(F.get("big"), "frontier.big")
    need(1 <= len(F.get("items", [])) <= 5, "frontier.items: 1 to 5 stories")
    for i, it in enumerate(F["items"]):
        w = f"frontier.items[{i}]"
        need(it.get("url", "").startswith("http"), f"{w}.url: original source link required")
        need(it.get("date"), f"{w}.date: required")
        bi(it.get("t"), w + ".t"); bi(it.get("p"), w + ".p", True); bi(it.get("w"), w + ".w")

    need(2 <= len(E.get("people", [])) <= 4, "people: 2 to 4 items")
    for i, it in enumerate(E["people"]):
        w = f"people[{i}]"
        need(it.get("url", "").startswith("http"), f"{w}.url: original source link required")
        need(it.get("date") and it.get("who"), f"{w}: date and who required")
        bi(it.get("t"), w + ".t"); bi(it.get("p"), w + ".p", True); bi(it.get("k"), w + ".k")

    for i, it in enumerate(E.get("work", [])):
        w = f"work[{i}]"
        bi(it.get("t"), w + ".t"); bi(it.get("p"), w + ".p", True); bi(it.get("k"), w + ".k")

    T = E.get("timeless")
    need(isinstance(T, dict), "timeless: missing")
    need(T.get("src"), "timeless.src: required")
    for k in ("q", "e", "x"):
        bi(T.get(k), "timeless." + k)
    bi(T.get("a"), "timeless.a", True)

    need(len(E.get("think", [])) == 3, "think: exactly 3 questions")
    for i, it in enumerate(E["think"]):
        bi(it.get("q"), f"think[{i}].q"); bi(it.get("c"), f"think[{i}].c")

    ex = E.get("exercises", [])
    need([e.get("k") for e in ex] == ["work", "write", "build"], "exercises: work, write, build in that order")
    for e in ex:
        w = "exercises." + e["k"]
        need(e.get("time"), w + ".time: required")
        bi(e.get("tag"), w + ".tag"); bi(e.get("g"), w + ".g"); bi(e.get("s"), w + ".s", True); bi(e.get("o"), w + ".o")

    no_dash(E)

    reused = {u: d for u, d in used_urls(E["date"]).items()
              if u in {x.get("url") for x in F["items"] + E["people"]}}
    need(not reused, "already sent before: " + ", ".join(f"{u} ({d})" for u, d in reused.items()))


def stamps(E):
    """Every news item of an edition, for the Chrome new tab (one stamp each)."""
    def st(it, kind, who=""):
        return {"t": it["t"], "src": it.get("src", ""), "url": it["url"], "date": it.get("date", ""),
                "tag": it.get("tag", ""), "who": who or it.get("who", ""), "kind": kind}
    if kind(E) == "weekly":
        site = "https://ellanguyen-isp.github.io/daily-spark/"  # community users: your own site
        out = [st(it, "shift") for it in E["market"]["shifts"]]
        out += [{"t": x["t"], "src": x.get("src", ""), "url": x.get("url") or f"{site}#{E['date']}", "date": x.get("date", ""),
                 "tag": "", "who": "", "kind": x["k"]} for x in E.get("trend", [])]
        caps = {x["id"]: x["cap"] for x in json.loads(RADAR.read_text())["entries"]} if RADAR.exists() else {}
        out += [{"t": caps.get(c["id"], c["e"]), "src": "radar · " + c["status"], "url": f"{site}#radar/{c['id']}", "date": E["date"], "tag": "", "who": "",
                 "kind": "radar"} for c in E.get("radar", {}).get("changes", [])]
        return out
    return [st(it, "frontier") for it in E["frontier"]["items"]] + [st(it, "people") for it in E["people"]]


def rebuild_index():
    eds = []
    for f in sorted(DATA.glob("*.json"), reverse=True):
        E = json.loads(f.read_text())
        eds.append({"date": E["date"], "edition": E["edition"], "type": kind(E), "summary": E["summary"], "minutes": E["minutes"]})
    (ROOT / "editions" / "index.json").write_text(json.dumps({"editions": eds}, ensure_ascii=False, indent=1))
    if eds:
        E = json.loads((DATA / f"{eds[0]['date']}.json").read_text())
        latest = {
            "type": "weekly", "date": E["date"], "edition": E["edition"], "summary": E["summary"],
            "big": E["market"]["big"],
            "headlines": [{"t": it["t"], "src": it.get("src", ""), "url": it["url"]} for it in E["market"]["shifts"]],
            "question": E["bet"]["t"],
            "exercises": [{"k": "bet", "tag": {"en": "Next week's bet", "vi": "Cược tuần tới"}, "time": E["bet"]["time"], "g": E["bet"]["t"]}],
        } if kind(E) == "weekly" else {
            "type": "daily",
            "date": E["date"], "edition": E["edition"], "summary": E["summary"],
            "big": E["frontier"]["big"],
            "headlines": [{"t": it["t"], "src": it.get("src", ""), "url": it["url"]} for it in E["frontier"]["items"]],
            "question": E["think"][0]["q"],
            "exercises": [{"k": e["k"], "tag": e["tag"], "time": e["time"], "g": e["g"]} for e in E["exercises"]],
        }
        latest["stamps"] = stamps(E)
        (ROOT / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=1))
    return eds


def weekly_markdown(E):
    en = lambda o: o["en"] if isinstance(o, dict) else o  # noqa: E731
    out = [f"---\ntype: daily-spark-weekly\ndate: {E['date']}\nedition: \"{E['edition']}\"\nweek: {E['week']['from']} to {E['week']['to']}\n---\n",
           f"# daily-spark weekly {E['date']} · {E['edition']}\n", f"> {en(E['summary'])}\n",
           "## Market overview\n", f"{en(E['market']['big'])}\n"]
    for it in E["market"]["shifts"]:
        out.append(f"### {en(it['t'])}\n{it['date']} · [{it.get('src') or it['url']}]({it['url']})\n")
        out += [f"- {p}" for p in en(it["p"])]
        out.append(f"\n**Why it matters:** {en(it['w'])}\n")
    out.append("## Mega trend vs hype\n")
    out += [f"- **{x['k'].upper()}: {en(x['t'])}** {en(x['e'])}" for x in E["trend"]]
    out.append(f"\n## Radar\n{en(E['radar']['note'])}\n")
    out += [f"- {c['id']} ({c['status']}): {en(c['e'])}" for c in E["radar"].get("changes", [])]
    if E.get("review"):
        V = E["review"]
        out.append("\n## Week in review (private)\n**Wins**")
        out += [f"- {p}" for p in en(V["wins"])]
        out.append("\n**Stuck**")
        out += [f"- {p}" for p in en(V["stuck"])]
        out.append(f"\n**Pattern:** {en(V['pattern'])}\n")
    B = E["bet"]
    out.append(f"\n## Next week's bet · {B['time']}\n**{en(B['t'])}**\n\n{en(B['why'])}\n")
    out += [f"{i + 1}. {s}" for i, s in enumerate(en(B["s"]))]
    out.append(f"\nYou will have: {en(B['o'])}\n")
    return "\n".join(out) + "\n"


def to_markdown(E):
    if kind(E) == "weekly":
        return weekly_markdown(E)
    en = lambda o: o["en"] if isinstance(o, dict) else o  # noqa: E731
    out = [f"---\ntype: daily-spark\ndate: {E['date']}\nedition: \"{E['edition']}\"\n---\n",
           f"# daily-spark {E['date']} · Edition {E['edition']}\n", f"> {en(E['summary'])}\n",
           "## Frontier\n", f"**The big picture:** {en(E['frontier']['big'])}\n"]
    for it in E["frontier"]["items"]:
        out.append(f"### {en(it['t'])}\n{it['date']} · [{it.get('src') or it['url']}]({it['url']})\n")
        out += [f"- {p}" for p in en(it["p"])]
        out.append(f"\n**Why it matters:** {en(it['w'])}\n")
    if E["frontier"].get("watch"):
        out.append(f"**What to watch next:** {en(E['frontier']['watch'])}\n")
    out.append("## From people you follow\n")
    for it in E["people"]:
        out.append(f"### {en(it['t'])}\n{it['date']} · {it['who']} · [{it.get('src') or it['url']}]({it['url']})\n")
        out += [f"- {p}" for p in en(it["p"])]
        out.append(f"\n**Takeaway:** {en(it['k'])}\n")
    if E.get("work"):
        out.append("## Relevant to your work (private)\n")
        for it in E["work"]:
            out.append(f"### {en(it['t'])}\n")
            out += [f"- {p}" for p in en(it["p"])]
            out.append(f"\n**Takeaway:** {en(it['k'])}\n")
    T = E["timeless"]
    out.append(f"## Timeless\n> {en(T['q'])}\n> {T['src']}\n\n{en(T['e'])}\n")
    out += [f"- {p}" for p in en(T["a"])]
    out.append(f"\n**Example:** {en(T['x'])}\n\n## Think\n")
    out += [f"{i + 1}. {en(q['q'])} _({en(q['c'])})_" for i, q in enumerate(E["think"])]
    out.append("\n## Exercises\n")
    for e in E["exercises"]:
        out.append(f"### {en(e['tag'])} · {e['time']}: {en(e['g'])}")
        out += [f"{i + 1}. {s}" for i, s in enumerate(en(e["s"]))]
        out.append(f"\nYou will have: {en(e['o'])}\n")
    return "\n".join(out) + "\n"


def cmd_ledger(_):
    files = sorted(DATA.glob("*.json"))
    eds = [json.loads(f.read_text()) for f in files]
    daily = [E for E in eds if kind(E) == "daily"]
    weekly = [E for E in eds if kind(E) == "weekly"]
    print(f"{len(daily)} daily + {len(weekly)} weekly editions published.",
          "Next daily:", f"{len(daily) + 1:03d}", "· next weekly:", f"W{len(weekly) + 1:02d}")
    for E in eds[-7:]:
        extra = "| timeless: " + E["timeless"]["src"] if kind(E) == "daily" else "| weekly"
        print(" ", E["date"], E["edition"], "|", E["summary"]["en"], extra)
    urls = used_urls()
    print(f"{len(urls)} source URLs already used (never reuse them in a daily).")
    return 0


def cmd_publish(a):
    E = json.loads(Path(a.file).read_text())
    try:
        validate(E)
    except Invalid as e:
        print("INVALID:", e, file=sys.stderr)
        return 1
    public = {k: v for k, v in E.items() if k not in PRIVATE}
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / f"{E['date']}.json").write_text(json.dumps(public, ensure_ascii=False, indent=1))
    eds = rebuild_index()
    print(f"published {E['date']} (edition {E['edition']}); {len(eds)} editions on the site")
    if a.private_dir:
        d = Path(a.private_dir)
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{E['date']}.md").write_text(to_markdown(E))
        (d / f"{E['date']}.json").write_text(json.dumps(E, ensure_ascii=False, indent=1))
        print("private copy ->", d / f"{E['date']}.md")
    return 0


def cmd_radar(_):
    try:
        ids = validate_radar(json.loads(RADAR.read_text()))
    except (Invalid, FileNotFoundError, json.JSONDecodeError) as e:
        print("INVALID:", e, file=sys.stderr)
        return 1
    print(f"radar.json ok: {len(ids)} capabilities")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("ledger")
    p = sub.add_parser("publish")
    p.add_argument("file")
    p.add_argument("--private-dir")
    sub.add_parser("radar")
    a = ap.parse_args(argv)
    return {"ledger": cmd_ledger, "publish": cmd_publish, "radar": cmd_radar}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
