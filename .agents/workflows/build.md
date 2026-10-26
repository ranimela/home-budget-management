---
description: Implements the next micro-task of the approved spec, or fixes a failed one. Run only when the user explicitly invokes /build.
---

# /build [feature]
1. Resolve the active feature. Load `00_router.md` and `builder.md`. Act ONLY as the Builder.
2. Require state `approved` or `building`. If the last Validator result is FAIL, fix only what `/.qa/report.md` lists.
3. Do the next micro-task per the Builder rule, then present the diff with the `Changed:` and `Check:` lines.
4. End with: `gate_mode: validator` -> "Next: run /validate." `human_per_task` -> "Review the diff; reply to approve, then run /validate."
