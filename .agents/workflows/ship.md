---
description: Final gate: README update, stage, secret scan, combined diff, wait for Ship, commit and push the branch. Run only when the user explicitly invokes /ship.
---

# /ship [feature]
1. Resolve the active feature. Load `00_router.md` and `release_wrangler.md`. Act ONLY as the Release Wrangler.
2. Require state `validated` and `validator_token.result == "PASS"`.
3. Follow the Wrangler workflow in order: branch, README, stage, secret scan, diff and summary, wait for "Ship", commit, push the branch.
4. Merge or push `main` only if the user explicitly asks in this session.
5. End by reporting the branch name, commit hashes, and any follow-up.
