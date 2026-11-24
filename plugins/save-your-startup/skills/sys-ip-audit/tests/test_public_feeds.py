"""Offline tests for scripts/public_feeds.py. Feeds are inline bytes and HTTP is a fake; no network.

Run from the skill folder:  python3 -m unittest discover -s tests -v
"""
import datetime as dt
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("public_feeds", SKILL / "scripts" / "public_feeds.py")
pf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pf)

RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
<channel><title>Jordan writes</title>
<item><title>Forecasting perishables \u2014 part 1</title><link>https://jordan.example.com/p/forecast-1</link>
<pubDate>Tue, 14 Jun 2022 15:04:05 GMT</pubDate><description>Why stock spoils.</description>
<content:encoded><![CDATA[<p>Inventory for restaurants spoils. Forecasting helps.</p>]]></content:encoded></item>
<item><title>Hiking notes</title><link>https://jordan.example.com/p/hike</link>
<pubDate>Sat, 01 Jul 2023 08:00:00 +0000</pubDate><description>&lt;p&gt;Trails.&lt;/p&gt;</description></item>
</channel></rss>""".encode("utf-8")

ATOM = b"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>Jordan</title>
<entry><title>Reorder points</title><link rel="alternate" href="https://jordan.example.com/reorder"/>
<link rel="edit" href="https://jordan.example.com/edit/1"/>
<published>2021-11-03T10:00:00Z</published><summary>Reorder points for inventory.</summary>
<content type="html">&lt;p&gt;Long body about inventory.&lt;/p&gt;</content></entry>
</feed>"""


class Feeds(unittest.TestCase):
    def test_rss(self):
        items = pf.parse_feed(RSS, ["inventory"])
        self.assertEqual([i["date"] for i in items], ["2023-07-01", "2022-06-14"])
        first = items[1]
        self.assertEqual(first["title"], "Forecasting perishables, part 1")
        self.assertNotIn("\u2014", json.dumps(items, ensure_ascii=False))
        self.assertEqual(first["url"], "https://jordan.example.com/p/forecast-1")
        self.assertEqual(first["summary"], "Why stock spoils.")
        self.assertEqual(first["hits"], {"inventory": 1})
        self.assertGreater(first["words"], 0)
        self.assertEqual(items[0]["summary"], "Trails.")

    def test_atom_prefers_alternate_link(self):
        (entry,) = pf.parse_feed(ATOM, ["inventory"])
        self.assertEqual(entry["url"], "https://jordan.example.com/reorder")
        self.assertEqual(entry["date"], "2021-11-03")
        self.assertEqual(entry["hits"]["inventory"], 2)

    def test_iso_day(self):
        self.assertEqual(pf.iso_day("Tue, 14 Jun 2022 15:04:05 GMT"), "2022-06-14")
        self.assertEqual(pf.iso_day("2024-02-29T23:00:00.000Z"), "2024-02-29")
        self.assertEqual(pf.iso_day("not a date"), "")
        self.assertEqual(pf.iso_day(None), "")


class SubstackArchive(unittest.TestCase):
    def test_pages_by_cursor_and_stops_cleanly_on_rate_limit(self):
        pages = [
            {"posts": [{"title": "A", "post_date": "2025-05-01T00:00:00Z", "canonical_url": "u/a",
                        "subtitle": "about inventory", "wordcount": 900, "audience": "everyone"}],
             "nextCursor": "c1"},
            {"posts": [{"title": "B", "post_date": "2024-01-01T00:00:00Z", "canonical_url": "u/b"}],
             "nextCursor": "c2"},
        ]
        calls = []

        def fake_get(url):
            calls.append(url)
            if len(calls) > len(pages):
                raise pf.RateLimited(url)
            return json.dumps(pages[len(calls) - 1]).encode()

        items, complete = pf.substack_archive("https://x.substack.com/", ["inventory"], get=fake_get, pause=0)
        self.assertFalse(complete)
        self.assertEqual([i["title"] for i in items], ["A", "B"])
        self.assertEqual(items[0]["words"], 900)
        self.assertIn("cursor=c1", calls[1])
        self.assertNotIn("offset", calls[0])

    def test_complete_when_no_cursor(self):
        items, complete = pf.substack_archive(
            "https://x.substack.com", get=lambda url: json.dumps({"posts": [{"title": "Only"}]}).encode(), pause=0)
        self.assertTrue(complete)
        self.assertEqual(len(items), 1)


class PostIds(unittest.TestCase):
    def test_x_round_trip(self):
        when = dt.datetime(2023, 4, 21, 14, 30, tzinfo=dt.timezone.utc)
        ms = int(when.timestamp() * 1000)
        post_id = ((ms - pf.X_EPOCH_MS) << 22) | 12345
        self.assertEqual(pf.decode_x(post_id), when)

    def test_x_known_public_post(self):
        # Michael Girdley's MOU thread (credited in sys:mou) is dated April 21, 2023.
        self.assertEqual(pf.decode_x(1649393986899959813).date(), dt.date(2023, 4, 21))

    def test_linkedin_round_trip(self):
        when = dt.datetime(2023, 12, 6, 20, 13, 58, tzinfo=dt.timezone.utc)
        post_id = (int(when.timestamp() * 1000) << 22) | 777
        self.assertEqual(pf.decode_linkedin(post_id), when)

    def test_id_from_link(self):
        self.assertEqual(pf.post_id_from("https://x.com/girdley/status/1649393986899959813?s=20"),
                         "1649393986899959813")
        self.assertEqual(pf.post_id_from("urn:li:activity:7138259296076619777"), "7138259296076619777")
        with self.assertRaises(ValueError):
            pf.post_id_from("https://example.com/no-id")


class Render(unittest.TestCase):
    def test_filters_and_flags_incomplete(self):
        doc = {"complete": False, "items": pf.parse_feed(RSS, ["inventory"])}
        out = pf.render(doc, ["inventory"])
        self.assertIn("forecast-1", out)
        self.assertNotIn("Hiking", out)
        self.assertIn("Incomplete", out)

    def test_write_json_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "feed.json")
            pf.write_json(path, {"items": []})
            with self.assertRaises(SystemExit):
                pf.write_json(path, {"items": [1]})
            self.assertEqual(json.load(open(path)), {"items": []})


if __name__ == "__main__":
    unittest.main()
