#!/usr/bin/env python3
"""Venice video kit: stills (Nano Banana Pro), video (Seedance 2.5) and music (Sonilo) from one SCRIPT.md.

Part of the sys:venice-video skill (https://github.com/rickmanelius/skills). Python 3.8 or newer, standard
library only. Not affiliated with Venice.

Every command except `new` works on a scenario folder that holds SCRIPT.md. The folder is, in order:
--dir PATH, the SEEDANCE_SCENARIO environment variable, the current folder if it has a SCRIPT.md, or the
folder this file sits in. The API key comes from VENICE_API_KEY, or from the variable that VENICE_KEY_ENV
names. It is never printed.

Free:
  seedance.py doctor                  Python, key present, Chrome, image resizer, ffmpeg, models on Venice
  seedance.py new <name> [--dest DIR] [--from FOLDER] [--cast-from DIR]
                                      a new scenario folder (default: ./<name>)
  seedance.py check                   validate SCRIPT.md without calling Venice
  seedance.py screens [WIDTH HEIGHT]  render screens.html to refs/screens/<name>.png (headless Chrome)
  seedance.py list                    jobs, and whether their references are ready
  seedance.py show <id|cut>           the composed prompt and the files to attach (also for the web app)
  seedance.py quote [cut|all|ids]     price quotes from Venice
  seedance.py fetch [--wait] [--timeout MINUTES]
                                      download finished work; marks refusals FAILED with the reason
  seedance.py status                  every submission, where it landed, why anything failed, quoted spend

Paid (each one prints its quoted total first):
  seedance.py stills [ids] [--variants N] [--replace]
  seedance.py draft <cut|ids> [--takes N] [--no-probe]
  seedance.py upgrade <job-id> <take> [--again]
  seedance.py music [ids]

A paid command goes ahead only after approval: type "yes" at its prompt, or pass --approve-up-to DOLLARS
with the amount the person paying agreed to. With no terminal and no approval it prints the quote, submits
nothing and exits with status 3.

A cut is any label in a video job's "cuts" list (for example "30"). Video jobs: "refs" make it
reference-to-video; "start_image" (and optional "end_image") make it image-to-video; neither makes it
text-to-video. Venice's public Seedance API refuses media with people in it (a content-policy 422 that
arrives at retrieve time, after the queue accepted the job), so references marked "person": true are
refused here before anything is sent.
"""
import base64
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

VERSION = "1.0.0"
API = "https://api.venice.ai/api/v1"
UA = f"venice-video-kit/{VERSION}"
NEEDS_APPROVAL = 3
KINDS = ("still", "video", "music")
PAID = ("stills", "draft", "upgrade", "music")
IMAGE_EXT = (".png", ".jpg", ".jpeg")
RESOLUTIONS = ("480p", "720p", "1080p", "4k")
RETRYABLE = (408, 425, 429, 500, 502, 503, 504)
DONE = ("COMPLETED", "FAILED")
DRAFT_DAYS = 7
MAX_PROMPT = 15000

HERE = Path.cwd()
STATE = HERE / "out" / "state.json"
APPROVAL = {"cap": None}
_IMAGE_MODELS = None


def set_folder(path):
    global HERE, STATE
    HERE = Path(path).expanduser().resolve()
    STATE = HERE / "out" / "state.json"


class Stop(SystemExit):
    """Ends the command with a message on stderr and an exit status."""

    def __init__(self, message, code=1):
        super().__init__(code)
        self.message = message


def die(message, code=1):
    raise Stop(message, code)


def say(*parts):
    print(*parts, flush=True)


# ---------- arguments ----------
def take_flag(args, name):
    if name in args:
        args.remove(name)
        return True
    return False


def take_option(args, name, cast=str, default=None):
    if name not in args:
        return default
    i = args.index(name)
    if i + 1 >= len(args):
        die(f"{name} needs a value")
    raw = args[i + 1]
    del args[i:i + 2]
    try:
        return cast(raw)
    except (ValueError, TypeError):
        die(f"{name}: not a valid value: {raw}")


def positive_int(s):
    n = int(s)
    if n < 1:
        raise ValueError(s)
    return n


def dollars(s):
    v = float(str(s).lstrip("$"))
    if not math.isfinite(v) or v < 0:
        raise ValueError(s)
    return v


def scenario_dir(args):
    path = take_option(args, "--dir")
    if path:
        return Path(path).expanduser().resolve()
    if os.environ.get("SEEDANCE_SCENARIO"):
        return Path(os.environ["SEEDANCE_SCENARIO"]).expanduser().resolve()
    if (Path.cwd() / "SCRIPT.md").exists():
        return Path.cwd().resolve()
    return Path(__file__).resolve().parent


# ---------- SCRIPT.md ----------
BLOCK = re.compile(r"^```(json job|json refs|text negative|text prompt [\w-]+)[ \t]*\n(.*?)\n```[ \t]*$", re.S | re.M)


class Script:
    def __init__(self):
        self.jobs, self.prompts, self.refs, self.neg = [], {}, {}, ""
        self.errors, self.warnings = [], []


def parse_script(text):
    s = Script()
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    negs, ref_blocks = [], 0
    for m in BLOCK.finditer(text):
        tag, body = m.group(1), m.group(2)
        line = text.count("\n", 0, m.start()) + 1
        if tag in ("json job", "json refs"):
            try:
                value = json.loads(body)
            except json.JSONDecodeError as e:
                s.errors.append(f"line {line}: the {tag} block is not valid JSON ({e.msg}, at its line {e.lineno})")
                continue
            if not isinstance(value, dict):
                s.errors.append(f"line {line}: the {tag} block must be one JSON object")
                continue
            if tag == "json job":
                value["_line"] = line
                s.jobs.append(value)
            else:
                ref_blocks += 1
                s.refs.update(value)
        elif tag == "text negative":
            negs.append(body.strip())
        else:
            pid = tag.split(" ", 2)[2]
            if pid in s.prompts:
                s.errors.append(f"line {line}: a second prompt block for {pid}")
            s.prompts[pid] = body.strip()
    if ref_blocks > 1:
        s.errors.append("SCRIPT.md has more than one json refs block; keep one table")
    if len(negs) > 1:
        s.errors.append("SCRIPT.md has more than one text negative block; keep one")
    s.neg = negs[0] if negs else ""
    return s


def ref_path_problem(file):
    if not isinstance(file, str) or not file.strip():
        return 'needs a "file" path such as refs/cast/C1-set.jpg'
    p = Path(file)
    if p.is_absolute() or file.startswith("~"):
        return f"{file} must be a path inside the scenario folder, such as refs/cast/C1-set.jpg"
    resolved = (HERE / p).resolve()
    if resolved != HERE and HERE not in resolved.parents:
        return f"{file} leaves the scenario folder; references must stay inside it"
    if p.suffix.lower() not in IMAGE_EXT:
        return f"{file} must be a .png, .jpg or .jpeg file"
    return None


def validate(s):
    e, w = s.errors, s.warnings
    seen = set()
    for rid, ref in s.refs.items():
        if not isinstance(ref, dict):
            e.append(f"reference {rid}: must be an object like {{\"file\": ..., \"caption\": ...}}")
            continue
        problem = ref_path_problem(ref.get("file"))
        if problem:
            e.append(f"reference {rid}: {problem}")
    for j in s.jobs:
        where = f"job at line {j['_line']}"
        jid = j.get("id")
        if not isinstance(jid, str) or not re.fullmatch(r"[\w-]+", jid):
            e.append(f"{where}: needs an \"id\" of letters, digits, _ or -")
            continue
        where = f"job {jid}"
        if jid in seen:
            e.append(f"{where}: the id is used twice")
        seen.add(jid)
        kind = j.get("kind")
        if kind not in KINDS:
            e.append(f"{where}: \"kind\" must be one of {', '.join(KINDS)}")
            continue
        if not isinstance(j.get("model"), str) or not j["model"]:
            e.append(f"{where}: needs a \"model\"")
        if jid not in s.prompts:
            e.append(f"{where}: no ```text prompt {jid}``` block")
        else:
            j["prompt"] = s.prompts[jid]
        if kind == "still":
            for k in ("aspect_ratio", "resolution"):
                if not j.get(k):
                    e.append(f"{where}: still jobs need \"{k}\"")
            ref = s.refs.get(jid)
            if not isinstance(ref, dict):
                e.append(f"{where}: add a reference with the same id ({jid}) so the tool knows where to save it")
            elif isinstance(ref.get("file"), str) and Path(ref["file"]).suffix.lower() not in (".jpg", ".jpeg"):
                e.append(f"{where}: stills are saved as JPEG; name its file .jpg")
        elif kind == "video":
            dur = j.get("duration")
            if not (isinstance(dur, str) and re.fullmatch(r"\d+s", dur)):
                e.append(f"{where}: \"duration\" must be a string like \"10s\"")
            elif not 4 <= int(dur[:-1]) <= 30:
                w.append(f"{where}: {dur} is outside 4 to 30 seconds, the Seedance 2.5 range read on 2026-11-16")
            cuts = j.get("cuts", [])
            if not isinstance(cuts, list):
                e.append(f"{where}: \"cuts\" must be a list such as [\"30\"]")
            else:
                j["cuts"] = [str(c) for c in cuts]
            refs = j.get("refs", [])
            refs_ok = isinstance(refs, list)
            if not refs_ok:
                e.append(f"{where}: \"refs\" must be a list of reference ids")
                refs = []
            for r in refs + [j[k] for k in ("start_image", "end_image") if j.get(k)]:
                ref = s.refs.get(r) if isinstance(r, str) else None
                if not isinstance(ref, dict):
                    e.append(f"{where}: reference {r} is not in the json refs table")
                    refs_ok = False
                elif r in refs and not ref.get("caption"):
                    e.append(f"{where}: reference {r} needs a \"caption\" (it goes into Seedance's reference line)")
                    refs_ok = False
                elif ref.get("person"):
                    w.append(f"{where}: attaches {r}, which shows a person; the API refuses it, so `draft` will too")
            fr = j.get("final_resolution")
            if fr is not None and fr not in RESOLUTIONS:
                w.append(f"{where}: final_resolution {fr} is not one of {', '.join(RESOLUTIONS)}")
            if refs_ok and jid in s.prompts and len(composed_prompt(j, s.refs)) > MAX_PROMPT:
                e.append(f"{where}: the prompt is over {MAX_PROMPT:,} characters with its reference line")
        elif kind == "music":
            d = j.get("duration_seconds")
            if not isinstance(d, int) or isinstance(d, bool) or d < 1:
                e.append(f"{where}: \"duration_seconds\" must be a whole number of seconds")
    for pid in s.prompts:
        if pid not in seen:
            w.append(f"prompt {pid} has no job block, so nothing reads it")
    for j in s.jobs:
        if "REPLACE" in j.get("prompt", ""):
            w.append(f"job {j['id']}: its prompt still says REPLACE; paid commands refuse it until it is written")
    if any(j.get("kind") == "video" for j in s.jobs) and not s.neg:
        w.append("no ```text negative``` block; video jobs will run without a negative prompt")
    return s


def load_script():
    path = HERE / "SCRIPT.md"
    if not path.exists():
        die(f"No SCRIPT.md in {HERE}. Run from a scenario folder, pass --dir PATH, or start one with `new`.")
    s = validate(parse_script(path.read_text(encoding="utf-8")))
    if s.errors:
        die("SCRIPT.md has problems; nothing was sent:\n  " + "\n  ".join(s.errors), 2)
    return s


def composed_prompt(job, refs):
    """Seedance's canonical reference line (Venice Seedance guide, read 2026-11-16): case-sensitive <Image N>;
    people as <Subject N> (web app only). For example: Refer to the kitchen in <Image 1> and the plain white
    mug in <Image 2> to generate the video described below."""
    parts, subject = [], 0
    for i, r in enumerate(job.get("refs", []), 1):
        ref = refs[r]
        if ref.get("person"):
            subject += 1
            parts.append(f"<Subject {subject}> in <Image {i}> ({ref['caption']})")
        else:
            parts.append(f"{ref['caption']} in <Image {i}>")
    if not parts:
        return job["prompt"]
    joined = parts[0] if len(parts) == 1 else ", ".join(parts[:-1]) + " and " + parts[-1]
    return f"Refer to {joined} to generate the video described below.\n\n" + job["prompt"]


def media_ids(job):
    """Every reference a video job sends: references, then start and end frames."""
    return list(job.get("refs", [])) + [job[k] for k in ("start_image", "end_image") if job.get(k)]


def person_refs(job, refs):
    return [r for r in media_ids(job) if refs[r].get("person")]


def select(s, args, kinds):
    pool = [j for j in s.jobs if j["kind"] in kinds]
    if not args:
        args = ["all"]
    cuts = {c for j in s.jobs for c in j.get("cuts", [])}
    out = []
    for a in args:
        if a == "all":
            out += pool
        elif a in cuts:
            out += [j for j in pool if j["kind"] == "video" and a in j.get("cuts", [])]
        elif a in ("stills", "music", "video"):
            out += [j for j in pool if j["kind"] == {"stills": "still"}.get(a, a)]
        else:
            hit = [j for j in pool if j["id"] == a] or [j for j in pool if j["id"].split("-")[0] == a]
            if not hit:
                die(f"No {' or '.join(kinds)} job matches {a}. `list` shows the ids and cuts.")
            out += hit
    seen, uniq = set(), []
    for j in out:
        if j["id"] not in seen:
            seen.add(j["id"])
            uniq.append(j)
    if not uniq:
        die(f"Nothing to do: SCRIPT.md has no {' or '.join(kinds)} job for {' '.join(args)}.")
    return uniq


def require_written(jobs):
    unwritten = [j["id"] for j in jobs if "REPLACE" in j["prompt"]]
    if unwritten:
        die(f"These prompts still say REPLACE: {', '.join(unwritten)}. Write them first; nothing was sent.")


# ---------- images ----------
SOF = {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}


def image_size(path):
    """(width, height) of a PNG or JPEG from its header, or None."""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
            if head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
                return struct.unpack(">II", head[16:24])
            if head[:2] != b"\xff\xd8":
                return None
            f.seek(2)
            while True:
                b = f.read(1)
                while b and b != b"\xff":
                    b = f.read(1)
                while b == b"\xff":
                    b = f.read(1)
                if not b:
                    return None
                marker = b[0]
                if marker == 0x01 or 0xD0 <= marker <= 0xD9:
                    continue
                seg = f.read(2)
                if len(seg) < 2:
                    return None
                length = struct.unpack(">H", seg)[0]
                if marker in SOF:
                    data = f.read(5)
                    if len(data) < 5:
                        return None
                    h, w = struct.unpack(">HH", data[1:5])
                    return w, h
                f.seek(length - 2, 1)
    except OSError:
        return None


def ref_problems(job, refs):
    out = []
    for r in media_ids(job):
        p = HERE / refs[r]["file"]
        if not p.exists():
            out.append(f"{r} is missing ({refs[r]['file']})")
            continue
        size = image_size(p)
        if size is None:
            out.append(f"{r} is not a readable PNG or JPEG ({refs[r]['file']})")
            continue
        w, h = size
        if min(w, h) < 300:
            out.append(f"{r} is {w}x{h}; its short side must be at least 300 px")
        if h and not 0.4 < w / h < 2.5:
            out.append(f"{r} is {w}x{h}; width over height must be between 0.4 and 2.5")
    return out


def shrink(src, dst):
    """A 1536 px JPEG copy with whatever is installed: macOS sips, ImageMagick, or Pillow."""
    tools = []
    if shutil.which("sips"):
        tools.append(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "85", "-Z", "1536", str(src), "--out", str(dst)])
    if shutil.which("magick"):
        tools.append(["magick", str(src), "-resize", "1536x1536>", "-quality", "85", str(dst)])
    elif os.name != "nt" and shutil.which("convert"):   # on Windows, convert.exe is a disk tool
        tools.append(["convert", str(src), "-resize", "1536x1536>", "-quality", "85", str(dst)])
    for cmd in tools:
        try:
            if subprocess.run(cmd, capture_output=True, timeout=120).returncode == 0 and dst.exists():
                return True
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        from PIL import Image
        with Image.open(src) as im:
            im = im.convert("RGB")
            im.thumbnail((1536, 1536))
            im.save(dst, "JPEG", quality=85)
        return True
    except Exception:
        return False


def resizer_name():
    if shutil.which("sips"):
        return "sips"
    if shutil.which("magick") or (os.name != "nt" and shutil.which("convert")):
        return "ImageMagick"
    try:
        import PIL  # noqa: F401
        return "Pillow"
    except ImportError:
        return None


def upload_copy(path):
    """Large references make a heavy request; send a 1536 px JPEG copy instead. The original stays."""
    if path.stat().st_size <= 1_500_000:
        return path
    rel = path.resolve().relative_to(HERE).as_posix().replace("/", "__")
    cache = HERE / "out" / ".refcache" / (Path(rel).stem + ".jpg")
    if cache.exists() and cache.stat().st_mtime >= path.stat().st_mtime:
        return cache
    cache.parent.mkdir(parents=True, exist_ok=True)
    if shrink(path, cache):
        return cache
    say(f"note: {path.name} is {path.stat().st_size / 1e6:.1f} MB and no resizer was found (sips, ImageMagick or "
        "Pillow); sending it as it is")
    return path


def data_url(path):
    resolved = path.resolve()
    if HERE not in resolved.parents:
        die(f"refusing to send {path}: it is outside the scenario folder")
    path = upload_copy(resolved)
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


# ---------- HTTP ----------
def key_name():
    return os.environ.get("VENICE_KEY_ENV") or "VENICE_API_KEY"


def key():
    k = os.environ.get(key_name(), "").strip()
    if not k:
        die(f"No Venice API key: set {key_name()} in this shell (make one in your Venice account's API settings). "
            "The tool never prints it.")
    return k


def request(path, body=None, method="POST", timeout=600):
    """(status, content type, body bytes, lower-cased headers). Network failures raise OSError."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": f"Bearer {key()}", "Content-Type": "application/json", "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.headers.get("Content-Type", ""), r.read(), {k.lower(): v for k, v in r.headers.items()}
    except urllib.error.HTTPError as e:
        hdrs = e.headers or {}
        return e.code, hdrs.get("Content-Type", ""), e.read(), {k.lower(): v for k, v in hdrs.items()}


def error_text(raw):
    try:
        info = json.loads(raw)
        text = info.get("error") or info.get("message") or info.get("details") or info
        text = text if isinstance(text, str) else json.dumps(text)
    except (ValueError, AttributeError):
        text = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
    k = os.environ.get(key_name(), "").strip()
    return (text.replace(k, "***") if k else text)[:600]


def net_reason(e):
    return str(getattr(e, "reason", "") or e)


def call(path, body=None, method="POST"):
    try:
        code, ctype, raw, headers = request(path, body, method)
    except OSError as e:
        die(f"Could not reach Venice ({path}): {net_reason(e)}")
    if code >= 400:
        die(f"Venice {path} returned {code}: {error_text(raw)}")
    return ctype, raw, headers


def call_json(path, body=None, method="POST"):
    ctype, raw, _ = call(path, body, method)
    try:
        return json.loads(raw)
    except ValueError:
        die(f"Venice {path} answered with something that is not JSON ({ctype or 'no content type'})")


# ---------- state ----------
def load_state():
    if STATE.exists():
        try:
            st = json.loads(STATE.read_text(encoding="utf-8"))
        except ValueError:
            die(f"{STATE} is not valid JSON. Fix it or move it aside; it holds the draft ids that upgrades need.")
        st.setdefault("submissions", [])
        return st
    return {"submissions": []}


def save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_name(STATE.name + ".tmp")
    tmp.write_text(json.dumps(st, indent=1), encoding="utf-8")
    os.replace(tmp, STATE)


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_time(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value / 1000 if value > 1e12 else value, timezone.utc)
    try:
        t = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# ---------- prices and approval ----------
def final_res(job):
    # A clip shown small (a 2x2 grid cell is 960 x 540) does not need 1080p; the job can say so.
    return job.get("final_resolution", "1080p")


def quote_video(job, mode, draft_task_id=None):
    body = {"model": job["model"], "duration": job["duration"], "audio": job.get("audio", True)}
    if job.get("aspect_ratio"):
        body["aspect_ratio"] = job["aspect_ratio"]
    if mode == "draft":
        body.update(resolution="480p", draft=True)
    elif mode == "upgrade":
        body.update(resolution=final_res(job), draft_task_id=draft_task_id)
    else:
        body.update(resolution=final_res(job))
    return as_price(call_json("/video/quote", body).get("quote"))


def quote_music(job):
    # /audio/quote rejects "prompt" (proven on the wire 2026-11-16); the queue call needs it.
    return as_price(call_json("/audio/quote", {"model": job["model"], "duration_seconds": job["duration_seconds"]}).get("quote"))


def still_price(job):
    global _IMAGE_MODELS
    if _IMAGE_MODELS is None:
        _IMAGE_MODELS = call_json("/models?type=image", method="GET").get("data", [])
    m = next((m for m in _IMAGE_MODELS if m.get("id") == job["model"]), None)
    try:
        return float(m["model_spec"]["pricing"]["resolutions"][job["resolution"]]["usd"])
    except (TypeError, KeyError, ValueError):
        return float("nan")


def as_price(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def money(v):
    return f"${v:.2f}" if math.isfinite(v) else "no price"


def confirm(total, what):
    """Go ahead only with approval: --approve-up-to covering the quote, or "yes" typed at a terminal."""
    if not math.isfinite(total):
        die(f"Venice gave no price for part of this ({what}); nothing was submitted. `quote` shows which job.")
    say(f"\nThis will spend about ${total:.2f} on Venice ({what}).")
    cap = APPROVAL["cap"]
    if cap is not None:
        if total <= cap + 0.005:
            say(f"Approved up to ${cap:.2f}; going ahead.")
            return
        die(f"The quote (${total:.2f}) is more than the ${cap:.2f} approved. Nothing was submitted.", NEEDS_APPROVAL)
    if not sys.stdin.isatty():
        die("Nothing was submitted: this needs approval. Show the person paying the total above; if they agree, run "
            f"the same command again with --approve-up-to {math.ceil(total * 100) / 100:.2f}", NEEDS_APPROVAL)
    try:
        answer = input('Type "yes" to go ahead: ')
    except EOFError:
        answer = ""
    if answer.strip().lower() != "yes":
        die("Stopped. Nothing was submitted.")


# ---------- free commands ----------
def cmd_check(s, args):
    for warning in s.warnings:
        say(f"warning: {warning}")
    kinds = {k: sum(1 for j in s.jobs if j["kind"] == k) for k in KINDS}
    say(f"SCRIPT.md is valid: {kinds['still']} still, {kinds['video']} video and {kinds['music']} music job(s), "
        f"{len(s.refs)} reference(s). Nothing was sent.")


def cmd_list(s, args):
    for j in s.jobs:
        length = str(j.get("duration", j.get("duration_seconds", ""))).ljust(5)
        if j["kind"] == "video":
            people = person_refs(j, s.refs)
            problems = ref_problems(j, s.refs)
            state = ("refuses: shows a person (" + ", ".join(people) + ")") if people else (
                "; ".join(problems) if problems else "references ready")
        elif j["kind"] == "still":
            state = "made" if (HERE / s.refs[j["id"]]["file"]).exists() else "not made yet"
        else:
            state = ""
        cuts = ",".join(j.get("cuts", []))
        say(f"{j['id']:<20} {j['kind']:<6} {length} {cuts:<8} {state}")


def cmd_show(s, args):
    for j in select(s, args, KINDS):
        say(f"===== {j['id']}  ({j['kind']}, model {j['model']})")
        settings = {k: v for k, v in j.items() if k not in ("prompt", "refs", "id", "kind") and not k.startswith("_")}
        say("Settings:", json.dumps(settings))
        if j.get("refs"):
            say("Attach these, in this order:")
            for i, r in enumerate(j["refs"], 1):
                say(f"  {i}. {s.refs[r]['file']}")
        for k, label in (("start_image", "Start frame"), ("end_image", "End frame")):
            if j.get(k):
                say(f"{label}: {s.refs[j[k]]['file']}")
        say("\nPrompt:\n" + (composed_prompt(j, s.refs) if j["kind"] == "video" else j["prompt"]))
        if j["kind"] == "video" and s.neg:
            say("\nNegative prompt:\n" + s.neg)
        say()


def cmd_quote(s, args):
    tot_d = tot_f = tot_other = 0.0
    for j in select(s, args, KINDS):
        if j["kind"] == "video":
            d, f = quote_video(j, "draft"), quote_video(j, "final")
            tot_d += d
            tot_f += f
            say(f"{j['id']:<20} {j['duration']:>4}  480p draft {money(d):>7}   {final_res(j):>5} {money(f):>7}")
        elif j["kind"] == "music":
            q = quote_music(j)
            tot_other += q
            say(f"{j['id']:<20} {j['duration_seconds']:>3}s  music {money(q):>7}")
        else:
            p = still_price(j)
            tot_other += p
            say(f"{j['id']:<20} still {j['resolution']:<4} {money(p):>7} per image")
    say(f"\nVideo: one draft take of each {money(tot_d)}; each at its final resolution {money(tot_f)}. "
        f"Stills (one each) and music {money(tot_other)}. Quotes are free; prices move, so quote again before spending.")


class _Frames(HTMLParser):
    def __init__(self):
        super().__init__()
        self.frames = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "frame" in (a.get("class") or "").split():
            self.frames.append((tag, a.get("data-name")))


def find_chrome():
    env = os.environ.get("CHROME")
    if env:
        return env if (Path(env).exists() or shutil.which(env)) else None
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ]
    for var in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
        if os.environ.get(var):
            candidates.append(str(Path(os.environ[var]) / "Google" / "Chrome" / "Application" / "chrome.exe"))
            candidates.append(str(Path(os.environ[var]) / "Microsoft" / "Edge" / "Application" / "msedge.exe"))
    for c in candidates:
        if Path(c).exists():
            return c
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"):
        if shutil.which(name):
            return shutil.which(name)
    return None


def cmd_screens(args):
    w, h = 1920, 1080
    if args:
        try:
            w, h = (int(args[0]), int(args[1]))
        except (ValueError, IndexError):
            die("usage: seedance.py screens [WIDTH HEIGHT]")
    html = HERE / "screens.html"
    if not html.exists():
        die(f"No screens.html in {HERE}.")
    parser = _Frames()
    parser.feed(html.read_text(encoding="utf-8"))
    names = [n for _, n in parser.frames]
    if not names:
        die('No frames in screens.html: give each one class="frame" and a data-name, like <section data-name="S1-email" class="frame">.')
    unnamed = [i + 1 for i, n in enumerate(names) if not n]
    if unnamed:
        die(f"Frame(s) {', '.join(map(str, unnamed))} in screens.html have no data-name, so the PNG has no name.")
    bad = [n for n in names if not re.fullmatch(r"[A-Za-z0-9_-]+", n)]
    if bad or len(set(names)) != len(names):
        die("Each frame's data-name must be unique and use only letters, digits, _ or -: " + ", ".join(bad or names))
    chrome = find_chrome()
    if not chrome:
        die("No Chrome, Chromium or Edge found. Install one, or set CHROME to its path.")
    out_dir = HERE / "refs" / "screens"
    out_dir.mkdir(parents=True, exist_ok=True)
    failed = []
    with tempfile.TemporaryDirectory() as profile:
        for n, name in enumerate(names, 1):
            out = out_dir / f"{name}.png"
            if out.exists():
                out.unlink()
            cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                   "--no-first-run", "--no-default-browser-check", f"--user-data-dir={profile}",
                   f"--window-size={w},{h}", "--virtual-time-budget=8000", f"--screenshot={out}",
                   f"{html.as_uri()}?only={n}"]
            try:
                subprocess.run(cmd, capture_output=True, timeout=90)
            except (OSError, subprocess.SubprocessError) as e:
                say(f"could not run Chrome for {name}: {e}")
            size = image_size(out) if out.exists() else None
            if not size:
                failed.append(name)
                say(f"FAILED  refs/screens/{name}.png")
            elif tuple(size) != (w, h):
                say(f"warning refs/screens/{name}.png is {size[0]}x{size[1]}, not {w}x{h}")
            else:
                say(f"rendered refs/screens/{name}.png")
    if failed:
        die(f"{len(failed)} frame(s) did not render. Open screens.html?only=N in a browser to see why.")
    say("Look at every PNG before using it: spelling, sample-data labels, nothing cut off.")


def cmd_doctor(args):
    problems = 0
    v = sys.version_info
    say(f"python      {v.major}.{v.minor}.{v.micro}" + ("" if v >= (3, 8) else "  (needs 3.8 or newer)"))
    problems += v < (3, 8)
    has_key = bool(os.environ.get(key_name(), "").strip())
    say(f"api key     {key_name()} is " + ("set (not shown)" if has_key else "NOT set; paid and quote commands need it"))
    problems += not has_key
    chrome = find_chrome()
    say(f"chrome      {chrome or 'not found; `screens` needs Chrome, Chromium or Edge (or set CHROME)'}")
    say(f"resizer     {resizer_name() or 'none (optional: large references go up at full size)'}")
    say(f"ffmpeg      {shutil.which('ffmpeg') or 'not found (optional: pull frames from drafts to review them)'}")
    if has_key and "--offline" not in args:
        try:
            found = {}
            for t in ("video", "image", "music"):
                code, _, raw, _ = request(f"/models?type={t}", method="GET", timeout=60)
                if code >= 400:
                    say(f"venice      /models?type={t} returned {code}: {error_text(raw)}")
                    problems += 1
                    continue
                found[t] = {m.get("id") for m in json.loads(raw).get("data", [])}
            seedance = sorted(m for m in found.get("video", ()) if m and m.startswith("seedance"))
            say(f"venice      reachable; {len(seedance)} Seedance model(s) listed")
            if (HERE / "SCRIPT.md").exists():
                s = validate(parse_script((HERE / "SCRIPT.md").read_text(encoding="utf-8")))
                all_models = set().union(*found.values()) if found else set()
                for j in s.jobs:
                    if j.get("model") and all_models and j["model"] not in all_models:
                        say(f"model       {j.get('id')}: {j['model']} is not in Venice's model list today")
                        problems += 1
        except OSError as e:
            say(f"venice      not reachable: {net_reason(e)}")
            problems += 1
    say("ready" if not problems else f"{problems} thing(s) to fix")


def cmd_new(args):
    dest = take_option(args, "--dest", str, ".")
    src = take_option(args, "--from")
    cast = take_option(args, "--cast-from")
    if len(args) != 1:
        die("usage: seedance.py new <name> [--dest DIR] [--from FOLDER] [--cast-from DIR]")
    name = args[0]
    if not re.fullmatch(r"[A-Za-z0-9][\w.-]*", name):
        die("The name becomes a folder: use letters, digits, ., _ or -, such as launch-spot.")
    folder = Path(dest).expanduser().resolve() / name
    if folder.exists() and any(folder.iterdir()):
        die(f"Refusing: {folder} exists and is not empty.")
    kit = Path(__file__).resolve().parent.parent
    template = kit / "templates"
    if not src and not (template / "SCRIPT.md").exists():
        die(f"No templates/ beside this copy of seedance.py ({kit}). Run `new` with the skill's own copy, or use --from.")
    if src:
        src_dir = Path(src).expanduser().resolve()
        if not (src_dir / "SCRIPT.md").exists():
            die(f"No SCRIPT.md in {src_dir}; --from takes an earlier scenario folder.")
    for sub in ("refs/cast", "refs/screens", "out/drafts", "out/final", "out/music"):
        (folder / sub).mkdir(parents=True, exist_ok=True)
    if src:
        shutil.copy2(src_dir / "SCRIPT.md", folder / "SCRIPT.md")
        for extra in ("screens.html",):
            if (src_dir / extra).exists():
                shutil.copy2(src_dir / extra, folder / extra)
        if (src_dir / "assets").is_dir():
            shutil.copytree(src_dir / "assets", folder / "assets")
    else:
        text = (template / "SCRIPT.md").read_text(encoding="utf-8")
        text = text.replace("{{NAME}}", name).replace("{{DATE}}", datetime.now().strftime("%Y-%m-%d"))
        (folder / "SCRIPT.md").write_text(text, encoding="utf-8")
        shutil.copy2(template / "screens.html", folder / "screens.html")
    copied = 0
    if cast:
        cast_dir = Path(cast).expanduser().resolve()
        if not cast_dir.is_dir():
            die(f"--cast-from: {cast_dir} is not a folder")
        for f in sorted(cast_dir.iterdir()):
            if f.is_file() and f.suffix.lower() in IMAGE_EXT:
                shutil.copy2(f, folder / "refs" / "cast" / f.name)
                copied += 1
    tool = folder / "seedance.py"
    shutil.copy2(Path(__file__).resolve(), tool)
    tool.chmod(0o755)
    (folder / ".gitignore").write_text(
        "# Generated media stays out of git: it is large and it was paid for. Keep out/state.json;\n"
        "# it holds the draft ids that upgrades need.\nout/drafts/\nout/final/\nout/music/\nout/.refcache/\n",
        encoding="utf-8")
    (folder / ".kit-version").write_text(
        f"venice-video kit {VERSION}, from {src or 'the template'}, created {datetime.now():%Y-%m-%d %H:%M}\n",
        encoding="utf-8")
    say(f"created {folder}" + (f" with {copied} still(s) in refs/cast/" if cast else ""))
    say("next, inside that folder:")
    say("  1. write SCRIPT.md and screens.html")
    say("  2. python3 seedance.py check && python3 seedance.py screens")
    say("  3. python3 seedance.py list && python3 seedance.py quote all")


# ---------- paid commands ----------
def cmd_stills(s, args):
    replace = take_flag(args, "--replace")
    variants = take_option(args, "--variants", positive_int, 1)
    sel = select(s, args or ["stills"], ("still",))
    require_written(sel)
    prices = {j["id"]: still_price(j) for j in sel}
    for j in sel:
        say(f"  {j['id']:<20} {variants} x {money(prices[j['id']])}")
    confirm(sum(prices[j["id"]] * variants for j in sel), f"{len(sel) * variants} image(s)")
    st, stamp, failed = load_state(), datetime.now().strftime("%Y%m%d-%H%M%S"), 0
    for j in sel:
        body = {"model": j["model"], "prompt": j["prompt"], "aspect_ratio": j["aspect_ratio"], "resolution": j["resolution"],
                "format": "jpeg", "variants": variants, "hide_watermark": True}
        try:
            code, _, raw, headers = request("/image/generate", body)
        except OSError as e:
            code, raw, headers = 0, net_reason(e).encode(), {}
        images = []
        if code and code < 400:
            try:
                images = json.loads(raw).get("images", [])
            except ValueError:
                pass
        record = {"job": j["id"], "kind": "still", "take": 1 + sum(1 for x in st["submissions"] if x["job"] == j["id"]),
                  "queue_id": None, "model": j["model"], "submitted": now(), "file": None,
                  "quoted_usd": prices[j["id"]] * variants}
        if not images:
            failed += 1
            record.update(status="FAILED", error=f"{code}: {error_text(raw)}" if code else f"network: {raw.decode()}")
            st["submissions"].append(record)
            save_state(st)
            say(f"{j['id']}: FAILED {record['error']}")
            continue
        target = HERE / s.refs[j["id"]]["file"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if replace and target.exists():
            aside = target.with_name(f"{target.stem}-old-{stamp}{target.suffix}")
            target.rename(aside)
            say(f"moved the old {target.name} aside as {aside.name}")
        saved = []
        for b64 in images:
            path, k = target, 1
            while path.exists():
                k += 1
                path = target.with_name(f"{target.stem}-v{k}{target.suffix}")
            path.write_bytes(base64.b64decode(b64))
            saved.append(str(path.relative_to(HERE)))
            say(f"saved {saved[-1]}")
        record.update(status="COMPLETED", file=saved[0], files=saved)
        st["submissions"].append(record)
        save_state(st)
        if headers.get("x-venice-is-content-violation") == "true":
            say(f"  note: Venice flagged a variant of {j['id']} as a content violation")
    say("\nLook at every still: no people in anything bound for the API, no logos, no readable text, the right place.")
    if failed:
        die(f"{failed} still job(s) failed; see above.")


def cmd_draft(s, args):
    takes = take_option(args, "--takes", positive_int, 1)
    no_probe = take_flag(args, "--no-probe")
    if not args:
        die("Name what to draft: a cut (such as 30), a job id, or several ids. `list` shows them.")
    sel = select(s, args, ("video",))
    for j in sel:
        people = person_refs(j, s.refs)
        if people:
            die(f"{j['id']} attaches a person ({', '.join(people)}). Venice's public Seedance API refuses media with "
                "people in it (it fails later, as a content-policy 422). Describe the person in the prompt instead, "
                f"or run this job in the Venice web app: python3 seedance.py show {j['id']}")
        problems = ref_problems(j, s.refs)
        if problems:
            die(f"{j['id']} is not ready: " + "; ".join(problems) + ". Make the stills or screens first.")
    require_written(sel)
    st = load_state()
    prices = {j["id"]: quote_video(j, "draft") for j in sel}
    proven = any(x["kind"] == "draft" and x.get("status") == "COMPLETED" for x in st["submissions"])
    if not proven and not no_probe and (len(sel) > 1 or takes > 1):
        cheapest = min(sel, key=lambda j: prices[j["id"]] if math.isfinite(prices[j["id"]]) else float("inf"))
        die("No draft has finished in this folder yet, so nothing has proven the request. Probe one first: "
            f"`draft {cheapest['id']}` ({money(prices[cheapest['id']])}), then `fetch --wait`. If a probe is still "
            "running, fetch it first. --no-probe skips this check.")
    for j in sel:
        say(f"  {j['id']:<20} {j['duration']:>4} x {takes} take(s) at {money(prices[j['id']])} each")
    confirm(sum(prices[j["id"]] * takes for j in sel), f"{len(sel) * takes} 480p draft clip(s)")
    for j in sel:
        body = {"model": j["model"], "prompt": composed_prompt(j, s.refs), "duration": j["duration"],
                "resolution": "480p", "audio": j.get("audio", True), "draft": True}
        if s.neg:
            body["negative_prompt"] = s.neg
        if j.get("aspect_ratio"):
            body["aspect_ratio"] = j["aspect_ratio"]
        if j.get("refs"):
            body["reference_image_urls"] = [data_url(HERE / s.refs[r]["file"]) for r in j["refs"]]
        if j.get("start_image"):
            body["image_url"] = data_url(HERE / s.refs[j["start_image"]]["file"])
        if j.get("end_image"):
            body["end_image_url"] = data_url(HERE / s.refs[j["end_image"]]["file"])
        if j.get("omni_reference_task_type"):
            body["omni_reference_task_type"] = j["omni_reference_task_type"]
        for _ in range(takes):
            res = call_json("/video/queue", body)
            if not res.get("queue_id"):
                die(f"Venice queued {j['id']} without a queue id: {json.dumps(res)[:300]}")
            take = 1 + sum(1 for x in st["submissions"] if x["job"] == j["id"] and x["kind"] == "draft")
            st["submissions"].append({"job": j["id"], "kind": "draft", "take": take, "queue_id": res["queue_id"],
                                      "model": j["model"], "status": "PROCESSING", "file": None, "submitted": now(),
                                      "quoted_usd": prices[j["id"]]})
            save_state(st)
            say(f"queued {j['id']} take {take}")
    say("\nNext: python3 seedance.py fetch --wait   (a 30 s clip can take 5 to 15 minutes)")


def cmd_upgrade(s, args):
    again = take_flag(args, "--again")
    if len(args) != 2:
        die("usage: seedance.py upgrade <job-id> <take>")
    hits = select(s, [args[0]], ("video",))
    if len(hits) != 1:
        die(f"{args[0]} matches {len(hits)} jobs; give the full id.")
    job = hits[0]
    try:
        take = int(args[1])
    except ValueError:
        die("The take is a number, as `status` shows it.")
    st = load_state()
    sub = next((x for x in st["submissions"] if x["job"] == job["id"] and x["kind"] == "draft" and x["take"] == take), None)
    if not sub:
        die(f"No draft take {take} of {job['id']} in out/state.json. `status` lists the takes.")
    if sub.get("status") != "COMPLETED":
        die(f"Draft take {take} of {job['id']} is {sub.get('status')}; only a finished draft can be upgraded.")
    expires = parse_time(sub["draft_expires_at"]) if sub.get("draft_expires_at") else None
    if expires and expires < datetime.now(timezone.utc):
        die(f"Draft take {take} of {job['id']} expired on {expires:%Y-%m-%d %H:%M} UTC; draft it again.")
    done = [x for x in st["submissions"] if x["job"] == job["id"] and x["kind"] == "final" and x["take"] == take
            and x.get("status") != "FAILED"]
    if done and not again:
        die(f"Take {take} of {job['id']} is already upgraded or upgrading ({done[-1]['status']}). --again makes another.")
    res_label = final_res(job)
    price = quote_video(job, "upgrade", sub["queue_id"])
    say(f"Upgrade {job['id']} take {take} to {res_label}: the same take, the same motion.")
    confirm(price, f"one {res_label} upgrade")
    body = {"model": job["model"], "prompt": composed_prompt(job, s.refs), "duration": job["duration"],
            "resolution": res_label, "draft_task_id": sub["queue_id"]}
    res = call_json("/video/queue", body)
    if not res.get("queue_id"):
        die(f"Venice queued the upgrade without a queue id: {json.dumps(res)[:300]}")
    st["submissions"].append({"job": job["id"], "kind": "final", "take": take, "queue_id": res["queue_id"],
                              "model": job["model"], "status": "PROCESSING", "file": None, "submitted": now(),
                              "resolution": res_label, "quoted_usd": price})
    save_state(st)
    say(f"queued the {res_label} upgrade of {job['id']} take {take}\nNext: python3 seedance.py fetch --wait")


def cmd_music(s, args):
    sel = select(s, args or ["music"], ("music",))
    require_written(sel)
    prices = {j["id"]: quote_music(j) for j in sel}
    for j in sel:
        say(f"  {j['id']:<20} {j['duration_seconds']}s {money(prices[j['id']])}")
    confirm(sum(prices.values()), f"{len(sel)} music track(s)")
    st = load_state()
    for j in sel:
        res = call_json("/audio/queue", {"model": j["model"], "prompt": j["prompt"], "duration_seconds": j["duration_seconds"]})
        if not res.get("queue_id"):
            die(f"Venice queued {j['id']} without a queue id: {json.dumps(res)[:300]}")
        take = 1 + sum(1 for x in st["submissions"] if x["job"] == j["id"])
        st["submissions"].append({"job": j["id"], "kind": "music", "take": take, "queue_id": res["queue_id"],
                                  "model": j["model"], "status": "PROCESSING", "file": None, "submitted": now(),
                                  "quoted_usd": prices[j["id"]]})
        save_state(st)
        say(f"queued {j['id']}")
    say("\nNext: python3 seedance.py fetch --wait")


# ---------- results ----------
def media_ext(raw, ctype):
    if raw[4:8] == b"ftyp":
        return ".mp4"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WAVE":
        return ".wav"
    if raw[:3] == b"ID3" or raw[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return ".mp3"
    if raw[:4] == b"OggS":
        return ".ogg"
    if raw[:4] == b"fLaC":
        return ".flac"
    for hint, ext in (("mp4", ".mp4"), ("wav", ".wav"), ("mpeg", ".mp3"), ("ogg", ".ogg"), ("flac", ".flac")):
        if hint in ctype:
            return ext
    return ".bin"


def label(x):
    return f"{x['job']} {x['kind']} take {x['take']}"


def fetch_once(st):
    for x in [x for x in st["submissions"] if x.get("status") not in DONE]:
        path = "/audio/retrieve" if x["kind"] == "music" else "/video/retrieve"
        try:
            code, ctype, raw, _ = request(path, {"queue_id": x["queue_id"], "model": x["model"]}, timeout=300)
        except OSError as e:
            say(f"{label(x)}: could not reach Venice ({net_reason(e)}); will try again")
            continue
        if code in RETRYABLE:
            say(f"{label(x)}: Venice answered {code}; will try again ({error_text(raw)[:120]})")
            continue
        if code >= 400:
            x["status"], x["error"] = "FAILED", f"{code}: {error_text(raw)}"
            say(f"{label(x)}: FAILED ({code}) {error_text(raw)}")
            continue
        if "json" in ctype:
            try:
                info = json.loads(raw)
            except ValueError:
                info = {}
            if info.get("draft_expires_at"):
                x["draft_expires_at"] = info["draft_expires_at"]
            status = str(info.get("status", "")).upper()
            if status in ("FAILED", "ERROR", "CANCELLED", "CANCELED"):
                x["status"], x["error"] = "FAILED", error_text(raw)
                say(f"{label(x)}: FAILED {x['error']}")
                continue
            el, avg = (info.get("execution_duration") or 0) / 1000, (info.get("average_execution_time") or 0) / 1000
            say(f"{label(x)}: {info.get('status', 'waiting')} ({el:.0f}s of about {avg:.0f}s)")
            continue
        folder = {"draft": "drafts", "final": "final", "music": "music"}[x["kind"]]
        ext = media_ext(raw, ctype)
        name = f"{x['job']}-take{x['take']}" + (f"-{x.get('resolution', '1080p')}" if x["kind"] == "final" else "") + ext
        out = HERE / "out" / folder / name
        out.parent.mkdir(parents=True, exist_ok=True)
        part = out.with_name(out.name + ".part")
        part.write_bytes(raw)
        os.replace(part, out)
        x["status"], x["file"] = "COMPLETED", str(out.relative_to(HERE))
        if x["kind"] == "draft" and not x.get("draft_expires_at"):
            x["draft_expires_note"] = f"upgrade within {DRAFT_DAYS} days of {x['submitted'][:10]}"
        say(f"saved {x['file']}" + ("  (unexpected file type; check it)" if ext == ".bin" else ""))
        save_state(st)
    save_state(st)
    return [x for x in st["submissions"] if x.get("status") not in DONE]


def cmd_fetch(args):
    wait = take_flag(args, "--wait")
    minutes = take_option(args, "--timeout", float, 60.0)
    st = load_state()
    if not st["submissions"]:
        say("Nothing has been submitted from this folder.")
        return
    left = fetch_once(st)
    deadline = time.monotonic() + minutes * 60
    while left and wait and time.monotonic() < deadline:
        time.sleep(20)
        left = fetch_once(st)
    failed = [x for x in st["submissions"] if x.get("status") == "FAILED"]
    say("Nothing still running." if not left else f"{len(left)} still running; run fetch again later.")
    if failed:
        say(f"{len(failed)} refused or failed; `status` shows why. A refused job is not retried.")


def cmd_status(args):
    st = load_state()
    subs = st["submissions"]
    if not subs:
        say("Nothing has been submitted from this folder.")
        return
    for x in subs:
        exp = ""
        if x["kind"] == "draft" and x.get("status") == "COMPLETED":
            exp = f"  upgrade by {x['draft_expires_at']}" if x.get("draft_expires_at") else (
                f"  {x['draft_expires_note']}" if x.get("draft_expires_note") else "")
        why = f"  {x['error']}" if x.get("error") else ""
        cost = money(x["quoted_usd"]) if isinstance(x.get("quoted_usd"), (int, float)) else ""
        say(f"{x['job']:<20} {x['kind']:<6} take {x['take']:<3} {x.get('status', ''):<10} {cost:>7}  {x.get('file') or ''}{exp}{why}")
    priced = [x for x in subs if isinstance(x.get("quoted_usd"), (int, float)) and math.isfinite(x["quoted_usd"])]
    total = sum(x["quoted_usd"] for x in priced)
    failed = sum(x["quoted_usd"] for x in priced if x.get("status") == "FAILED")
    say(f"\nQuoted spend from this folder: ${total:.2f}" + (
        f", of which ${failed:.2f} went to refused or failed jobs (billing for those is unknown)" if failed else "")
        + ". Your Venice account has the real charges.")


COMMANDS = {"doctor", "new", "check", "screens", "list", "show", "quote", "fetch", "status", *PAID}
NEEDS_SCRIPT = {"check": cmd_check, "list": cmd_list, "show": cmd_show, "quote": cmd_quote,
                "stills": cmd_stills, "draft": cmd_draft, "upgrade": cmd_upgrade, "music": cmd_music}
NO_SCRIPT = {"doctor": cmd_doctor, "screens": cmd_screens, "fetch": cmd_fetch, "status": cmd_status}


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if not args or args[0] in ("-h", "--help", "help"):
        say(__doc__)
        return 0
    if args[0] in ("-V", "--version", "version"):
        say(VERSION)
        return 0
    try:
        folder = scenario_dir(args) if "--dir" in args else None
        APPROVAL["cap"] = take_option(args, "--approve-up-to", dollars)
        cmd, rest = args[0], args[1:]
        if cmd not in COMMANDS:
            die(f"Unknown command: {cmd}. Run with --help to see the commands.")
        if APPROVAL["cap"] is not None and cmd not in PAID:
            die("--approve-up-to only applies to stills, draft, upgrade and music.")
        if cmd == "new":
            cmd_new(rest)
            return 0
        set_folder(folder or scenario_dir(rest))
        if cmd in NO_SCRIPT:
            NO_SCRIPT[cmd](rest)
        else:
            NEEDS_SCRIPT[cmd](load_script(), rest)
        return 0
    except Stop as e:
        print(e.message, file=sys.stderr, flush=True)
        return e.code
    except KeyboardInterrupt:
        print("\nStopped. Anything already queued keeps running at Venice; run `fetch` later.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
