# BillWakeel — Definition of Ready, Definition of Done and Role Rotation

**Course:** EC-360 Software Engineering (CEP), NUST CEME | **Team:** Rehan, Baig, Abdullah Swati (GC), Ayesha Zafar

## Definition of Ready (DoR)
A story may enter a sprint only when all of these are true:
1. Written as "As a ___, I want ___, so that ___".
2. Has acceptance criteria that can be demonstrated or tested.
3. Has a story point estimate agreed by the Developers (Fibonacci: 1, 2, 3, 5, 8).
4. Small enough to finish within one sprint (8 points or less; split larger stories).
5. Dependencies identified and unblocked, or scheduled earlier in the same sprint.
6. Needed data, samples or tariff documents are available or assigned.
7. Prioritised by the Product Owner and has one named owner.

## Definition of Done (DoD)
A story is Done only when all of these are true:
1. Code is merged to `dev` through a pull request reviewed by someone who did not write it.
2. Unit tests are written and passing.
3. All acceptance criteria are demonstrated in the sprint review.
4. Every commit uses the smart-commit format (`SCRUM-10 #comment ...`) and the PR title carries the Jira key.
5. If an agent or prompt changed: prompt version bumped, changelog updated, prompt test run.
6. No secrets committed; `.env` is gitignored.
7. README or docs updated when behaviour or setup changed, and `docs/decisions.md` updated if an architecture decision was made.
8. Jira ticket is in Done with story points recorded.

## Scrum role rotation
| Sprint | Dates | Scrum Master | Product Owner | Developers |
|---|---|---|---|---|
| 1 | 12 Oct – 23 Oct | Ayesha Zafar | Abdullah Swati | Rehan, Baig |
| 2 | 26 Oct – 6 Nov | Rehan | Baig | Ayesha, Swati |
| 3 | 9 Nov – 20 Nov | Swati | Ayesha | Rehan, Baig |
| 4 | 23 Nov – 4 Dec | Baig | Rehan | Ayesha, Swati |

Everyone is Scrum Master once, Product Owner once and Developer twice. All roles still write code and make individual commits every sprint.

## Role responsibilities
- **Scrum Master:** runs standups, planning, review and retro; keeps Jira up to date; removes blockers; captures burndown screenshots; logs velocity.
- **Product Owner:** owns and orders the backlog; writes and clarifies acceptance criteria; accepts or rejects finished stories at the review.
- **Developers:** estimate, build, test and demo stories; review each other's PRs.

## Ceremonies
| When | Ceremony | Output |
|---|---|---|
| Sprint day 1 | Planning | Sprint goal, committed stories with points and owners |
| Daily | 10-minute standup (chat is fine) | Blockers surfaced |
| Mid-sprint | Check-in | Burndown screenshot #1 |
| Last working day | Review and demo | Working increment, burndown screenshot #2 |
| Last working day | Retrospective | Keep/change items, velocity logged, roles rotated |
