# Contributing to BillWakeel

Everyone on the team follows these rules so Jira, GitHub and the sprint evidence stay consistent.
Jira project key: **SCRUM**. Board: see the link in the README.

## 1. Branches

| Branch | Purpose | Direct commits? |
|---|---|---|
| `main` | Always working and demoable. Updated only by merging `dev` at the end of a sprint. | No |
| `dev` | Integration branch. All finished stories land here. | No (use a PR) |
| `feature/SCRUM-<n>-<short-name>` | One branch per Jira story, created from `dev`. | Yes |

Examples: `feature/SCRUM-6-fastapi-skeleton`, `feature/SCRUM-10-extraction-agent`.
Use lowercase and hyphens. The branch name must contain the Jira key so Jira links it to the ticket.

Start a story:
```bash
git checkout dev
git pull
git checkout -b feature/SCRUM-10-extraction-agent
```

**Always branch from `dev` and keep your branch in sync with `dev`, never `main`.** Other people's work lands on `dev` while you work, so your branch slowly falls behind and can end up conflicting with theirs. To avoid that, bring the latest `dev` into your branch at least once a day and always before opening a PR:
```bash
git checkout feature/SCRUM-10-extraction-agent
git pull origin dev
```
Resolve any conflicts on your branch, run the tests again, then push. Do not merge `main` into a feature branch. If `git merge` shows conflicts you do not understand, ask the person who wrote the other change before choosing a side.

## 2. Commits (smart commits are mandatory)

Every commit message must follow this format, on **one line**:

```
<JIRA-KEY> #comment <short imperative description of the change>
```

```bash
git commit -m "SCRUM-10 #comment add BillExtraction pydantic schema"
git commit -m "SCRUM-10 #comment retry once on invalid model output"
```

- The Jira key comes first, then `#comment`, then the description. A commit without both is not accepted by the team.
- The comment shows up on the Jira ticket, so write it so a teammate can understand it without opening the code.
- Optional extra: `#time 2h` to log time, for example `SCRUM-10 #time 2h #comment first extraction prompt`.
- Do **not** use `#done` or other transition commands in commits. Tickets are moved on the board by hand (see section 4).
- Small, frequent commits. One logical change each. Individual commits are graded.
- Never commit secrets. `.env` is gitignored. Share keys through chat or a password manager, not the repo.

**IMPORTANT: the email in your Git config must be the same email as your Jira (Atlassian) account, and it must also be added to your GitHub account. If the emails differ, Jira cannot match the commit to you, the smart commit will not work, and your commit will not count towards your individual contribution.**

Set your identity once and check it:
```bash
git config --global user.name "Your Name"
git config --global user.email "email-used-on-jira-and-github"
git config --global user.email    # confirm it prints the right address
```

Quick test after your first commit: open the ticket in Jira and check that the comment and the commit appear in the Development panel. If not, fix your email before continuing.

## 3. Pull requests

1. Push your branch: `git push -u origin feature/SCRUM-10-extraction-agent`
2. Open a PR **into `dev`**. Title starts with the key: `SCRUM-10 Extraction Agent v0`.
3. In the description, state what changed and how to test it.
4. At least one teammate who did **not** write the code reviews and approves.
5. Merge using **Create a merge commit** (not Squash, not Rebase). This keeps every individual commit, with its author, on `dev`. Squashing here would collapse your commits into one and hurt individual-commit grading.
6. Delete the feature branch after merging (the **Delete branch** button on the PR). The commits remain on `dev`.

## 4. Jira workflow

| Event | Ticket status |
|---|---|
| Start working | In Progress |
| PR opened | In Review |
| PR approved and merged, acceptance criteria shown | Done |

Record story points on every ticket. Do not change points after the sprint starts.

## 5. Definition of Done

A story is Done only when:
1. Code is merged to `dev` through a reviewed PR.
2. Unit tests are written and passing.
3. Acceptance criteria are demonstrated in the sprint review.
4. Every commit uses the smart-commit format (`KEY #comment ...`) and the PR title carries the Jira key.
5. If an agent or prompt changed: prompt version bumped, changelog updated, prompt test run.
6. No secrets committed.
7. README or docs updated if behaviour or setup changed, and `docs/decisions.md` updated if an architecture decision was made.
8. Jira ticket is in Done with story points recorded.

## 6. Prompts and engineering decisions

**What a prompt is here:** each agent (extraction, grounding, anomaly, letter) sends a block of written instructions to the Gemini model telling it exactly what to do. That text is stored as a file so it is reviewed, tested and traced like code. Example: `prompts/extraction/v1.md` holds the instructions "read this bill, return only what is printed, use null if unsure".

**Where they live:** `prompts/<agent>/vN.md` (for example `prompts/extraction/v1.md`, then `v2.md`).

**The rule:** never edit or delete a released version. To change a prompt, copy it to the next version number, edit the copy, point the code at the new version, and add a row to `prompts/CHANGELOG.md`.

**Why we keep old versions:**
- Test and evaluation results are tied to a version ("v2 scored 8/10, v3 scored 9/10"). If v2 is deleted, that evidence cannot be reproduced.
- We can roll back to a known-good version if a new one performs worse.
- The report and viva require traceability from requirement to prompt version to test. The `prompts/` folder plus the changelog shows this at a glance.
- The files are small text, so keeping them costs nothing. Only the newest version is used by the running code.

**Who updates the changelog:** whoever changes the prompt, in the same PR as the change. This follows the work, not the Scrum role, so it does not matter who is Developer, Scrum Master or Product Owner in the current sprint. The PR reviewer checks that a new prompt version always comes with a changelog row and an updated evaluation result.

**Changelog row format:**
```
| Date | Agent | Version | Jira | Change |
| 2026-10-16 | extraction | v2 | SCRUM-10 | Return null instead of guessing; eval 7/10 schema-valid |
```

**Commit example:** `SCRUM-10 #comment add extraction prompt v2 and changelog entry`

### Engineering decisions (`docs/decisions.md`)

Keep a written record of architecture decisions. We will be asked to defend them in the report and the viva, and memory fades.

**Add an entry when** the team decides something that affects the architecture or scope, for example:
- choosing a library, model or approach (how PDFs are sent to Gemini, which vector store to use)
- changing the API contract or the `BillExtraction` schema
- a design trade-off (in-memory store now, database later)
- a scope cut or addition (dropping the water pilot, adding a new DISCO)

**Do not add an entry for** routine work such as bug fixes, small UI changes or refactors.

**Who and when:** whoever makes or proposes the decision, in the same PR as the change. As with prompts, this follows the work, not the Scrum role. The PR reviewer checks that a decision-level change comes with an entry.

**Entry format:** a date, a short heading, and one paragraph covering what was decided, why, and what was rejected. Mention the Jira key if there is one. Never edit an old entry. If a decision is reversed, add a new entry that says so and links to the old one.

```
## 2026-10-16: PDFs are sent to Gemini as media parts (SCRUM-10)
Bills uploaded as PDF are sent directly to the model rather than converted to images first. This keeps the code simple and preserves text quality. Rejected: converting every page to PNG, which adds a dependency and loses sharpness.
```

**Commit example:** `SCRUM-10 #comment record pdf input decision in decisions log`

## 7. Sprint end: merging `dev` into `main` and tagging

At the end of each sprint, after the sprint review is done and the Product Owner has accepted the stories, `dev` is merged into `main` and tagged. **We do this through GitHub (the web interface), not the terminal.** The ruleset on `main` requires a pull request and one approval, so direct terminal pushes to `main` are blocked anyway.

### Step 1: Merge the Pull Request
1. On GitHub, open a Pull Request from `dev` to `main` (Pull requests, New pull request, base `main`, compare `dev`). Title: `Sprint 1 release` (use the right sprint number), and list the merged stories in the description.
2. Ensure all required approvals are met (one teammate who did not open the PR) and any checks have passed.
3. Click the dropdown arrow next to the merge button and select **Squash and merge**.
4. Click the button to confirm the merge.

### Step 2: Tag the Release via GitHub UI
You cannot tag directly inside the PR timeline, but you can create the tag through GitHub Releases immediately after:
1. On the main repository page, look at the right-hand sidebar and click **Releases** (or click the **Tags** tab above the file list).
2. Click **Draft a new release**.
3. Click **Choose a tag**, type the version name (for example `sprint-1`), and click **Create new tag**.
4. Make sure the **Target branch** dropdown is explicitly set to `main`.
5. Add a release title and description (you can use **Auto-generate release notes** to pull info from merged PRs).
6. Click **Publish release**. This creates the Git tag and anchors it to the exact merge commit on `main`.

### Rules for our repo
- **Who:** the Scrum Master coordinates this on the last day of the sprint. The repo owner (Rehan) merges or tags if admin rights are needed. Tell the group chat before you start so nobody clicks merge at the same time.
- **Tag names:** `sprint-1`, `sprint-2`, `sprint-3`, `sprint-4`.
- **Delete feature branches after they are merged into `dev`; never delete `dev`.** Feature PRs use "Create a merge commit", so all individual commits stay on `dev` with their authors. Squash merging is used only for `dev` to `main`, which collapses commits on `main` but leaves the full history on `dev`. Take commit evidence for grading from `dev`.
- **Sync `dev` with `main` before the next sprint.** After a squash merge the two branches have different histories, so the next `dev` to `main` PR can show conflicts or repeat old changes. Fix it once, right after the release (one person, announced in the group chat):
  ```bash
  git checkout dev
  git pull origin dev
  git pull origin main
  git push origin dev
  ```
  If the ruleset blocks that push, do it through a short PR from a temporary branch into `dev`.

## 8. Repository settings (set once by the repo owner, Rehan)

Settings → Rules → Rulesets → New branch ruleset. Create it only **after** you have committed the starter docs to `main` and created `dev`, and before the rest of the team starts branching, because the ruleset blocks direct pushes.

- **Name:** protect main and dev. **Enforcement status:** Active.
- **Target branches:** the default branch (`main`) plus `dev` (Add target → Include by pattern → `dev`).
- **Tick:** Restrict deletions, Block force pushes, Require a pull request before merging with **1 required approval**.
- **Leave unticked:** Restrict creations, Restrict updates, Require linear history, Require deployments, Require signed commits, dismiss stale approvals, required teams, Code Owners, status checks (no CI yet).
- **Bypass list:** the repo admin role only, for emergencies. If you use it, tell the team.

The author of a PR cannot approve it, so a teammate must review every PR.
