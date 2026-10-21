# Job log

| # | Paid | Chain and payer | Transaction | Request id | Order | Job id |
|---|---|---|---|---|---|---|
| 1 | 2026-10-21 07:21 UTC | Ethereum, 0x5bff2a2fecd1d6152676813b21346238733beab1 (Rabby) | 0x0b0d82774bf50ff3b4fcd7bb1bf438f259c2a0c813c75ac089c04cadb6e94a35 | 0x67fcde3a96531cbae7b5a90fe8f24f8fd26c392c542e838c0aab32031590a871 | ea601221-5430-4d34-9be7-f9d5a091646a | 4cc83fbc-42d7-49fe-a9db-4310fb61a570 |

Job 1 body: `job-1-shell-and-store.json` at spec commit 3d4ef5bd (v1.9). Paid on-chain through the Intake (`job.open@job-1`, 0.5 IMD) from the owner's second wallet; IMD admitted it the same second. Status: `GET https://api.imd.fun/jobs/4cc83fbc-42d7-49fe-a9db-4310fb61a570`, result at `/result`, report at `/report.md` when done.

Job 2 continues job 1: `parentJobId` 4cc83fbc-42d7-49fe-a9db-4310fb61a570 is filled in.
