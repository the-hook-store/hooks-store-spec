# Launch 5 (test token) reviews, copied from https://explorer.imd.fun/jobs/a01dd7fe-7f49-4efa-a87d-bd32293d0bc2 on 2026-10-22

Implemented TEST and the immutable hook with IMD fees and claims, pool-specific pause controls, and the buyer allowlist window. Dependencies and deployment documentation are included.
Validation passed: forge build, all 66 tests, and forge fmt --check.
Full fork rehearsal could not run: Foundry’s RPC connection was refused. No transactions were broadcast.

---

Created launch.json with matching contract names, constructor placeholders, permissions, and pool settings.
forge build passed. forge test passed all 66 tests with the specified fuzz seed. Only launch.json changed.

---

I found one low-severity defect in the economics of src/TestHook.sol. Nothing reached medium or above. The findings and coverage are in .imd-findings.json (no source files changed), and the project's own suite passes (66 tests).
Finding (low): wallets not on the allowlist can still get TEST during the 15-minute window, and pay no hook fee doing it. The allowlist is only checked when someone swaps. Adding liquidity has no checks at all, because the hook has no liquidity callbacks. So a wallet that isn't allowed to buy can deposit IMD alone into a narrow price range just below the current price. That works like a buy order: when anyone sells TEST during the window, the price moves through the range and turns that IMD into TEST. The wallet then withdraws and keeps the TEST, without paying the 1% hook fee. Only the seller pays the fee.

Reproduction (TEST as currency0, IMD as currency1, price 1, factory seeds liquidity across ticks -120 to 120):

bob, who isn't allowlisted, tries a direct buy. It reverts with BuyerNotAllowed, as it should.
bob adds 1e22 of IMD-only liquidity across ticks -180 to -120.
alice sells 5e22 TEST.
bob removes his position and receives about 30.6 TEST while allowlistActive(poolId) is still true.


Verification: I ran this as a throwaway Foundry test against the real PoolManager, then deleted it.
Fix: either have beforeAddLiquidity block anyone except the factory while the window is open, or document this as an accepted limit of the allowlist. The brief already accepts that several wallets or a shared relayer can get round it.

What holds:

Fee size: the hook fee is 1% of the full IMD amount in all four swap types (buy and sell, exact input and exact output), in both token orders, computed with mulDiv and rounded down.
No double charge or TEST fee: the fee is never taken twice, and never in TEST.
Partial fills: a swap that names its IMD amount but is only partly filled reverts.
Fee claims: when the PoolManager can't pay the fee directly, the hook mints a claim. Every claim is backed, and claimFees pays only the fixed recipient, keeping any part it can't yet pay.
Pause and window: pausing blocks only swaps and doesn't restart or extend the window. The window starts on the first swap that actually trades.
Static-analysis leads: the tx.origin warnings describe the allowlist rule the brief asks for. The reentrancy warnings are covered by nonReentrant and the one-time claim flag.

Coverage: every listed entry point has a row in the file. beforeSwap is marked as the finding. The others hold, and I added two rows for the fee and claim-backing invariants.
Not covered: I didn't look at deployment or the manifest. The protected floor tests sit outside my area, and I didn't run them.

---

Added failure-path and fuzz tests for swap rollback, claim redemption after full LP withdrawal, and initialization safety in both token orders. Expanded hook invariants and added token balance/allowance invariants.
forge build passed. Seeded forge test: 79 passed, 0 failed, 0 skipped.
Only test/ changed. No implementation defects found; live-chain verification remains separate.

---

The review is complete. The findings file is written with an empty findings list and a 15-row coverage record, and the scratch tests are removed so the tree is unchanged.
Result: no substantiated defect in the Math Precision, Boundary or Numerical Gap area.
What I checked and how:

Fee formulas. For IMD-specified swaps the hook charges floor(|A|/100) on exact input and floor(A/99) on exact output. For TEST-specified swaps it charges floor(B/100) on sells and floor(B/99) on buys from the core delta. I proved algebraically that floor(B/99) equals floor((B + floor(B/99))/100), so every mode is exactly 1% of the gross IMD leg rounded down, as the README states. All four modes use mulDiv, and int256.min is handled without signed overflow.
Delta routing against v4-core. I traced the Pool swap loop and the step math to confirm a full fill always leaves the core specified delta equal to the hook-adjusted amount, so the equality check in afterSwap is exact and only partial fills revert. Hook deltas net to zero through take, mint or burn on every path.
Boundaries probed with scratch tests in both currency orders. Launch-realistic price from a 2,500 IMD cap with 100M TEST seeded one-sided, an IMD-specified sell against a pool holding no IMD, a TEST sell with no IMD liquidity, 1 wei and 99 wei legs, and the claim cap when the manager's IMD belongs to LPs. All behaved as specified.
Static-analysis leads. The tx.origin, timestamp and reentrancy lines are either required by the brief or benign, and the shared guard blocks claim reentry during fee payout. None reproduced as a defect.

Two observations that are by design rather than defects, recorded in the coverage rows: IMD legs under 100 wei pay no fee, and a TEST sell into a pool with no IMD moves the price to the limit at zero cost, which is inherent v4 behaviour that moves no value and does not start the allowlist window.

---

The review is complete and .imd-findings.json holds the result. No source file was changed.
Outcome: no permission, trust-gap or asymmetry defect found in TestHook or TestToken. The project's 66 tests pass on the pinned toolchain, and I traced each entry point against the Access Control, Trust Gap and Asymmetry guides plus the v4 security checklist.
What I verified in depth:

Access control. Every callback is onlyPoolManager. beforeInitialize additionally requires the factory as sender and binds once. The owner's only powers are pause, unpause and setAllowed, checked on msg.sender against an immutable owner. There is no ownership transfer, upgrade, approval, arbitrary call or settable recipient. unlockCallback is reachable only through the hook's own claimFees, and its authorization flag is consumed before any external interaction.
Fee accounting symmetry. Using the vendored Hooks.afterSwap and PoolManager.swap, I confirmed the specified-side fee returned in beforeSwap and the unspecified-side fee returned in afterSwap both land on the swapper, that take or mint inside afterSwap is cancelled by the manager's credit after return, and that all four swap modes charge 1% of the gross IMD leg to the same fixed recipient. Partial fills of IMD-specified swaps revert as the brief requires.
Trust gaps. Pause blocks swaps only. Liquidity removal and the factory's zero-change collect have no callbacks and always pass. claimFees is permissionless but can only pay the fixed recipient and is capped to the manager's IMD balance. Claims cannot be moved by anyone since the hook grants no operator approval.
Static-analysis leads. The tx.origin lines implement the brief's explicit wallet definition. The reentrancy lines are covered by the shared guard, which I traced in both directions.

One informational note is recorded: beforeInitialize pins fee 12500, tick spacing 60 and the IMD address. These match the policy tier and the example manifest, so the launch proceeds, but the manifest step should confirm those exact values since any other pool terms revert with InvalidPool.
Coverage has 15 rows: all 11 listed entry points answered, three invariants marked as holding, and one unreached row for live Robinhood Chain IMD token behaviour, which needs a fork rehearsal this review could not run.

---

Review complete. The findings file is valid, both snippets match the tree at their cited lines, and no tracked file was modified (only .imd-findings.json and the scratch test under test/scratch/).
Outcome
The hook's control flow in my area (Execution Trace, Periphery, First Principles) holds up. I traced every swap path against the vendored v4-core Hooks.beforeSwap/afterSwap and PoolManager.swap/take/mint/burn: the specified-IMD fee is returned once in beforeSwap and verified by a strict full-fill check in afterSwap, the unspecified-IMD fee is grossed up correctly from the core delta, the hook's delta nets to zero on both the direct-take and claim-mint paths, and claims are fully backed by the swapper's own settlement. The claim redemption path is correctly gated by a consumed authorization flag and cannot run inside another unlock. The vendored SafeCast.toInt128 and FullMath.mulDiv are checked. The slither/aderyn leads (tx.origin, reentrancy ordering) are either required by the brief or already guarded, and I did not promote them.
Findings reported

Low: any TEST holder can start the 15-minute allowlist clock by selling 1 wei, and the owner cannot pre-populate the allowlist until the pool is bound, so a non-allowlisted party can consume the head start before the owner acts. Proven with a scratch test at test/scratch/WindowStart.t.sol (both behaviours pass against current code). No fund loss, and the brief's literal wording permits it, so I rated it low with a minimal fix suggestion.
Info: beforeInitialize hard-codes tick spacing 60 and the IMD address, so the manifest must name exactly those or the launch reverts.

Coverage
All 11 listed entry points have rows (9 hold, 2 reference finding 1), plus five invariant/lead rows. Nothing was left unreached. The one area I could not exercise is a real-IMD fork rehearsal, which the README also notes was not run; everything else was checked against the vendored PoolManager.

---

I found one defect, rated low, and dropped the specialists' other three findings. The findings and coverage are in .imd-findings.json. The hook and token build cleanly, all 79 project tests pass, and both contracts are well under the size limits (hook runtime 7,918 bytes).
Finding 1 (low): the buyer allowlist doesn't cover range orders (src/TestHook.sol:193)

Problem: the allowlist is only checked in beforeSwap, and the hook has no liquidity callbacks. Anyone can add an IMD-only position just past the current price, which acts as a buy order. When someone sells TEST through it during the 15-minute window, the position's IMD turns into TEST, and the owner withdraws it. No allowlisted wallet or relayer is involved, and no 1% hook fee is charged, because it isn't a swap. The README and the manifest notes don't mention this.
Reproduction: I wrote my own Foundry test. Bob is not allowlisted, and his direct buy reverts. He adds liquidity in the range [-180, -120] with only IMD. Someone else sells 5e22 TEST. Bob withdraws and ends up with about 30.6 TEST (30606921186237476658 wei) while allowlistActive is still true. This is the same amount the economics specialist reported, so I merged their finding into this one. The test source is attached as the finding's proof.
Fix: add a beforeAddLiquidity check that applies before the first swap and during the window, and only allows the factory or an allowlisted tx.origin. Removals stay unrestricted, so the factory's fee collection and removing liquidity while paused still work. This changes the hook's address mask to 0x28cc and the permissions in launch.json. The alternative is to document the route as an accepted limit.

Dropped specialist findings

Fee 12500 and tick spacing 60 are hard-coded (two info notes): this is not a defect. It matches the policy tier and launch.json, so the launch can initialize.
A 1-wei sell can start the allowlist clock (low): this follows the brief, which starts the window at the pool's first swap, and a sell is a swap. The owner also can't fill the allowlist before initialization under any design, because the factory creates the hook and the pool in one transaction.

My own pass over the code

Fee math: correct for all four swap shapes in both currency orders. The fee is 1% of the IMD side via mulDiv. A partial fill where the swap names its IMD amount reverts. Otherwise the fee is on the amount actually traded.
Fee settlement: the fee is paid directly when the PoolManager holds enough IMD, and minted as a claim otherwise. claimFees redeems claims to the fixed recipient, and the hook's balances net to zero on every path.
Owner and constructor: the owner can only pause, unpause and edit the allowlist, all keyed by pool id. Constructor arguments and permissions in launch.json match the code.

All 11 entry points have a coverage row, plus two invariant rows. The tree is as I found it: the scratch test and Forge's out/ and cache/ are deleted.
