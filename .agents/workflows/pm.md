---
description: Starts a new feature in the full lane: interviews the user with questions only, then writes the PRD. Run only when the user explicitly invokes /pm.
---

# /pm [feature]
1. Resolve the feature name (argument, else ask; kebab-case).
2. Load `.agents/rules/00_router.md` and `.agents/rules/product_manager.md`. Act ONLY as the PM.
3. If `/.plans/<feature>.status.json` is missing, create it from `/.plans/status.template.json` with `feature` set, `lane: full`, `state: prd_drafted`.
4. If the state is `prd_drafted` and a PRD already exists: show it and wait. If the user types "PRD approved", set `prd_approved`.
5. Otherwise follow the PM rule: questions only, then wait, then draft `/.plans/prd.md`, then wait for "PRD approved".
6. End with: "Next: run /plan."
