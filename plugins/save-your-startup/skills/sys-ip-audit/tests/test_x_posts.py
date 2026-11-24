"""Offline tests for scripts/x_posts.py. Nothing here calls X: the HTTP layer is replaced by a fake that fails
the test if it is called when it shouldn't be.

Run from the skill folder:  python3 -m unittest discover -s tests -v
"""
import contextlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("x_posts", SKILL / "scripts" / "x_posts.py")
xp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(xp)


def never_called(url, token):
    raise AssertionError("the X API was called without approval")


class Queries(unittest.TestCase):
    def test_single_query(self):
        self.assertEqual(xp.build_queries("@jordan_dev", ["inventory", "demand forecasting"]),
                         ['from:jordan_dev (inventory OR "demand forecasting") -is:retweet'])

    def test_no_keywords_and_no_replies(self):
        self.assertEqual(xp.build_queries("jordan_dev", [], include_replies=False),
                         ["from:jordan_dev -is:retweet -is:reply"])

    def test_hyphenated_term_is_quoted(self):
        self.assertIn('"just-in-time"', xp.build_queries("j", ["just-in-time"])[0])

    def test_splits_long_queries(self):
        words = [f"keyword{i:02d}" for i in range(40)]
        queries = xp.build_queries("jordan_dev", words, max_chars=120)
        self.assertGreater(len(queries), 1)
        self.assertTrue(all(len(q) <= 120 for q in queries))
        joined = " ".join(queries)
        self.assertTrue(all(w in joined for w in words))

    def test_empty_handle(self):
        with self.assertRaises(ValueError):
            xp.build_queries("@", ["x"])

    def test_worst_case(self):
        self.assertEqual(xp.worst_case(["a", "b"], 200, 0.005), (400, 2.0))


class Approval(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "data", "x-posts.jsonl")
        self.ledger = os.path.join(self.tmp.name, "data", "ledger.jsonl")
        self.base = ["--handle", "jordan_dev", "--keyword", "inventory", "--out", self.out, "--ledger", self.ledger]

    def tearDown(self):
        self.tmp.cleanup()

    def call(self, extra, env=None):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(xp, "http_get_json", never_called), \
                mock.patch.dict(os.environ, env or {"X_BEARER_TOKEN": "t0ken"}), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = xp.main(self.base + extra)
        return code, out.getvalue(), err.getvalue()

    def test_no_approval_sends_nothing_and_exits_3(self):
        code, out, err = self.call([])
        self.assertEqual(code, xp.NEEDS_APPROVAL)
        self.assertIn("$1.00", out)
        self.assertIn("--approve-up-to 1.00", err)
        self.assertFalse(os.path.exists(self.out))
        self.assertFalse(os.path.exists(self.ledger))

    def test_dry_run_sends_nothing(self):
        code, out, _ = self.call(["--dry-run"])
        self.assertEqual(code, 0)
        self.assertIn("from:jordan_dev", out)
        self.assertFalse(os.path.exists(self.ledger))

    def test_zero_approval_refused(self):
        code, _, _ = self.call(["--approve-up-to", "0"])
        self.assertEqual(code, xp.NEEDS_APPROVAL)

    def test_missing_token_sends_nothing(self):
        code, _, err = self.call(["--approve-up-to", "1"], env={"X_BEARER_TOKEN": ""})
        self.assertEqual(code, 1)
        self.assertIn("not set", err)

    def test_token_never_printed(self):
        _, out, err = self.call(["--dry-run"])
        self.assertNotIn("t0ken", out + err)

    def test_max_posts_floor(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            xp.main(self.base + ["--max-posts", "5", "--dry-run"])


class Spending(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "posts.jsonl")
        self.ledger = os.path.join(self.tmp.name, "ledger.jsonl")

    def tearDown(self):
        self.tmp.cleanup()

    def fake(self, per_page):
        calls = []

        def get(url, token):
            calls.append(url)
            n = len(calls)
            return {"data": [{"id": f"{n}-{i}", "text": "inventory"} for i in range(per_page)],
                    "meta": {"next_token": f"t{n}"}}
        return get, calls

    def test_stops_before_a_page_that_could_pass_the_cap(self):
        get, calls = self.fake(100)
        spend = xp.Spend(0.75, 0.005, self.ledger)
        with contextlib.redirect_stdout(io.StringIO()):
            n = xp.run(["q"], endpoint="all", since="2022-01-01", until=None, max_posts=500, spend=spend,
                       out_path=self.out, token="t", get=get, pause=0)
        self.assertEqual(len(calls), 1)  # a second page of 100 would reach $1.00, past the $0.75 cap
        self.assertEqual(n, 100)
        self.assertAlmostEqual(spend.total, 0.50)
        lines = [json.loads(x) for x in Path(self.ledger).read_text().splitlines()]
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["running_usd"], 0.5)
        self.assertIn("start_time=2022-01-01", calls[0])

    def test_per_query_cap_never_overshoots(self):
        get, calls = self.fake(100)
        spend = xp.Spend(100, 0.005, self.ledger)
        with contextlib.redirect_stdout(io.StringIO()):
            n = xp.run(["q"], endpoint="all", since=None, until=None, max_posts=205, spend=spend,
                       out_path=self.out, token="t", get=get, pause=0)
        self.assertEqual(len(calls), 2)  # 100 + 100, then 5 left is under X's 10-post minimum page
        self.assertEqual(n, 200)

    def test_charges_only_for_posts_returned(self):
        def get(url, token):
            return {"data": [{"id": "1"}, {"id": "2"}], "meta": {}}
        spend = xp.Spend(5, 0.005, self.ledger)
        with contextlib.redirect_stdout(io.StringIO()):
            xp.run(["q1", "q2"], endpoint="recent", since=None, until=None, max_posts=100, spend=spend,
                   out_path=self.out, token="t", get=get, pause=0)
        self.assertAlmostEqual(spend.total, 0.02)
        self.assertEqual(len(Path(self.out).read_text().splitlines()), 2)  # duplicates across queries dropped

    def test_main_end_to_end_with_approval(self):
        get, calls = self.fake(10)
        args = ["--handle", "jordan_dev", "--keyword", "inventory", "--out", self.out, "--ledger", self.ledger,
                "--max-posts", "20", "--approve-up-to", "0.10"]
        with mock.patch.object(xp, "http_get_json", get), mock.patch.dict(os.environ, {"X_BEARER_TOKEN": "t"}), \
                mock.patch.object(xp.time, "sleep"), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(xp.main(args), 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(len(Path(self.out).read_text().splitlines()), 20)


if __name__ == "__main__":
    unittest.main()
