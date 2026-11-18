# {{NAME}} · production script for Venice (Seedance 2.5)

Started {{DATE}}. **This file is the single source.** `seedance.py` reads every job and prompt from the
tagged blocks below (`json job`, `text prompt <id>`, `json refs`, `text negative`); edit here, then run
`python3 seedance.py check`. Read the skill's `references/knowledge.md` before writing prompts. Replace
every line marked REPLACE (paid commands refuse a prompt that still says it) and delete the examples you do
not need. Everything outside the tagged blocks is prose for people.

## The spot in one breath

REPLACE: who, what goes wrong, what they do, how it ends, in four sentences.

**The line the viewer leaves with:** REPLACE. **WIIFM order:** the should (never sold), the want (lead with
it), the need (shown briefly). Every scene answers "so what?" for the viewer.

**Budget cap:** REPLACE (the most the person paying will spend on this spot).

## Budget (quote before you spend: `python3 seedance.py quote all`)

| Step | Command | Price read on 2026-11-16 (re-quote; prices move) |
|---|---|---|
| Stills, Nano Banana Pro 2K | `stills` | $0.23 each |
| One probe draft, then 480p takes, Seedance 2.5 R2V | `draft <id>`, then `draft <cut> --takes 2` | $0.129 per second |
| 1080p upgrade of the chosen take | `upgrade <id> <take>` | up to $0.711 per second |
| Music, Sonilo | `music` | about $0.003 per second |

## Settings for every video job

- Model `seedance-2-5-reference-to-video-basic`, 16:9, audio on, task type `reference`.
- **No people in any reference, start frame or end frame on the API.** Describe people in text, the same
  words every time. Mark any reference with a person `"person": true`; the tool refuses it (web app only).
- One clip per stretch of story where a face must stay the same; hide faces in clips that cannot match.
- Readable text never comes from the video model: make it a screen insert in `screens.html`.

```text negative
readable text, legible words, letters, captions, subtitles, logos, brand names, watermarks, extra fingers, distorted hands, warped face, the face changing between shots, flicker, cartoon, illustration, 3D render, plastic skin
```

## References

Every file stays inside this folder (`refs/cast/` for stills, `refs/screens/` for rendered screens) and is a
.png or .jpg. Short captions: the tool writes them into Seedance's line ("the desk in <Image 1>").

```json refs
{
  "C1-set":    {"file": "refs/cast/C1-set.jpg",       "caption": "the setting"},
  "C2-object": {"file": "refs/cast/C2-object.jpg",    "caption": "the hero object"},
  "S1-insert": {"file": "refs/screens/S1-insert.png", "caption": "the look of the screen on the monitor"}
}
```

## Step 1 · Stills (Nano Banana Pro, 2K)

```json job
{"id": "C1-set", "kind": "still", "model": "nano-banana-pro", "aspect_ratio": "16:9", "resolution": "2K"}
```
```text prompt C1-set
REPLACE. Photoreal film still, no people: the place where the story happens, the time of day and the light, the lens (35mm), cinematic colour. No readable text, no logos, no watermark.
```

```json job
{"id": "C2-object", "kind": "still", "model": "nano-banana-pro", "aspect_ratio": "1:1", "resolution": "2K"}
```
```text prompt C2-object
REPLACE. Photoreal product photograph of the hero object, its size, material and colour, completely plain with no logo and no text, on a surface, soft window light, shallow depth of field, 85mm lens. No text, no logos, no watermark.
```

For a person you want consistent in the Venice web app (not the API), a four-view character sheet works
well: "Character reference sheet ... the same person shown four times side by side: front, three-quarter,
left profile, full body ... the identical face in all four views". Mark it `"person": true`.

## Step 2 · Video (Seedance 2.5 reference-to-video, through the API)

```json job
{"id": "V1-story", "kind": "video", "cuts": ["30"], "model": "seedance-2-5-reference-to-video-basic", "duration": "30s", "aspect_ratio": "16:9", "audio": true, "omni_reference_task_type": "reference", "refs": ["C1-set", "C2-object", "S1-insert"]}
```
```text prompt V1-story
REPLACE. A photoreal cinematic 30 second commercial told in N shots, natural colour grade, soft contrast, shallow depth of field, gentle handheld camera, set in REPLACE.

The main character is REPLACE: age, hair, skin, glasses, clothes. They are the same person in every shot: the same face, hair, glasses and clothes.

Shot 1, 0 to 4 seconds: REPLACE (framing, action, light).

Shot 2, 4 to 8 seconds: REPLACE.

Every screen stays a soft, unreadable glow. No object has a logo.

Audio: REPLACE room tone; each sound effect with its second; "No music." Add "No speech." unless a line is spoken, then give the line in quotes with its second.
```

Other video shapes (copy one into a `json job` block when needed; the tool does not read this block):

```json example
{"id": "V2-from-a-frame", "kind": "video", "cuts": ["30"], "model": "seedance-2-5-image-to-video-basic", "duration": "8s", "audio": true, "start_image": "C1-set"}
{"id": "V3-text-only", "kind": "video", "cuts": ["30"], "model": "seedance-2-5-text-to-video-basic", "duration": "10s", "aspect_ratio": "16:9", "audio": true}
{"id": "G1-grid-cell", "kind": "video", "cuts": ["grid"], "model": "seedance-2-5-reference-to-video-basic", "duration": "10s", "aspect_ratio": "16:9", "audio": true, "final_resolution": "720p", "refs": ["C1-set"]}
```

## Step 3 · Music (Sonilo, instrumental, commercial-use safe)

```json job
{"id": "M30", "kind": "music", "model": "sonilo-v1-1-music", "duration_seconds": 30}
```
```text prompt M30
REPLACE. Minimal modern commercial score for a 30 second ad about REPLACE, 96 BPM, instrumental. How it opens, where it thins out, where it builds, where it resolves (seconds). Mood words. No vocals.
```

## Step 4 · The edit

Inserts from `refs/screens/` get a slow push-in (100% to about 106%). Source times are seconds inside the
generated clip; check them against frames pulled from the chosen take, not against the shot timings above.

| # | Timeline | Source | What the viewer sees |
|---|---|---|---|
| 1 | 0:00.0 to 0:03.0 | V1 0.0 to 3.0 | REPLACE |
| 2 | 0:03.0 to 0:05.0 | S1-insert | REPLACE |
| 3 | 0:28.0 to 0:30.0 | E1-endcard | The line. The mark. "Dramatization." |

## Honesty notes

- "Dramatization." on the end card; fictional names and data, labelled "Sample data" where numbers show.
- Show only what the product does today; no speed claims from a time-lapse.
- No real person's face, voice or name, and no real brand's logo, look or sound, without their permission.
- Label it as AI-generated wherever the platform asks you to.
- REPLACE: anything only the owner can confirm.
