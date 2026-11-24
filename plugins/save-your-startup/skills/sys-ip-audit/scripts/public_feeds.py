#!/usr/bin/env python3
"""Index your public writing, and date public posts from their IDs. Free: public feeds only, no keys.

    # Any RSS or Atom feed: Substack (<site>/feed), Ghost (<site>/rss/), Medium (medium.com/feed/@you),
    # Paragraph, WordPress (<site>/feed/), a personal site.
    python3 -I public_feeds.py feed https://example.substack.com/feed --keyword inventory \
        --out data/feed-blog-2026-11-24.json

    # A full Substack archive (a feed only carries the latest posts). Pages with a cursor; stops cleanly on a
    # rate limit and saves what it has, marked incomplete. Rerun later.
    python3 -I public_feeds.py substack-archive https://example.substack.com --out data/substack-2026-11-24.json

    # Date a post from its link alone.
    python3 -I public_feeds.py decode-id x 1649393986899959813
    python3 -I public_feeds.py decode-id linkedin 7130000000000000000

    # Print a Markdown table for the ledger, optionally only posts mentioning a keyword.
    python3 -I public_feeds.py render data/feed-blog-2026-11-24.json --keyword inventory

Output JSON: {"source", "fetched", "complete", "items": [{date, title, url, words, summary, hits}]}.
Em and en dashes are swapped for plain punctuation so the text can go straight into a document.
Python standard library only.
"""
import argparse
import datetime as dt
import email.utils
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

UA = {"User-Agent": "ip-audit-skill/1.0 (public feed reader)"}
X_EPOCH_MS = 1288834974657
ATOM = "{http://www.w3.org/2005/Atom}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"


class RateLimited(Exception):
    pass


def dashless(text):
    """Swap em and en dashes for plain punctuation, so the text can go straight into a document."""
    en, em = chr(0x2013), chr(0x2014)
    text = re.sub(r"(?<=\d)" + en + r"(?=\d)", "-", text or "")
    return re.sub(r"\s*[" + en + em + r"]\s*", ", ", text)


def plain(markup):
    """Visible text from an HTML fragment, whitespace collapsed."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", markup or ""))
    return re.sub(r"\s+", " ", dashless(text)).strip()


def iso_day(value):
    """YYYY-MM-DD from an RFC 822 date (RSS) or an ISO 8601 date (Atom, JSON APIs); '' if unparseable."""
    value = (value or "").strip()
    if not value:
        return ""
    try:
        return email.utils.parsedate_to_datetime(value).date().isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    m = re.match(r"(\d{4}-\d{2}-\d{2})", value)
    return m.group(1) if m else ""


def keyword_hits(text, keywords):
    low = (text or "").lower()
    return {k: low.count(k.lower()) for k in keywords or []}


def item(date, title, url, body, summary, keywords):
    body_text = plain(body)
    summary_text = plain(summary) or " ".join(re.split(r"(?<=[.!?])\s+", body_text)[:2])
    return {
        "date": date,
        "title": plain(title),
        "url": (url or "").strip(),
        "words": len(body_text.split()) if body_text else 0,
        "summary": summary_text[:220],
        "hits": keyword_hits(" ".join([plain(title), summary_text, body_text]), keywords),
    }


def parse_feed(data, keywords=None):
    """Items from RSS 2.0 or Atom bytes, newest first."""
    root = ET.fromstring(data)
    items = []
    if root.tag == f"{ATOM}feed":
        for e in root.findall(f"{ATOM}entry"):
            link = ""
            for ln in e.findall(f"{ATOM}link"):
                if ln.get("rel", "alternate") == "alternate":
                    link = ln.get("href", "")
                    break
            date = iso_day(e.findtext(f"{ATOM}published") or e.findtext(f"{ATOM}updated"))
            body = e.findtext(f"{ATOM}content") or ""
            items.append(item(date, e.findtext(f"{ATOM}title"), link, body, e.findtext(f"{ATOM}summary"), keywords))
    else:
        channel = root.find("channel")
        for e in (channel.findall("item") if channel is not None else []):
            body = e.findtext(CONTENT) or ""
            desc = e.findtext("description") or ""
            items.append(item(iso_day(e.findtext("pubDate")), e.findtext("title"), e.findtext("link"),
                              body or desc, desc if body else "", keywords))
    items.sort(key=lambda r: r["date"], reverse=True)
    return items


def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise RateLimited(url) from e
        raise


def substack_archive(site, keywords=None, get=None, pause=0.5, limit=3000):
    """Every post in a Substack archive, via its public JSON API. Returns (items, complete)."""
    get = get or http_get
    base = site.rstrip("/")
    rows, cursor, complete = [], None, True
    while len(rows) < limit:
        url = f"{base}/api/v1/archive?sort=new&limit=12"
        if cursor:
            url += "&cursor=" + urllib.parse.quote(cursor)
        try:
            data = json.loads(get(url).decode("utf-8"))
        except RateLimited:
            complete = False
            break
        page = data.get("posts", []) if isinstance(data, dict) else data
        if not page:
            break
        for p in page:
            r = item(iso_day(p.get("post_date")), p.get("title"), p.get("canonical_url"),
                     "", p.get("subtitle") or p.get("description") or "", keywords)
            r["words"] = p.get("wordcount") or 0
            r["audience"] = p.get("audience", "")
            rows.append(r)
        cursor = data.get("nextCursor") if isinstance(data, dict) else None
        if not cursor:
            break
        time.sleep(pause)
    return rows, complete


def decode_x(post_id):
    """UTC datetime from an X (Twitter) post ID: a Snowflake ID carries ms since X's epoch in its top bits."""
    ms = (int(post_id) >> 22) + X_EPOCH_MS
    return dt.datetime.fromtimestamp(ms / 1000, tz=dt.timezone.utc)


def decode_linkedin(post_id):
    """UTC datetime from a LinkedIn activity or post ID, read as ms since 1970 in the bits above the lowest 22.

    LinkedIn doesn't document this. It's a rule of thumb used by third-party date tools, so check the result
    against the date shown on the post before relying on it.
    """
    ms = int(post_id) >> 22
    return dt.datetime.fromtimestamp(ms / 1000, tz=dt.timezone.utc)


def post_id_from(text):
    """The numeric ID from a pasted link or a bare number."""
    m = re.search(r"(\d{15,20})", text or "")
    if not m:
        raise ValueError(f"no post ID found in {text!r}")
    return m.group(1)


def render(doc, keywords=None):
    lines = ["| Date | Title | Summary |", "|---|---|---|"]
    for r in doc.get("items", []):
        text = " ".join([r.get("title", ""), r.get("summary", "")]).lower()
        if keywords and not any(k.lower() in text or r.get("hits", {}).get(k) for k in keywords):
            continue
        title = r.get("title", "").replace("|", "/")
        summary = r.get("summary", "").replace("|", "/")
        lines.append(f"| {r.get('date', '')} | [{title}]({r.get('url', '')}) | {summary} |")
    if not doc.get("complete", True):
        lines.append("")
        lines.append("Incomplete: the source rate-limited the fetch. Rerun later for the rest.")
    return "\n".join(lines)


def write_json(path, doc):
    if os.path.exists(path):
        raise SystemExit(f"{path} already exists; pick a new dated name. Nothing was written.")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Index public writing and date public posts.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("feed", help="read an RSS or Atom feed")
    f.add_argument("url")
    f.add_argument("--keyword", action="append")
    f.add_argument("--out", required=True)
    s = sub.add_parser("substack-archive", help="page through a whole Substack archive")
    s.add_argument("site")
    s.add_argument("--keyword", action="append")
    s.add_argument("--out", required=True)
    d = sub.add_parser("decode-id", help="date a post from its ID or link")
    d.add_argument("network", choices=["x", "linkedin"])
    d.add_argument("id")
    r = sub.add_parser("render", help="print a Markdown table from a saved index")
    r.add_argument("path")
    r.add_argument("--keyword", action="append")
    args = ap.parse_args(argv)
    today = dt.date.today().isoformat()

    if args.cmd == "feed":
        items = parse_feed(http_get(args.url), args.keyword)
        write_json(args.out, {"source": args.url, "fetched": today, "complete": True, "items": items})
        span = f", {items[-1]['date']} to {items[0]['date']}" if items else ""
        print(f"{len(items)} items{span} -> {args.out}")
        print("A feed carries only recent posts. For a full Substack archive, use substack-archive.")
    elif args.cmd == "substack-archive":
        items, complete = substack_archive(args.site, args.keyword)
        write_json(args.out, {"source": args.site, "fetched": today, "complete": complete, "items": items})
        print(f"{len(items)} posts -> {args.out}")
        if not complete:
            print("Stopped at a rate limit (HTTP 429). Saved what it had, marked incomplete. Rerun later.")
    elif args.cmd == "decode-id":
        when = (decode_x if args.network == "x" else decode_linkedin)(post_id_from(args.id))
        print(when.strftime("%Y-%m-%d %H:%M:%S UTC"))
        if args.network == "linkedin":
            print("LinkedIn doesn't document this rule; check it against the date shown on the post.",
                  file=sys.stderr)
    elif args.cmd == "render":
        with open(args.path, encoding="utf-8") as fh:
            print(render(json.load(fh), args.keyword))
    return 0


if __name__ == "__main__":
    sys.exit(main())
