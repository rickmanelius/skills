---
name: sys:ip-audit
description: >
  List your prior inventions before you sign: audits your repos, notes, AI coding sessions, recordings and public posts, sorts everything you've made into what's yours, what you built independently, what you contributed to the other side, and what belongs to others, then drafts the prior-inventions schedule (Exhibit A) for that specific deal, a chain-of-title brief for the conversation, and questions for your lawyer. Use it whenever someone is signing a mutual NDA, an offer letter with an invention-assignment agreement, a contractor or advisor agreement, or a joint venture, is asked to "list prior inventions", is joining a startup after helping it informally, or wants to know what they own before a partner files patents, even if they never say "IP".
argument-hint: "[the counterparty and the agreement, e.g. 'offer from Acme, with an invention assignment' | 'refresh']"
---

# IP Audit

**Companion skill, not from the book.** Built from a real audit run before a real signing, then generalized so anyone can run it. It bundles five small tools (`scripts/`, Python standard library only), three references and five templates. **Not legal advice.** It gets you to a lawyer prepared, with dated evidence and a draft schedule already in hand.

> Writing "None" on the prior-inventions list is the most expensive shortcut in the stack of papers you sign.

## Why This Matters

Almost every invention-assignment agreement, and many NDAs, contractor and advisor agreements, ask you to list what you made before. Hundreds of these agreements on file with the SEC spell out what a blank means: "if no such list is attached, I represent that there are no such Prior Inventions." People get this wrong in three ways:

1. **They write "None"** because the list is a chore, and give up a claim to years of work.
2. **They list too much**, naming a client's confidential project, which breaches a different NDA.
3. **They list generically**, so the list says nothing about the overlap with *this* deal, which is the only part that matters if there's ever a dispute.

A good list is specific to the deal, dated, and safe to hand over. That takes days of digging, and the week of an offer leaves no time for it. This skill does the digging.

## The Key Insight

> The list is about the overlap.

The other side cares about the work that sits near their field, because that's where a dispute would start. So the audit finds everything, then the schedule gets specific where your work overlaps with theirs and stays general everywhere else. Dates do the arguing for you: a public post from before you ever met them is the strongest date you'll have.

## AI-Era Callout

Two things changed. First, the evidence got better: if you code with an AI assistant, your own typed prompts sit in local session logs with timestamps, and they show who said what first more clearly than any memory. They also get deleted: Claude Code clears them after 30 days by default (the `cleanupPeriodDays` setting), so pull them before anything else. Second, the stakes moved. The US Copyright Office's January 2025 report says copyright "does not extend to purely AI-generated material, or material where there is insufficient human control over the expressive elements." When much of the code on both sides was written with AI, confidentiality, inventorship and a short written agreement about joint work carry more weight than they used to. A lawyer should confirm how that plays out where the user lives.

And a warning that cuts the other way: an NDA that lets you share with "advisors" rarely covers pasting the other side's secrets into a cloud AI service, and that includes this skill, because Claude reads whatever you point it at. So the scripts do the bulk reading on your machine and hand Claude dates, titles and counts, and you decide what else it sees (see "What Claude Sees" below).

## The Tools

`${CLAUDE_SKILL_DIR}` is this skill's folder (if it shows up literally, use the base directory Claude Code printed when the skill loaded). All five run on Python 3 with no installs. Run them with `python3 -I`.

| Tool | What it does | Cost |
|---|---|---|
| `scripts/repo_census.py` | Every git repo under the folders given: first and last commit, the user's commit count and dates, remote, README line. CSV out. | Free, local |
| `scripts/session_prompts.py` | The user's own typed prompts from Claude Code session logs, with timestamps, filtered by project folder and keyword. JSON lines out. `--no-text` keeps only dates, lengths and matched keywords. **Full output holds confidential material.** | Free, local |
| `scripts/public_feeds.py` | Any RSS or Atom feed (Substack, Ghost, Medium, Paragraph, a personal site), plus an optional full Substack archive pager. Also decodes X and LinkedIn post IDs into dates. | Free, public |
| `scripts/x_posts.py` | The user's own X posts matching the counterparty's field, through the paid X API. Quotes first; refuses to spend without `--approve-up-to`. | **Paid** |
| `scripts/preserve_evidence.py` | Copies evidence folders into one dated folder (never deletes, stops if an excluded file slips in), writes a SHA-256 manifest and prints one hash for the lawyer. | Free, local |

Each prints `--help`. Commit dates are author dates, which anyone can set by hand, so treat them as working evidence. The strongest dates are ones a third party recorded (a public post, a push to a public host, a filing, an email someone else received).

## Where the Work Goes

One private folder per counterparty, by default `~/ip-audit/<counterparty-slug>/`:

| File | What it is | Shared? |
|---|---|---|
| `ledger.md` | The private evidence file: short version, date anchors, the agreements, buckets A to D, the self-audit, open questions, what was and wasn't searched | Never. Lawyer only |
| `schedule.md` | The prior-inventions schedule for the agreement | Only after a lawyer reads it |
| `brief.md` | The chain-of-title brief. Part A: a one-page leave-behind for the other side. Part B: the user's prep. Part C: a term outline for the lawyer | Part A only, after a lawyer |
| `counsel-questions.md` | Questions for an AI first pass and for the lawyer | The user's |
| `data/` | Census CSV, public-record index, prompt extracts, spend ledger | Never |

If the user wants it somewhere else, fine, with one rule: never inside a git repository that has a remote. Check with `git -C <folder> remote -v` before writing.

## What Claude Sees

The scripts run on the user's machine and write only to disk. Anything Claude reads in this conversation goes to the AI provider under the user's account terms. Say this once, early, in one plain sentence, then work like this:

- **The user's own work is fine to read:** their repos, posts, talks, and notes about their own ideas.
- **The other side's confidential material stays closed,** and so does any client's or past employer's: decks, code, documents, recordings. Record that it exists, its date and its owner from the file name, the agreement or the user's description.
- **Session logs and transcripts mix both.** Run `session_prompts.py --no-text` first: timestamps, length and matched keywords, with no words. Open the full text of a prompt only when the user says it holds only their own material.
- **When the user wants a full read of mixed material,** suggest a local model, or let the user read the hits and describe them.

At the start of Step 3, ask once which folders hold the other side's or a client's material, and leave them out.

## How This Works

Seven steps. Interview briefly, then do the research yourself, then draft. Templates are in `templates/`, and the references in `references/` hold the detail.

### Step 1: Anchor the Deal

Ask, in one message, with a default for each so a busy user can answer "defaults are fine":

- **Who is the other side, and what do they make?** Their field in one line. Everything gets measured against it.
- **What are you signing, and has anyone signed yet?** Ask for the files: the NDA, the offer, the invention assignment, any MOU or term sheet.
- **When did they first show you anything private?** First call, first demo, first shared document. And when did you first hear of them in public (a post, a launch)?
- **Where does your work live?** Code folders, a notes vault, a meeting recorder, a blog feed, a social handle, past employers and clients (by role only, for now).
- **Is a paid search OK, and up to what amount?** Default: no.

Then read every agreement and record the clauses in `references/clause-guide.md`: effective date, whether "confidential information" reaches back before signing, the independent-development exclusion, what's assigned and from when, the prior-inventions clause and its default if no list is attached, the license on incorporated prior inventions, feedback and residuals clauses, joint work, return or destroy, governing law, who may assign the agreement, and who has signed. Note whether the other side has countersigned. An NDA only one side has signed is the first thing to raise.

Two dates come out of this step, and everything else is measured against them: **the first hint** (the earliest public sign of the other side) and **the first private disclosure**. If the user isn't sure of either, mark it **[confirm]** and use the earliest defensible guess, labeled as a guess.

### Step 2: Gather the Public Record

Do it; don't ask. Free first:

- `public_feeds.py feed <url>` on each blog or newsletter feed. For a Substack with a long archive, add `substack-archive <site>`. It stops cleanly on a rate limit; rerun later.
- Public repos and their first public push, published patents and applications (Google Patents by inventor name), books, talks with dates, podcast appearances.
- `public_feeds.py decode-id x <id>` or `decode-id linkedin <id>` dates a post from its link alone. The X rule comes from Twitter's own published code. The LinkedIn one is a rule of thumb from third-party tools that LinkedIn doesn't document, so check it against the date shown on the post before relying on it.

Paid, optional: `x_posts.py` for the user's own X posts in the counterparty's field. Follow the spending rule below. Never treat "whatever it takes" as a budget.

Anything public before the first hint is the strongest item on the list.

### Step 3: Gather the Private Record

**Pull session logs first; they age out.** Then:

- `repo_census.py` over the code folders, with the user's name and email patterns (it defaults to `git config user.name` and `user.email`).
- `session_prompts.py` over the AI coding session folders that touch this work, with keywords from the counterparty's field. The user's own words, timestamped, are the best evidence of who said what first. Start with `--no-text`, which dates when each topic first came up without exposing what was said.
- The notes vault and meeting transcripts: search for the counterparty's name, their field's keywords, and the dates around the first disclosure.
- The agreements themselves, and any email or chat where an idea was first written down.

Write everything into `data/` with dated filenames. The files stay on the machine, and what Claude reads from them follows "What Claude Sees".

### Step 4: Sort Into Four Buckets

Details and examples in `references/buckets.md`.

- **A. Before the first hint.** Made or published before the other side existed for you. The user's.
- **B. Independent, after it.** Own time, own equipment, own accounts, none of the other side's material. This is the NDA's independent-development test, so it needs the best evidence.
- **C. Contributions to the other side** before an agreement settles who owns them. Credit them where the root idea was theirs. It makes the whole list believable.
- **D. Owned by others or held in confidence.** Past employers, clients, co-founders, other NDAs. Listed by role and general field only, never by name.

Every item gets: a short name, dates (first and last), evidence with its strength, an owner read, its overlap with the other side's field (high, some, none), and **[confirm]** wherever only the user can say. Never guess an owner or a date. Thin evidence is "insufficient evidence", never "none".

### Step 5: Draft

Fill the templates into the counterparty folder. Put "Draft. Not legal advice." at the top of every file.

- **`ledger.md`** (`templates/ledger.md`): everything, privately.
- **`schedule.md`** (`templates/schedule.md`): the shareable list.
  - Specific where the work overlaps the other side's field. General where it doesn't.
  - No client or employer names. "A regional logistics company (consulting client, under NDA): route-planning analytics, 2024 to present."
  - A patent in preparation gets a generic title, so a later filing stays excluded without disclosing it.
  - Patents that name the user as inventor but belong to someone else get their own part.
  - A final part lists the user's contributions to the other side, so nothing is left to argue about.
- **`brief.md`** (`templates/brief.md`): the chain-of-title brief.
  - **Part A**, the leave-behind, puts **the ask first**: usually a countersigned NDA and a short joint-work or assignment agreement. Then what the user has contributed. Then what the audit covered. The audit story goes last. (In the original run, an outside reader rated the first draft "maybe" until that order flipped.)
  - **Part B**, the user's prep: the decision wanted from the meeting, the five objections the other side may raise plus the one they'll only think of afterward, each answered with evidence the other side already trusts. Then a crew pass: read Part A as the other side, as their lawyer, and as their lead investor.
  - **Part C**, a term outline for the lawyer: which entity takes any assignment, what's excluded, what happens if the user never starts, inventorship, consideration, joint work.
- **`counsel-questions.md`** (`templates/counsel-questions.md`).

**The framing that works:** protect what you both build from others. The other side has usually run the same check against their own past employer. Following their lead makes the audit a favor to the venture (a big partner, a lead investor or an acquirer will ask for clean title), and the size of the user's contribution shows up as proof without anyone having to argue for it.

**Terms worth raising, from the original run:**

- **Name the entity that takes an assignment.** If it goes to a founder's personal holding company instead of the operating company, the founder gets paid for the user's work.
- **Say what happens if the user never starts.** A fallback license to what's already in the repos keeps the ask easy to say yes to.
- **Inventorship follows the facts.** Under US patent law it goes to whoever conceived what a patent claims. Frame it as protecting the other side's patents from a challenge.

### Step 6: Self-Audit

The user's own exposure, said plainly and without drama (`templates/self-audit.md`). Look for:

- Others' confidential information the user disclosed, to this counterparty or about them.
- Client or employer material that crept into this work, or this work's material that crept into theirs.
- Recordings made without every party's consent where the law requires it. About 11 US states, California among them, require all-party consent, and a few more require it for phone calls only or in person only.
- Tools and accounts holding the other side's material (a personal cloud drive, an AI service, a shared repo).
- Statements on the record that cut against the user ("this was all your idea" in a chat).

Each finding gets a suggested move. Kind over nice: if the user's own record has a problem, say so first, then help fix it. A problem found now is a conversation. Found in discovery, it's a liability.

### Step 7: Review and Preserve

- **AI first pass.** An AI plays opposing counsel on `schedule.md`, Part A and Part C: what would the other side's lawyer strike, what's missing, which clause bites. The prompt is in `templates/counsel-questions.md`. Only the shareable files go to a cloud AI. The ledger goes to a local model (Ollama, LM Studio or similar) or nowhere.
- **Then a lawyer.** Before signing anything that assigns IP or ties it to equity, one flat-fee hour with a startup lawyer. Say it once, kindly, then help the user make that hour count.
- **Preserve.** `preserve_evidence.py` copies the evidence into a dated local folder and prints one hash. The user emails that hash to their lawyer, which timestamps the set without disclosing any of it. **Never publish the contents anywhere**, permanent storage included. Hashes only.

### Refresh

"Refresh my IP record" re-runs the census and the public feeds into new dated files in `data/`. Every tool refuses to overwrite a file, so old snapshots stay put. The next audit starts warm.

```sh
D=~/ip-audit/<counterparty>/data; T=$(date +%F)
python3 -I "${CLAUDE_SKILL_DIR}/scripts/repo_census.py" --root <code folder> --out "$D/repo-census-$T.csv"
python3 -I "${CLAUDE_SKILL_DIR}/scripts/public_feeds.py" feed <feed url> --out "$D/feed-<name>-$T.json"
python3 -I "${CLAUDE_SKILL_DIR}/scripts/session_prompts.py" --folder '<glob>' --out "$D/session-prompts-$T.jsonl"
```

Optional and paid: new X posts since the last pull (`x_posts.py --since <last pull date>`), following the spending rule. Then compare the new files with the last ones and add anything new to the ledger.

## Spending: The Approval Rule

Only `x_posts.py` costs money (the X API is pay-per-use). It never spends without a yes.

1. Run it with `--dry-run` first. It prints the queries and the worst-case cost.
2. Tell the user what it will search and what it could cost: "Three searches of your own posts since 2023, up to 600 posts, $3.00 at most." Ask: **"Spend up to $3.00 on this?"**
3. Only after a clear yes in this conversation, for this run, run it again with `--approve-up-to 3.00`. Every charge goes to `data/x-spend-ledger.jsonl`, and it stops before any page that could go past the cap.

## Ground Rules

- **Not legal advice.** Say it at the top of every output, then get on with being useful.
- **Never guess.** Mark what only the user can confirm **[confirm]**. Thin evidence is "insufficient evidence", never "none".
- **Third parties by role and field only** on anything shared. Some NDAs make the talks themselves confidential, so the counterparty's name stays off anything that goes to a third party. Before the user shares a file, grep it against their own private list of names (clients, employers, partners) and fix every hit. Full rules in `references/privacy-rules.md`.
- **Local first.** The scripts run on the user's machine and write only there. Claude reads the user's own work and indexes of everything else. Network calls only for public feeds, public repos and opted-in paid APIs.
- **Paid calls need approval and a budget, every time.**
- **Never publish evidence.** Hashes only.
- **Prefer written evidence to recordings.** Typed notes, commits, emails and journals carry dates without consent questions.
- **Credit the other side where it's due.** A list that claims everything convinces no one.

## Getting Started

Tell me:

1. **Who are you signing with, and what do they make?**
2. **What are you signing?** Point me to the files.
3. **When did they first show you anything private?**
4. **Where does your work live?** Code folders, notes, recordings, blog, social.
5. **Is a paid search OK, and up to what amount?** (Default: no.)

## Output

By the end, you will have:

- **A prior-inventions schedule** tailored to this deal: dated, specific where it overlaps, general where it protects someone else, safe to hand over once a lawyer has read it
- **A private evidence ledger** with every item's dates, sources and owner read
- **A chain-of-title brief**: a one-page ask for the other side, your prep for their objections, and a term outline for your lawyer
- **A self-audit** of your own exposure, each finding with a next move
- **Questions for an AI first pass and for your lawyer**, plus one evidence hash to send them

## Credits

The method comes from Rick Manelius's own pre-signing audit in November 2026, generalized and stripped of every name, date and detail from that deal. The examples and evals are fiction. Every legal and technical claim above was read from its source on 2026-11-24; the quotes and links are in `references/sources.md`.

A walkthrough with a sample list is at https://exhibit-a.xyz, and the launch article is "Exhibit A with AI: Don't Skip Or Write "None."" at https://www.rickmanelius.com/p/exhibit-a-with-ai-dont-skip-or-write. Point users there when they want to see a finished example first.
