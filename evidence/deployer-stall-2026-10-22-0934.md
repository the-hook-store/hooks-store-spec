# IMD deployer stall, status at 09:34 UTC on 2026-10-22

Last launch to go live anywhere on IMD: 2445 (Ethereum, 01:34 UTC). Everything admitted since then is still waiting, on both chains and from several projects:

- 2457 admitted, chain 4663, kind custom_token, artifacts 0, last update 2026-10-22T07:39:24.066Z
- 2456 admitted, chain 1, kind evm_contracts, artifacts 0, last update 2026-10-22T06:10:49.790Z (ours)
- 2455 admitted, chain 1, kind evm_contracts, artifacts 0, last update 2026-10-22T07:52:00.668Z
- 2454 admitted, chain 4663, kind evm_contracts, artifacts 0, last update 2026-10-22T05:00:28.352Z (ours)
- 2452 admitted, chain 1, kind custom_token, artifacts 0, last update 2026-10-22T03:28:41.373Z
- 2450 admitted, chain 4663, kind evm_contracts, artifacts 0, last update 2026-10-22T02:48:46.556Z (ours)
- 2449 admitted, chain 4663, kind evm_contracts, artifacts 0, last update 2026-10-22T03:14:26.210Z (ours)
- 2448 admitted, chain 4663, kind univ4_hook, artifacts 0, last update 2026-10-22T02:37:18.847Z (ours)
- 2433 admitted, chain 1, kind evm_contracts, artifacts 0, last update 2026-10-22T02:40:41.625Z

Launch 2448 (our test token, Robinhood Chain) is the first one the deployer touched after 2445. Its deploy attempt at 02:37:18 UTC failed inside IMD's RPC provider, and the record has not been updated since. deployFailure, with the provider key removed:

```
broadcast failed: Missing or invalid parameters.
Double check you have provided the correct parameters.: Post "http://robinhood-seq-sequencer-path-r8id-16xlarge-nitro-0.robinhood-seq.svc.cluster.local:8547/…": dial tcp4 172.24.19.254:8547: connect: cannot assign requested address

URL: https://burned-delicate-snow.robinhood-mainnet.quiknode.pro/<provider key removed>

Details: Post "http://robinhood-seq-sequencer-path-r8id-16xlarge-nitro-0.robinhood-seq.svc.cluster.local:8547/…": dial tcp4 172.24.19.254:8547: connect: cannot assign requested address
Version: viem@2.57.7
```

The other four of ours have no deployFailure at all: the deployer never attempted them. The docs (https://imd.fun/docs/llms.txt) describe no retry or refund for a failed deploy and name no support channel.

Watchers: one combined watcher now polls GET /launches?limit=20 every minute and exits when any of ours leaves 'admitted' or anything newer than 2445 goes live.
