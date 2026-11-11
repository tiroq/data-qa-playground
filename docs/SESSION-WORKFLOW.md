# Session Workflow and Language Agreement

## Chat naming convention (Sessions 09–17)

Use the same short title in the calendar and when renaming a ChatGPT conversation:

`🎯 Exness | Session NN — Short Title`

The full canonical **Chat title** is provided at the top of each session's `README.md` (and `START_HERE.md` where present). The chat name is metadata for navigation, not proof of session completion. Never rename existing chats automatically.

## Language and format

The Exness technical interview on **2026-11-16** is conducted **in Russian**. Each ChatGPT learning session therefore uses Russian for all task explanation, spoken/written discussion, assessment and follow-up. SQL/Python and ordinary technology terms may remain in English. Exercise specifications and code committed to this GitHub repository remain in English.

## Before a session

1. Open the numbered `exercises/NN-.../README.md` file and copy its standalone Russian-language kickoff prompt into a fresh ChatGPT conversation.
2. Read only the problem statement and prerequisites. Do **not** generate or expose reference code before an independent attempt.
3. Check the **actual** available services and data; only PostgreSQL and Session 01 seed are initially implemented.
4. If an exercise needs additional test data, add an isolated, named fixture rather than rewriting the original seed.

## During a session

1. Present one practical task at a time; wait for the candidate's answer.
2. Ask for assumptions about data grain, keys, temporal eligibility and expected output columns.
3. Challenge missing rows, duplicated keys, nullability, many-to-many joins, event-time order and slow/partial processing.
4. Review submitted code and reasoning before presenting possible reference alternatives.
5. Prefer runnable minimal reproductions to abstract claims; record what was observed versus inferred.

## After a session

1. Save the original attempt, reviewed correction and tests **separately**, when appropriate.
2. Write a short outcome report with score, verified commands/results, what failed, what was fixed and three next priorities.
3. Mark status in `ROADMAP.md`; update only when evidence exists.
4. Link resulting branch/PR to the relevant session notes or acceptance checklist.
5. Feed gaps into later sessions and calendar prompts; do not repeat basic content that was demonstrated correctly.

## PR conventions

- Typical branch: `session/02-sql-live-coding`.
- Keep one session's solutions or infrastructure changes in a focused PR when possible.
- PR body: session goal, links to exercise, tests run, measured outputs, deviations from acceptance criteria, next gaps.
- Do not make a mock-interview answer public as if it were an automatic test result.
- No unverified claims that tests passed; never invent outcomes.

## Suggested per-session review note

```markdown
# Session NN — Review
Date / duration:
Attempt and commit/PR:
What was actually executed:
Verification command(s) and output:
Correctness /10:
Completeness /10:
Edge cases /10:
Explanation /10:
Overall /10:
Top 3 weak points:
Next-session adjustment:
```
