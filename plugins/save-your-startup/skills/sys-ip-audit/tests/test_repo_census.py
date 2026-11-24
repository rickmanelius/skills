"""Offline tests for scripts/repo_census.py. Uses throwaway local git repositories; no network.

Run from the skill folder:  python3 -m unittest discover -s tests -v
"""
import contextlib
import csv
import importlib.util
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SKILL = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("repo_census", SKILL / "scripts" / "repo_census.py")
rc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rc)

GIT_ENV = {"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def make_repo(path, commits, remote=None):
    """commits: list of (name, email, YYYY-MM-DD)."""
    os.makedirs(path, exist_ok=True)
    env = {**os.environ, **GIT_ENV}
    subprocess.run(["git", "init", "-q", path], check=True, env=env)
    for i, (name, email, day) in enumerate(commits):
        stamp = f"{day}T12:00:00"
        subprocess.run(["git", "-C", path, "-c", f"user.name={name}", "-c", f"user.email={email}",
                        "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", f"c{i}"],
                       check=True, env={**env, "GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp})
    if remote:
        subprocess.run(["git", "-C", path, "remote", "add", "origin", remote], check=True, env=env)


class Pure(unittest.TestCase):
    def test_clean_remote_strips_credentials(self):
        self.assertEqual(rc.clean_remote("https://jordan:secret123@github.com/j/lib.git"),
                         "https://github.com/j/lib.git")
        self.assertEqual(rc.clean_remote("https://token@gitlab.com/j/lib.git"), "https://gitlab.com/j/lib.git")
        self.assertEqual(rc.clean_remote("git@github.com:j/lib.git"), "git@github.com:j/lib.git")
        self.assertEqual(rc.clean_remote(""), "")

    def test_dashless(self):
        self.assertEqual(rc.dashless("a\u2014b \u2013 c, 2022\u20132023"), "a, b, c, 2022-2023")

    def test_parse_log(self):
        sep = rc.SEP
        log = "\n".join([
            f"2023-03-01{sep}Jordan Avery{sep}jordan@example.com",
            f"2021-06-15{sep}Someone Else{sep}else@example.com",
            f"2025-01-09{sep}J. Avery{sep}jordan@example.com",
            "garbage line",
        ])
        import re
        out = rc.parse_log(log, re.compile("jordan", re.I))
        self.assertEqual(out["commits"], 3)
        self.assertEqual(out["first_commit"], "2021-06-15")
        self.assertEqual(out["last_commit"], "2025-01-09")
        self.assertEqual(out["my_commits"], 2)
        self.assertEqual((out["my_first"], out["my_last"]), ("2023-03-01", "2025-01-09"))

    def test_parse_log_without_author(self):
        out = rc.parse_log(f"2023-03-01{rc.SEP}a{rc.SEP}b", None)
        self.assertEqual(out["my_commits"], 0)

    def test_readme_line_and_dashes(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "README.md").write_text("# Inventory Lib\n\n![badge](x)\nForecasts stock \u2014 fast.\n")
            self.assertEqual(rc.readme_line(d), "Inventory Lib: Forecasts stock, fast.")


class Discovery(unittest.TestCase):
    def test_find_repos_skips_hidden_vendor_and_nested(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, GIT_ENV):
            make_repo(os.path.join(d, "org", "lib"), [])
            make_repo(os.path.join(d, "org", "lib", "inner"), [])  # inside a repo: not listed separately
            make_repo(os.path.join(d, "node_modules", "dep"), [])
            make_repo(os.path.join(d, ".hidden", "x"), [])
            make_repo(os.path.join(d, "a", "b", "c", "d", "e", "deep"), [])
            found = [os.path.relpath(p, d) for p in rc.find_repos(d, depth=4)]
            self.assertEqual(found, [os.path.join("org", "lib")])

    def test_root_that_is_a_repo(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, GIT_ENV):
            make_repo(d, [])
            self.assertEqual(rc.find_repos(d), [os.path.abspath(d)])


class EndToEnd(unittest.TestCase):
    def test_census_csv(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.dict(os.environ, GIT_ENV):
            root = os.path.join(d, "code")
            make_repo(os.path.join(root, "inventory-lib"),
                      [("Jordan Avery", "jordan@example.com", "2023-03-01"),
                       ("Friend", "friend@example.com", "2023-04-01"),
                       ("Jordan Avery", "jordan@example.com", "2024-02-02")],
                      remote="https://jordan:hunter2@github.com/jordan/inventory-lib.git")
            make_repo(os.path.join(root, "someone-elses"), [("Friend", "friend@example.com", "2022-01-01")])
            Path(root, "inventory-lib", "README.md").write_text("# Inventory Lib\nForecasting for perishables.\n")
            out = os.path.join(d, "data", "census.csv")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(rc.main(["--root", root, "--author", "jordan@example", "--out", out]), 0)
            with open(out, encoding="utf-8") as f:
                rows = {r["repo"]: r for r in csv.DictReader(f)}
            lib = rows["inventory-lib"]
            self.assertEqual((lib["commits"], lib["my_commits"]), ("3", "2"))
            self.assertEqual((lib["my_first"], lib["my_last"]), ("2023-03-01", "2024-02-02"))
            self.assertEqual(lib["remote"], "https://github.com/jordan/inventory-lib.git")
            self.assertNotIn("hunter2", Path(out).read_text())
            self.assertEqual(lib["readme"], "Inventory Lib: Forecasting for perishables.")
            self.assertEqual(rows["someone-elses"]["my_commits"], "0")

    def test_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d, "census.csv")
            out.write_text("keep me")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(rc.main(["--root", d, "--author", "x", "--out", str(out)]), 2)
            self.assertEqual(out.read_text(), "keep me")


if __name__ == "__main__":
    unittest.main()
