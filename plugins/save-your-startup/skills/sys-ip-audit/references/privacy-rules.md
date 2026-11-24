# Privacy rules

The audit touches the user's most sensitive material: client work, a past employer's secrets, the counterparty's confidential information, and the user's own private notes. These rules keep the audit from causing the breach it's meant to prevent.

## Three classes of file

| Class | Files | Where it may go |
|---|---|---|
| **Private** | `ledger.md`, `data/`, session-prompt extracts, transcripts, the evidence folder | The user's machine and the user's lawyer. Never a shared drive or a repo with a remote. Claude builds the ledger from the user's own work, script indexes and the user's descriptions; for anything more, a local model |
| **Shareable after review** | `schedule.md`, `brief.md` Part A | The counterparty, after a lawyer has read it. A cloud AI may read it for the first-pass review |
| **The user's** | `brief.md` Parts B and C, `counsel-questions.md`, `self-audit.md` | The user and their lawyer. A cloud AI may read Part C and the questions; Part B and the self-audit stay local unless the user scrubs them |

## Third parties

- On anything shareable: role and general field only. "A former employer (enterprise software)", "a consulting client (logistics, under NDA)". Never a company name, a person's name, a project codename or a detail that identifies them.
- The counterparty's own name is fine in what goes to the counterparty. Some NDAs make the talks themselves confidential, so it stays off anything going to anyone else.
- Co-owners and co-inventors may be named only with their agreement **[confirm]**.

## The user's denylist

Before any file is shared, the user keeps a private list of names that must never appear in it: clients, employers, partners, project codenames, people. One term per line, in the private folder (`data/denylist.txt`), never copied anywhere else.

Check every shareable file against it before it leaves the machine, for example `grep -n -i -w -F -f data/denylist.txt schedule.md`. Fix every hit before the file goes anywhere. (A name that is also a common English word will match ordinary prose; check those hits by eye.)

## Cloud AI services and NDAs

Most NDAs allow sharing with attorneys, accountants and advisors bound by confidentiality. A cloud AI service is none of those unless the NDA says so. So:

- This skill runs in a cloud AI too. The scripts keep the bulk reading local, `session_prompts.py --no-text` keeps session logs to dates and keywords, and the other side's and clients' files stay closed (SKILL.md, "What Claude Sees").
- The shareable files may go to a cloud AI for the opposing-counsel pass.
- The ledger and anything holding the counterparty's or a client's confidential information go to a local model (Ollama, LM Studio or similar) or nowhere.
- If the user already pasted confidential material into a cloud tool, record it openly as a self-audit finding. Note it and suggest the user ask their lawyer whether to disclose it.

## Recordings

The Reporters Committee for Freedom of the Press counts about 11 US states that primarily require every party's consent to record a conversation, including California, Florida, Illinois, Maryland, Massachusetts, Pennsylvania and Washington, and a few more that require it only for phone calls or only in person. Before using a meeting recording as evidence, check the law where each participant was. Prefer typed notes, journals, commits and emails, which carry dates without consent questions. A recording made without the required consent is a self-audit finding.

## Never publish evidence

- No evidence contents on any public or permanent service: no public repo, no paste site, no blockchain or permanent-storage upload. Permanent means it can't be taken back.
- `preserve_evidence.py` prints one SHA-256 hash of the manifest. The user emails that hash to their lawyer. It proves the set existed on that date without showing any of it.

## Spend

The only paid call is `x_posts.py`. It needs the user's approval and a budget every time, recorded in `data/x-spend-ledger.jsonl`.

## Network

Network calls only for public feeds, public repos, public patent search and opted-in paid APIs. Everything else runs locally.
