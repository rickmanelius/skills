"""Offline tests for scripts/session_prompts.py. Builds a fake ~/.claude/projects tree; no network.

Run from the skill folder:  python3 -m unittest discover -s tests -v
"""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("session_prompts", SKILL / "scripts" / "session_prompts.py")
sp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sp)

GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def user(text, ts="2026-03-02T10:00:00Z", **extra):
    return {"type": "user", "timestamp": ts, "sessionId": "s1", "cwd": "/home/jordan/code/acme",
            "message": {"role": "user", "content": text}, **extra}


RECORDS = [
    user("Sketch an inventory forecast for perishables", ts="2026-01-05T09:00:00Z"),
    user([{"type": "text", "text": "<system-reminder>ignore me</system-reminder>Add a reorder alert"}],
         ts="2026-02-10T09:00:00Z"),
    user([{"type": "tool_result", "content": "tool output"}]),
    user("meta line", isMeta=True),
    user("summary of earlier conversation", isCompactSummary=True),
    user("<command-name>/clear</command-name>"),
    user("<task-notification>done</task-notification>"),
    {"type": "assistant", "timestamp": "2026-02-10T09:01:00Z", "message": {"role": "assistant", "content": "ok"}},
    user("Draft the pricing page", ts="2026-04-01T09:00:00Z"),
]


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name, "projects")
        folder = self.root / "-home-jordan-code-acme"
        folder.mkdir(parents=True)
        with open(folder / "s1.jsonl", "w", encoding="utf-8") as f:
            for r in RECORDS:
                f.write(json.dumps(r) + "\n")
            f.write("not json\n")
        sub = folder / "s1" / "subagents"
        sub.mkdir(parents=True)
        (sub / "agent.jsonl").write_text(json.dumps(user("agent prompt, not yours")) + "\n")
        other = self.root / "-home-jordan-code-other"
        other.mkdir()
        (other / "s2.jsonl").write_text(json.dumps(user("unrelated inventory prompt")) + "\n")

    def tearDown(self):
        self.tmp.cleanup()

    def texts(self, **kw):
        return [r["text"] for r in sp.iter_prompts(str(self.root), kw.pop("folders", ["*acme*"]), **kw)]


class Extraction(Fixture):
    def test_keeps_only_typed_prompts(self):
        self.assertEqual(self.texts(), ["Sketch an inventory forecast for perishables", "Add a reorder alert",
                                        "Draft the pricing page"])

    def test_skips_subagent_logs_and_other_folders(self):
        self.assertNotIn("agent prompt, not yours", self.texts(folders=["*"]))
        self.assertIn("unrelated inventory prompt", self.texts(folders=["*"]))

    def test_keyword_filter_is_case_insensitive(self):
        self.assertEqual(self.texts(keywords=["INVENTORY", "reorder"]),
                         ["Sketch an inventory forecast for perishables", "Add a reorder alert"])

    def test_date_window(self):
        self.assertEqual(self.texts(since="2026-02-01", until="2026-03-31"), ["Add a reorder alert"])

    def test_row_shape(self):
        row = next(sp.iter_prompts(str(self.root), ["*acme*"]))
        self.assertEqual(set(row), {"ts", "folder", "session", "cwd", "text"})
        self.assertEqual(row["folder"], "-home-jordan-code-acme")


class Main(Fixture):
    def test_writes_jsonl(self):
        out = Path(self.tmp.name, "private", "prompts.jsonl")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
                mock.patch.dict(os.environ, GIT_ENV):
            code = sp.main(["--projects", str(self.root), "--folder", "*acme*", "--out", str(out)])
        self.assertEqual(code, 0)
        self.assertEqual(len(out.read_text().splitlines()), 3)

    def test_no_text_keeps_dates_and_keywords_only(self):
        out = Path(self.tmp.name, "private", "dates-only.jsonl")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
                mock.patch.dict(os.environ, GIT_ENV):
            code = sp.main(["--projects", str(self.root), "--folder", "*acme*", "--keyword", "Inventory",
                            "--no-text", "--out", str(out)])
        self.assertEqual(code, 0)
        rows = [json.loads(x) for x in out.read_text().splitlines()]
        self.assertEqual(len(rows), 1)
        self.assertNotIn("text", rows[0])
        self.assertNotIn("perishables", out.read_text())
        self.assertEqual(rows[0]["keywords"], ["Inventory"])
        self.assertEqual(rows[0]["chars"], len("Sketch an inventory forecast for perishables"))
        self.assertEqual(rows[0]["ts"], "2026-01-05T09:00:00Z")

    def test_refuses_repo_with_remote(self):
        repo = Path(self.tmp.name, "public-repo")
        with mock.patch.dict(os.environ, GIT_ENV):
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", "https://example.com/r.git"],
                           check=True)
            out = repo / "data" / "prompts.jsonl"
            err = io.StringIO()
            with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sp.main(["--projects", str(self.root), "--out", str(out)]), 2)
            self.assertFalse(out.exists())
            self.assertIn("has a remote", err.getvalue())
            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(sp.main(["--projects", str(self.root), "--out", str(out), "--force-location"]), 0)
            self.assertTrue(out.exists())

    def test_refuses_to_overwrite(self):
        out = Path(self.tmp.name, "prompts.jsonl")
        out.write_text("keep")
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(sp.main(["--projects", str(self.root), "--out", str(out)]), 2)
        self.assertEqual(out.read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
