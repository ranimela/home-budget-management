---
description: Writes the implementation spec (full lane, after the PRD is approved) or the mini-spec (quick lane), and sets high_risk and tasks_total. Run only when the user explicitly invokes /plan.
---

# /plan [feature]
1. Resolve the active feature (see the router). Load `00_router.md` and `planner.md`. Act ONLY as the Planner.
2. Full lane: require state `prd_approved` (otherwise tell the user to run `/pm`). Fill any `EDIT` lines in `conventions.md` first, run `/grill-me`, then write `/.plans/<feature>.md`.
3. If the state is `planned` with open Chaos findings, revise the spec per planner directive 12 instead of starting over.
4. Set `high_risk`, `tasks_total`, and state `planned` in the status file. If the change must be full lane, say why and tell the user to run `/pm`.
5. End with: if `high_risk` is true, "Next: run /chaos in a fresh chat." Otherwise, "Read the Summary for Approval, then run /approve."
