# What we know about making ads with Venice and Seedance

Field notes from the first commercials made with this kit (November 2026): a 30 second spot that shipped to
social media, and a second one scripted and quoted. Read this before writing a new `SCRIPT.md`. Facts about
Venice are dated. Models, prices and limits move, so re-read the live sources named below, and run `quote`,
before relying on a number.

## 1. The five rules that cost us time

1. **No people in any media sent to Seedance through the public API.** Venice's Seedance guide
   (https://docs.venice.ai/guides/media/seedance-2-0.md, read 2026-11-16): "Person-bearing media is not
   supported on the public Seedance API. Public `*-basic` models do not use consent attestation ... Such
   inputs may be rejected upstream as a content-policy or provider error. Use the Venice app or Studio for
   the full Seedance feature set." Every Seedance model on the API is `-basic`. Our first eight drafts each
   carried a character sheet; Venice **accepted them at queue and refused them at retrieve** with
   `422 Your prompt violates the content policy of Venice.ai or the model provider`. People go in the text
   only. This covers references, start frames and end frames.
2. **Faces stay consistent inside one generation, not across generations.** Without face references, separate
   clips each invent their own person. Put a whole stretch of story with one face in one clip (a 30 s
   multi-shot generation held the hero steady across eight shots), and in other clips show that person only
   from behind or over the shoulder.
3. **Video models cannot write.** Every readable word (an email, an app, a dashboard, a receipt, a reply) is
   a clean 1920 x 1080 insert rendered from HTML and cut in during the edit. The same inserts can go to
   Seedance as references so the screens it draws have the right shape and colour; prompts say every screen
   stays "a soft, unreadable glow".
4. **Probe with one cheap draft before a batch.** We queued eight drafts at once and all eight failed for the
   same reason. One 480p draft of the cheapest job proves the request first. The tool now refuses a batch
   until one draft in the folder has finished (`--no-probe` overrides it).
5. **Prove request shapes on the wire with the free quote endpoints.** The audio quote rejects a `prompt`
   field that the audio queue requires; only a live call showed it.

## 2. The workflow that shipped

| Step | What | Command |
|---|---|---|
| 0 | The story: WIIFM order (the should is never sold, the want leads, the need is shown briefly); every scene answers "so what?". Write it as shots with seconds. | `SCRIPT.md` |
| 1 | Screens: the readable beats as HTML frames, rendered to PNG for free. Look at every one. | `screens` |
| 2 | Quote everything (free). | `quote all` |
| 3 | Stills: sets and objects (and, for the web app only, four-view character sheets) with Nano Banana Pro at 2K. Look at every one; redo bad ones with `--replace`. | `stills` |
| 4 | One probe draft, then 2 or 3 takes of each clip at 480p. | `draft <id>`, then `draft <cut> --takes 2` |
| 5 | Download, review, pick a take per clip. | `fetch --wait` |
| 6 | Upgrade the chosen takes within 7 days (same take, same motion). | `upgrade <id> <take>` |
| 7 | Music: Sonilo (licensed, commercial-use safe), instrumental. | `music` |
| 8 | Edit to the decision list in `SCRIPT.md`: clips, inserts with a slow push-in, the super, the end card, music ducked under key sounds. | an editor |
| 9 | Post; record what shipped in the folder's `RESULT.md`. | |

## 3. Venice API, as verified 2026-11-16

Base `https://api.venice.ai/api/v1`, `Authorization: Bearer <key>`. Docs index:
https://docs.venice.ai/llms.txt (append `.md` to any docs page for clean text). Some keys can generate and
others cannot; if a call returns 401, try another key from the same account before debugging the request.

**Models and limits** (`GET /models?type=video|image|music|tts`; image and music prices are in each model's
`model_spec.pricing`; video prices come only from the quote endpoint):

| Model | Use | Limits read on 2026-11-16 |
|---|---|---|
| `seedance-2-5-reference-to-video-basic` | Video from references | 4 to 30 s; up to 30 reference images and 10 videos; 480p, 720p, 1080p, 4k; aspect 21:9 to 9:16; prompt up to 15,000 characters; native audio; draft mode |
| `seedance-2-5-image-to-video-basic` | Video from a start (and end) frame | 4 to 30 s |
| `seedance-2-5-text-to-video-basic` | Video from text | 4 to 30 s |
| `seedance-2-5-flash-reference-to-video-basic` | Cheaper reference-to-video | up to 720p, 10 references |
| `seedance-2-0-*-basic` | Older family | 4 to 15 s; reference-to-video up to 9 images, 3 videos |
| `nano-banana-pro` | Stills | 1K, 2K, 4K; many aspect ratios |
| `sonilo-v1-1-music` | Music | per second; licensed, commercial-use safe |

Reference images: short side at least 300 px; width over height strictly between 0.4 and 2.5 (the tool
checks both). Large files make heavy requests; the tool sends a 1536 px JPEG copy of anything over 1.5 MB
(with macOS `sips`, ImageMagick or Pillow, whichever is installed).

**Endpoints and fields the tool uses**

- `POST /video/quote` `{model, duration, aspect_ratio?, resolution, audio, draft?, draft_task_id?}` returns
  `{"quote": dollars}`. Free.
- `POST /video/queue` `{model, prompt, negative_prompt, duration, aspect_ratio, resolution, audio,
  draft: true, reference_image_urls[], image_url?, end_image_url?, omni_reference_task_type?}` returns
  `{model, queue_id}`. References as `data:` URLs work. `omni_reference_task_type`: `reference`, `edit`,
  `extend` or `auto` (Seedance 2.5 reference-to-video); we send `reference`.
- `POST /video/retrieve` `{queue_id, model}` returns JSON `{status: PROCESSING, execution_duration,
  average_execution_time, draft_expires_at ...}` while running and the MP4 bytes when done. A refusal
  arrives here as an HTTP 422.
- Draft mode (Seedance 2.5): `draft: true` makes a fast 480p clip; send its `queue_id` as `draft_task_id` on a
  new queue call (with the final resolution) within 7 days to upgrade that exact take. Duration, aspect and
  audio follow the draft; media inputs are ignored; billed separately.
- `POST /image/generate` `{model, prompt, aspect_ratio, resolution, format: jpeg, variants, hide_watermark}`
  returns `{images: [base64 ...]}`.
- `POST /audio/quote` `{model, duration_seconds}` (**no `prompt`**); `POST /audio/queue` `{model, prompt,
  duration_seconds}`; `POST /audio/retrieve` `{queue_id, model}` returns JSON while running, audio when done.
- Usage history (`GET /billing/usage-history`) needs an **admin** key; an inference key is refused with
  "Admin API key required". Check charges in the Venice app. `seedance.py status` adds up what the tool
  was quoted, which is the next best thing.
- Face consent (`consents.seedance`, a free `409 needs_consent` then a resubmit) exists only for non-public
  Seedance 2.0 models; it is not available on the public API.

**Prices quoted 2026-11-16** (re-quote; the tool does it): Seedance 2.5 reference-to-video 1080p $0.711 per
second ($21.32 for 30 s), 720p $0.289, 480p draft $0.129 ($3.86 for 30 s); Flash 720p $0.189; audio on or
off costs the same. Nano Banana Pro $0.18 at 1K, $0.23 at 2K. Sonilo about $0.003 per second ($0.09 for 30 s).

## 4. Prompt craft that worked (Seedance 2.5)

- **Open with the canonical reference line**, case-sensitive, which the tool builds from the reference list:
  `Refer to the kitchen and morning light in <Image 1>, the plain white mug in <Image 2> ... to generate
  the video described below.` People (web app only) are `<Subject N> in <Image N>`. Keep captions short.
- **Then the frame:** "A photoreal cinematic 30 second commercial told in eight shots, natural colour grade,
  soft contrast, shallow depth of field, gentle handheld camera, set in ..."
- **Describe each person once, fully, and say they are the same in every shot**: age, hair, skin, glasses,
  clothes; "the same face, hair, glasses and clothes".
- **Shots with seconds**: "Shot 3, 8 to 10 seconds: ..." Two to eight shots per clip worked. Give framing,
  action and light in each.
- **An audio line with timed cues**: "a soft notification chime at 1 second", "one long audible sigh at about
  5 seconds", then "No music. No speech." (music comes separately). A spoken word goes in quotes with its
  second.
- **Screens and logos**: "Every screen stays a soft, unreadable glow. No object has a logo."
- **Negative prompt** (shared): readable text, logos, watermarks, extra fingers, warped face, the face
  changing between shots, flicker, cartoon, 3D render, plastic skin.
- Readable story beats belong to inserts; leave the generated clip a second of slack either side.

## 5. Stills (Nano Banana Pro, 2K)

- People-free set and object stills are the API's references: "Photoreal film still, no people: ..." Check
  each one for stray people (an office still with "a few people arriving" is a person reference) and for
  logos.
- Four-view character sheets ("the same person shown four times side by side: front, three-quarter, left
  profile, full body ... the identical face in all four views") came out excellent and consistent. They are
  for the Venice web app, which takes face media with a one-time consent.
- Say what the place is not: our first security room came out as a grimy bunker with CRT monitors. The fix
  was "modern, clean ... no old equipment".
- `stills <id> --replace` moves the old image aside (`-old-<time>`) only after approval.

## 6. Screens, inserts and end cards

- Built as HTML (`screens.html`), one `class="frame"` element with a `data-name` per PNG, rendered 1920 x
  1080 by headless Chrome (`seedance.py screens`). Free, exact, re-renderable.
- Generic UI only for other companies' apps: no real mail app's look, no third-party logos. Your own
  product's real screens are fair, rebuilt from its published screenshots with sample values labelled.
- Fictional names; numbers labelled "Sample data". End cards carry "Dramatization."
- Big type: anything the viewer must read in two seconds is at least 44 px at 1080p. A 1x screenshot of a
  social post (about 590 px wide) lands at about 16 px in a 1080p frame, so rebuild it in HTML instead.
- A real public post used as an insert keeps its exact text and date and is credited. Never invent a post,
  quote or endorsement and attribute it to a real person or company.

## 7. The creative method (WIIFM)

From the WIIFM chapter of *Save Your Startup* (and `/sys:wiifm-check`): sell the want, prove the need, never
lead with the should. In our first spot, a policy email banning a tool was the should, a calm dashboard and a
relieved smile were the want, and a short receipt of what the product had done was the need. Each beat climbs
the so-what ladder to something the viewer wants. Honesty rules: show only what the product does today; a
time-lapse is not a speed claim; fictional data says so.

## 8. The edit

- A decision list in `SCRIPT.md`: timeline, source clip and seconds, what the viewer sees. 30 s held 14 cuts;
  60 s held 24.
- Inserts get a slow push-in from 100% to about 106%. One lower-third super. End card 2 s.
- Music ducked about 8 dB under the key sounds (a sigh, a spoken word); silence under the punchline.
- Vertical: redraft at 9:16; inserts become a card on a blurred background.
- **Pick in-points from frames, not from the script's shot timings.** Pull frames with
  `ffmpeg -ss <t> -i take.mp4 -frames:v 1 frame.png` and look at them; in our first spot the lean-back
  started at 24 s, not the 22.8 s the shot timings implied.
- **Seedance footage inside a code-rendered explainer** (for example HyperFrames) works: a 480p draft scaled
  to cover 1080p is soft but holds for social, and the clip's native audio comes through. The scenes around
  the footage need their own music bed, or the film goes silent between clips.

## 9. What a first spot cost (approximate)

Stills 10 x $0.23 = $2.30 (nine plus one redo). Eight refused drafts about $9.28, **billing unknown**
(refused after queuing). One 30 s clip, two 480p takes, $7.72. About $10 known, about $19 if the refused
drafts were billed. A 1080p upgrade of that clip quotes at $21.32 on top. Budget for the upgrade before you
fall in love with a draft.

## 10. Patterns from the second spot (scripted and quoted, not yet generated)

- **A 2x2 grid of different people**: one short clip per person (10 s), the same shot timings in every
  prompt (find it 0 to 4 s, use it 4 to 7 s, the line at 8 s) so the cells play in sync; slip each clip in
  the edit so the spoken lines land on one frame.
- **`final_resolution` per job**: a grid cell is 960 x 540, so `upgrade` makes it 720p ($0.289 a second,
  $2.89 for 10 s, quoted on the wire) instead of 1080p ($7.11).
- **Spoken lines** are untested with Seedance 2.5 on Venice; make the first probe draft a clip with a line.
  Fallback: cut away from the mouth, or record the line.
- **Sound marks**: never use a real brand's signature sound (a well-known computer startup chime is a
  registered sound mark); ask for a generic one in the prompt.

## 11. Open questions

- Whether the Venice web app runs Seedance 2.5 with face references (the docs name 2.0 for consent).
- Whether refused-after-queue drafts are billed.
- Whether the upgrade price equals the full final-resolution rate (the quote needs a real draft id).
- Whether the upgrade call is right as the tool sends it: it follows the docs but had not been run on the
  wire by the time of writing, so treat the first upgrade as a probe.
- Whether Seedance 2.5 on the API speaks a quoted line on cue with matching lips.
