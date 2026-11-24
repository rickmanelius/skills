# Save Your Startup — Skills Plugin

12 battle-tested founder mentorship skills from [*Save Your Startup*](https://saveyourstartup.com) by Rick Manelius, plus 5 companion skills (`/sys:prioritize`, `/sys:time-to-wow`, `/sys:mou`, `/sys:venice-video`, `/sys:ip-audit`). Built as Claude Code slash commands, in the spirit of [Sahil Lavingia's skills](https://github.com/slavingia/skills).

## Install

```bash
/plugin marketplace add rickmanelius/skills
/plugin install save-your-startup
```

That's it. All 17 skills are now available as `/sys:*` slash commands.

## What You Get

A Techstars All-Star Mentor in your terminal. Each skill is a structured walkthrough — not a wall of advice, but a guided conversation that adapts to your specific situation.

### Alignment & Planning

| Skill | What it does |
|-------|-------------|
| `/sys:paint-done` | Define "done" before any work begins. Prevents the #1 cause of wasted effort: misaligned expectations. |
| `/sys:chunk` | Break a 10-year vision into today's next action across 7 time horizons. |
| `/sys:high-medium-low` | Define LOW/MEDIUM/HIGH scope tiers so you build the right amount, not the most. |
| `/sys:mou` | Write a two-page Memorandum of Understanding with a business partner before the lawyers: vision, who puts in what, who owns what, structure, exit, first moves. It interviews you, drafts, reads the draft the way your partner will, and keeps refining until you would send it. Built on [Michael Girdley's MOU template](https://x.com/girdley/status/1649393986899959813). |
| `/sys:ip-audit` | List your prior inventions before you sign an NDA, offer letter, contractor or advisor agreement. It digs through your repos, AI session logs, notes and public posts, sorts your work into what's yours, what you built independently, what you contributed to the other side and what belongs to others, then drafts the schedule (Exhibit A) for that deal, a chain-of-title brief for the conversation and questions for your lawyer. Its scripts do the bulk reading on your machine, and the other side's confidential files stay closed. Not legal advice. |

### Decision Support

| Skill | What it does |
|-------|-------------|
| `/sys:prioritize` | Rank a list of ideas across 2-4 dimensions with coarse 1-5 scoring. The simplest matrix that still beats gut-feel — works for startup roadmaps, AI bets, and life decisions alike. |

### Financial Reality

| Skill | What it does |
|-------|-------------|
| `/sys:assumptions-audit` | Surface every hidden cost and revenue assumption in your business model. |
| `/sys:napkin-math` | Walk backward from a revenue target to the daily growth you actually need. Takes 5 minutes. |

### Self-Assessment

| Skill | What it does |
|-------|-------------|
| `/sys:capability-willingness-matrix` | 2x2 assessment: do you have the skills AND the willingness for what you're about to do? |
| `/sys:founder-type-check` | Honest behavioral check — are you operating as delusional, pretender, or real deal? |
| `/sys:fear-setting` | Name the fears blocking a hard decision, write mitigations, rate actual severity. |

### Customer & Market

| Skill | What it does |
|-------|-------------|
| `/sys:wiifm-check` | Run your product through the 7 questions every prospect silently asks before they care. |
| `/sys:time-to-wow` | Audit and optimize the path from trial sign-up to first delight, then systematically reduce friction and drop-off. Based on David Skok's "Time to Wow" framework. |
| `/sys:five-finger-pitch` | Build a 5-finger, 5-minute verbal pitch. One finger per minute. No slides needed. |
| `/sys:venice-video` | Make a live-action-looking video ad or launch video with Venice's API (Seedance 2.5, Nano Banana Pro, Sonilo). It writes the story in WIIFM order, renders the readable screens for free, then makes stills, drafts, upgrades and music, with a free quote and your approval before every dollar. Needs a Venice API key, Python 3 and Chrome. |

### Execution

| Skill | What it does |
|-------|-------------|
| `/sys:ruthless-elimination` | Reclaim 5-15 hours per week by applying Delete, Delegate, Delay to everything. |
| `/sys:break-bottleneck` | Find and fix your #1 throughput constraint using Theory of Constraints. |

## Quick Start

Try one of these right now:

```
/sys:paint-done I want to launch an MVP of my SaaS product by end of Q2
```

```
/sys:napkin-math I need to hit $1M ARR in 18 months with a $49/mo product
```

```
/sys:five-finger-pitch Heli — an AI workflow coach for enterprises
```

```
/sys:prioritize 8 features for our Q3 roadmap
```

```
/sys:mou My co-founder goes full time, I fund it and keep my day job, and we said 60/40
```

```
/sys:venice-video A 30 second launch video for our meal-planning app, budget $40
```

```
/sys:ip-audit Offer from a seed-stage startup I've been helping for free; they want my prior inventions list by Friday
```

## How It Works

Each skill follows the same pattern:

1. You provide context (a goal, a decision, a product)
2. The AI walks you through a structured framework, one step at a time
3. It asks probing questions and pushes back when answers are vague
4. You get specific, usable output — not generic advice

The tone is **kind over nice**: direct, honest, and adapted to your situation. These frameworks have been tested with real founders through Techstars and beyond.

## About

**Rick Manelius** is a repeat founder, Techstars All-Star Mentor, and author of [*Save Your Startup*](https://saveyourstartup.com). The 12 `sys:` skills in this plugin are distilled from the frameworks in that book: the ones that actually moved the needle for the founders he's mentored. `/sys:prioritize`, `/sys:time-to-wow`, `/sys:mou`, `/sys:venice-video` and `/sys:ip-audit` are companion skills: not from the book, but in the same spirit of "simple frameworks, honestly applied." `/sys:mou` builds on Michael Girdley's MOU template and thread, cited in the skill and its references. `/sys:ip-audit` is generalized from Rick's own audit before a signing.

## Components

| Type | Count |
|------|-------|
| Skills | 17 |
| Agents | 0 |
| MCP Servers | 0 |

## License

MIT
