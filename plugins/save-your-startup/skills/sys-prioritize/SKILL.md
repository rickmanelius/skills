---
name: sys:prioritize
description: >
  Rank a list of ideas, initiatives, features, or life decisions by scoring
  2-4 dimensions on a coarse 1-5 scale. The simplest matrix that still beats
  gut-feel ordering. Walks through dimension selection, legend calibration,
  and item-by-item scoring, then offers to persist the result as markdown
  (and optionally CSV).
argument-hint: "[ideas to prioritize, or path to a file containing them]"
---

# Prioritize

**Companion skill — not from the book.** Inspired by RICE, ICE, and the lived reality that any scoring matrix beats gut-feel ordering — but only if it is simple enough to actually use.

> "If everything is a priority, nothing is."

## Why This Matters

Prioritization is hard everywhere it matters: startups, AI bets, product roadmaps, life. The failure mode is almost never "we picked the wrong framework." It is "we picked a framework so heavy that we never finished the exercise" — or worse, "we skipped the exercise entirely and argued from gut-feel."

Heavyweight frameworks collapse under their own weight. RICE with confidence intervals. Weighted scoring across seven axes. Portfolio theory applied to a five-person startup. They feel rigorous, but the math is spurious precision on top of guesses.

The simplest workable matrix beats the most rigorous unused one.

## The Key Insight

> Calibration matters more than precision.

If you score everything a 5, the ranking is useless. Coarse 1-5 integer scoring forces honest tradeoffs *because it strips away the illusion of precision*. You cannot hide behind 4.3 vs 4.4. You have to decide: is this a 4 or a 5?

That forced choice is the point.

## The Default Four Dimensions

Each dimension is scored 1-5. Higher is better.

| Score | Effort (to build) | Impact (when used) | Reach (who benefits) | Recurring (how often used) |
|-------|-------------------|--------------------|-----------------------|-----------------------------|
| **5** | 1 hour            | Transformative     | Everyone              | Hourly                      |
| **4** | 1 day             | Great              | Majority              | Daily                       |
| **3** | 1 week            | Good               | Minority              | Weekly                      |
| **2** | 1 month           | Minimal            | Couple / few          | Monthly                     |
| **1** | 1 quarter         | Zero               | 0 to 1                | Quarterly / never           |

**Formula:** `Score = Effort + Impact + Reach + Recurring` (equal weight, max 20, min 4)

No tie-breakers by default — if two items tie, the cheaper-to-build one wins.

## AI-Era Callout

The Effort axis has been compressed hard. What was a "1 week build" (score 3) in 2023 is often a "1 day build" (score 4) in 2026 with AI tooling. Recalibrate the legend every quarter or two — otherwise your rankings will systematically undervalue small, fast, high-leverage work.

The other three axes are stable. Only Effort drifts.

## How This Works

We will work through six phases. Your answers drive the scoring; the matrix is just the scaffolding.

### Phase 1 — Inventory

Tell me what you are prioritizing. Any of these works:

- A bullet or numbered list pasted directly
- A file path to read
- A paragraph of prose I can pull items out of

I will ask:

- **What are the items?** (If fewer than two, we have nothing to rank — let's generate more options first.)
- **What domain are they in?** (Startup roadmap? AI experiments? Life decisions? Side projects?)
- **Is the list final, or still open?** (If open, we will score what you have and flag the gap.)

### Phase 2 — Pick Your Dimensions

Default: all four (Effort, Impact, Reach, Recurring). Use this when the items are repeated-use things — features, internal tools, processes.

Simpler modes exist for different jobs:

- **2-axis (Effort × Impact)** — great on-ramp. Use for one-shot decisions or when you are brand new to scoring. Max score 10.
- **3-axis (Effort + Impact + Reach)** — drop Recurring for one-time initiatives: a launch, a hire, a migration.
- **4-axis (default)** — repeated-use items where frequency matters.

I will ask:

- **How often will the winning item get used?** (If "once" — drop Recurring.)
- **Does reach even apply?** (If the beneficiary is always "one person / me" — drop Reach.)

If you want more than four dimensions, I will push back. More axes usually means you are avoiding a decision, not making one. Pick four, live with the imperfection.

### Phase 3 — Calibrate the Legend

This is the most-skipped, most-important step. Before we score anything, we anchor the scale to your domain.

For each dimension you picked, I will ask:

- **Give me a real-world example of a 5 in your world.** ("Transformative impact" means what, to you? "1 hour to build" assumes what skill level?)
- **Give me a real-world example of a 1.** (What does "zero impact" look like? What does "takes a quarter" mean given your team size?)
- **What is a typical 3?** (This becomes your gut-check midpoint.)

If you cannot name a concrete 5 and a concrete 1 for each axis, we are not ready to score yet. Keep calibrating.

### Phase 4 — Score Each Item

Now we go item by item. For each, I will assign or ask for integer scores on each dimension, plus a one-sentence **quick take**.

For each item:

- **Effort:** How long to build / decide / execute? (Use the legend — no half-points.)
- **Impact:** What changes when it is in use? (Transformative or marginal?)
- **Reach:** Who benefits? (One person or everyone?)
- **Recurring:** How often does the benefit repeat? (Hourly or once-and-done?)
- **Quick take:** One sentence in plain language. *This is the part you will actually quote in a meeting.* Example: "Dead simple, daily use, benefits everyone — start here."

Calibration tip: if every item is scoring 4-5 on Impact, you are inflating. Force yourself to give at least one item a 2 on each axis, and see if the ranking feels right.

### Phase 5 — Rank & Discuss

I will produce a ranked markdown table inline, sorted by total score, with quick takes. Then we stress-test it:

- **Does the top item surprise you?** If yes — good, the matrix earned its keep. If no — confirm it against your gut before proceeding.
- **Are there gated items?** (High score but blocked on a dependency — call it out.)
- **What is the natural sequence?** (Top 3 in order, or parallel tracks?)
- **Would you actually do what the ranking says?** If not, why not — and does that reveal a missing dimension?

### Phase 6 — Persist (Optional)

I will ask if you want to save the result as files. If yes:

- **`prioritization-{slug}.md`** — ranked table, scored matrix, legend, quick takes, playbook notes
- **`prioritization-{slug}.csv`** — same data, spreadsheet-friendly

Default output directory: `./` (or `deliverables/` if it exists). Default basename: a short kebab-case slug from your topic, or `prioritization-{YYYY-MM-DD}` if no good slug is obvious. The markdown file uses the template at `templates/output-template.md`.

Say "no" and we stop with just the inline ranking. Both are valid.

## Getting Started

Tell me:

1. **What are you prioritizing?** (Paste the list, or point me at a file.)
2. **What is the domain?** (Startup features? AI projects? Life decisions? Side projects?)
3. **What is your gut-instinct top pick?** (We will score against it and see if the matrix agrees.)

## Ground Rules

- **Equal weights are deliberate.** Weighted formulas look rigorous and are usually spurious precision. Equal weights are easier to defend and easier to recalibrate. Do not weight unless you have a hard reason.
- **Integer scores only.** No 3.5s. If you are tempted to split the difference, pick the score that reflects the dominant reality.
- **The quick take is the product.** Numbers give the ranking; the one-liner is what you will quote. Write it like you mean it.
- **Calibrate against the rest of the list.** If everything is a 5, the ranking is useless. Spread the scores.
- **Two dimensions is fine. Four is the sweet spot. More than four is usually procrastination dressed as rigor.**
- **Recalibrate quarterly.** Especially the Effort axis. AI keeps compressing it.

## Output

By the end, you will have:

- **A ranked list** of every item with total scores
- **A scored matrix** showing each dimension for each item
- **Quick takes** — one sentence per item, meeting-ready
- **A recommended starting point** with clear reasoning
- **Optional persisted files** — markdown and/or CSV, saved to disk

Let's rank it. What are you prioritizing?
