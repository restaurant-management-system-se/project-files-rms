# RMS evaluation checklist

Audit: 11 November 2026, default branch 566d0a8. Branch checks and feature-branch merges are not main delivery.

## 1. Requirements and design

- **SRS:** IEEE 830-1998 structure; sections 1–2 cover introduction and description; §§5–6 give numbered FRs/NFRs and measurable targets. §4.1 Figure 1 is the UML use case diagram. §6 lists four security objectives and eight requirements.
- **Test Plan:** IEEE 829 structure; sections 3–5 cover scope, exclusions and approach. §5.1 and Appendix D cover security. §13 and SRS Appendix C provide traceability. The minimum case count is exceeded: the validator verified 29 requirements and 58 planned cases across FRs and NFRs.
- **SAD:** Architectural pattern, components, security and traceability in §§2–4 and §10. Three sequence diagrams in §5; API design and errors in §§7–8. IEEE conformance is unverified; the SAD does not identify the standard or a conformance mapping.

## 2. Agile planning and delivery

- [Linked Product Backlog](https://github.com/orgs/restaurant-management-system-se/projects/1): 32 SRS-based issues, all assigned, with a Story Points field and 134 provisional points reported. Per-item estimates were not independently verified. The board says sprint planning was deferred. Confirm actual sprint allocations with the team for 19–23 and 26–31 October 2026.
- **Sprint 1:** Actions runs on pushes and PRs. Sampled owner-authored work: #35/#38/#39 (Captain-King-2024), #34 (AkulkrishnaMS), #33/#36 (Noctowl-Abhay). Merges exist; #35/#38/#39 have no submitted formal reviews. Blanket conformance/method approval is unverified. No one-minute recording found on main or in releases.
- **Sprint 2:** #46 and #53–#58 were open; #52 and #59–#62 merged into feature branches. No final freeze record or two-minute recording found. The [deviation register](../Issues/Backlog/DEVIATION_REGISTER.md) has recorded and pending decisions. #57 documentation remains open; the main README's Node startup instruction points to a missing entry point.

## 3. Testing and reports

- Source cases, executable mappings and feature evidence exist; original documents and outstanding branches still need reconciliation.
- [PostgreSQL CI](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/41185753231) passed at main 566d0a8. [PR #56 Chromium and Firefox](https://github.com/restaurant-management-system-se/project-files-rms/actions/runs/41185342546) passed at f132b25c, superseding earlier failures; this is partial ST_13, not full browser acceptance. Full Test Plan execution is unverified.
- [Feature reports and booking output](../backend/docs) and [quality evidence/templates](../quality) exist. Final execution summary, including manual and security results, remains open.

## 4. Final demonstration and viva

- On a pinned SHA, rehearse public availability, signed-in confirmation, overlapping booking rejection, history and permitted cancellation. Show staff and live tracking only on a rehearsed integration SHA.
- Show the register and explain Django/PostgreSQL as the source of truth and Node as the planned/branch realtime delivery layer. Distinguish approved decisions and proposals.
- Show the public repository and version history. Each developer should open their own issue, PR, and test evidence. Explain an estimate, sprint objective, actual blocker, row locking, authorization, and what CI did and did not cover.

## Closeout

Confirm sprint assignments and all estimates; review and integrate the intended branches; rerun and record actual Test Plan outcomes on one SHA; record the owner's freeze; upload real one-minute and two-minute videos with their demo SHA. Leave review and approval evidence to the team members responsible.
