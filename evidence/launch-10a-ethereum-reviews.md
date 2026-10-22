# Ad contracts launch (Ethereum) reviews, copied from https://explorer.imd.fun/jobs/a9818b4d-a1fe-4ef7-bab0-82509f56b0ac on 2026-10-22

Implemented both contracts. The registry remains byte-identical to the pinned source; V2 adds 24-hour placements, nonrefundable boosts, ranking totals, and tested escrow conservation.
Passed forge build, all 65 tests with the supplied fuzz seed, and forge fmt --check.
Deployment parameters, owner setup, and ABI changes are documented in README.md.

---

I found no defects I could back up with a failing input, so .imd-findings.json has an empty findings list. Its coverage record has a row for all 18 entry points, each marked holds, plus rows for the balance invariant and the source diff. No repository files were changed.
What I checked:

Changes against the starting source. I fetched the original contracts at commit 46e17ea. HookListingRegistry, StoreAdmin and ExactStoreToken are byte-identical. FeaturedPlacementsV2 differs only in what was asked for:

DURATION is 24 hours.
It adds totalBoost, boost and rankOf.
featured also returns each placement's total.
The cancel and settle events now carry the #ad label.


Following the money. boost moves the caller's deposited balance into escrow. cancel refunds the base price to the payer pro rata exactly as before, and sends the earned base plus the whole boost to the recipient fixed at purchase. settle sends price plus boost to that recipient and can't run twice. Every path moves equal amounts between buckets, so the balance rule (available + escrowed + proceeds) always holds. Boosts are refused after a placement closes or expires.
Access. Owner functions are owner-only with an explicit owner argument. There is no admin sweep. Changing the proceeds recipient affects only future purchases, and existing placements, boosts included, keep theirs.
Static-analysis leads. None held up:

The reentrancy leads are blocked by the reentrancy guard.
The external call in purchase only reads from the fixed registry address.
The flagged "strict equality" is a status check, not a balance check.
The registry's loops are capped at 16 labels of 32 bytes.


The IMD token. Read on Ethereum mainnet, 0xd34a99bc…63b7 reports 18 decimals and symbol IMD, and has no proxy. That fits configureToken's checks and the exact-transfer checks.
Tests. forge test passes all 65 tests, including the boost tests and the invariant tests with boosts.

One behaviour I left out as a finding because the specified boost(uint256,uint256) signature doesn't allow for it: a boost has no deadline. A boost waiting in the mempool could land a few seconds before the placement expires and still be kept in full.
A clean review doesn't prove the contracts are free of defects.

---

Created launch.json with both contracts in dependency order and the required $owner argument.
Manifest checks and compiled ABI comparison passed. forge build succeeded; all 65 tests passed with the supplied fuzz seed. Only launch.json is changed for submission.

---

The findings file is in place at the repository root (excluded from git by the harness's own exclude rule, as expected), it parses, and both snippets match the tree line for line. No other file was created or changed.
Scope
Files read: src/store/FeaturedPlacementsV2.sol, ExactStoreToken.sol, StoreAdmin.sol, HookListingRegistry.sol, all eight test suites and both helpers, the README and verification notes, the Pashov Mindset plus the Economic Security, Invariant and Flow Gap guides, and the protected deployment floor. The existing suite runs green at 65 tests including two stateful invariant suites of 128 runs by 128 calls.
Severity counts: 0 Critical · 0 High · 0 Medium · 0 Low · 2 Info
Result: no defect found in the economic area. The two info entries are design consequences the brief itself mandates, recorded so the judge and operator see them, not fixes the author must make.

Boost forfeiture with no expectation guard. A third party's boost can be back-run by the payer's cancel in the same block, sending the whole boost to the proceeds recipient for zero delivered exposure. The brief requires exactly this ("never refunded"), and the existing immediate-cancel test reproduces it. Conservation holds throughout.
Stray IMD sent directly to the escrow is unrecoverable. Nothing can sweep it, including the owner. The original design states there is no sweep, and the existing direct-transfer test reproduces it.

What I verified and concluded holds:

Conservation. Every writer of the three totals was traced. Deposit and withdraw move only available balance behind exact delta checks. Purchase and boost move available into escrow one for one. Cancel removes exactly base plus boost from escrow and splits it into refund and earned. Settle moves base plus boost to proceeds.
One live placement per listing. A new purchase needs the latest placement to be dead, and earlier placements always end sooner, so none can come back to life. Listing transfers keep the same id and the rule survives.
Pinned terms. Recipient and revision are captured at purchase. Rotating the recipient or editing the listing cannot redirect existing escrow or boosts.
Live dependency. I read the IMD token on mainnet. It is "Identity.md", 18 decimals, a LayerZero OFT over a standard ERC-20. Its selector set has no pause, fee, or blacklist entry, and the only owner-side token powers are name and symbol updates and messaging configuration, so the dependency cannot freeze deposits or withdrawals.
Static analysis leads. The strict-equality lines compare an enum to None, the reentrancy line is a staticcall into the immutable registry, and the unused-return line is an intentional ABI probe. None reproduces as a defect.

The coverage record answers all 18 entry points and adds rows for the conservation, boost-escrow, ranking and rounding invariants. No part of the assigned area was left unreached.

---

All 73 tests pass under forge build and forge test with the verifier's fuzz seed (65 already there plus 8 new). I found no defects, so I did not write .imd-findings.json. The new tests are on disk but not committed. Everything I added is under test/, and the source, config and earlier tests are unchanged.
The earlier tests already covered everything the brief asked for: the 24-hour duration, a third party boosting, the boost being lost on cancel, ranking ties, and the balance invariant with boosts. I added three files for what was still missing:


test/FeaturedModelInvariant.t.sol: random call sequences against FeaturedPlacementsV2. The earlier invariant handlers skip calls that should fail; this one makes every call. That includes callers who should be refused: Carol, who boosts but never owns a listing; Mallory, an outsider who also tries the owner-only functions; and the proceeds recipients. Each call must succeed exactly when a separate model of the contract says it should, so a refused call is shown to change nothing. It also mixes in boosts right at the expiry second, listing transfers, recipient changes and tokens sent directly to the contract. After every sequence it checks that:

the contract's token balance equals totalAvailable + totalEscrowed + totalProceeds, plus any tokens sent directly;
each account's balances, each placement's status, refund and boost, and rankOf match the model;
a closed placement never reopens, and each listing has at most one live placement;
featured returns totals that line up with rankOf, in ascending id order;
only proceeds recipients ever earn anything;
at the end, everything still locked can be paid out without the owner.

To check that this suite can actually fail, I ran a copy with a deliberately wrong cancel rule. It failed straight away.


test/HookListingRegistryInvariant.t.sol: random create, update, hide/show, propose, cancel and accept calls on the registry from any caller, checked against a model. Every listing must stay findable under its current owner, with no stale entries left behind after a transfer. Labels, revisions and search results must match, and isAudited must stay false.


test/FeaturedBoostEdges.t.sol (6 tests):

a fuzz test showing a boost can spend exactly the caller's deposited balance and not 1 more;
a fuzz test where a new listing owner cancels a placement Carol boosted, at a random time: the seller gets the pro-rata base refund, Carol gets nothing back, and her whole boost goes to the pinned recipient;
earned proceeds can't pay for a boost, and deposits can't be withdrawn as proceeds;
a booster can't cancel, and nobody can settle early;
an owner who has proposed a transfer, and a former owner, have no owner powers;
an ad stays live and boostable after its listing is hidden, but the listing can't buy another while hidden.



Two behaviours match the brief as I read it, so I didn't report them as defects; they're worth deciding on deliberately:

Boosting stops at expiry. Once a placement's 24 hours are up, boosting it is refused, even before anyone settles it. The brief says boosts are allowed "while the placement is open", which I took to mean live.
A booster can lose their boost almost immediately. If the buyer or the listing's current owner cancels one second after a third party boosts, the whole boost goes to the proceeds recipient. That is the "never refunded" rule working as written, but the website may want to warn boosters about it.

No tests were needed against the live IMD token: the contract never calls it at construction, and the earlier tests cover badly behaved tokens with a local mock.

---

The review is complete and the findings file is in place. No source files were changed, and the scratch tests were removed.
Outcome: the math in FeaturedPlacementsV2 holds. I found no defect that loses funds, pays the wrong party, or breaks the conservation rule. The file .imd-findings.json holds two info-level notes and a coverage row for all 18 entry points plus three invariant rows.
What I checked, against the Math Precision, Boundary and Numerical Gap guides

The diff against the audited original is exactly the briefed change set. The three unchanged files match the provenance hashes byte for byte. The pro-rata formula is identical to the original with only the divisor changed.
The single division in cancel cannot overflow (product under 9e21) and is bounded by the expiry guard, so refund plus earned always equals the base price exactly. Boosts are added outside the division, so they never round.
Every boundary comparison is consistent: boost and cancel reject at or after expiry, settle accepts at expiry, purchase allows renewal exactly at expiry, and the one-live-placement check uses the same predicate as the active view.
Escrow accounting increments and decrements pair exactly across all seven state-changing functions, so the conservation rule holds with boosts counted in escrow until close. The existing invariant suite with boosts passes.
The live IMD token on Ethereum reports 18 decimals and passed a throwaway fork run of the full deposit, purchase, boost, cancel and proceeds cycle under the exact-transfer checks.
All 65 existing tests pass on forge 1.8.3, including the required boost, forfeiture, tie and invariant tests.
Static-analysis leads were all benign: enum strict-equality, an intentional ABI probe, and a view call to the immutable registry.

The two info notes, with concrete inputs

Cancelling in the same block as the purchase earns the recipient zero and returns the full base, and at one second elapsed the recipient is short by under one wei. This is the agreed pro-rata rule, not a defect. The only effect is that a listing owner can inflate the placement ID space for gas alone.
The pinned proceeds recipient, which is the owner wallet, can boost any placement and receive the same tokens back as proceeds. The paid ranking is therefore a trust assumption on the owner, not an enforced guarantee.

Not reached: nothing in my assigned area. I did not independently audit the access-control or economics areas beyond what the coverage rows state, since other specialists hold those.

---

The review is complete. The findings file is written and the tree is otherwise unchanged.
Result: no defect in the permission model. The Access Control, Trust Gap and Asymmetry checks all hold against the code as it stands. The file .imd-findings.json carries one informational trust note and a coverage row for all 18 entry points plus three invariants.
What I verified

Every owner power is exactly what the brief lists: one-time token choice, recipient for future purchases, two-step rotation. The owner has no sweep, cancel, spend or redirect path. A scratch test confirmed the owner's calls to cancel, withdraw, withdrawProceeds, boost and early settle all revert.
Recipient rotation cannot touch in-flight value. Each placement pins its recipient at purchase, and purchase takes an expected recipient, so the owner cannot sandwich a buyer or sweep escrowed boosts.
Every storage variable written by two or more functions is written only on behalf of msg.sender or the pinned payer and recipient. The deposit and withdraw, purchase and cancel or settle, and boost and close pairs mirror each other exactly.
The registry has no administrator. Listing identity includes the creator, so nobody can squat or block another claim. Self-transfer and relist-after-transfer keep the identity index consistent.
The vendored sources are byte-identical to the pinned upstream commit, and the V2 diff is confined to the briefed changes.
The live Ethereum IMD token is a verified, exact-match OpenZeppelin v5 ERC20 with a LayerZero OFT extension. It has no transfer fee, pause or blacklist. A fork rehearsal of deposit, purchase, boost, cancel and withdraw passed against it.
The full suite passes with the README's fuzz seed.

CheckResultFoundry tests65 passed, 0 failedEntry points covered18 of 18
The one note is a design-level trust assumption rather than a defect. Anyone may boost a placement, but the payer or the current listing owner may cancel it at any moment and the whole boost then goes to the proceeds recipient. The brief requires this and the README discloses it. The website should keep that disclosure next to the boost action.
Not covered: the token owner's LayerZero bridge configuration can mint IMD on Ethereum. That is a property of the token, not of these contracts, and the brief fixes the token address.

---

The review found no defects, so .imd-findings.json has an empty findings list and a coverage record of 20 rows. Those rows cover all 18 entry points, each marked holds, plus one row for the conservation invariant and one for deployment.
What I checked against the code

Changes from the audited original: I cloned the source at commit 46e17ea. HookListingRegistry, ExactStoreToken and StoreAdmin are byte-identical to it. FeaturedPlacementsV2 changes only what the brief asks for: the 24-hour duration, totalBoost, boost, rankOf, and the per-placement totals returned by featured. It also adds the #ad label to the cancel and settle events, which the brief requires.
Tests: forge test passes all 73 tests. The suite already has the tests the brief asked for: a third-party boost, boost forfeiture on cancel, ranking ties, and invariant tests that include boosts (FeaturedInvariant and FeaturedModelInvariant).
Deployment: neither constructor calls another contract. Deployed sizes are 9,108 and 9,035 bytes, well under the 24,576 limit. launch.json has only kind, contracts and notes. Its constructor arguments match the declared parameters: none for the registry, and $owner then $contract:HookListingRegistry for FeaturedPlacementsV2. There is no delegatecall, selfdestruct or tx.origin, and ownership never comes from msg.sender at construction.

Specialist findings (all 5 were info level)
I reproduced each one in a scratch Foundry test, which I deleted afterwards. All four tests passed, and each describes behaviour the brief asks for, so I kept none as defects:

Boost can be lost to an immediate cancel: the economics and permissions specialists reported the same thing, so I merged them. If the payer or listing owner cancels right after someone boosts, the boost goes to the proceeds recipient. The brief says boosts are never refunded.
Free cancel in the same block, and rounding: cancelling in the same block refunds the full price. After 1 second, the refund is 99998842592592593 and the recipient's proceeds are 1157407407407, so rounding favours the payer by under 1 wei. The formula is the same as in the audited original.
The proceeds recipient can boost for free: boosting then settling returns everything to the recipient, so their ranking costs them only gas. This is an owner trust assumption.
Tokens sent directly to the contract are stuck: they aren't recorded as anyone's balance, and there is deliberately no admin sweep to recover them.

Static-analysis leads, all rejected

The "strict equality" warnings are enum status checks.
The ignored return value in configureToken is a deliberate check that the token has a working balance function.
The "reentrancy" warnings concern code that is already guarded against reentrancy, plus a read-only call to the project's own fixed registry.
The timestamp warnings are for the 24-hour expiry checks, which need the timestamp.

The working tree also has untracked files I didn't create (.bashrc, .claude/, .vscode and others). I left them alone.
