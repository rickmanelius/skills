# Save Your Startup — Skills Project

## What This Repo Is

This repo (`rickmanelius/skills`) is a Claude Code marketplace containing the **save-your-startup** plugin: 12 AI-powered founder mentorship skills derived from the book **Save Your Startup** by Rick Manelius, plus 5 companion skills (`/sys:prioritize`, `/sys:time-to-wow`, `/sys:mou`, `/sys:venice-video`, `/sys:ip-audit`). It follows the playbook established by Sahil Lavingia's [slavingia/skills](https://github.com/slavingia/skills).

## Installation

```
/plugin marketplace add rickmanelius/skills
/plugin install save-your-startup
```

## Project Status

- Book PDF: `context/book/SaveYourStartup-RM-book 11.27.pdf`
- Reference material: `context/references/sahil-skills-playbook.md`
- Chapter-by-chapter analysis: `context/analysis/ch01-*.md` through `ch12-*.md`
- Master ranking of top 12 skills: `context/analysis/00-master-ranking.md`
- Plugin README: `plugins/save-your-startup/README.md`

## Tone & Voice

Skills should reflect Rick's **Techstars mentor voice**:
- **Kind over nice** — direct and honest, not gentle to the point of being unhelpful
- **Wizard/walkthrough format** — guide through structured thinking, don't dump answers
- **Context-oriented** — adapt to the founder's specific situation
- **AI-era aware** — flag or adapt frameworks that have shifted due to AI
- **Battle-tested** — preserve practical credibility; these have helped real founders

## The Top 12 Skills

1. `/sys:paint-done` — Alignment before action
2. `/sys:assumptions-audit` — Financial reality check
3. `/sys:chunk` — Vision to daily action
4. `/sys:capability-willingness-matrix` — Founder self-assessment
5. `/sys:fear-setting` — Unblocking hard decisions
6. `/sys:ruthless-elimination` — Reclaiming capacity
7. `/sys:napkin-math` — Quick feasibility check
8. `/sys:founder-type-check` — Honest self-categorization
9. `/sys:wiifm-check` — Customer value lens
10. `/sys:five-finger-pitch` — Verbal pitch mastery
11. `/sys:break-bottleneck` — Throughput optimization
12. `/sys:high-medium-low` — Scope right-sizing

## Companion Skills

These live in the same plugin but are **not** derived from the book. Same `sys:` prefix and Techstars mentor voice; different lineage.

- `/sys:prioritize` — Generic prioritization matrix. Rank a list across 2-4 dimensions with coarse 1-5 scoring. Inspired by RICE/ICE but simpler; works for startup roadmaps, AI bets, and life decisions.
- `/sys:time-to-wow`: Audit and shorten the path from trial sign-up to the first "wow". Based on David Skok's framework.
- `/sys:mou`: A two-page Memorandum of Understanding between partners, written before the lawyers. Interviews the user, drafts, then reads the draft as the partner would and loops until the user says it is clear enough to send. Built on Michael Girdley's MOU template and thread (https://x.com/girdley/status/1649393986899959813); credit him in anything derived from it.
- `/sys:venice-video`: Generated video ads and launch videos through Venice's API (Seedance 2.5 video, Nano Banana Pro stills, Sonilo music). Bundles `scripts/seedance.py` (Python standard library, offline tests in `tests/`), a SCRIPT.md template and dated field notes in `references/knowledge.md`. Every paid call needs the user's approval (`--approve-up-to`); keep it that way. Story method is the book's WIIFM chapter. Run `python3 -m unittest discover -s tests` in the skill folder after any change to the tool.
- `/sys:ip-audit`: The prior-inventions list (Exhibit A) for an NDA, offer letter, contractor or advisor agreement, tailored to that deal. Researches the user's repos, AI session logs, notes and public posts, sorts the work into four buckets, then drafts a private ledger, the shareable schedule, a chain-of-title brief and counsel questions. Generalized from Rick's own pre-signing audit; every example and eval is fiction, and nothing from the real audit belongs in this repo. Bundles five stdlib scripts in `scripts/` with offline tests in `tests/` (run `python3 -m unittest discover -s tests` in the skill folder after any change). `x_posts.py` is the only paid call and refuses to spend without `--approve-up-to`; keep it that way. Legal and technical claims are quoted from fetched sources in `references/sources.md`; re-fetch before changing one. Not legal advice, and it says so.

## Skill Format (SKILL.md)

Following slavingia/skills convention:
1. YAML frontmatter: `name`, `description`, `argument-hint`
2. Persona/philosophy opening (Techstars mentor voice)
3. Core principle from the book
4. Multi-step walkthrough with questions, checklists, and book quotes
5. Output section (3-5 specific deliverables)

Each skill lives in `plugins/save-your-startup/skills/sys-<skill-name>/SKILL.md`.

## Repo Structure

```
.claude-plugin/           — Marketplace catalog (marketplace.json)
plugins/save-your-startup/              — The installable plugin
  .claude-plugin/         — Plugin manifest (plugin.json)
  skills/                 — 17 SKILL.md files (12 book-derived + 5 companion)
  AGENTS.md               — Plugin voice & conventions
  README.md               — Install + overview + WIIFM
  LICENSE                 — MIT
context/
  book/                   — Source PDF
  references/             — Sahil's playbook and other references
  analysis/               — Chapter-by-chapter skill extraction and master ranking
docs/plans/               — Work plans
```
