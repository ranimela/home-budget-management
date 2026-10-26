---
description: Interviews the user on edge cases, data constraints, and dependencies before planning, with questions only. Run only when the Planner or the user invokes /grill-me.
---

# /grill-me
1. Read `/.plans/prd.md` and `/.plans/context-map.json` (if present). Do not ask anything the PRD already answers.
2. Reply with questions ONLY (max 8, grouped): data structures and ownership, external dependencies and rate limits, environment and OS constraints, failure behavior, volume and scale, security and secrets.
3. Be blunt. No recommendations and no draft plan until the user answers.
4. After the answers, list the assumptions you will carry into the plan and mark each `[CONFIRMED]` or `[UNVERIFIED]`.
