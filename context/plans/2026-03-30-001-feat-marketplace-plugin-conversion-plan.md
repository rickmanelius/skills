---
title: "feat: Convert Save Your Startup skills to Claude Code marketplace plugin"
type: feat
status: completed
date: 2026-03-30
---

# Convert Save Your Startup Skills to Claude Code Marketplace Plugin

## Overview

Restructure the 12 Save Your Startup skills into a Claude Code marketplace plugin so anyone can install them with a single command and use `/sys:paint-done`, `/sys:chunk`, etc. as slash commands. Follows the pattern established by the [compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin).

## Problem Statement / Motivation

The 12 skills exist as SKILL.md files in `skills/` but aren't installable as a plugin. Users currently have to manually read the files or ask Claude to follow them. Converting to a marketplace plugin means:

- One-command install: `claude plugin:install` from the marketplace
- All 12 skills available as `/sys:*` slash commands
- Discoverable via Claude Code's plugin ecosystem
- Professional README that sells the value (WIIFM for founders)

## Proposed Solution

Restructure the repo to match the marketplace plugin convention, add manifests, prefix all skills with `sys:`, and create a compelling README.

## Technical Approach

### Phase 1: Plugin Directory Structure

Create the marketplace plugin structure alongside existing content:

```
.claude-plugin/
  marketplace.json              # NEW - marketplace catalog
plugins/
  sys/                          # NEW - the plugin
    .claude-plugin/
      plugin.json               # NEW - plugin manifest
    AGENTS.md                   # NEW - plugin instructions
    CLAUDE.md                   # NEW - shim (@AGENTS.md)
    LICENSE                     # NEW - MIT
    README.md                   # NEW - comprehensive install + skills overview
    skills/
      sys-paint-done/
        SKILL.md                # MOVED + MODIFIED (name: sys:paint-done)
      sys-assumptions-audit/
        SKILL.md
      sys-chunk/
        SKILL.md
      sys-capability-willingness-matrix/
        SKILL.md
      sys-fear-setting/
        SKILL.md
      sys-ruthless-elimination/
        SKILL.md
      sys-napkin-math/
        SKILL.md
      sys-founder-type-check/
        SKILL.md
      sys-wiifm-check/
        SKILL.md
      sys-five-finger-pitch/
        SKILL.md
      sys-break-bottleneck/
        SKILL.md
      sys-high-medium-low/
        SKILL.md
context/                        # KEEP - source material stays at repo root
  book/
  references/
  analysis/
skills/                         # KEEP or REMOVE - original location (see decision below)
```

**Decision: Keep or remove `skills/` at root?**
Remove it. The canonical location becomes `plugins/sys/skills/`. Keeping both creates confusion about which is authoritative. The git history preserves the originals.

### Phase 2: Skill Modifications

For each of the 12 SKILL.md files:

1. **Update frontmatter `name`** to include `sys:` prefix
   - `name: paint-done` → `name: sys:paint-done`
   - `name: assumptions-audit` → `name: sys:assumptions-audit`
   - etc.

2. **Update frontmatter `description`** — ensure colons are quoted (YAML compliance)

3. **Content stays the same** — the skill bodies are already well-written and tested

**Skill directory naming convention:** `sys-<skill-name>/SKILL.md` (hyphen in directory, colon in frontmatter name). This matches compound-engineering's pattern where directory is `ce-plan/` but name is `ce:plan`.

### Phase 3: Manifest Files

**`.claude-plugin/marketplace.json`** (repo root):

```json
{
  "name": "sys-plugin",
  "owner": {
    "name": "Rick Manelius",
    "url": "https://github.com/rickmanelius"
  },
  "metadata": {
    "description": "Save Your Startup — AI-powered founder mentorship skills",
    "version": "1.0.0"
  },
  "plugins": [
    {
      "name": "sys",
      "description": "12 battle-tested founder skills from Save Your Startup by Rick Manelius. Techstars mentor voice. Walkthrough format.",
      "author": {
        "name": "Rick Manelius",
        "url": "https://github.com/rickmanelius"
      },
      "homepage": "https://github.com/rickmanelius/sys",
      "tags": ["startup", "founder", "mentorship", "techstars", "pitch", "planning", "decision-making"],
      "source": "./plugins/sys"
    }
  ]
}
```

**`plugins/sys/.claude-plugin/plugin.json`**:

```json
{
  "name": "sys",
  "version": "1.0.0",
  "description": "12 battle-tested founder skills from Save Your Startup by Rick Manelius",
  "author": {
    "name": "Rick Manelius",
    "url": "https://github.com/rickmanelius"
  },
  "homepage": "https://github.com/rickmanelius/sys",
  "repository": "https://github.com/rickmanelius/sys",
  "license": "MIT",
  "keywords": ["startup", "founder", "mentorship", "techstars", "skills"]
}
```

### Phase 4: AGENTS.md

Plugin-level instructions that tell Claude how to behave when these skills are active:

- Techstars mentor voice (kind over nice, walkthrough format)
- Context-oriented — adapt to the founder's specific situation
- AI-era aware — flag or adapt frameworks that have shifted due to AI
- The `sys:` prefix convention and why it exists
- List of all 12 skills with one-line descriptions

### Phase 5: README.md (Plugin-Level)

This is the most important file for adoption. Structure:

```markdown
# Save Your Startup — Skills Plugin

One-liner: 12 battle-tested founder mentorship skills as Claude Code slash commands.

## Install

claude plugin:install from marketplace (one command)

## What You Get (WIIFM)

Table of all 12 skills organized by category:
- Alignment & Planning: paint-done, chunk, high-medium-low
- Financial Reality: assumptions-audit, napkin-math
- Self-Assessment: capability-willingness-matrix, founder-type-check, fear-setting
- Customer & Market: wiifm-check, five-finger-pitch
- Execution: ruthless-elimination, break-bottleneck

## Quick Start

3 example commands to try immediately

## About

Brief on the book, Rick's background, Techstars context

## License
```

### Phase 6: Repo-Level README.md

Update the current minimal README to:
- Explain what the repo is (source + plugin for Save Your Startup skills)
- Link to the plugin README for install instructions
- Link to the book
- Keep it short — the plugin README is the main docs

## Acceptance Criteria

- [ ] `.claude-plugin/marketplace.json` exists and is valid JSON
- [ ] `plugins/sys/.claude-plugin/plugin.json` exists and is valid JSON
- [ ] All 12 SKILL.md files moved to `plugins/sys/skills/sys-<name>/SKILL.md`
- [ ] All 12 skills have `name: sys:<skill-name>` in frontmatter
- [ ] `plugins/sys/AGENTS.md` documents voice, conventions, and skill list
- [ ] `plugins/sys/CLAUDE.md` contains `@AGENTS.md` shim
- [ ] `plugins/sys/README.md` has install instructions, skill table, quick start, WIIFM
- [ ] `plugins/sys/LICENSE` exists (MIT)
- [ ] Root `README.md` updated with overview and link to plugin
- [ ] Original `skills/` directory removed
- [ ] CLAUDE.md updated to reflect new structure
- [ ] All 12 slash commands are usable after install: `/sys:paint-done`, `/sys:assumptions-audit`, `/sys:chunk`, `/sys:capability-willingness-matrix`, `/sys:fear-setting`, `/sys:ruthless-elimination`, `/sys:napkin-math`, `/sys:founder-type-check`, `/sys:wiifm-check`, `/sys:five-finger-pitch`, `/sys:break-bottleneck`, `/sys:high-medium-low`

## Complete File List

| File | Action | Description |
|------|--------|-------------|
| `.claude-plugin/marketplace.json` | CREATE | Marketplace catalog |
| `plugins/sys/.claude-plugin/plugin.json` | CREATE | Plugin manifest |
| `plugins/sys/AGENTS.md` | CREATE | Plugin voice + conventions |
| `plugins/sys/CLAUDE.md` | CREATE | Shim to AGENTS.md |
| `plugins/sys/LICENSE` | CREATE | MIT license |
| `plugins/sys/README.md` | CREATE | Install + overview + WIIFM |
| `plugins/sys/skills/sys-paint-done/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `plugins/sys/skills/sys-assumptions-audit/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `plugins/sys/skills/sys-chunk/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `plugins/sys/skills/sys-capability-willingness-matrix/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `plugins/sys/skills/sys-fear-setting/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `plugins/sys/skills/sys-ruthless-elimination/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `plugins/sys/skills/sys-napkin-math/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `plugins/sys/skills/sys-founder-type-check/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `plugins/sys/skills/sys-wiifm-check/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `plugins/sys/skills/sys-five-finger-pitch/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `plugins/sys/skills/sys-break-bottleneck/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `plugins/sys/skills/sys-high-medium-low/SKILL.md` | MOVE+EDIT | Add sys: prefix |
| `skills/` | DELETE | Remove original location |
| `README.md` | EDIT | Update with overview + plugin link |
| `CLAUDE.md` | EDIT | Update repo structure section |

## Sources & References

- Template: [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin)
- Plugin structure convention: compound-engineering's `plugins/<name>/skills/<skill-name>/SKILL.md` pattern
- Marketplace install: `claude plugin:install` from GitHub repos
- Skill naming: `sys:` prefix mirrors `ce:` convention for namespace clarity
