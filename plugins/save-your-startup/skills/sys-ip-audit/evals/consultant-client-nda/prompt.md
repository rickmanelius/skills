---
tags: [skill-creator, sys-ip-audit]
max_turns: 40
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

A new client sent me their mutual NDA to sign before we start. I'm a fractional CTO (Priya Raman). The client is Bluepaw Veterinary Partners, a chain of about 60 vet clinics building their own appointment scheduling and reminders app. Kickoff is Monday.

The NDA has a "Schedule A: Recipient's Prior Inventions" and says anything not listed there that I develop "relating to the Purpose" is presumed to be based on their confidential information. It also says: "Any suggestions or feedback Recipient provides regarding Discloser's products may be used by Discloser without restriction or compensation." Delaware law.

Put the files in ./ip-audit/ here. My stuff isn't on this machine; here's the summary. Please don't spend any money.

- slotsmith: my open-source appointment scheduling engine (constraint solver for staff, rooms, equipment). Public on GitHub since 2021-05-03, Apache 2.0. I still maintain it.
- Talks: "Scheduling is a graph problem" at a regional Python conference, 2023-10-12, video is public.
- Current clients (all under NDA):
  - Molar Labs, a dental practice software company. I'm building their appointment scheduling module right now, since 2025-09.
  - Kestrel Lending, a fintech lender. Payments reconciliation, 2024 to now.
  - Pallet Path, warehouse software. Slotting optimization, 2023 to 2025, ended.
- Older: a former employer, a large EHR company (2015 to 2020). I'm a named inventor on one of their patents on clinical scheduling (they own it; I can look up the number).
- I have half-written notes for a patent of my own on scheduling with equipment sterilization windows. Not filed.
- First contact with Bluepaw: their CTO emailed me on 2026-11-02 and showed me their roadmap on a call 2026-11-09.

What should go on Schedule A, and is there anything in this NDA I should push back on?
