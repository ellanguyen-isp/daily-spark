#!/usr/bin/env python3
"""daily-spark fetch layer.

Reads config/sources.yaml, collects new items from RSS/Atom feeds and YouTube
channels, removes anything already sent, and writes data/candidates/<date>.json.

YouTube: YouTube Data API first (needs YOUTUBE_API_KEY), channel RSS as fallback.
Standard library + PyYAML only.

Usage:
  python3 scripts/fetch.py                # today (Asia/Ho_Chi_Minh), last 3 days
  python3 scripts/fetch.py --days 7       # wider window
  python3 scripts/fetch.py --check        # just report which sources work
"""
import argparse
import datetime as dt
import email.utils
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TZ = dt.timezone(dt.timedelta(hours=7))  # Asia/Ho_Chi_Minh, no DST
UA = "daily-spark-fetch/1.0 (+https://github.com/ellanguyen-isp/daily-spark)"
TIMEOUT = 20


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def clean(text, limit=600):
    text = html.unescape(re.sub(r"<[^>]+>", " ", text or ""))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def parse_date(s):
    if not s:
        return None
    s = s.strip()
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        d = None
    if d is None:
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d


def local(tag):
    return tag.rsplit("}", 1)[-1]


def parse_feed(raw):
    """Return list of dicts from RSS 2.0 or Atom bytes."""
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        # Some feeds use HTML entities (&nbsp;, &rsquo;) that XML does not define.
        txt = raw.decode("utf-8", "replace")
        txt = re.sub(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)(\w+);",
                     lambda m: html.unescape(m.group(0)).replace("&", "&amp;"), txt)
        root = ET.fromstring(txt.encode("utf-8"))
    items = []
    if local(root.tag) == "rss" or root.find("channel") is not None:
        for it in root.iter():
            if local(it.tag) != "item":
                continue
            f = {local(c.tag): c for c in it}
            items.append({
                "title": clean(f["title"].text if "title" in f else "", 200),
                "url": (f["link"].text or "").strip() if "link" in f else "",
                "published": parse_date(f["pubDate"].text if "pubDate" in f else (f["date"].text if "date" in f else None)),
                "summary": clean((f["description"].text if "description" in f else "") or (f["encoded"].text if "encoded" in f else "")),
            })
    else:  # Atom
        for e in root:
            if local(e.tag) != "entry":
                continue
            title = url = summary = pub = ""
            for c in e:
                n = local(c.tag)
                if n == "title":
                    title = c.text or ""
                elif n == "link" and (c.get("rel") in (None, "alternate")):
                    url = c.get("href") or url
                elif n in ("summary", "content") and not summary:
                    summary = "".join(c.itertext())
                elif n in ("published", "updated") and not pub:
                    pub = c.text or ""
                elif n == "group":  # YouTube media:group
                    for g in c:
                        if local(g.tag) == "description" and not summary:
                            summary = g.text or ""
            items.append({"title": clean(title, 200), "url": url.strip(), "published": parse_date(pub), "summary": clean(summary)})
    return items


def youtube_api(channel_id, key, n=5):
    uploads = "UU" + channel_id[2:]
    q = urllib.parse.urlencode({"part": "snippet,contentDetails", "playlistId": uploads, "maxResults": n, "key": key})
    data = json.loads(get("https://www.googleapis.com/youtube/v3/playlistItems?" + q))
    out = []
    for it in data.get("items", []):
        sn = it["snippet"]
        vid = it["contentDetails"]["videoId"]
        out.append({
            "title": clean(sn.get("title"), 200),
            "url": "https://www.youtube.com/watch?v=" + vid,
            "published": parse_date(it["contentDetails"].get("videoPublishedAt") or sn.get("publishedAt")),
            "summary": clean(sn.get("description"), 1200),
        })
    return out


def youtube_rss(channel_id):
    return parse_feed(get("https://www.youtube.com/feeds/videos.xml?channel_id=" + channel_id))


def sent_urls():
    """Every source URL already used in a published edition."""
    urls = set()
    for f in (ROOT / "editions" / "data").glob("*.json"):
        try:
            urls.update(re.findall(r'"url":\s*"([^"]+)"', f.read_text()))
        except OSError:
            pass
    return urls


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=3, help="look-back window in days (default 3)")
    ap.add_argument("--date", help="edition date YYYY-MM-DD (default: today in Vietnam)")
    ap.add_argument("--check", action="store_true", help="only report which sources work")
    a = ap.parse_args(argv)

    today = a.date or dt.datetime.now(TZ).date().isoformat()
    since = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=a.days)
    cfg = yaml.safe_load((ROOT / "config" / "sources.yaml").read_text())
    key = os.environ.get("YOUTUBE_API_KEY", "").strip()
    already = sent_urls()

    candidates, report = [], []

    def add(src, items, via):
        kept = 0
        for it in items:
            if not it["url"] or it["url"] in already:
                continue
            if it["published"] and it["published"] < since:
                continue
            candidates.append({
                "source": src["name"], "type": src.get("type", "rss"), "role": src.get("role", "people"),
                "priority": src.get("priority", 2), "tags": src.get("tags", []), "via": via,
                "title": it["title"], "url": it["url"],
                "published": it["published"].astimezone(TZ).date().isoformat() if it["published"] else None,
                "summary": it["summary"],
            })
            kept += 1
        report.append({"source": src["name"], "ok": True, "via": via, "new": kept})

    for y in cfg.get("youtube", []):
        y = dict(y, type="youtube")
        items, via, err = None, None, None
        if key:
            try:
                items, via = youtube_api(y["channel_id"], key), "youtube-api"
            except Exception as e:  # noqa: BLE001
                err = "api: " + str(e)[:80]
        if items is None:
            try:
                items, via = youtube_rss(y["channel_id"]), "youtube-rss"
            except Exception as e:  # noqa: BLE001
                err = (err + " | " if err else "") + "rss: " + str(e)[:80]
        if items is None:
            report.append({"source": y["name"], "ok": False, "error": err})
        else:
            add(y, items, via)

    for r in cfg.get("rss", []):
        if r.get("type") == "web":
            report.append({"source": r["name"], "ok": None, "note": "no feed; the Worker reads the page"})
            continue
        try:
            add(r, parse_feed(get(r["url"])), "rss")
        except Exception as e:  # noqa: BLE001
            report.append({"source": r["name"], "ok": False, "error": str(e)[:120]})

    ok = sum(1 for x in report if x.get("ok"))
    bad = [x for x in report if x.get("ok") is False]
    print(f"{ok} sources ok, {len(bad)} failed, {len(candidates)} new items since {since.date()}")
    for x in bad:
        print("  FAILED", x["source"], "-", x.get("error"))
    if a.check:
        return 0

    candidates.sort(key=lambda c: (c["priority"], c["published"] or ""), reverse=False)
    candidates.sort(key=lambda c: c["published"] or "", reverse=True)
    out = ROOT / "data" / "candidates" / f"{today}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "date": today, "generated_at": dt.datetime.now(TZ).isoformat(timespec="minutes"),
        "window_days": a.days, "youtube_api": bool(key), "sources": report, "items": candidates,
    }, ensure_ascii=False, indent=1))
    print("wrote", out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
