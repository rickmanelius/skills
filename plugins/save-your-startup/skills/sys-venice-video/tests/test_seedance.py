"""Offline tests for scripts/seedance.py. Nothing here calls Venice: the HTTP layer is replaced by a fake.

Run from the skill folder:  python3 -m unittest discover -s tests -v
"""
import base64
import contextlib
import importlib.util
import io
import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest import mock

SKILL = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("seedance", SKILL / "scripts" / "seedance.py")
sd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sd)

FENCE = "`" * 3


def block(tag, body):
    return f"{FENCE}{tag}\n{body}\n{FENCE}\n"


def png(w, h):
    raw = b"".join(b"\x00" + b"\x00" * (w * 3) for _ in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def jpeg_header(w, h):
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    sof = b"\xff\xc0" + struct.pack(">HBHHB", 17, 8, h, w, 3) + b"\x01\x11\x00\x02\x11\x01\x03\x11\x01"
    return b"\xff\xd8" + app0 + sof + b"\xff\xd9"


def ok(payload):
    return 200, "application/json", json.dumps(payload).encode(), {}


def err(code, message):
    return code, "application/json", json.dumps({"error": message}).encode(), {}


class FakeVenice:
    """Stands in for seedance.request. routes: path (without query) -> response tuple, callable or exception."""

    def __init__(self, routes):
        self.routes, self.calls = routes, []

    def __call__(self, path, body=None, method="POST", timeout=600):
        self.calls.append((path, body))
        r = self.routes[path.split("?")[0]]
        if callable(r) and not isinstance(r, tuple):
            r = r(body)
        if isinstance(r, Exception):
            raise r
        return r

    def paths(self):
        return [p for p, _ in self.calls]


MODELS = ok({"data": [{"id": "nano-banana-pro", "model_spec": {"pricing": {"resolutions": {"2K": {"usd": 0.23}}}}}]})

SCRIPT = (
    block("json refs", json.dumps({
        "C1-set": {"file": "refs/cast/C1-set.jpg", "caption": "the kitchen"},
        "P1-face": {"file": "refs/cast/P1-face.jpg", "caption": "Ana, the founder", "person": True},
    }))
    + block("text negative", "readable text, logos")
    + block("json job", '{"id": "C1-set", "kind": "still", "model": "nano-banana-pro", "aspect_ratio": "16:9", "resolution": "2K"}')
    + block("text prompt C1-set", "Photoreal film still, no people: a small kitchen at dawn.")
    + block("json job", '{"id": "V1-open", "kind": "video", "cuts": [30], "model": "seedance-2-5-reference-to-video-basic", "duration": "10s", "aspect_ratio": "16:9", "audio": true, "refs": ["C1-set"]}')
    + block("text prompt V1-open", "Shot 1, 0 to 10 seconds: steam rises from a mug.")
    + block("json job", '{"id": "V2-close", "kind": "video", "cuts": ["30"], "model": "seedance-2-5-reference-to-video-basic", "duration": "5s", "refs": ["C1-set"]}')
    + block("text prompt V2-close", "Shot 1, 0 to 5 seconds: the mug, close.")
    + block("json job", '{"id": "V3-face", "kind": "video", "model": "seedance-2-5-reference-to-video-basic", "duration": "5s", "refs": ["P1-face"]}')
    + block("text prompt V3-face", "Shot 1: Ana smiles.")
    + block("json job", '{"id": "M30", "kind": "music", "model": "sonilo-v1-1-music", "duration_seconds": 30}')
    + block("text prompt M30", "Warm, sparse piano, 90 BPM. No vocals.")
)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name).resolve()
        (self.dir / "refs" / "cast").mkdir(parents=True)
        (self.dir / "SCRIPT.md").write_text(SCRIPT, encoding="utf-8")
        (self.dir / "refs" / "cast" / "C1-set.jpg").write_bytes(jpeg_header(1600, 900))
        (self.dir / "refs" / "cast" / "P1-face.jpg").write_bytes(jpeg_header(1024, 1024))
        sd._IMAGE_MODELS = None
        sd.set_folder(self.dir)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *argv, fake=None, stdin=""):
        out, errs = io.StringIO(), io.StringIO()
        patches = [mock.patch("sys.stdin", io.StringIO(stdin))]
        if fake is not None:
            patches.append(mock.patch.object(sd, "request", fake))
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            stack.enter_context(contextlib.redirect_stdout(out))
            stack.enter_context(contextlib.redirect_stderr(errs))
            code = sd.main(list(argv) + ["--dir", str(self.dir)])
        return code, out.getvalue(), errs.getvalue()

    def state(self):
        return json.loads((self.dir / "out" / "state.json").read_text())

    def write_state(self, subs):
        (self.dir / "out").mkdir(exist_ok=True)
        (self.dir / "out" / "state.json").write_text(json.dumps({"submissions": subs}))


class ParseAndValidate(Base):
    def parse(self, text):
        return sd.validate(sd.parse_script(text))

    def test_fixture_is_valid_with_one_person_warning(self):
        s = self.parse(SCRIPT)
        self.assertEqual(s.errors, [])
        self.assertTrue(any("V3-face" in w and "person" in w for w in s.warnings))
        self.assertEqual(next(j for j in s.jobs if j["id"] == "V1-open")["cuts"], ["30"])

    def test_shipped_template_parses_and_flags_replace(self):
        text = (SKILL / "templates" / "SCRIPT.md").read_text(encoding="utf-8")
        s = self.parse(text.replace("{{NAME}}", "x").replace("{{DATE}}", "2026-11-17"))
        self.assertEqual(s.errors, [])
        self.assertEqual({j["kind"] for j in s.jobs}, {"still", "video", "music"})
        self.assertTrue(any("REPLACE" in w for w in s.warnings))

    def test_windows_line_endings(self):
        s = self.parse(SCRIPT.replace("\n", "\r\n"))
        self.assertEqual(s.errors, [])
        self.assertEqual(len(s.jobs), 5)

    def test_reference_paths_must_stay_inside_the_folder(self):
        for bad in ("../secret.png", "/etc/passwd.png", "~/.ssh/id.png", "refs/notes.txt", "refs/../../x.jpg"):
            text = SCRIPT.replace("refs/cast/P1-face.jpg", bad)
            s = self.parse(text)
            self.assertTrue(any("P1-face" in e for e in s.errors), bad)

    def test_symlink_out_of_the_folder_is_refused(self):
        outside = Path(tempfile.mkdtemp()) / "private.jpg"
        outside.write_bytes(jpeg_header(800, 800))
        link = self.dir / "refs" / "cast" / "link.jpg"
        link.symlink_to(outside)
        s = self.parse(SCRIPT.replace("refs/cast/P1-face.jpg", "refs/cast/link.jpg"))
        self.assertTrue(any("leaves the scenario folder" in e for e in s.errors))

    def test_unknown_reference_and_missing_prompt_are_errors_not_crashes(self):
        text = SCRIPT.replace('"refs": ["C1-set"]}', '"refs": ["NOPE"]}', 1).replace("text prompt M30", "text prompt M31")
        s = self.parse(text)
        self.assertTrue(any("NOPE" in e for e in s.errors))
        self.assertTrue(any("M30" in e and "prompt" in e for e in s.errors))

    def test_duplicate_ids_and_bad_duration(self):
        text = SCRIPT.replace('"id": "V2-close"', '"id": "V1-open"').replace('"duration": "5s"', '"duration": 5', 1)
        s = self.parse(text)
        self.assertTrue(any("used twice" in e for e in s.errors))
        self.assertTrue(any("duration" in e for e in s.errors))

    def test_bad_json_names_the_line(self):
        s = self.parse(block("json job", '{"id": "X", }'))
        self.assertTrue(s.errors and s.errors[0].startswith("line 1"))

    def test_inline_mentions_of_blocks_are_not_parsed(self):
        s = self.parse("Use a ```` ```json job ```` block.\n" + SCRIPT)
        self.assertEqual(s.errors, [])

    def test_composed_prompt(self):
        s = self.parse(SCRIPT)
        v1 = next(j for j in s.jobs if j["id"] == "V1-open")
        self.assertTrue(sd.composed_prompt(v1, s.refs).startswith(
            "Refer to the kitchen in <Image 1> to generate the video described below.\n\n"))
        v3 = next(j for j in s.jobs if j["id"] == "V3-face")
        self.assertIn("<Subject 1> in <Image 1> (Ana, the founder)", sd.composed_prompt(v3, s.refs))

    def test_select_prefers_an_exact_id(self):
        s = self.parse(SCRIPT)
        self.assertEqual([j["id"] for j in sd.select(s, ["V1"], ("video",))], ["V1-open"])
        self.assertEqual([j["id"] for j in sd.select(s, ["30"], ("video",))], ["V1-open", "V2-close"])


class Images(Base):
    def test_sizes(self):
        p = self.dir / "a.png"
        p.write_bytes(png(640, 360))
        self.assertEqual(tuple(sd.image_size(p)), (640, 360))
        self.assertEqual(tuple(sd.image_size(self.dir / "refs" / "cast" / "C1-set.jpg")), (1600, 900))
        (self.dir / "junk.jpg").write_bytes(b"not an image")
        self.assertIsNone(sd.image_size(self.dir / "junk.jpg"))

    def test_reference_limits(self):
        (self.dir / "refs" / "cast" / "C1-set.jpg").write_bytes(jpeg_header(200, 200))
        s = sd.load_script()
        v1 = next(j for j in s.jobs if j["id"] == "V1-open")
        self.assertTrue(any("300 px" in p for p in sd.ref_problems(v1, s.refs)))
        (self.dir / "refs" / "cast" / "C1-set.jpg").write_bytes(jpeg_header(3000, 1000))
        self.assertTrue(any("0.4 and 2.5" in p for p in sd.ref_problems(v1, s.refs)))


class Approval(Base):
    def video_fake(self, quote=1.29):
        return FakeVenice({"/video/quote": ok({"quote": quote}), "/video/queue": ok({"queue_id": "q-1", "model": "m"})})

    def test_no_terminal_and_no_approval_submits_nothing(self):
        fake = self.video_fake()
        code, out, errs = self.run_cli("draft", "V1-open", fake=fake)
        self.assertEqual(code, sd.NEEDS_APPROVAL)
        self.assertNotIn("/video/queue", fake.paths())
        self.assertIn("--approve-up-to 1.29", errs)
        self.assertFalse((self.dir / "out" / "state.json").exists())

    def test_approval_below_the_quote_refuses(self):
        fake = self.video_fake()
        code, _, errs = self.run_cli("draft", "V1-open", "--approve-up-to", "1.00", fake=fake)
        self.assertEqual(code, sd.NEEDS_APPROVAL)
        self.assertNotIn("/video/queue", fake.paths())
        self.assertIn("more than the $1.00 approved", errs)

    def test_approval_covering_the_quote_queues_and_records_the_price(self):
        fake = self.video_fake()
        code, out, _ = self.run_cli("draft", "V1-open", "--approve-up-to", "$1.29", fake=fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.paths().count("/video/queue"), 1)
        body = next(b for p, b in fake.calls if p == "/video/queue")
        self.assertTrue(body["reference_image_urls"][0].startswith("data:image/jpeg;base64,"))
        self.assertEqual(body["negative_prompt"], "readable text, logos")
        sub = self.state()["submissions"][0]
        self.assertEqual((sub["job"], sub["take"], sub["status"], sub["quoted_usd"]), ("V1-open", 1, "PROCESSING", 1.29))

    def test_a_missing_price_never_spends(self):
        fake = FakeVenice({"/video/quote": ok({}), "/video/queue": ok({"queue_id": "q"})})
        code, _, errs = self.run_cli("draft", "V1-open", "--approve-up-to", "100", fake=fake)
        self.assertEqual(code, 1)
        self.assertNotIn("/video/queue", fake.paths())

    def test_typed_no_at_a_terminal_stops(self):
        fake = self.video_fake()
        tty = io.StringIO("no\n")
        tty.isatty = lambda: True
        with mock.patch("sys.stdin", tty), mock.patch.object(sd, "request", fake), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = sd.main(["draft", "V1-open", "--dir", str(self.dir)])
        self.assertEqual(code, 1)
        self.assertNotIn("/video/queue", fake.paths())

    def test_approval_flag_is_refused_on_free_commands(self):
        code, _, errs = self.run_cli("quote", "--approve-up-to", "5", fake=self.video_fake())
        self.assertEqual(code, 1)

    def test_person_reference_is_refused_before_any_call(self):
        fake = self.video_fake()
        code, _, errs = self.run_cli("draft", "V3-face", "--approve-up-to", "100", fake=fake)
        self.assertEqual(code, 1)
        self.assertEqual(fake.calls, [])
        self.assertIn("person", errs)

    def test_unwritten_prompt_is_refused(self):
        (self.dir / "SCRIPT.md").write_text(SCRIPT.replace("steam rises", "REPLACE steam rises"))
        fake = self.video_fake()
        code, _, errs = self.run_cli("draft", "V1-open", "--approve-up-to", "100", fake=fake)
        self.assertEqual(code, 1)
        self.assertNotIn("/video/queue", fake.paths())

    def test_batch_waits_for_a_probe(self):
        fake = self.video_fake()
        code, _, errs = self.run_cli("draft", "30", "--approve-up-to", "100", fake=fake)
        self.assertEqual(code, 1)
        self.assertIn("Probe one first", errs)
        self.assertNotIn("/video/queue", fake.paths())
        code, _, _ = self.run_cli("draft", "30", "--no-probe", "--approve-up-to", "2.58", fake=fake)
        self.assertEqual(code, 0)
        self.assertEqual(fake.paths().count("/video/queue"), 2)

    def test_batch_after_a_finished_probe(self):
        self.write_state([{"job": "V2-close", "kind": "draft", "take": 1, "queue_id": "q0", "model": "m",
                           "status": "COMPLETED", "file": "out/drafts/x.mp4", "submitted": "2026-11-17T00:00:00+00:00"}])
        fake = self.video_fake()
        code, _, _ = self.run_cli("draft", "V1-open", "--takes", "2", "--approve-up-to", "2.58", fake=fake)
        self.assertEqual(code, 0)
        takes = [x["take"] for x in self.state()["submissions"] if x["job"] == "V1-open"]
        self.assertEqual(takes, [1, 2])


class Stills(Base):
    def test_stills_save_the_image_and_replace_moves_the_old_one_aside(self):
        img = base64.b64encode(jpeg_header(1600, 900)).decode()
        fake = FakeVenice({"/models": MODELS, "/image/generate": ok({"images": [img]})})
        code, out, _ = self.run_cli("stills", "C1-set", "--replace", "--approve-up-to", "0.23", fake=fake)
        self.assertEqual(code, 0, out)
        cast = sorted(p.name for p in (self.dir / "refs" / "cast").iterdir())
        self.assertIn("C1-set.jpg", cast)
        self.assertTrue(any(n.startswith("C1-set-old-") for n in cast))
        sub = self.state()["submissions"][0]
        self.assertEqual((sub["kind"], sub["status"], sub["quoted_usd"]), ("still", "COMPLETED", 0.23))

    def test_a_refused_still_is_recorded_and_reported(self):
        fake = FakeVenice({"/models": MODELS, "/image/generate": err(400, "bad prompt")})
        code, out, _ = self.run_cli("stills", "--approve-up-to", "0.23", fake=fake)
        self.assertEqual(code, 1)
        self.assertEqual(self.state()["submissions"][0]["status"], "FAILED")


class Music(Base):
    def test_quote_leaves_out_the_prompt_and_the_queue_sends_it(self):
        fake = FakeVenice({"/audio/quote": ok({"quote": 0.09}), "/audio/queue": ok({"queue_id": "q-m"})})
        code, _, _ = self.run_cli("music", "--approve-up-to", "0.09", fake=fake)
        self.assertEqual(code, 0)
        quote = next(b for p, b in fake.calls if p == "/audio/quote")
        queue = next(b for p, b in fake.calls if p == "/audio/queue")
        self.assertNotIn("prompt", quote)
        self.assertEqual(queue["prompt"], "Warm, sparse piano, 90 BPM. No vocals.")
        self.assertEqual(self.state()["submissions"][0]["quoted_usd"], 0.09)


class Fetch(Base):
    def test_fetch_handles_refusals_retries_and_downloads(self):
        self.write_state([
            {"job": "V1-open", "kind": "draft", "take": 1, "queue_id": "refused", "model": "m", "status": "PROCESSING", "file": None, "submitted": "2026-11-17T00:00:00+00:00"},
            {"job": "V1-open", "kind": "draft", "take": 2, "queue_id": "busy", "model": "m", "status": "PROCESSING", "file": None, "submitted": "2026-11-17T00:00:00+00:00"},
            {"job": "V1-open", "kind": "draft", "take": 3, "queue_id": "offline", "model": "m", "status": "PROCESSING", "file": None, "submitted": "2026-11-17T00:00:00+00:00"},
            {"job": "V1-open", "kind": "draft", "take": 4, "queue_id": "done", "model": "m", "status": "PROCESSING", "file": None, "submitted": "2026-11-17T00:00:00+00:00"},
            {"job": "V1-open", "kind": "draft", "take": 5, "queue_id": "running", "model": "m", "status": "PROCESSING", "file": None, "submitted": "2026-11-17T00:00:00+00:00"},
        ])

        def retrieve(body):
            return {
                "refused": err(422, "Your prompt violates the content policy"),
                "busy": err(503, "try later"),
                "offline": OSError("network is down"),
                "done": (200, "video/mp4", b"\x00\x00\x00\x18ftypmp42rest", {}),
                "running": ok({"status": "PROCESSING", "execution_duration": 30000, "average_execution_time": 90000,
                               "draft_expires_at": "2026-11-24T00:00:00Z"}),
            }[body["queue_id"]]

        code, out, _ = self.run_cli("fetch", fake=FakeVenice({"/video/retrieve": retrieve}))
        self.assertEqual(code, 0)
        subs = {x["take"]: x for x in self.state()["submissions"]}
        self.assertEqual(subs[1]["status"], "FAILED")
        self.assertIn("422", subs[1]["error"])
        self.assertEqual(subs[2]["status"], "PROCESSING")
        self.assertEqual(subs[3]["status"], "PROCESSING")
        self.assertEqual((subs[4]["status"], subs[4]["file"]), ("COMPLETED", "out/drafts/V1-open-take4.mp4"))
        self.assertTrue((self.dir / "out" / "drafts" / "V1-open-take4.mp4").exists())
        self.assertEqual(subs[5]["draft_expires_at"], "2026-11-24T00:00:00Z")

    def test_fetch_and_status_work_without_a_valid_script(self):
        (self.dir / "SCRIPT.md").write_text(block("json job", "{broken"))
        self.write_state([{"job": "V1-open", "kind": "draft", "take": 1, "queue_id": "q", "model": "m",
                           "status": "COMPLETED", "file": "x.mp4", "submitted": "2026-11-17T00:00:00+00:00", "quoted_usd": 1.29}])
        code, out, _ = self.run_cli("status")
        self.assertEqual(code, 0)
        self.assertIn("$1.29", out)


class Upgrade(Base):
    def draft(self, **over):
        sub = {"job": "V1-open", "kind": "draft", "take": 1, "queue_id": "q-draft", "model": "m",
               "status": "COMPLETED", "file": "out/drafts/V1-open-take1.mp4", "submitted": "2026-11-17T00:00:00+00:00"}
        sub.update(over)
        return sub

    def fake(self):
        return FakeVenice({"/video/quote": ok({"quote": 7.11}), "/video/queue": ok({"queue_id": "q-final"})})

    def test_unfinished_and_expired_drafts_are_refused(self):
        for sub, words in ((self.draft(status="PROCESSING"), "only a finished draft"),
                           (self.draft(draft_expires_at="2020-01-01T00:00:00Z"), "expired")):
            self.write_state([sub])
            fake = self.fake()
            code, _, errs = self.run_cli("upgrade", "V1-open", "1", "--approve-up-to", "10", fake=fake)
            self.assertEqual(code, 1)
            self.assertIn(words, errs)
            self.assertNotIn("/video/queue", fake.paths())

    def test_upgrade_sends_the_draft_id_once(self):
        self.write_state([self.draft()])
        fake = self.fake()
        code, _, _ = self.run_cli("upgrade", "V1-open", "1", "--approve-up-to", "7.11", fake=fake)
        self.assertEqual(code, 0)
        body = next(b for p, b in fake.calls if p == "/video/queue")
        self.assertEqual((body["draft_task_id"], body["resolution"]), ("q-draft", "1080p"))
        code, _, errs = self.run_cli("upgrade", "V1-open", "1", "--approve-up-to", "7.11", fake=self.fake())
        self.assertEqual(code, 1)
        self.assertIn("already upgraded", errs)


class NewAndScreens(Base):
    def test_new_scaffolds_a_working_folder_and_refuses_to_overwrite(self):
        dest = self.dir / "work"
        out, errs = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(errs):
            self.assertEqual(sd.main(["new", "launch-spot", "--dest", str(dest)]), 0)
            folder = dest / "launch-spot"
            text = (folder / "SCRIPT.md").read_text()
            self.assertIn("# launch-spot ·", text)
            self.assertNotIn("{{", text)
            for name in ("screens.html", "seedance.py", ".gitignore", ".kit-version"):
                self.assertTrue((folder / name).exists(), name)
            self.assertIn("out/drafts/", (folder / ".gitignore").read_text())
            self.assertEqual(sd.main(["new", "launch-spot", "--dest", str(dest)]), 1)
            self.assertEqual(sd.main(["new", "../escape", "--dest", str(dest)]), 1)

    def test_new_from_an_earlier_folder_with_its_cast(self):
        dest = self.dir / "work"
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = sd.main(["new", "sequel", "--dest", str(dest), "--from", str(self.dir),
                            "--cast-from", str(self.dir / "refs" / "cast")])
        self.assertEqual(code, 0)
        self.assertEqual((dest / "sequel" / "SCRIPT.md").read_text(), SCRIPT)
        self.assertTrue((dest / "sequel" / "refs" / "cast" / "C1-set.jpg").exists())

    def test_screens_needs_a_name_on_every_frame_before_starting_chrome(self):
        (self.dir / "screens.html").write_text('<section class="frame" data-name="S1">a</section><section class="frame">b</section>')
        with mock.patch.object(sd, "find_chrome", side_effect=AssertionError("should not look for Chrome")):
            code, _, errs = self.run_cli("screens")
        self.assertEqual(code, 1)
        self.assertIn("no data-name", errs)


class Hygiene(unittest.TestCase):
    def test_the_key_is_redacted_from_error_text(self):
        with mock.patch.dict("os.environ", {"VENICE_API_KEY": "sk-secret-123", "VENICE_KEY_ENV": ""}):
            self.assertNotIn("sk-secret-123", sd.error_text(b'{"error": "bad key sk-secret-123"}'))

    def test_no_em_or_en_dashes_in_the_skill(self):
        for path in SKILL.rglob("*"):
            if path.is_file() and path.suffix in (".md", ".py", ".html", ".yaml"):
                text = path.read_text(encoding="utf-8")
                for dash in (chr(0x2014), chr(0x2013)):
                    self.assertNotIn(dash, text, f"{path} has an em or en dash")


if __name__ == "__main__":
    unittest.main()
