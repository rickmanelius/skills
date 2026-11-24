<!--
Template for ledger.md: the private evidence file. Never shared except with the user's lawyer. Never sent to a cloud AI service. Mark everything only the user can confirm with **[confirm]**. Thin evidence is "insufficient evidence", never "none".
-->

> **Private. Not legal advice.** For [the user] and their lawyer only. Last updated [date].

# IP ledger: [the user] and [counterparty]

## 1. The short version

Five to eight bullets the user can read in a minute:

- What's being signed, with whom, and whether they've countersigned.
- The two anchor dates.
- How many items in each bucket, and the two or three that matter most because they overlap the counterparty's field.
- The biggest risk in the user's own record (from the self-audit).
- The one thing to do before signing.

## 2. Date anchors

| Anchor | Date | Evidence | Strength | [confirm]? |
|---|---|---|---|---|
| First hint (earliest public sign of the counterparty) | | | | |
| First private disclosure | | | | |
| First contribution by the user | | | | |
| Agreement effective date | | | | |
| Signature dates (each side) | | | | |

## 3. Agreements in play

The table from `references/clause-guide.md`, one block per agreement.

## 4. Do these before anything gets signed

Numbered, each with an owner and a date. Typically: get the NDA countersigned, settle bucket C in writing, fix any self-audit findings, lawyer review.

## 5. Bucket A: yours, before [first-hint date]

| Item | First | Last | Evidence (strongest first) | Strength | Owner read | Overlap | [confirm]? |
|---|---|---|---|---|---|---|---|

## 6. Bucket B: yours, independent, after [first-hint date]

| Item | First | Last | Own time, equipment, accounts? | No counterparty material? | Evidence | Overlap | [confirm]? |
|---|---|---|---|---|---|---|---|

## 7. Bucket C: contributions to [counterparty]

| Contribution | First | Last | Where it lives | Whose idea (with evidence) | Paid? | [confirm]? |
|---|---|---|---|---|---|---|

## 8. Bucket D: owned by others or held in confidence

Real names are allowed here, because this file never leaves the user and their lawyer. The schedule uses roles.

| Owner | Role on the schedule | Field | Dates | Agreement that governs it | Any overlap with this work? |
|---|---|---|---|---|---|

## 9. Self-audit

The findings from `self-audit.md`, or a pointer to it.

## 10. Open questions

| Question | Who answers | By when |
|---|---|---|

## 11. Coverage

What was searched, with dates and tool runs, and what wasn't. Every gap is listed as "not searched" or "insufficient evidence".

| Source | Searched? | Run date | Output file | Notes |
|---|---|---|---|---|
| Code folders (repo census) | | | `data/repo-census-[date].csv` | |
| AI session logs | | | `data/session-prompts-[date].jsonl` | |
| Blog and newsletter feeds | | | `data/feed-[name]-[date].json` | |
| Public repos and patents | | | | |
| X posts (paid) | | | `data/x-posts-[date].jsonl` | |
| Notes vault | | | | |
| Meeting transcripts | | | | |
| Email and chat | | | | |
