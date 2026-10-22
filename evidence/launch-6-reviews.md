# Launch 6 (ReedGuard) reviews, copied from https://explorer.imd.fun/jobs/292d0dab-c9a9-4c74-951d-c36d9855680b on 2026-10-22

Implemented ReedGuard and constructor-only ReedGuardDeployer, with offline dependencies and deployment documentation.
Validation passed:

forge build
forge test: 42 passed with the supplied seed, including 8,192 invariant operations
forge fmt --check

Deployment parameters, assumptions and operational responsibilities are documented in README.md. Live deployment remains with the launch pipeline.

---

I've written the review to .imd-findings.json. It has one low-severity finding and a coverage row for all 7 entry points, plus two rows for invariants I checked. No source files were changed. I didn't write or run a Foundry proof test, since that was only required for critical or high findings.
Finding 1 (low): the fee rate depends on how the swap is specified (src/ReedGuard.sol, _specifiedFee)

What's right: when the swap specifies the token amount, afterSwap takes 1% of the ETH the pool actually traded.
What's wrong: when the swap specifies the ETH amount, the fee is 1% of the amount the user typed in, and the pool then trades that amount adjusted by the fee.
Buys, exact ETH in: amountSpecified = -1e18 gives a fee of 1e16, but the pool trades only 0.99e18. That's 1.0101% of what was traded.
Buys, exact tokens out: a buy that makes the pool take the same 0.99e18 ETH pays 9.9e15.
Sells, exact ETH out: asking for 1e18 ETH out makes the pool pay out 1.01e18 and charges 1e16, which is 0.990099% of what was traded.
Why it matters: the brief says fees are computed on the amount actually traded. The gap is about 0.01% of volume, but it is systematic, and sellers can pay slightly less by asking for an exact ETH output.
Suggested fix: compute the ETH-specified fee as mulDiv(|s|, 100, 10100) for exact input and mulDiv(|s|, 100, 9900) for exact output, where |s| is the specified ETH amount. Alternatively, document that these fees are taken on the amount the user specifies.

What holds:

ETH-side fee: the fee is always taken in ETH, never from the token. It is calculated with mulDiv, rounds down by under 1 wei in the swapper's favour, and amounts are range-checked before conversion.
Partial fills: amountSpecified + fee matches how Uniswap v4 adjusts the swap amount, so a partly filled ETH-specified swap reverts as the brief requires.
Pool rules:

Only native-ETH currency0 pools can be initialised.
Pause is checked per pool.
The 30-second cooldown allows the next swap exactly at timestamp + 30, as specified.
Liquidity callbacks aren't enabled, so removing liquidity always works.


Fee payout: _payOrDefer either sends the fee or mints a claim. claimFees/unlockCallback burn the claim and send it to the fixed recipient, capped at the PoolManager's ETH balance, with the PoolManager's accounting netting to zero.
Deployer: the CREATE2 address calculation in ReedGuardDeployer is laid out correctly.

Static-analysis leads: I checked them and none turned into findings. Aderyn's hash-collision and shift-order warnings are false positives. Its reentrancy warning and Slither's unused-return warning on claimFees are by design: the state is updated before the external call, and the ignored return value isn't needed.
Not covered: I didn't measure gas costs, and I didn't run the mixed-route arithmetic on-chain; it is worked out by hand from v4-core's Hooks.beforeSwap.

---

Created launch.json with one ReedGuardDeployer entry and the required constructor arguments.
Verified against the compiled ABI. forge build passed; all 42 tests passed with the supplied fuzz seed. Only launch.json changed.

---

The review is complete and .imd-findings.json holds the result: one low-severity finding and coverage rows for all seven entry points plus six checked invariants and leads. The scratch test directory was removed and the tree is otherwise unchanged.
What I checked, against the Economic Security, Invariant and Flow Gap guides:

Fee settlement and delta netting. Traced all four swap modes through the pinned v4 Hooks.beforeSwap/afterSwap and Pool.swap. The hook's returned deltas always equal what it takes or mints, so its balance nets to zero. The ETH fee is settled inside the paying swap, never from the pool token. The token-only-seeded fresh-manager case correctly mints a claim.
Partial-fill guarantee. The afterSwap equality on the raw pool delta cannot be satisfied by any price-limit or empty-liquidity stop, so ETH-specified partial fills revert with fee, cooldown and price rolled back.
Claim ledger invariant. Per-pool ledger and the hook's ERC-6909 ETH balance move together in exactly two places, claims are always ETH-backed by the swapper's settlement, proceeds reach only the immutable recipient, and a rejecting recipient cannot block swaps or lose a claim.
Dependency and reentrancy seams. The recipient's receive hook runs mid-swap but the shared execution guard rejects re-entered swaps and claims. No oracle, outside pool or token call sits on the swap path.
Deployment economics. The unbounded salt search measured about 1.85M gas and 37,944 iterations in the two existing tests, well inside any transaction gas limit.
Static-analysis leads. All slither and aderyn lines were traced and are false positives or harmless redundancy.

The one finding (low): the fee basis differs by swap mode. For an identical pool trade from the same state, exact-input ETH buys pay 0.0100 ETH while exact-output token buys pay 0.0099 ETH, and exact-output ETH sells pay 0.0100 ETH while exact-input token sells pay 0.0101 ETH. Swappers can pick the cheaper mode and the recipient collects 1% less fee. The README documents the two bases, so this is a clarification against the brief's single fee rule rather than a loss of funds. The reproduction with exact wei amounts is in the file.
Not reached: nothing in my assigned area. I did not independently verify that the Robinhood Chain PoolManager address runs the pinned v4-core revision, which is outside the economics scope and needs a network check by the deployment rehearsal.

---

Review complete. The findings file is written and validated, and the working tree holds no source changes.
Outcome
The ReedGuard control flow holds under the Execution Trace, Periphery and First Principles passes. I traced every entry point, re-derived the v4 delta arithmetic for all four swap modes, and probed the two riskiest paths with scratch tests on the vendored PoolManager. Both passed: a multi-hop through two ReedGuard pools in one unlock settles cleanly with both fees paid, and enabling a protocol fee does not break the exact-fill check for ETH-specified swaps.
One finding, low severity

beforeInitialize accepts a pool key carrying the dynamic-fee flag. Such a pool opens at a zero LP fee, and only the hook could ever change it, which it never does. LPs in that pool earn nothing while the hook still takes its 1% ETH fee. The README acknowledges this, so it is a footgun for third parties rather than a loss to the owner. The fix is a one-line rejection of dynamic-fee keys in beforeInitialize.

What held, and why

The ETH-specified fee path is sound: the specified-side delta from beforeSwap, the partial-fill comparison in afterSwap, and the take-or-mint settlement net the hook's delta to zero on every path.
Claims are isolated per pool, decremented before the unlock, restored on any revert, and the callback is usable only during a hook-initiated claim.
Reentrancy from a paying recipient is blocked for swaps and claims through the shared guard.
The deployer's CREATE2 preimage layout, salt progression, mask and argument forwarding are correct. The aderyn shift-order and hash-collision leads are false positives, and the slither leads are all intended behavior.

Coverage
All seven listed entry points have rows, plus rows for the deployer constructor, two invariants and the static-analysis leads. Nothing was left unreached.
Not a finding, but worth the launch operator's attention
The pinned univ4_hook protected tests initialize the launch pool with whatever paired currency the environment names. This hook rejects any pool whose currency0 is not native ETH, as the brief requires, so if those tests run with an ERC-20 pair they fail in the initialization check. That is a service-configuration question for a contracts-only launch, not a code defect.

---

The review is complete and .imd-findings.json is written at the repository root with 3 findings and 11 coverage rows. All 7 listed entry points have a row.
Outcome. The access-control, trust-gap and asymmetry surface of ReedGuard holds. Every hook callback and the unlock callback accept only the PoolManager. The owner can do nothing but pause and unpause, and both are checked on msg.sender. The claim ledger is decremented before the external unlock, the hook never grants ERC-6909 approvals, and the delta accounting matches the vendored v4 Hooks.beforeSwap/afterSwap on all four swap modes. On Robinhood Chain the recipient is a plain EOA and the PoolManager holds about 24,000 ETH, so fees will be paid directly in production. The static-analysis leads were all false positives when traced, including aderyn's two "high" lines on the deployer's CREATE2 preimage.
Findings reported:

Low, fee basis asymmetry at src/ReedGuard.sol:183. Exact-input swaps pay 1.00% of gross ETH and exact-output swaps pay 0.99%. A trader who submits exact-output orders pays one basis point less on volume, and the recipient receives less than the stated 1.0% on that flow. Measured with a scratch test; concrete amounts are in the file.
Info, dynamic-fee flag accepted at beforeInitialize. Such a pool has a permanent zero LP fee because the hook never sets one.
Info, shared tx.origin cooldown. One relayer or bundler origin blocks every user it serves for 30 seconds per pool. This is the agreed design, recorded as a trust assumption.

Not reached. Nothing in my assigned area. The unbounded salt search gas and the exact-input price-limit revert are both behaviors the brief asks for, so I did not report them. No critical or high finding exists, so no proof test is attached. The probe test under test/scratch/ is not part of the submission.

---

Added tests for batch rollback, fee and supply boundaries, claim recovery, and liquidity lifecycle invariants. Changes are confined to test/.
forge build and forge test pass with the required seed: 64 passed, 0 failed, 0 skipped, including 24,576 new invariant calls.
No implementation defect was reproduced. Testing used the local PoolManager; no live-chain fork was run.

---

The review is complete and .imd-findings.json is written. The working tree is clean apart from the ignored test/scratch/ and the findings file.
Outcome: no critical, high or medium defects. The hook's delta accounting, reentrancy guards, pause and cooldown isolation, claim ledger and the deployer's CREATE2 mining all hold under trace and under scratch tests run against the vendored v4 PoolManager. The existing suite passes 64 of 64.
Findings kept (3):

Low, fee basis differs by swap mode. Three specialists reported the same root cause, merged into one. ETH-specified swaps charge 1% of the caller's amount, token-specified swaps charge 1% of the pool's realized ETH delta. Reproduced from one snapshot: identical pool trades paid 0.0100 vs 0.0099 ETH on buys and 0.0100 vs 0.0101 ETH on sells. No funds lost, but routers can pick the cheaper side.
Low, dynamic-fee pools accepted. Two specialists, merged. Initializing with fee 0x800000 succeeds and the pool sits at 0 LP fee forever because the hook never updates or overrides it. Reproduced: slot0 reports lpFee 0 and updateDynamicLPFee is unauthorized for anyone else.
Info, stale README. Line 38 says the repository contains no launch.json, but one is present and schema-valid.

Dropped: the tx.origin shared-relayer note is the trust assumption the brief itself states, not a defect. All static-analysis leads were false positives or benign: the Yul shift order is correct, the encodePacked hash has fixed-size trailing args, the "reentrancy" sites are guarded by the paying flag, and the unused unlock return is empty bytes.
Coverage: all 7 entry points answered, 5 hold, 2 carry findings, plus rows for the deployer constructor and the delta-conservation invariant.
