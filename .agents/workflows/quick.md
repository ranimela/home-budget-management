---
description: Small change to existing code (max 3 files, no money, personal data, auth, deletion, migration or new dependency); skips PRD, interview, and Chaos. Run only when the user explicitly invokes /quick.
---

# /quick [feature] [one-line description]
1. Load `00_router.md` and `planner.md`. Act ONLY as the Planner.
2. Check the quick-lane exclusions in the router. If any apply, set nothing, say why, and tell the user to run `/pm`.
3. Create `/.plans/<feature>.status.json` from the template with `lane: quick`, then write the mini-spec to `/.plans/<feature>.md` (Goal, Files, Change, Verify). Set `tasks_total: 1` and state `planned`.
4. Fill any `EDIT` lines in `conventions.md` that this change needs.
5. End with: "Read the mini-spec, then run /approve."
