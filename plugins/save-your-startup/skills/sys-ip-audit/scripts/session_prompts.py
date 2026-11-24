#!/usr/bin/env python3
"""Your own typed prompts, with timestamps, from Claude Code session logs.

Claude Code keeps one JSON-lines log per session under ~/.claude/projects/<folder>/, where <folder> is the
working directory with slashes turned into dashes. This reads the top-level logs (subagent logs are skipped,
since those prompts are the agent's, not yours) and keeps the user turns you typed: it drops tool results,
slash-command wrappers, system reminders, compaction summaries and meta lines.

    python3 -I session_prompts.py --folder '*acme*' --out data/session-prompts-2026-11-24.jsonl
    python3 -I session_prompts.py --folder '*acme*' --keyword inventory --keyword forecast --since 2026-01-01 \
        --out data/session-prompts-inventory.jsonl

One JSON line per prompt: ts, folder, session, cwd, text.

THE OUTPUT HOLDS CONFIDENTIAL MATERIAL: your words, and often a client's or the counterparty's. Keep it on this
machine. It refuses to write inside a git repository that has a remote unless you pass --force-location.

Claude Code deletes session logs after 30 days by default (the `cleanupPeriodDays` setting), so run this first.
Local only, no network, Python standard library only.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys

DEFAULT_PROJECTS = os.path.expanduser("~/.claude/projects")
SKIP = re.compile(r"^\s*(<command-|<local-command|<system-reminder|<bash-|<task-notification|Caveat:"
                  r"|\[Request interrupted)")
REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)
MAX_CHARS = 4000


def texts(content):
    """The text blocks of a user message, or nothing if it's a tool result."""
    if isinstance(content, str):
        return [content]
    out = []
    for block in content or []:
        if isinstance(block, dict):
            if block.get("type") == "tool_result":
                return []
            if block.get("type") == "text":
                out.append(block.get("text", ""))
    return out


def prompts_from_record(record):
    """The typed prompts in one log record (usually zero or one)."""
    if record.get("type") != "user" or record.get("isMeta") or record.get("isCompactSummary"):
        return []
    msg = record.get("message") or {}
    if msg.get("role") != "user":
        return []
    found = []
    for t in texts(msg.get("content")):
        t = REMINDER.sub("", t).strip()  # strip injected reminders first, so the typed text after one survives
        if t and not SKIP.match(t):
            found.append(t[:MAX_CHARS])
    return found


def matches(text, keywords):
    if not keywords:
        return True
    low = text.lower()
    return any(k.lower() in low for k in keywords)


def in_window(ts, since, until):
    day = (ts or "")[:10]
    if since and day and day < since:
        return False
    if until and day and day > until:
        return False
    return True


def iter_prompts(projects, folder_globs, keywords=None, since=None, until=None):
    folders = sorted({f for g in folder_globs for f in glob.glob(os.path.join(projects, g)) if os.path.isdir(f)})
    for folder in folders:
        for path in sorted(glob.glob(os.path.join(folder, "*.jsonl"))):
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                    except ValueError:
                        continue
                    if not isinstance(record, dict):
                        continue
                    ts = record.get("timestamp", "")
                    if not in_window(ts, since, until):
                        continue
                    for text in prompts_from_record(record):
                        if matches(text, keywords):
                            yield {
                                "ts": ts,
                                "folder": os.path.basename(folder),
                                "session": record.get("sessionId", os.path.basename(path)[:-6]),
                                "cwd": record.get("cwd", ""),
                                "text": text,
                            }


def repo_with_remote(path):
    """The git repository holding `path` if it has a remote, else None."""
    folder = os.path.dirname(os.path.abspath(path)) or "."
    while not os.path.isdir(folder):
        folder = os.path.dirname(folder)
    try:
        top = subprocess.run(["git", "-C", folder, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=30)
        if top.returncode != 0:
            return None
        remotes = subprocess.run(["git", "-C", folder, "remote"], capture_output=True, text=True, timeout=30)
        return top.stdout.strip() if remotes.stdout.strip() else None
    except (OSError, subprocess.SubprocessError):
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Extract your own typed prompts from Claude Code session logs.")
    ap.add_argument("--projects", default=DEFAULT_PROJECTS, help="session log root (default ~/.claude/projects)")
    ap.add_argument("--folder", action="append", default=None,
                    help="glob for project folders to read (repeatable), e.g. '*acme*'; default: all")
    ap.add_argument("--keyword", action="append", default=None,
                    help="keep prompts containing this word (repeatable, case-insensitive, any match)")
    ap.add_argument("--since", help="YYYY-MM-DD, inclusive")
    ap.add_argument("--until", help="YYYY-MM-DD, inclusive")
    ap.add_argument("--out", required=True, help="JSON-lines file to write (refuses to overwrite)")
    ap.add_argument("--force-location", action="store_true",
                    help="allow writing inside a git repository that has a remote (not recommended)")
    args = ap.parse_args(argv)

    if os.path.exists(args.out):
        print(f"{args.out} already exists; pick a new dated name. Nothing was written.", file=sys.stderr)
        return 2
    repo = repo_with_remote(args.out)
    if repo and not args.force_location:
        print(f"{args.out} is inside {repo}, which has a remote. This output holds confidential material; "
              "write it somewhere private instead. Nothing was written.", file=sys.stderr)
        return 2
    if not os.path.isdir(args.projects):
        print(f"No session logs at {args.projects}.", file=sys.stderr)
        return 1

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    n = 0
    folders = set()
    with open(args.out, "w", encoding="utf-8") as out:
        for row in iter_prompts(args.projects, args.folder or ["*"], args.keyword, args.since, args.until):
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
            folders.add(row["folder"])
            n += 1
    print(f"{n} prompts from {len(folders)} project folders -> {args.out}")
    print("This file holds confidential material. Keep it on this machine and out of git.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
