# Save Your Startup — Skills Project

## What This Repo Is

This repo (`rickmanelius/skills`) is a Claude Code marketplace containing the **save-your-startup** plugin — 12 AI-powered founder mentorship skills derived from the book **Save Your Startup** by Rick Manelius. It follows the playbook established by Sahil Lavingia's [slavingia/skills](https://github.com/slavingia/skills).

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
  skills/                 — 12 SKILL.md files
  AGENTS.md               — Plugin voice & conventions
  README.md               — Install + overview + WIIFM
  LICENSE                 — MIT
context/
  book/                   — Source PDF
  references/             — Sahil's playbook and other references
  analysis/               — Chapter-by-chapter skill extraction and master ranking
docs/plans/               — Work plans
```
