---
description: The user's approval gate: records Approved and the review mode before any code is written. Run only when the user explicitly invokes /approve.
---

# /approve [feature]
1. Resolve the active feature. Load `00_router.md`. Act as the Planner (gate recorder only).
2. Require state `planned` (when `high_risk` is false) or `hardened` (when `high_risk` is true). Otherwise tell the user what is missing.
3. Show the spec's `## Summary for Approval`, the task count, and any open P2 findings. Ask for two things: the word "Approved", and the review mode (`validator` default, or `human_per_task`).
4. On "Approved", set `state: approved` and `gate_mode`.
5. End with: "Next: run /build."
