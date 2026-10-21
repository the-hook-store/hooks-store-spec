# Job log

| # | Paid | Chain and payer | Transaction | Request id | Order | Job id |
|---|---|---|---|---|---|---|
| 1 | 2026-10-21 07:21 UTC | Ethereum, 0x5bff2a2fecd1d6152676813b21346238733beab1 (Rabby) | 0x0b0d82774bf50ff3b4fcd7bb1bf438f259c2a0c813c75ac089c04cadb6e94a35 | 0x67fcde3a96531cbae7b5a90fe8f24f8fd26c392c542e838c0aab32031590a871 | ea601221-5430-4d34-9be7-f9d5a091646a | 4cc83fbc-42d7-49fe-a9db-4310fb61a570 |
| 2 | 2026-10-21 09:09 UTC | Ethereum, 0x5bff2a2fecd1d6152676813b21346238733beab1 (Rabby) | 0x0200bd97e7e5c2adc87d3f463637c0be162ec6adf412c241cffc70feedfa0fd9 | 0x7c7a661267d1971793386311c93174136a25dc8d74ee5bff8d33e2f7139ac6ef | e5ae47be-14a9-4519-abd8-a2a76dc1932f | a9268c47-5864-45b4-ae6e-022d726eed3c |

Job 1 body: `job-1-shell-and-store.json` at spec commit 3d4ef5bd (v1.9). Paid on-chain through the Intake (`job.open@job-1`, 0.5 IMD) from the owner's second wallet; IMD admitted it the same second. Status: `GET https://api.imd.fun/jobs/4cc83fbc-42d7-49fe-a9db-4310fb61a570`, result at `/result`, report at `/report.md` when done.

Job 2 continues job 1: `parentJobId` 4cc83fbc-42d7-49fe-a9db-4310fb61a570 is filled in.

## Job 1 delivered (2026-10-21 08:48 UTC)

- Nodes: `site_content_check` accepted 07:30, `build_website` accepted 08:34 (structural verification, tree f6e354e8), `design_critic` accepted 08:47. The critic raised 9 findings; the worker reproduced all 9 and fixed them before acceptance (see `tests/results/audit-reproduction.json` in the delivery). One of them was ours: the mockup's Learn cost answer said 0.1 IMD for 7 days; the site says 24 hours and the mockup is corrected in this repo.
- Delivery: https://github.com/identity-md-launches/launch-2369-build-hooks-store-phase at commit 19b00e34 (pull request 1, merged). Built from this repo at 3d4ef5bd. Vite + React + TypeScript under `web/`, the pond engine under `src/scene/`, export in `dist/`.
- Site: https://the-hooks-store.sites.imd.fun, pinned CID bafybeihqdd2ubw6amcjxmhrn6far5ramzsnwwkmmojexena7jwcsgl2kke (1,067,311 bytes).
- Owner's check: headless screenshots at 1440, 500 and 390 of Store, Learn and Builder against the mockup. The pond is a faithful port (same Pepe, boat, rod, fish; the cast sequence runs). Two cosmetic deviations go to the top of job 2's objective: the desktop top bar is smaller and more cramped than the mockup's, and the landing eyebrow and lede use different text and faces. Records: `evidence/job-1-job.json`, `evidence/job-1-result.json`.

## Job 2 paid (2026-10-21 09:09 UTC)

Job 2 body: `job-2-builder.json` at spec commit 52e5b06 (v1.11), `job.continue@job-1` on the project of job 1 (0.5 IMD, one transaction: the allowance from job 1 covered it). IMD admitted it the same second and recorded exactly our objective. Status: `GET https://api.imd.fun/jobs/a9268c47-5864-45b4-ae6e-022d726eed3c`. Job 3's `parentJobId` is set to it.
