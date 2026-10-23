# Continuous integration and review workflow

RMS-31 / #32 extends the PostgreSQL workflow from #35 in place. The existing `postgres` job/service remains the only database test infrastructure. A separate `node` job tests the Socket.io client fixture on Node 22. No production feature code, automatic merge or review bypass is added.

Both push-to-main and pull_request events run the relevant Django and Node checks when backend, realtime, quality, formal source documents or this workflow change. Main pushes provide post-merge regression coverage; PRs include stacked dependencies. The PostgreSQL job installs pinned requirements, validates RTM/source hashes, records versions, checks Django/migration consistency, migrates a clean database, seeds twice, and discovers every feature test plus shared harness tests. PostgreSQL uses normal settings and real PBKDF2. The Node job uses `npm ci` and produces JUnit for its three fixture checks.

Django's runner emits per-executable JSON with commit, environment, IDs, scope and outcome. Raw logs and environment output accompany it. `always()` upload steps preserve available artifacts even after failure; absent files produce a warning, never a fabricated pass. Artifacts retain for 30 days. Reproduce and copy important evidence into the repository through a reviewed PR before expiration.

The README reminder matches actual document folders, paginates comments, recognizes the old reminder, and updates only the GitHub Actions bot's own marked comment. A per-PR concurrency group prevents parallel duplicates. It runs only for same-repository PRs because fork tokens are read-only; it never executes fork code with write permissions. No pull_request_target event is introduced.

The PR template records the owned issue, SRS IDs, executed checks, exact build/database, evidence, deviations, blocked work, demo and independent review. These checked boxes are declarations by actual reviewers, not automatic approval. Branch-protection rules are an owner-admin configuration task: this PR does not claim checks are enforced or alter repository security settings.

Review order: RMS-29 traceability → RMS-30 harness → RMS-31 workflow. Stacked PRs target their predecessor to keep diffs focused. After owner merge, retarget the next PR to main and rerun its checks. Keep #30/#31/#32 open/In Review until independent teammate review and owner merge; do not silently close them because local tests pass.

Current release limitations remain in INTEGRATION.md and the deviation register. Production realtime, menu/cart/checkout, deployed TLS/browser/security acceptance and PERF/QA procedures remain pending. Actions status is regression evidence, not a release sign-off.
