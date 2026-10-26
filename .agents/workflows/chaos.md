---
description: Adversarial review of a high-risk spec, in a fresh chat, max 2 rounds. Run only when the user explicitly invokes /chaos.
---

# /chaos [feature]
1. Resolve the active feature. Load `00_router.md` and `chaos_monkey.md`. Act ONLY as the Chaos Monkey.
2. Require `high_risk: true` and state `planned`. Otherwise say why it is not needed or not ready, and stop.
3. Follow the Chaos Monkey rule (P0/P1/P2 findings, max 2 rounds, edit only your own section and the review file).
4. End with: if P0/P1 remain open, "Next: run /plan to revise, then /chaos again." Otherwise, "Next: run /approve."
