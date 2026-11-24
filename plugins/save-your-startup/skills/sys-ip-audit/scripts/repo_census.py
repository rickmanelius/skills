#!/usr/bin/env python3
"""Dated census of every git repository under the folders you name.

For each repository: first and last commit date (all branches), total commits, your commits and their first
and last dates, the remote (with any credentials removed) and the first heading or line of the README.

    python3 -I repo_census.py --root ~/code --root ~/work --out data/repo-census-2026-11-24.csv
    python3 -I repo_census.py --root ~/code --author "jordan" --author "jordan@example.com" --out census.csv

Your commits are matched against --author patterns (case-insensitive regular expressions, tried on both the
author name and email). With no --author, it uses `git config user.name` and `git config user.email`.

Commit dates are author dates, which anyone can set by hand, so treat them as working evidence. The strongest
dates are ones a third party recorded (a public push, a filing, a publication).

Local only: it reads repositories on this machine and touches no network. Python standard library only.
"""
import argparse
import csv
import os
import re
import subprocess
import sys

SEP = "\x1f"  # unit separator: can't appear in a name or email
SKIP_DIRS = {"node_modules", ".venv", "venv", "__pycache__", "vendor", "Pods", "DerivedData", "build", "dist"}
README_NAMES = ("README.md", "readme.md", "README", "README.txt", "README.rst", "AGENTS.md", "CLAUDE.md")
FIELDS = ["repo", "root", "first_commit", "last_commit", "commits", "my_commits", "my_first", "my_last",
          "remote", "readme"]


def dashless(text):
    """Swap em and en dashes for plain punctuation, so the output can go straight into a document."""
    en, em = chr(0x2013), chr(0x2014)
    text = re.sub(r"(?<=\d)" + en + r"(?=\d)", "-", text or "")
    return re.sub(r"\s*[" + en + em + r"]\s*", ", ", text)


def clean_remote(url):
    """Drop any user:password@ or token@ from a remote URL, so credentials never reach the CSV."""
    return re.sub(r"(?<=://)[^/@\s]+@", "", (url or "").strip())


def git(repo, *args):
    try:
        out = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=120)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def default_authors():
    pats = []
    for key in ("user.name", "user.email"):
        val = git(os.getcwd(), "config", "--get", key) or git(os.path.expanduser("~"), "config", "--global", key)
        if val:
            pats.append(re.escape(val))
    return pats


def is_repo(path):
    return os.path.isdir(os.path.join(path, ".git")) or os.path.isfile(os.path.join(path, ".git"))


def find_repos(root, depth=4):
    """Every repository under root, down to `depth` folder levels. Doesn't descend into a repository."""
    root = os.path.abspath(os.path.expanduser(root))
    if is_repo(root):
        return [root]
    found = []

    def walk(path, level):
        try:
            names = sorted(os.listdir(path))
        except OSError:
            return
        for name in names:
            if name.startswith(".") or name in SKIP_DIRS:
                continue
            sub = os.path.join(path, name)
            if not os.path.isdir(sub) or os.path.islink(sub):
                continue
            if is_repo(sub):
                found.append(sub)
            elif level < depth:
                walk(sub, level + 1)

    walk(root, 1)
    return found


def parse_log(text, author_re):
    """Summarize `git log --format=%ad<SEP>%an<SEP>%ae --date=short` output."""
    entries = [line.split(SEP) for line in text.splitlines() if line.count(SEP) == 2]
    dates = sorted(e[0] for e in entries)
    mine = sorted(e[0] for e in entries if author_re and (author_re.search(e[1]) or author_re.search(e[2])))
    return {
        "first_commit": dates[0] if dates else "",
        "last_commit": dates[-1] if dates else "",
        "commits": len(entries),
        "my_commits": len(mine),
        "my_first": mine[0] if mine else "",
        "my_last": mine[-1] if mine else "",
    }


def readme_line(repo):
    for name in README_NAMES:
        path = os.path.join(repo, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                lines = [line.strip() for line in f.readlines()[:40]]
        except OSError:
            return ""
        heading = next((line.lstrip("# ").strip() for line in lines if line.startswith("#")), "")
        body = next((line for line in lines
                     if line and not line.startswith(("#", "!", "[", "<", "```", "|", "---", "==="))), "")
        text = f"{heading}: {body}" if heading and body else heading or body
        return dashless(text)[:220]
    return ""


def census(roots, author_patterns, depth=4):
    author_re = re.compile("|".join(f"(?:{p})" for p in author_patterns), re.I) if author_patterns else None
    rows = []
    for root in roots:
        base = os.path.abspath(os.path.expanduser(root))
        for repo in find_repos(base, depth):
            log = git(repo, "log", "--all", f"--format=%ad{SEP}%an{SEP}%ae", "--date=short")
            row = {"repo": os.path.relpath(repo, base) if repo != base else os.path.basename(repo),
                   "root": root}
            row.update(parse_log(log, author_re))
            row["remote"] = clean_remote(git(repo, "remote", "get-url", "origin"))
            row["readme"] = readme_line(repo)
            rows.append(row)
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser(description="Dated census of git repositories, for a prior-inventions audit.")
    ap.add_argument("--root", action="append", required=True, help="a folder to search (repeatable)")
    ap.add_argument("--author", action="append", default=None,
                    help="regex matched on author name or email (repeatable); default: your git config")
    ap.add_argument("--depth", type=int, default=4, help="folder levels to search below each root (default 4)")
    ap.add_argument("--out", required=True, help="CSV file to write (refuses to overwrite)")
    args = ap.parse_args(argv)

    if os.path.exists(args.out):
        print(f"{args.out} already exists; pick a new dated name. Nothing was written.", file=sys.stderr)
        return 2
    authors = args.author if args.author is not None else default_authors()
    if not authors:
        print("No --author given and no git user.name or user.email found; 'my_commits' will be 0.",
              file=sys.stderr)
    rows = census(args.root, authors, args.depth)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    mine = sum(1 for r in rows if r["my_commits"])
    print(f"{len(rows)} repositories ({mine} with your commits) -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
