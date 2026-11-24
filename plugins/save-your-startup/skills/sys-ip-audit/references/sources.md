# Sources

Every legal or technical claim in this skill was read from the page below on 2026-11-24. Laws and policies change; check the page again before you rely on a claim, and let a lawyer confirm how it applies to you.

## The prior-inventions clause

- **"If no such list is attached."** Invention-assignment agreements filed with the SEC as exhibits. Red Hat, 10-K Exhibit 10.18 (2014): "If no such list is attached, I represent that there are no Prior Inventions." https://www.sec.gov/Archives/edgar/data/1087423/000119312514157171/d671918dex1018.htm Varonis, 10-K Exhibit 10.13 (filed 2026-02-04): "or, if no such list is attached, I represent that there are no such Prior Inventions." https://www.sec.gov/Archives/edgar/data/1361113/000162828026005450/vrnsq420251013.htm An EDGAR full-text search returned 493 filings with "there are no such Prior Inventions" and 8 more with "there are no Prior Inventions".
- **The license on incorporation.** Red Hat, same exhibit: "If in the course of my employment with the Company, I incorporate into a Company product, process, technology or machine a Prior Invention, the Company is hereby granted and shall have a nonexclusive, royalty-free, irrevocable, perpetual, worldwide license (with the right to sublicense) to make, have made, modify, make derivative works of, use, sell and otherwise distribute or exploit such Prior Invention as part of or in connection with such product, process, technology or machine."

## State limits on invention assignment

- **California Labor Code section 2870(a):** an assignment provision "shall not apply to an invention that the employee developed entirely on his or her own time without using the employer's equipment, supplies, facilities, or trade secret information except for those inventions that either: (1) Relate at the time of conception or reduction to practice of the invention to the employer's business, or actual or demonstrably anticipated research or development of the employer; or (2) Result from any work performed by the employee for the employer." https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=LAB&sectionNum=2870
- **Other states.** Wilson Sonsini, "New York Redefines the Permissible Scope of Invention Assignment Provisions" (March 6, 2024), lists California, Delaware, Illinois, Kansas, Minnesota, New Jersey, North Carolina, Utah and Washington, plus New York Labor Law section 203-F (signed September 15, 2023), and notes that "Nevada has a substantially different enactment." https://www.wsgr.com/en/insights/new-york-redefines-the-permissible-scope-of-invention-assignment-provisions.html

## Recording consent

- Reporters Committee for Freedom of the Press, "Introduction to the Reporter's Recording Guide": "About 11 states primarily have all-party consent requirements for recording. These states are California, Delaware, Florida, Illinois, Maryland, Massachusetts, Michigan (at least for recordings made by a third party who is not involved in the conversation), Montana, New Hampshire, Pennsylvania and Washington." It adds that Missouri and Oregon require all parties' consent for in-person conversations only, and Connecticut and Nevada for phone calls. https://www.rcfp.org/introduction-to-reporters-recording-guide/
- Justia's 50-state survey (last reviewed September 2024) treats several of these states with more nuance. https://www.justia.com/50-state-surveys/recording-phone-calls-and-conversations/

## Copyright and AI

- US Copyright Office, "Copyright and Artificial Intelligence, Part 2: Copyrightability" (January 2025): "Copyright does not extend to purely AI-generated material, or material where there is insufficient human control over the expressive elements." and "Based on the functioning of current generally available technology, prompts do not alone provide sufficient control." https://www.copyright.gov/ai/Copyright-and-Artificial-Intelligence-Part-2-Copyrightability-Report.pdf

## Dating posts from their IDs

- **X:** Twitter's published Snowflake code sets `twepoch = 1288834974657` and shifts the timestamp left by 22 bits, so milliseconds = (id >> 22) + 1288834974657. https://github.com/twitter-archive/snowflake/blob/snowflake-2010/src/main/scala/com/twitter/service/snowflake/IdWorker.scala
- **LinkedIn:** insufficient evidence from LinkedIn itself; its API documentation says nothing about timestamps in IDs. Third-party tools read the bits above the lowest 22 as milliseconds since 1970; on the one example checked, that matched the tool's displayed time once the time zone was allowed for. Treat it as a rule of thumb and cross-check.

## Claude Code session logs

- Claude Code settings reference: `cleanupPeriodDays` sets "how many days Claude Code keeps session transcripts and other application data before deleting them." Default: 30. https://code.claude.com/docs/en/settings-reference.md
- Claude Code data usage: transcripts are stored "locally in plaintext under `~/.claude/projects/` for 30 days by default." https://code.claude.com/docs/en/data-usage.md
