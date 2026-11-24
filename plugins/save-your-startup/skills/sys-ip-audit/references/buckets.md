# The four buckets

Every item the audit finds goes into exactly one bucket. If it seems to fit two, split it: the 2023 open-source
library is bucket A; the feature added to it last month for the counterparty's demo is bucket C.

Two dates anchor everything (Step 1):

- **The first hint:** the earliest public sign of the counterparty (their launch, a post, a talk).
- **The first private disclosure:** the first call, demo or document that showed the user anything confidential.

The examples below are fiction, from the eval cases.

## A. Made or published before the first hint

The user's, and the easiest to defend. Public is better than private: a dated blog post, a public repo's first
push, a published patent, a conference talk. Private records (commit dates, file dates, notes) still count, with
less weight.

*Example:* Jordan's 2022 blog series on demand forecasting for perishable goods, and an open-source inventory
library first pushed to a public host in March 2023. The counterparty (restaurant inventory tools) launched in
2025.

**On the schedule:** listed specifically when it overlaps the counterparty's field, with the date and a link.
Grouped generally when it doesn't.

## B. Made independently after the first hint

Own time, own equipment, own accounts, none of the counterparty's material. This is the independent-development
test from the NDA, so it needs the best evidence: timestamps, the machine and account it lived on, and a clear
line showing it didn't use anything the counterparty shared.

*Example:* a weekend side project Jordan built on a personal laptop in a personal account, a grocery price
tracker, after first hearing of the startup but before any private meeting.

**On the schedule:** listed specifically, with dates, and with the words "developed on my own time, equipment
and accounts, without use of [counterparty]'s confidential information" **only if the evidence supports every
part of that sentence**. If it doesn't, the ledger says what's missing and the item gets **[confirm]**.

## C. Contributions to the counterparty before an agreement settles them

Work the user did for or with the counterparty before anything in writing says who owns it: unpaid help, a
prototype, a design session, code in their repo.

**Credit the counterparty where the root idea was theirs.** If the founder described the feature and the user
built it, say so. It costs nothing, it's usually true, and it makes every other line on the list believable.

*Example:* two months of unpaid contributions to the startup's ordering prototype; the founder's idea, Jordan's
code, in the startup's repo, with Jordan's commits dated.

**On the schedule:** its own final part, "Contributions to [counterparty] before this agreement". The brief's
Part A asks for a short agreement that settles these.

## D. Owned by others, or held in confidence

Work owned by a past employer, a client, a co-founder or anyone under another NDA. The user can't list it as
theirs and mustn't disclose it, but should still name its existence, so the other side can't later say the
user brought it in.

*Example:* Jordan's consulting work for a regional logistics company, under NDA; a side product co-owned with a
friend.

**On the schedule:** by role and general field only. "A regional logistics company (consulting client, under
NDA): route-planning analytics, 2024 to present." Never the client's name, the project's name or its details.
A co-owned project may be named if the co-owner agrees **[confirm]**; otherwise describe it the same way.

## Evidence strength, strongest first

1. Recorded by a third party: a public post, a push to a public host, a patent filing, a publication, an email
   someone else received.
2. A dated file on a system the user doesn't control alone: a shared drive's version history, a hosted repo.
3. AI session logs and notes with timestamps, on the user's machine.
4. Local commit and file dates (anyone can set them by hand).
5. Memory. Never enough alone. Mark it **[confirm]** and say "insufficient evidence".

## Overlap with the counterparty's field

Every item gets one of three marks, which decides how specific the schedule is:

- **High:** same problem or same customer as the counterparty. List specifically, with dates and evidence.
- **Some:** adjacent technique or market. List specifically but briefly.
- **None:** unrelated. Group it ("Other software and writing unrelated to [field], 2015 to present, records
  available on request").

## Patents

- Published patents and applications naming the user as an inventor: list by number if the user owns them;
  if someone else owns them, list them in their own part with the owner's role.
- A patent in preparation: a generic title ("a method for scheduling perishable inventory") so it's excluded
  without disclosing the invention. The lawyer confirms the wording.
