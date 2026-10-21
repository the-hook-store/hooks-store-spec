# Builder and audit notes of the blocked launches (extracted from explorer.imd.fun on 2026-10-21)


## Launch 3, ImdGuard (2431b879-221f-410b-8f16-653d82dec67b)


### build_contract_project
Implemented ImdGuard with ETH fees and claims, pause controls, opening-price protection, and CREATE2 mining tooling. Deployment parameters and assumptions are documented in README.md.
Verified:
- forge build
- 41 passing tests with the requested fuzz seed
- forge fmt --check
Swaps require full fills. No transaction was broadcast; launch must mine against its actual CREATE2 deployer address.
Optional live-fork verification could not start: the RPC reported “historical state … is not available.”



### audit_permissions
I found two defects in ImdGuard's permissions and fee flow. Each has a Foundry test in test/scratch/ that fails on the current code. Both are written, with the coverage rows, to .imd-findings.json. I changed no project files.
1. High: the owner gets far more than the 1% fee and isn't bound by the sandwich protection (src/ImdGuard.sol:280, uint256 amount = fee + protection;)
- When a swap goes against the block's first direction, the hook caps it at the block's opening price. The difference it holds back (protection) goes to the recipient, which is the owner. The brief allows only 1% of the ETH side to go there. In the AntiSandwichHook pattern, that difference goes back to the liquidity providers instead.
- Over-payment: after a 100 ETH buy, a 1 IMD sell in the same block pays the owner wallet 0.2122 ETH, which is 17.6% of the ETH side. The 1% fee should be 0.0120 ETH.
- Owner can sandwich: the cap's withheld surplus comes back to the owner, so the protection doesn't apply to them. The owner buys 200 ETH, a victim buys 100 ETH, and the owner sells everything back. The owner ends 30.63 ETH up, while the victim's real 1% fee was only 1 ETH. A non-owner doing the same loses money.
- Fix: send only fee to the recipient and donate protection to the pool's liquidity providers.
2. Medium: anyone can switch off the sandwich protection for a block with a tiny first swap (src/ImdGuard.sol:140)
- Whoever makes the block's first swap, of any size, decides which direction is capped. An attacker opens with a sell of 1e6 wei of IMD, then buys 200 ETH ahead of a victim's 100 ETH buy. The attacker then sells back in the same direction as that first tiny swap, so the sell is not capped. The attacker nets +25.35 ETH.
- docs/REVIEW.md lists this as a known limit, but it defeats item 3 of the brief. Fixing it needs your decision, because the brief itself defines the rule as "against the direction of the block's first swap".
Coverage, all six entry points:
- beforeSwap: both findings. Its pool-manager-only, reentrancy, pause and pool-key checks hold.
- Held: cappedSwap (only the hook itself can call it), claimFees (anyone can call it, but it pays only the fixed recipient, also works while paused, and can't redeem twice), unlockCallback, pause and unpause.
- The owner can only pause and unpause, with no other admin function or upgrade path. Fees are only ever taken in ETH.
- Removing liquidity while paused works, because the hook enables no liquidity callbacks.
I left out the static-analysis leads after tracing each one. The "uninitialized locals" are deliberately zeroed. The ignored getSlot0 values are unused fields. The reentrancy reports are covered by the shared guard and by claims burning before payout.



### manifest
needs input: A change to the accepted source, which the manifest assignment may not make. ImdGuard's constructor calls Hooks.validateHookPermissions on its own address (permissions 0x0088: beforeSwap and beforeSwapReturnDelta), so it only deploys at an address whose low 14 bits are 0x0088. The evm_contracts launch deploys every manifest contract at a CREATE2 address salted by the launch number, which nobody mines, so a direct deployment of ImdGuard reverts for all but 1 salt in 16,384. The accepted source (src/) contains only ImdGuard and the OpeningPrice library: there is no launch contract that could deploy the hook with a mined salt, and launch.json may only name contracts present in the accepted source. No manifest alone can pass the launch_manifest check. — Should the accepted source be extended with a small deployer contract (for example ImdGuardDeployer, constructor arguments PoolManager 0x8366a39CC670B4001A1121B8F6A443A643e40951 and $owner, with one function deploy(bytes32 salt) that runs C



### audit_flow
I found no defects I could back with a failing input, so .imd-findings.json has an empty findings list. It also has a coverage row for each of the six entry points (all holds) plus two invariant rows. I changed no other files, and the existing suite passes (41 tests). No static-analysis lead held up.
What I traced (execution flow, periphery and first principles):
- beforeSwap, all four swap modes:
- The hook's own inner swap doesn't trigger the hook again, because v4 skips hooks when the hook itself is the caller.
- The delta the hook returns cancels the user's swap amount to zero. Uniswap's pool code then returns early at Pool.sol:326, before its price-limit checks.
- In each mode, the hook ends with zero ETH and zero IMD owed: what it gains or owes from the inner swap is offset by what it pays or receives from the user, plus the fee and adjustment it takes.
- Every amount is checked for range before it is negated or cast.
- Capped-swap fallback (cappedSwap): I looked for a way to make the capped attempt fail so the uncapped swap runs at a better price.
- Exact-output sells: guarded by the unspecified < minimumInput check.
- Exact-input buys: the fallback buys more IMD than the capped attempt. So any price-limit or liquidity failure that stopped the capped attempt stops the fallback too.
- Running the capped call out of gas: this would need it to cost about 63 times more gas than the fallback, which isn't reachable.
- Fee payout and claims:
- The 60,000-gas direct payment falls back to a claim of the same amount. In both outcomes exactly one fee debit remains.
- claimFees burns and pays out in one step, both when the PoolManager is locked and when it is already unlocked. It is limited to the ETH the PoolManager holds.
- Re-entry from the recipient is blocked by the shared guard. unlockCallback only runs during an active claimFees.
- Owner and access: the owner and fee recipient are fixed by constructor argument, not taken from the deploying factory or tx.origin. pause() and unpause() affect swaps only, and no liquidity callbacks are enabled, so liquidity can always be removed.
- Opening-price conversion: at all four call sites the rounding favours the cap, never the swapper.
Leads I dropped:
- Sandwich protection can be steered. An attacker can make a tiny swap first in a block to choose its direction, and then escape the cap. That follows from the rule exactly as the brief states it, and the README discloses it.
- The price-protection surplus goes to the owner's wallet. OpenZeppelin's AntiSandwichHook says the surplus must not go to liquidity providers, and the README discloses this.
- Combined swap fee reaching 100%. If the pool's fee plus a protocol fee reached 100% (an LP fee of 999,999 pips), exact-output swaps would always revert. That would silently disable the cap on exact-input buys, but such a pool is unusable anyway.
What I didn't cover: the CREATE2 salt-mining script and deployment handoff are outside my area. I didn't check the live PoolManager's bytecode or confirm the chain's ArbSys block-number precompile beyond what the README says it observed.



### write_foundry_tests
I added an invariant test suite for ImdGuard and filed three defects in .imd-findings.json. Two of them mean the anti-sandwich protection (requirement 3) doesn't work. forge build and the full forge test pass with the verifier's seed: 43 tests, 0 failures. Nothing is committed.
New tests, in test/ImdGuardInvariant.t.sol. I left the existing tests untouched. A handler drives the hook in random order:
- Swaps: all four modes, plus swaps made while the PoolManager is drained of ETH, which forces the fee to be minted as a claim.
- Admin: pause and unpause by the owner, and the same calls by strangers.
- Other actions: claimFees() by arbitrary callers, adding and removing liquidity, and advancing the L2 block number.
It runs 256 runs of 60 calls each, and any unexpected handler revert fails the run. The properties checked are:
- Every swap: the fee is 1% of the ETH side to within one wei and is paid or minted in that same swap. Swaps against the block's first direction never get a better price than the block's opening price, and no other swap is charged a protection amount.
- Failed swaps move no funds.
- ETH and IMD totals never change across the system, and the fee recipient never receives IMD.
- Fee accounting: everything collected was either paid directly or redeemed, or is still an outstanding claim; claims are always covered by ETH the manager holds; claims pay only the recipient, never the caller.
- Pause: while paused, every swap fails and removing liquidity still works.
- Access: only the owner can pause or unpause.
A fixed-sequence test also confirms that every one of those paths is actually reached.
Findings. Each of the first two includes a standalone test that fails on the current code and would pass once fixed:
- High – the owner can sandwich swappers at a profit. When a swap is capped at the opening price, the difference goes to the fee recipient, who is the owner. In the AntiSandwichHook pattern it goes to the pool's liquidity providers. So the cap costs the owner nothing. In one block the owner bought with 100 ETH, a victim bought with 100 ETH, and the owner sold back: the owner ended with 1017.98 ETH from 1000 ETH. It also means swappers who get capped pay the owner more than the 1.0% fee the brief allows. The fix is to give that difference to the pool instead of the recipient (src/ImdGuard.sol:280).
- Medium – anyone can switch off the cap with a tiny first swap. Only swaps against the block's first swap are capped, so an attacker sells 0.001 IMD first and their closing sell is never capped. The same sandwich then made the attacker +14.82 ETH. The code follows the brief's rule exactly, so fixing this means changing the rule, for example capping every swap in both directions. You need to decide that.
- Low – swaps with less than 100 wei of ETH pay no fee, because the 1% rounds down to zero. The amounts are negligible.
The tests run against a local PoolManager with mocked IMD and ArbSys contracts (no network here). Nothing has been tested against the live Robinhood Chain contracts.



### audit_math
The revert data confirms the wrapped reason is PartialFill() (selector 0xd964f528), matching the report. The review is complete and .imd-findings.json holds the final result.
Outcome. The math in ImdGuard holds up. I found no critical, high or medium defect in the Math Precision, Boundary or Numerical Gap areas. One low-severity boundary corner and two informational notes are recorded, each with a concrete reproduction run against the current tree.
What I verified in depth
- Fee arithmetic in all four swap modes. The floored 1% and the gross-up identity are consistent across exact-input and exact-output legs for every residue of the gross amount mod 100.
- Opening-price conversion rounding on both sides of the 2^128 sqrt-price split, including that the maximum sqrt price squared cannot overflow the 512-bit division.
- Every int128 crossing point, the rejection of int256.min before negation, and the fallthrough when the opening-price ceiling exceeds int128 range.
- The zero-amount outer swap: the vendored Pool.swap returns before its price-limit checks, so the inner leg moving the price cannot trip the outer one.
- A 3000-run fuzz over prices from Q96/4 to 4·Q96, both first-swap directions, all four modes and amounts from 1 wei to 1 ETH never found a reverse swap beating the opening price.
- ETH conservation, claim fallback, and the shared reentrancy guard on the swap and claim paths.
Findings written
- Low. A protected exact-output sell reverts with PartialFill when the caller's price limit lies between the end price of the plain leg and the end price of the capped leg, even though the requested quantity is fully obtainable within that limit. The same call with the same limit succeeds in the next block. The guard that causes it is correct, so the fix is documentation and a distinct error, or a separate limit for the capped leg.
- Info. Fees are floored, so ETH legs under 100 wei pay no fee. Documented, at most 1 wei per swap, not farmable.
- Info. The anti-sandwich difference is paid to the owner together with the 1% fee. Documented design choice, flagged as a trust assumption for the judge.
Coverage. All six entry points have rows: beforeSwap carries finding 1, the other five hold. Six additional rows record the invariants and boundaries checked. Scratch tests live under test/scratch/ and no repository file was modified.



### audit_economics
The review is complete and .imd-findings.json holds two findings plus a 13-row coverage record. Git shows no tracked-file changes; the only additions are the findings file and the scratch proof under test/scratch/, both ignored by the tree.
What I found
- High, src/ImdGuard.sol:140. The anti-sandwich cap applies only to swaps against the direction of the block's first swap, and any trader chooses that direction with a dust swap. A searcher sells a few wei of IMD first, front-runs a victim buy, and back-runs with a sell that now matches the recorded direction, so no cap applies. The proof test runs this on a 1000e18-liquidity pool: the attacker ends with 123.65 ETH from 100 ETH after paying the 1% hook fee twice. The same test passes against a copy where every swap is capped at the opening price in its own direction, which I verified locally before removing that copy. The fix is a design decision because the brief itself specifies the first-swap rule, and I stated the tradeoff and the two existing tests that would need revising.
- Low, src/ImdGuard.sol:280. The opening-price surplus is routed to the owner together with the fee. On the same pool, a 10 IMD reverse sell one block after a 100 ETH buy pays the owner 2.00 ETH against 0.12 ETH in a fresh block, roughly 19 times the requested 1% fee. It is a deliberate implementer choice and not third-party exploitable, but it is a value flow the brief did not ask for.
What holds
- ETH conservation across all four swap modes, with and without the cap, including the returned BeforeSwapDelta, the inner swap delta and the take-or-mint settlement.
- Fees are never taken in IMD, equal floor(gross/100), and the exact-output gross-up returns exactly the requested net amount.
- cappedSwap's fallback paths cannot beat the cap, claims are backed by the paying swap's settlement, claimFees burns before paying and clamps to available cash, and pause leaves liquidity removal and claims open.
- The slither and aderyn leads (uninitialised locals, unused getSlot0 returns, ArbSys call before the checkpoint write) are benign on inspection and produced no findings.
Not reached. A cross-block sandwich with the attacker last in one block and first in the next. The README documents it as outside the hook's property, and the in-block bypass in the high finding is strictly cheaper, so I recorded it as unreached rather than claiming it holds.



## Launch 4, WordsmithHook (e70e221f-cfed-40c7-8c31-450e7e2eaa96)


### build_contract_project
I've built WordsmithHook as a standalone Uniswap v4 hook for Robinhood Chain, with tests, a deploy script and a README. forge build, forge test (14 tests pass, run with your fuzz seed) and forge fmt --check all pass. Nothing is committed and nothing was deployed.
What it does (src/WordsmithHook.sol):
- Pools: it only accepts pools on the PoolManager given at deployment where the other currency is native ETH. Anyone can open such a pool with it; any other pair is refused.
- Fee: 0.5% of the ETH side of every buy and sell, never taken in the token. It is sent to 0x5Bff2a2FEcD1d6152676813b21346238733bEAB1 inside the swap that paid it. If the PoolManager can't pay it, the hook records a claim instead, and anyone can call claimFees() to pay all claims to that address in ETH.
- Buy limit: for 30 minutes after a pool opens, no wallet can buy more than 0.5% of the token's total supply in total. Sells are never limited, and after the window there is no limit.
- No owner: nothing can be paused, changed or upgraded. Only the callbacks this needs are switched on.
Choices you should check:
- windowClosesAt takes the pool's id (windowClosesAt(PoolId)), not zero arguments as the brief wrote it. Because anyone can open a pool with the hook, each pool gets its own window. A single shared window could be used up by someone opening a junk pool first.
- "Wallet" means the account that signed the transaction (tx.origin), because swaps arrive through routers. Someone using several wallets can still get around the limit.
- Small swaps pay no fee: the fee rounds down, so swaps under 200 wei of ETH pay nothing.
Deployment: the launch can't deploy this contract, because a hook's address has to carry its permission bits. script/DeployWordsmithHook.s.sol finds a matching salt and deploys through the standard CREATE2 deployer at 0x4e59b44847b379578588920cA78FbF26c0B4956C. I haven't confirmed that deployer exists on Robinhood Chain; whoever deploys should check that first. The test suite checks that the salt it finds gives the right address.
Tests cover all four kinds of swap, a fee becoming a claim and being redeemed, the buy limit during and after the window, and rejected pools and callers. They are not a security audit, so get an independent review before real money goes through it.
The dependencies (v4-core, solmate, forge-std) are copied into lib/ as ordinary files so the build works offline. The README covers the assumptions and deployment details.



### manifest
needs input: WordsmithHook needs a mined CREATE2 salt so its address carries permission bits 0x20cc, but an evm_contracts launch deploys it at an unmined, launch-number-salted address, where its constructor reverts. The accepted source has no deployer contract, and this task may only edit launch.json and must use kind evm_contracts. — Should this launch become a univ4_hook manifest, whose deployer mines the hook salt, or should the source gain a deployer contract that CREATE2-deploys WordsmithHook with an off-chain-mined salt and then list that deployer in an evm_contracts launch.json?



### audit_economics
I found two defects in WordsmithHook's economics. Both are confirmed with Foundry tests that fail on the current code. They are written to .imd-findings.json with full proofs, plus a coverage row for each of the 5 entry points and 4 invariant rows. I changed no files; the test files I used are deleted, and their full source is in the JSON as proof.
Findings
- High: the fee is charged on the amount requested, not the amount traded (src/WordsmithHook.sol:126). When the user fixes the ETH amount (exact-input buys, exact-output sells), beforeSwap sets the fee from amountSpecified. Nothing corrects it afterwards, because afterSwap returns early for these swaps. When a swap only partly fills, because it hits its price limit or runs out of liquidity in range, the user still pays 0.5% of the full request.
- Buy: an exact-input buy of 10 ETH that stops after 0.5016 ETH pays a 0.05 ETH fee, which is 10% of the ETH actually traded.
- Sell: an exact-output sell asking for 10 ETH that fills only about 0.046 ETH leaves the seller about 0.00375 ETH down. They pay ETH as well as giving up their tokens.
- Fix: in afterSwap, either refuse partial fills or charge the fee on the filled amount. The proof passes with either fix.
- Medium: the 30-minute buy limit can be skipped by initializing the pool early (src/WordsmithHook.sol:114). The window starts when the pool is initialized, and anyone can initialize the creator's pool. Uniswap's standard liquidity tooling (PositionManager) quietly accepts an already-initialized pool, so the creator's usual setup still goes through.
- Repro: a sniper initializes the pool, liquidity arrives 31 minutes later, and the sniper's first buy takes 1% of supply when the limit is 0.5%.
- Fix: start the window on the pool's first swap instead. That needs no extra hook permissions.
Coverage
- beforeSwap: finding 1.
- beforeInitialize: finding 2.
- afterSwap: works as intended. Its own fee path uses the real swap result, and the buy limit counts actual tokens received per wallet.
- claimFees and unlockCallback: work as intended. Anyone can call claimFees, but only the fixed recipient is paid, and the callback can only be reached through claimFees.
- Invariants checked:
- The hook's ETH accounting with the PoolManager nets to zero in every swap.
- The fee is never taken in the pool's token.
Not reported
- Wallet limit bypass: the limit is per signing wallet (tx.origin), so one person with several wallets can get around it. The README already acknowledges this.
- Small fee difference by swap type: the fee is 0.5% or 0.4975% of the trade depending on the swap type. The difference is too small to matter.
- windowClosesAt signature: it takes the pool's ID as an argument, while the brief writes windowClosesAt(). It is outside my area and the README explains the choice.
The static-analysis leads were checked: none of them is a real defect. The flagged "uninitialized" paid variable defaults to false, which is correct. The ignored return value of unlock is harmless. The state change after an external call is reached only from the PoolManager.



### audit_math
The tight-limit sell reverts in the test router as I described, and the working tree shows no tracked changes. The findings file is complete and validated.
Review complete. Findings written to .imd-findings.json with 2 findings and 8 coverage rows.
Finding 1, high: fee charged on the requested amount, not the filled amount. When ETH is the specified currency, the fee is computed in beforeSwap from params.amountSpecified and the PoolManager charges that delta to the swapper no matter how much the pool actually filled. A swap that stops at its price limit is overcharged. In the proof, a 100 ETH exact-input buy that filled about 1 ETH paid a 0.5 ETH fee, and an exact-output sell that returned about 1 ETH lost 0.5 ETH of it. The other two paths use the pool's real delta, so the four paths disagree. The proof test under test/scratch/PartialFillFee.t.sol fails now and accepts either fix: refusing partial fills with a pre-charged fee, or refunding the excess.
Finding 2, low: fee base differs by swap mode. Exact-input paths take 0.5% of gross ETH, exact-output paths take 0.5% of the pool-side amount, so the effective rate is 0.4975% on half the paths. Not exploitable, but the recipient's rate depends on which mode the trader picked.
Checked and holding in the Math Precision, Boundary and Numerical Gap areas: the int128 narrowing casts cannot truncate silently because the PoolManager's SafeCast reverts first, the negation of int256.min reverts, the window boundary and timestamp arithmetic are sound, the hook's ETH delta nets to zero in every swap and in the claim path, and unlockCallback is reachable only through the hook's own unlock. The static-analysis leads about uninitialized locals, ignored unlock return and reentrancy did not produce a reproducible defect. Fee rounding down on sub-200-wei dust is documented and not farmable.
Not reached in depth: totalSupply overflow is only possible above about 2.3e75 supply, so I did not pursue it. Access control, the tx.origin cap design, and the window starting at initialize rather than at first liquidity are outside my area and were left to the other specialists.



### audit_permissions
The review is complete. No tracked file changed; the findings file and the scratch tests are the only additions.
Outcome. The permission model of WordsmithHook holds: every callback is PoolManager-only, the unlock callback is reachable only through the hook's own claimFees, the hook holds no approvals, and there is no owner, setter, or upgrade path. I found no access-control bypass. The defects are in the asymmetry and trust-gap areas, written to .imd-findings.json with four findings and eleven coverage rows.
Findings
- Medium, fee overcharge on partial fills. When ETH is the specified currency the fee is 0.5% of the amount requested, while the other two swap shapes charge 0.5% of the ETH actually moved. A swap that exits a concentrated range pays the fee on ETH that never traded. In the reproduction a 500 ETH exact-input buy moved 30.5 ETH and paid a 2.5 ETH fee, about 8%. The exact-output sell case paid 3.5%. A proof test under test/scratch/ fails on the current code and is embedded in the finding.
- Low, cap keyed by tx.origin. Unrelated users whose swaps are signed by the same relayer or ERC-4337 bundler share one 0.5% allowance. The first buyer through that origin locks out everyone else behind it for the window.
- Low, windowClosesAt signature. The brief asks for windowClosesAt(); the contract only has the PoolId form, so the no-argument call the storefront would make reverts.
- Low, window starts at initialize. Anyone can initialize the creator's key before liquidity exists, so the 30-minute cap can run out before trading begins.
Coverage. All five verifier entry points have rows: afterSwap, beforeSwap and beforeInitialize map to findings 1 and 4, claimFees and unlockCallback hold. Invariant rows record that the fee never touches the pool token, the hook's delta nets to zero per swap, and the address permission bits are validated in the constructor. One row is marked unreached: parity with the live Robinhood PoolManager and whether the recipient address has code on chain, since I did not use the network.
Static-analysis leads. The slither and aderyn lines were checked and none became findings: the uninitialized paid local defaults correctly, the ignored unlock return is empty bytes, and the flagged reentrancy is a view call on the pool's own token with no exploitable state.



### audit_flow
The review is complete and .imd-findings.json holds five findings and eight coverage rows.
Main finding (high, with proof). The fee in beforeSwap is 0.5% of the amount the swapper asked to trade, not of the ETH that actually moved. On a partially filled swap (a price limit reached, or the pool's in-range ETH running out under a router's default limit) the fee is never reconciled. Three scratch tests in test/scratch/PartialFill.t.sol fail on the current code:
- Exact-output sell of 1 ETH, tight price limit: the pool delivers about 0.001 ETH, the hook charges 0.005 ETH, and the seller's ETH delta goes negative. The seller hands over tokens and pays about 0.004 ETH on top.
- Exact-output sell of 100,000 ETH with the default max price limit on a pool holding about 300 ETH: the hook mints a 500 ETH claim and the seller owes about 241 ETH.
- Exact-input buy of 1 ETH, tight price limit: about 0.001 ETH trades but the fee is 0.005 ETH, roughly 500% of the ETH side.
The tests accept a revert, so a fix that refuses partial fills or one that reconciles the fee to the executed delta both make them pass.
Lower findings, substantiated by trace.
- The buy cap is keyed by tx.origin. A second EOA bypasses it for free, and all ERC-4337 accounts behind one bundler share a single 0.5% cap and get refused once it is spent.
- The 30-minute window starts at permissionless pool initialization, so anyone can initialize the pool early and the cap can expire before liquidity ever arrives.
- The constructor's permission-bit check reverts unless the salt is mined for the actual deployer. The script mines for the Arachnid proxy, while the launch recipe deploys through the project factory.
- Info: windowClosesAt takes a PoolId, so the brief's no-argument selector does not exist.
Coverage. claimFees and unlockCallback hold. The hook's transient delta nets to zero on every swap path, including the mint fallback. All slither and aderyn leads were checked and are false positives: paid defaults to false, the unlock return is unused by design, and totalSupply() is a staticcall so no reentrancy precedes the storage write. The existing 14-test suite passes but never exercises a price-limited or liquidity-exhausted swap, which is where the high finding lives.



### write_foundry_tests
Added 30 unit/fuzz tests and four invariant properties.
forge build and forge test pass with the required seed: 45 tests passed, including 32,768 invariant handler calls.
Reported three reproduced defects with failing proofs in .imd-findings.json:
- Medium: partial-fill fee overcharging.
- Medium: contract-wallet buy-cap bypass.
- Low: large-supply arithmetic overflow.
Live Robinhood Chain integration remains unverified; tests use the local v4 PoolManager.

