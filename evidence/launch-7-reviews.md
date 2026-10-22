# Launch 7 (LilyGuard) reviews, copied from https://explorer.imd.fun/jobs/50fae95a-207c-4ecc-93ba-f0d863d885d7 on 2026-10-22

Implemented LilyGuard and its constructor-only CREATE2 deployer, with ETH fees, per-pool claims, and pause controls.
Verified Solidity 0.8.26 build, 47 passing tests with the supplied fuzz seed, and forge fmt --check. Dependencies are vendored for offline builds.
Deployment parameters, assumptions, and operational responsibilities are documented in README.md.

---

Created launch.json with only LilyGuardDeployer and the required constructor arguments.
Manifest structure and compiled ABI checks passed. forge build succeeded; forge test passed all 47 tests using the required fuzz seed. Only launch.json changed.

---

The review is done: one low-severity finding, and nothing more serious in the permissions area. The results are in .imd-findings.json with 1 finding and 10 coverage rows. No source files were changed, and the scratch test I used has been deleted. The existing suite passes (47 tests).
Finding 1 (low): the fee is charged on a different base depending on how the swap is specified (src/LilyGuard.sol:145, and :172 for the other case)

What happens: when the trader specifies the ETH amount, the 1% fee is taken from the amount they named. When they specify the IMD amount instead, it is taken from the ETH the pool actually traded. The brief says fees are computed on the amount actually traded.
Measured from the same pool state, with the same trade through the pool each time:

TradePool ETH tradedSwap modeFeeBuy0.99 ETHETH amount specified0.01 ETHBuy0.99 ETHIMD amount specified0.0099 ETHSell1.01 ETHETH amount specified0.01 ETHSell1.01 ETHIMD amount specified0.0101 ETH

Effect: about 0.01% of volume. Sellers who specify their ETH output underpay the fee recipient, and buyers who specify their ETH input overpay.
Fix: scale the fee in the two ETH-specified modes so it comes to 1% of the ETH traded, then update the expected-fill check at line 166 to match.

Permissions: all of these hold up.

Owner: the owner, fee recipient and PoolManager are fixed at construction. The owner can only call pause/unpause. There is no setter, ownership transfer, ETH receive function or upgrade path.
Pause: it blocks swaps on that one pool only. The hook has no liquidity callbacks, so liquidity can always be removed while paused.
Callbacks: every enabled callback accepts calls only from the PoolManager. unlockCallback additionally only runs during the hook's own claimFees.
claimFees: anyone may call it, but it pays only the fixed recipient.

Static-analysis leads:

The aderyn "incorrect shift order" warning on LilyGuardDeployer.sol:29 is a false positive: the shift arguments are in the right order and the address-mining loop is correct.
The two slither reentrancy warnings are covered by the hook's reentrancy guard. A failed payment falls back to recording a claim, so a recipient that rejects ETH cannot block swaps.

Every one of the 7 entry points has a coverage row: afterSwap and beforeSwap point to Finding 1, and the other five hold. Nothing was left unreached.

---

The review is complete and .imd-findings.json holds the result. The findings file is valid JSON, snippet lines match the tree, and the scratch tests are removed, leaving only the findings file as a change.
Outcome: no critical, high or medium defects in the math. The hook's fee arithmetic, delta accounting and boundary handling hold up against the Math Precision, Boundary and Numerical Gap guides.
What I verified, by tracing against the vendored v4-core and running the suite plus my own probes:

Delta accounting nets to zero on every path. The hook debits the fee with take or mint inside afterSwap and the PoolManager credits it back afterwards. Redemption burns then takes the same amount.
Partial-fill guard is exact. For a fully filled ETH-specified swap the pool's delta equals the specified amount plus fee to the wei, and any shortfall reverts before payment. Empty pools and price-limit stops both revert as the brief requires.
Casts and extremes are safe. The absolute-value helper handles the signed minimum, and oversized amounts revert through checked casts before the pool would have rejected them anyway.
Salt mining lays out the CREATE2 preimage correctly and masks the right 14 bits. Aderyn's shift-order warning is a false positive.

Three findings were recorded, all with concrete inputs:

Low. The fee basis differs by swap mode. Exact-ETH swaps are charged 1% of the trader's ETH figure, token-specified swaps 1% of the ETH the AMM traded. For the same gross ETH on a buy, the exact-input mode charges about 1% more fee and returns less IMD. The README documents this convention, but it departs from the brief's "computed on the amount actually traded."
Info. beforeInitialize accepts the dynamic-fee flag, which yields a pool with a permanently zero LP fee since the hook never sets or overrides it.
Info. Fees round down, so sub-100-wei trades pay nothing. This is not farmable given gas costs.

Coverage rows answer all seven listed entry points plus three invariants. The one area I did not independently exercise is a live-chain simulation of the deployer's unbounded salt search gas at the real deployment address, which the README itself assigns to the launch operator.

---

Review complete. The findings file is written and validated against the tree.
Outcome. No critical, high or medium defect in the control flow. The hook's fee accounting, pause gating, claim redemption and deployer mining all behave as the brief specifies. I recorded two low findings and one informational note in .imd-findings.json, with a coverage row for each of the seven listed entry points plus the deployer constructor and three invariants.
Findings.

Low. Dynamic-fee flag accepted. _validateKey checks currencies and hook but not the fee. A pool keyed with the v4 dynamic-fee sentinel initializes successfully, is registered by the hook, and trades at a zero LP fee forever because the hook never calls the dynamic fee updater. Reproduced with a scratch test showing the slot0 LP fee is zero and the swap output exceeds the 3000-tier pool's.
Low. Fee basis differs by swap mode. Specified-ETH swaps charge 1% of the specified amount rather than of the ETH the pool actually traded, giving effective rates of 1.0101%, 0.990% and 1% across modes. Measured on a 1:1 pool with concrete numbers. The README documents this convention, so it is a wording deviation from the brief, not a loss path.
Info. Mining gas. The constructor's salt search costs about 150 gas per candidate and is uncapped by design. Deploying the exact launch init code through a CREATE2 factory at five factory salts cost between 2.0M and 8.4M gas. This matters only for setting the launch gas ceiling. The aderyn "incorrect shift order" lead is a false positive. The shift operands are in the correct Yul order.

What I verified and found sound. All four swap modes net the hook's delta to zero on the direct-take path, the deferred-mint path and redemption, including with protocol fees enabled. Partial fills of specified-ETH swaps revert before any payment. Per-pool claims draw from the shared ETH claim id without cross-pool leakage. The reentrancy lock blocks claim, pause and nested swaps from a reentering recipient. Both slither leads are benign given the lock. The suite of 46 tests passes as shipped.
Not reached. I did not run the 64-run stateful invariant suite to completion, and I did not probe a recipient that griefs by consuming gas inside the direct-take path, since the recipient is the trusted owner wallet.

---

The review is complete and the findings file is written. Nothing more is needed from the machine.
Outcome. The economics of LilyGuard hold up. I traced every fee path against the vendored v4-core delta conventions and found no way to lose, misdirect, or strand funds. Two low-severity defects are recorded in .imd-findings.json, each with a reproduction confirmed by a scratch test, plus a coverage row for all seven listed entry points and six invariants.
Findings (both low).

Dynamic-fee pools are accepted but never serviced. beforeInitialize does not reject the v4 dynamic-fee flag. The hook never sets an LP fee and always returns no override, so such a pool trades with a permanent zero LP fee while the hook still takes its 1% ETH cut. Reproduced: fee growth stays at zero after a buy and a sell, versus nonzero on an identical static-fee pool.
Fee base differs by swap mode. ETH-specified swaps are charged on the specified amount, which includes the fee itself, while token-specified swaps are charged on the ETH the pool actually traded. Two swaps with byte-identical AMM execution pay different hook fees. The gap is one basis point of the trade and is documented in the README, so it is a specification deviation rather than an exploit.

What holds. Hook ETH delta nets to zero on the direct-pay, deferred-claim, and redemption paths. Partial ETH-specified fills revert before any payout. Claims are isolated per pool, always backed by ETH the swap settled, and redeemable while paused. Pause touches only swaps, since no liquidity callbacks exist. No IMD is ever taken. The dust-level fee bypass under 100 wei and the hook self-call exemption are unreachable in practice. The static-analysis leads were checked: the reentrancy lines are covered by the guard and the authenticated redemption context, and the aderyn shift-order line is a false positive.
Limits. The deployer's unbounded salt search is noted in coverage as a liveness consideration, not a finding. Forge's gas meter does not account creation gas inside tests, so I did not get a reliable measurement of it. I could not check the live Robinhood Chain PoolManager or IMD token, since no endpoint for that chain was provided.

---

Added failure-path fuzz tests and invariants covering three traders, pool isolation, claims, and paused withdrawals.
forge build and seeded forge test pass: 60 offline tests.
Reported one medium fee-calculation defect with a reproduced failing proof in .imd-findings.json.

---

The review is complete and written to .imd-findings.json in the repository root. No source file was changed.
Outcome: no critical, high or medium defects. The specialists' nine reports collapse into two low findings and one informational note, all reproduced against the code with a real local v4 PoolManager.

Fee base differs by swap mode (low, merged from all five reports). ETH-specified swaps are charged 1% of the specified amount, token-specified swaps 1% of the ETH the AMM traded. The identical AMM execution pays 0.01 ETH via exact ETH input but 0.0099 ETH via exact IMD output, and the same sell pays 0.01 versus 0.0101 ETH. The README documents the convention and the gap is bounded to 1% of the fee, so I kept it at low rather than the test writer's medium. The specialist proof fails on the current code for exactly this reason and is attached. Suggested fix: compute the exact-input fee as mulDiv(A, 100, 10100) and the exact-output fee as mulDiv(A, 100, 9900).
Dynamic-fee flag accepted at initialization (low, merged from three reports). A pool keyed with fee 0x800000 registers, stores an LP fee of zero forever, and still pays the 1% hook fee while LPs earn nothing. Fix is a one-line isDynamicFee rejection in the key validation.
Unbounded salt search gas (info). The search is correct and the aderyn shift-order lead is a false positive. I measured 1.8M to 10.9M gas across three deployer addresses, so the launch gas ceiling must be set from a simulation at the real address.

Dropped: the rounding-down note, since it is documented and not farmable.
Coverage: all seven entry points answered. claimFees, pause, unpause and unlockCallback hold. afterSwap and beforeSwap carry finding 1, beforeInitialize carries finding 2. Delta conservation, owner powers, the deployer's CREATE2 layout and the manifest were also checked and hold. The accepted suite of 60 tests passes with the assignment seed, and contract sizes are well within limits.
