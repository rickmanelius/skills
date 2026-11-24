<!--
Template for counsel-questions.md: questions for an AI first pass, then for a lawyer. Only shareable files (schedule.md, brief.md Part A and Part C, this file) go to a cloud AI service. The ledger goes to a local model or nowhere.
-->

> **Not legal advice.** Prepared [date] for [the user].

# Questions for counsel: [the user] and [counterparty]

## 1. AI first pass: opposing counsel

Give an AI these files only: `schedule.md`, Part A and Part C of `brief.md`, and the agreement itself if the NDA allows sharing it (if unsure, describe the clauses instead of pasting them). Then this prompt:

```
You are counsel for [counterparty], reviewing a prior-inventions schedule and a short
brief from a person about to sign [agreement type]. Your job is to protect [counterparty].

1. Which items on the schedule would you push back on, and why?
2. What's missing that you'd expect to see, given [counterparty]'s field: [field]?
3. Which clause in the agreement most limits what this person can keep?
4. Is anything on the schedule vague enough to cause a dispute later?
5. Does anything on the schedule or in the brief disclose a third party's confidential
   information?
6. In the term outline, what would you strike or change, and what would you accept?

Be specific. Quote the line you're objecting to.
```

Record the answers in the ledger's open questions. Fix what's clearly right; take the rest to the lawyer.

## 2. For the lawyer

One flat-fee hour, before signing anything that assigns IP or ties it to equity. Send the schedule, the brief, the agreements and the evidence hash ahead. The ledger goes too: it's the file the lawyer most needs, and most NDAs allow sharing with your own attorney where they don't allow a cloud AI service.

**About the agreement**

1. Does [clause] reach work I did before [date], including the unpaid contributions in Part 5?
2. Does the independent-development exclusion cover the items in Part 2, given how they were made?
3. Which state's employee-invention protections apply to me, if any, and does the agreement include the required notice?
4. If I list an item and later use it in my work for [counterparty], what license does the agreement grant them?
5. Is there a feedback or residuals clause, and what has it already covered?

**About the schedule**

6. Is each description in Part 4 general enough not to breach my other agreements, and specific enough to protect me?
7. Is the generic title for the patent in preparation enough to exclude it?
8. Anything I should remove, add or reword before attaching it?

**About the brief and the terms**

9. Which entity should take any assignment, and what should I ask for in return?
10. What's the cleanest fallback if I never start?
11. How do inventorship and copyright apply to work written with AI tools, where I live?
12. Should anything in the self-audit be disclosed to [counterparty] before signing?

**Add the user's own questions here.**
