#!/usr/bin/env python3
"""Your own public X posts in the counterparty's field, as dated evidence. PAID: the X API bills per post read.

    # 1. Free: see the queries and the worst-case cost. Sends nothing.
    python3 -I x_posts.py --handle jordan_dev --keyword inventory --keyword "demand forecasting" \
        --since 2022-01-01 --out data/x-posts-2026-11-24.jsonl --dry-run

    # 2. Only after the user approves a dollar amount in conversation:
    python3 -I x_posts.py --handle jordan_dev --keyword inventory --keyword "demand forecasting" \
        --since 2022-01-01 --out data/x-posts-2026-11-24.jsonl --approve-up-to 2.00

Without --approve-up-to it prints the quote, sends nothing and exits with status 3. With it, every page is
checked against the cap before it's requested: a page that could push spend past the cap is never sent. Each
charge is appended to the spend ledger (default data/x-spend-ledger.jsonl) with a running total. No expansions
are requested, so referenced posts are never billed.

The price per post read changes; check the X developer pricing page and pass --price if it differs from the
default. The token comes from the X_BEARER_TOKEN environment variable (or the one named by --token-env) and is
never printed or written anywhere.

Python standard library only.
"""
import argparse
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

NEEDS_APPROVAL = 3
DEFAULT_PRICE = 0.005  # USD per post read, pay-per-use, as of late 2026; check before relying on it
FIELDS = "created_at,conversation_id,in_reply_to_user_id,referenced_tweets,public_metrics,entities,note_tweet"
ENDPOINTS = {
    "all": ("https://api.x.com/2/tweets/search/all", 500),
    "recent": ("https://api.x.com/2/tweets/search/recent", 100),
}
UA = "ip-audit-skill/1.0"


def term(word):
    word = word.strip().replace('"', "")
    return f'"{word}"' if " " in word or "-" in word else word


def build_queries(handle, keywords, max_chars=512, include_replies=True):
    """X search queries for one handle's own posts, split so none is longer than max_chars."""
    handle = handle.lstrip("@").strip()
    if not handle:
        raise ValueError("a handle is needed")
    tail = " -is:retweet" + ("" if include_replies else " -is:reply")
    head = f"from:{handle}"
    terms = [term(k) for k in keywords if k.strip()]
    if not terms:
        return [head + tail]
    queries, group = [], []
    for t in terms:
        trial = f"{head} ({' OR '.join(group + [t])}){tail}"
        if group and len(trial) > max_chars:
            queries.append(f"{head} ({' OR '.join(group)}){tail}")
            group = [t]
        else:
            group.append(t)
    single = f"{head} ({' OR '.join(group)}){tail}"
    if len(single) > max_chars:
        raise ValueError(f"one keyword makes a query longer than {max_chars} characters: {group[-1]}")
    queries.append(single)
    return queries


def worst_case(queries, max_posts, price):
    posts = len(queries) * max_posts
    return posts, posts * price


class Spend:
    def __init__(self, cap, price, ledger_path):
        self.cap, self.price, self.ledger_path, self.total = cap, price, ledger_path, 0.0

    def allows(self, posts):
        return self.total + posts * self.price <= self.cap + 1e-9

    def charge(self, label, posts):
        cost = posts * self.price
        self.total += cost
        os.makedirs(os.path.dirname(os.path.abspath(self.ledger_path)), exist_ok=True)
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "call": label, "posts": posts,
                                "usd": round(cost, 4), "running_usd": round(self.total, 4)}) + "\n")


def http_get_json(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "User-Agent": UA})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                time.sleep(2 ** attempt * 5)
                continue
            body = e.read().decode("utf-8", "replace")[:300]
            raise SystemExit(f"HTTP {e.code} from {url.split('?')[0]}: {body}")
    raise SystemExit("X kept refusing (rate limit or server error); stopped. Nothing more was requested.")


def run(queries, *, endpoint, since, until, max_posts, spend, out_path, token, get=None, pause=1.2):
    get = get or http_get_json
    url, page_max = ENDPOINTS[endpoint]
    seen = set()
    with open(out_path, "w", encoding="utf-8") as out:
        for qi, q in enumerate(queries, 1):
            got, next_token, pages = 0, None, 0
            while got < max_posts:
                size = min(100, page_max, max_posts - got)
                if size < 10:  # X's smallest page is 10; asking for it would pass the per-query cap
                    break
                if not spend.allows(size):
                    print(f"[query {qi}] stopped: the next page could pass the ${spend.cap:.2f} cap")
                    break
                params = {"query": q, "max_results": size, "tweet.fields": FIELDS, "sort_order": "recency"}
                if since:
                    params["start_time"] = f"{since}T00:00:00Z"
                if until:
                    params["end_time"] = f"{until}T23:59:59Z"
                if next_token:
                    params["next_token"] = next_token
                data = get(url + "?" + urllib.parse.urlencode(params), token)
                rows = data.get("data", []) or []
                pages += 1
                spend.charge(f"search:q{qi}:p{pages}", len(rows))
                got += len(rows)
                for t in rows:
                    if t.get("id") in seen:
                        continue
                    seen.add(t.get("id"))
                    t["_query"] = qi
                    out.write(json.dumps(t, ensure_ascii=False) + "\n")
                next_token = (data.get("meta") or {}).get("next_token")
                if not next_token:
                    break
                time.sleep(pause)
            more = " (more exist; per-query cap reached)" if next_token and got >= max_posts else ""
            print(f"[query {qi}] {got} posts in {pages} pages{more}")
    return len(seen)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Your own X posts in a field, as dated evidence. Paid.")
    ap.add_argument("--handle", required=True, help="your X handle, with or without @")
    ap.add_argument("--keyword", action="append", default=[], help="a term from the counterparty's field (repeatable)")
    ap.add_argument("--since", help="YYYY-MM-DD; the full-archive search starts here")
    ap.add_argument("--until", help="YYYY-MM-DD")
    ap.add_argument("--endpoint", choices=sorted(ENDPOINTS), default="all",
                    help="'all' searches the full archive; 'recent' only the last 7 days")
    ap.add_argument("--max-posts", type=int, default=200, help="cap per query (default 200)")
    ap.add_argument("--max-query-chars", type=int, default=512, help="split queries longer than this (default 512)")
    ap.add_argument("--no-replies", action="store_true", help="skip your replies to others")
    ap.add_argument("--price", type=float, default=DEFAULT_PRICE, help=f"USD per post read (default {DEFAULT_PRICE})")
    ap.add_argument("--out", required=True, help="JSON-lines file for the posts (refuses to overwrite)")
    ap.add_argument("--ledger", default="data/x-spend-ledger.jsonl", help="spend ledger, appended to")
    ap.add_argument("--token-env", default="X_BEARER_TOKEN", help="environment variable holding the bearer token")
    ap.add_argument("--dry-run", action="store_true", help="print the queries and the quote; send nothing")
    ap.add_argument("--approve-up-to", type=float, help="USD the user approved for this run")
    args = ap.parse_args(argv)
    if args.max_posts < 10:
        ap.error("--max-posts must be at least 10 (X's smallest page)")

    queries = build_queries(args.handle, args.keyword, args.max_query_chars, not args.no_replies)
    posts, cost = worst_case(queries, args.max_posts, args.price)
    print(f"{len(queries)} queries, up to {args.max_posts} posts each: at most {posts} posts, "
          f"${cost:.2f} at ${args.price} per post. Window: {args.since or 'all time'} to {args.until or 'now'}.")
    for i, q in enumerate(queries, 1):
        print(f"  [query {i}] {q}")

    if args.dry_run:
        print("Dry run: nothing was sent.")
        return 0
    if args.approve_up_to is None:
        print(f"Nothing was sent: this costs money. Show the user the quote above; if they approve an amount, run "
              f"the same command again with --approve-up-to {math.ceil(cost * 100) / 100:.2f} (or less, to stop "
              "early).", file=sys.stderr)
        return NEEDS_APPROVAL
    if args.approve_up_to <= 0:
        print("--approve-up-to must be more than zero. Nothing was sent.", file=sys.stderr)
        return NEEDS_APPROVAL
    if os.path.exists(args.out):
        print(f"{args.out} already exists; pick a new dated name. Nothing was sent.", file=sys.stderr)
        return 2
    token = os.environ.get(args.token_env, "")
    if not token:
        print(f"{args.token_env} is not set. Nothing was sent.", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    spend = Spend(args.approve_up_to, args.price, args.ledger)
    n = run(queries, endpoint=args.endpoint, since=args.since, until=args.until, max_posts=args.max_posts,
            spend=spend, out_path=args.out, token=token)
    print(f"{n} unique posts -> {args.out}; spent ${spend.total:.2f} of ${args.approve_up_to:.2f} approved "
          f"(ledger: {args.ledger})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
