---
description: Checks the current micro-task with lint, security scan, tests, and acceptance criteria, then issues PASS or FAIL. Run only when the user explicitly invokes /validate.
---

# /validate [feature]
1. Resolve the active feature. Load `00_router.md` and `validator.md`. Act ONLY as the Validator.
2. Require state `building`. Validate `current_task`. For the last task (`current_task == tasks_total`), prefer a fresh chat.
3. Follow the Validator rule and write `/.qa/report.md`.
4. End with: PASS and not last task -> "Next: run /build." PASS and last task -> "State is validated. Next: run /ship." FAIL -> "Next: run /build to fix (attempt n of 3)."
