#!/usr/bin/env python3
"""Preserve your evidence in one dated folder, then hash it. Copies only; never deletes or edits anything.

    python3 -I preserve_evidence.py \
        --source ~/notes/acme --source ~/ip-audit/acme/data \
        --bundle-repo ~/code/inventory-lib --bundle-repo ~/code/acme-prototype \
        --exclude '*client-logistics*' --exclude '*.env' \
        --dest ~/ip-evidence

What it does, in plain words:
  1. Makes a new folder <dest>/evidence-<timestamp>. If it somehow exists, it stops; nothing is overwritten.
  2. Copies each --source folder (or file) into files/<name>/, skipping anything matching an --exclude pattern
     and any symbolic link (a link can point anywhere, including material that isn't yours to keep).
  3. For each --bundle-repo, writes a full git bundle (every branch and tag) and a dated commit log.
  4. Checks the copy: if any excluded name slipped in, it stops with an error.
  5. Writes MANIFEST.sha256 (one SHA-256 per file, the same format `shasum -a 256 -c` reads) and prints one
     hash of the manifest.

Email that one hash to your lawyer. It proves this exact set of files existed on that date without showing any
of it. Never publish the folder or its contents anywhere, including permanent storage. The folder holds
confidential material, so it refuses to write inside a git repository that has a remote.

--dry-run lists what would be copied and skipped, and copies nothing. Python standard library only.
"""
import argparse
import fnmatch
import hashlib
import os
import shutil
import subprocess
import sys
import time

MANIFEST = "MANIFEST.sha256"


def excluded(rel_path, patterns):
    """True if the relative path, or any part of it, matches an exclude pattern."""
    rel_path = rel_path.replace(os.sep, "/")
    parts = rel_path.split("/")
    for pat in patterns:
        if fnmatch.fnmatch(rel_path, pat) or any(fnmatch.fnmatch(p, pat) for p in parts):
            return True
    return False


def plan_copy(source, patterns):
    """(to_copy, skipped) for one source folder or file. Paths in to_copy are relative to the source."""
    source = os.path.abspath(os.path.expanduser(source))
    to_copy, skipped = [], []
    if os.path.isfile(source):
        name = os.path.basename(source)
        (skipped if excluded(name, patterns) or os.path.islink(source) else to_copy).append(name)
        return to_copy, skipped
    for dirpath, dirnames, filenames in os.walk(source, followlinks=False):
        rel_dir = os.path.relpath(dirpath, source)
        keep = []
        for d in sorted(dirnames):
            rel = os.path.normpath(os.path.join(rel_dir, d))
            if os.path.islink(os.path.join(dirpath, d)) or excluded(rel, patterns):
                skipped.append(rel + "/")
            else:
                keep.append(d)
        dirnames[:] = keep
        for f in sorted(filenames):
            rel = os.path.normpath(os.path.join(rel_dir, f))
            if os.path.islink(os.path.join(dirpath, f)) or excluded(rel, patterns):
                skipped.append(rel)
            else:
                to_copy.append(rel)
    return to_copy, skipped


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(folder):
    """Hash every file under folder (except the manifest) into MANIFEST.sha256; return the manifest's hash."""
    lines = []
    for dirpath, _dirs, files in os.walk(folder):
        for f in files:
            full = os.path.join(dirpath, f)
            rel = "./" + os.path.relpath(full, folder).replace(os.sep, "/")
            if rel == "./" + MANIFEST:
                continue
            lines.append(f"{sha256_file(full)}  {rel}")
    lines.sort(key=lambda line: line.split("  ", 1)[1])
    path = os.path.join(folder, MANIFEST)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + ("\n" if lines else ""))
    return sha256_file(path), len(lines)


def repo_with_remote(path):
    folder = os.path.abspath(path)
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


def unique_name(name, used):
    base, n = name, 2
    while name in used:
        name = f"{base}-{n}"
        n += 1
    used.add(name)
    return name


def bundle_repo(repo, dest_dir):
    repo = os.path.abspath(os.path.expanduser(repo))
    name = os.path.basename(repo.rstrip("/"))
    bundle = os.path.join(dest_dir, f"{name}.bundle")
    for cmd in (["git", "-C", repo, "bundle", "create", bundle, "--all"],
                ["git", "-C", repo, "bundle", "verify", bundle]):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit(f"git bundle failed for {repo}: {r.stderr.strip()[:300]}")
    log = subprocess.run(["git", "-C", repo, "log", "--all", "--format=%H %ad %an <%ae> %s", "--date=iso"],
                         capture_output=True, text=True)
    with open(os.path.join(dest_dir, f"{name}-log.txt"), "w", encoding="utf-8") as f:
        f.write(log.stdout)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Copy evidence into one dated folder and hash it. Never deletes.")
    ap.add_argument("--source", action="append", default=[], help="a folder or file to copy (repeatable)")
    ap.add_argument("--bundle-repo", action="append", default=[], help="a git repository to bundle (repeatable)")
    ap.add_argument("--exclude", action="append", default=[],
                    help="glob matched against each path and each path part (repeatable)")
    ap.add_argument("--dest", default=os.path.expanduser("~/ip-evidence"),
                    help="parent folder for the dated evidence folder (default ~/ip-evidence)")
    ap.add_argument("--dry-run", action="store_true", help="list what would be copied; copy nothing")
    ap.add_argument("--force-location", action="store_true",
                    help="allow a destination inside a git repository with a remote (not recommended)")
    args = ap.parse_args(argv)

    if not args.source and not args.bundle_repo:
        ap.error("give at least one --source or --bundle-repo")
    for s in args.source + args.bundle_repo:
        if not os.path.exists(os.path.expanduser(s)):
            print(f"Not found: {s}. Nothing was copied.", file=sys.stderr)
            return 1

    plans, used = [], set()
    for s in args.source:
        to_copy, skipped = plan_copy(s, args.exclude)
        plans.append((s, unique_name(os.path.basename(os.path.abspath(os.path.expanduser(s))), used),
                      to_copy, skipped))

    if args.dry_run:
        for s, name, to_copy, skipped in plans:
            print(f"{s} -> files/{name}/: {len(to_copy)} files to copy, {len(skipped)} skipped")
            for rel in skipped:
                print(f"  skip {rel}")
        for r in args.bundle_repo:
            print(f"{r} -> bundles/ (full git bundle and log)")
        print("Dry run: nothing was copied.")
        return 0

    dest_parent = os.path.abspath(os.path.expanduser(args.dest))
    repo = repo_with_remote(dest_parent)
    if repo and not args.force_location:
        print(f"{dest_parent} is inside {repo}, which has a remote. Evidence holds confidential material; "
              "pick a private folder. Nothing was copied.", file=sys.stderr)
        return 2
    os.makedirs(dest_parent, exist_ok=True)
    out = os.path.join(dest_parent, "evidence-" + time.strftime("%Y-%m-%d-%H%M%S"))
    os.mkdir(out)  # fails if it exists: nothing is ever overwritten

    step = 1
    total_steps = (1 if plans else 0) + (1 if args.bundle_repo else 0) + 2
    if plans:
        print(f"{step}/{total_steps}  Copying {len(plans)} sources")
        for s, name, to_copy, _skipped in plans:
            src = os.path.abspath(os.path.expanduser(s))
            for rel in to_copy:
                from_path = src if os.path.isfile(src) else os.path.join(src, rel)
                to_path = os.path.join(out, "files", name, rel)
                os.makedirs(os.path.dirname(to_path), exist_ok=True)
                shutil.copy2(from_path, to_path, follow_symlinks=False)
        step += 1
    if args.bundle_repo:
        print(f"{step}/{total_steps}  Bundling {len(args.bundle_repo)} repositories")
        os.makedirs(os.path.join(out, "bundles"))
        for r in args.bundle_repo:
            bundle_repo(r, os.path.join(out, "bundles"))
        step += 1

    print(f"{step}/{total_steps}  Checking for excluded files")
    for dirpath, dirs, files in os.walk(os.path.join(out, "files")):
        for f in dirs + files:
            rel = os.path.relpath(os.path.join(dirpath, f), os.path.join(out, "files"))
            rel_in_source = rel.split(os.sep, 1)[1] if os.sep in rel else rel
            if excluded(rel_in_source, args.exclude):
                print(f"Excluded file found in the copy: {rel}. Stopping; check {out} by hand before using it.",
                      file=sys.stderr)
                return 1
    step += 1

    print(f"{step}/{total_steps}  Hashing")
    digest, count = write_manifest(out)
    skipped = sum(len(p[3]) for p in plans)
    print()
    print(f"Saved to: {out}")
    print(f"Files:    {count} ({skipped} skipped by --exclude or as links)")
    print(f"Manifest hash (email this to your lawyer): {digest}")
    print("Keep the folder private. Never publish its contents.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
