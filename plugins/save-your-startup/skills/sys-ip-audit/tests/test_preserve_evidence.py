"""Offline tests for scripts/preserve_evidence.py. Temporary folders and throwaway git repositories; no network.

Run from the skill folder:  python3 -m unittest discover -s tests -v
"""
import contextlib
import hashlib
import importlib.util
import io
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("preserve_evidence", SKILL / "scripts" / "preserve_evidence.py")
pe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pe)

GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Fixture(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        self.notes = t / "notes"
        (self.notes / "client-logistics").mkdir(parents=True)
        (self.notes / "acme").mkdir()
        (self.notes / "acme" / "call-2026-03-02.md").write_text("first demo notes")
        (self.notes / "acme" / "ideas.md").write_text("reorder alerts")
        (self.notes / "client-logistics" / "secret.md").write_text("client material")
        (self.notes / ".env").write_text("TOKEN=x")
        (self.notes / "link.md").symlink_to(t / "outside.md")
        (t / "outside.md").write_text("not mine to keep")
        self.dest = t / "evidence"
        self.env = mock.patch.dict(os.environ, GIT_ENV)
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def run_main(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = pe.main(args)
        return code, out.getvalue(), err.getvalue()


class Planning(Fixture):
    def test_excluded_matches_any_path_part(self):
        self.assertTrue(pe.excluded("client-logistics/secret.md", ["*client-logistics*"]))
        self.assertTrue(pe.excluded("a/b/.env", ["*.env"]))
        self.assertFalse(pe.excluded("acme/ideas.md", ["*client*"]))

    def test_plan_skips_excluded_and_links(self):
        to_copy, skipped = pe.plan_copy(str(self.notes), ["*client-logistics*", ".env"])
        self.assertEqual(sorted(to_copy), ["acme/call-2026-03-02.md", "acme/ideas.md"])
        self.assertIn("client-logistics/", skipped)
        self.assertIn(".env", skipped)
        self.assertIn("link.md", skipped)

    def test_single_file_source(self):
        to_copy, _ = pe.plan_copy(str(self.notes / "acme" / "ideas.md"), [])
        self.assertEqual(to_copy, ["ideas.md"])


class Run(Fixture):
    def test_copies_hashes_and_never_touches_the_source(self):
        before = {p: p.read_bytes() for p in self.notes.rglob("*") if p.is_file() and not p.is_symlink()}
        code, out, _ = self.run_main(["--source", str(self.notes), "--exclude", "*client-logistics*",
                                      "--exclude", ".env", "--dest", str(self.dest)])
        self.assertEqual(code, 0)
        after = {p: p.read_bytes() for p in self.notes.rglob("*") if p.is_file() and not p.is_symlink()}
        self.assertEqual(before, after)

        (folder,) = list(self.dest.iterdir())
        copied = sorted(str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file())
        self.assertEqual(copied, ["MANIFEST.sha256", "files/notes/acme/call-2026-03-02.md",
                                  "files/notes/acme/ideas.md"])

        manifest = (folder / "MANIFEST.sha256").read_text().splitlines()
        self.assertEqual(len(manifest), 2)
        for line in manifest:
            digest, rel = line.split("  ", 1)
            self.assertEqual(digest, sha(folder / rel))
        printed = re.search(r"Manifest hash \(email this to your lawyer\): ([0-9a-f]{64})", out).group(1)
        self.assertEqual(printed, sha(folder / "MANIFEST.sha256"))

    def test_bundles_a_repository(self):
        repo = Path(self.tmp.name, "lib")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        (repo / "a.txt").write_text("a")
        subprocess.run(["git", "-C", str(repo), "add", "a.txt"], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=J", "-c", "user.email=j@example.com",
                        "-c", "commit.gpgsign=false", "commit", "-q", "-m", "first"], check=True)
        code, _, _ = self.run_main(["--bundle-repo", str(repo), "--dest", str(self.dest)])
        self.assertEqual(code, 0)
        (folder,) = list(self.dest.iterdir())
        self.assertTrue((folder / "bundles" / "lib.bundle").stat().st_size > 0)
        self.assertIn("first", (folder / "bundles" / "lib-log.txt").read_text())
        self.assertIn("./bundles/lib.bundle", (folder / "MANIFEST.sha256").read_text())

    def test_dry_run_copies_nothing(self):
        code, out, _ = self.run_main(["--source", str(self.notes), "--exclude", "*client*", "--dry-run",
                                      "--dest", str(self.dest)])
        self.assertEqual(code, 0)
        self.assertIn("skip client-logistics/", out)
        self.assertFalse(self.dest.exists())

    def test_refuses_destination_in_repo_with_remote(self):
        repo = Path(self.tmp.name, "public")
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        subprocess.run(["git", "-C", str(repo), "remote", "add", "origin", "https://example.com/p.git"], check=True)
        code, _, err = self.run_main(["--source", str(self.notes), "--dest", str(repo / "evidence")])
        self.assertEqual(code, 2)
        self.assertIn("has a remote", err)
        self.assertFalse((repo / "evidence").exists())

    def test_missing_source(self):
        code, _, err = self.run_main(["--source", str(Path(self.tmp.name, "nope")), "--dest", str(self.dest)])
        self.assertEqual(code, 1)
        self.assertFalse(self.dest.exists())

    def test_needs_a_source(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            pe.main(["--dest", str(self.dest)])


if __name__ == "__main__":
    unittest.main()
