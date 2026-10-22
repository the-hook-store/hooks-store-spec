# Ad contracts launch (Robinhood Chain) reviews, copied from https://explorer.imd.fun/jobs/7f951ad8-ac62-41f0-b968-79737c96623e on 2026-10-22

Implemented both contracts, preserving HookListingRegistry unchanged. V2 includes 24-hour placements, nonrefundable boosts, ranking totals, and boost-aware escrow accounting.
Validation passed: forge build, all 61 tests with the specified fuzz seed, and forge fmt --check.
Dependencies are vendored. Deployment parameters and owner setup responsibilities are documented in README.md.

---

I found no math defect worth fixing in the boost and placement contracts. The only finding is info-level: rankOf reports a placement's total differently from what its comment promises. The full test suite passes (forge test: 61 passed, 0 failed), and no repository files were changed.
Scope: I compared FeaturedPlacementsV2 line by line against the original contract at the specified commit. The changes match the brief and add nothing else: the 24-hour duration, boost, boost handling on cancel and settle, rankOf, totals in featured, and the #ad label on events. The other three contract files are unchanged.
Math precision:

Refund rounding: the fee kept on cancel is 0.1 IMD × elapsed / 86,400, rounded down. Elapsed time is always under 86,400 seconds, so it can't overflow, and refund plus kept fee always equals exactly 0.1 IMD. Rounding favours the payer by under 1 wei per cancel, as in the original.
Boost amounts: there are no casts to smaller types and no division in the boost logic. Base price plus boosts can't overflow because it never exceeds the tokens the contract actually holds. Token decimals are checked to be exactly 18 when the token is configured.

Boundaries:

Expiry: a placement can be boosted or cancelled only before its end time, and settled only at or after it, so there's no gap or overlap at expiry. The purchase deadline includes its last second.
Bad inputs: zero amounts, placement id 0 and unknown ids are all rejected.
External calls: the registry lookup during purchase goes to a fixed, read-only contract. Token transfers check the exact balance change on both sides and are protected against reentrancy.

Conservation and ranking:

Balance rule: every function moves value between available, escrowed and earned without creating or losing any, or makes an exact-checked transfer in or out. Boosts stay in escrow until the placement closes.
Ranking: featured keeps each total paired with its placement after filtering, and returns placements in ascending id order, which gives the lower-id-first tie-break.

Finding 1 (info), src/store/FeaturedPlacementsV2.sol:249: rankOf is documented as "Total paid … Retained after closure", but for a cancelled placement it still adds the full 0.1 IMD base, even though some or all of it was refunded.

Reproduction: buy a placement, boost it with 0.05 IMD, then cancel in the same block. The payer gets the full 0.1 IMD back and the recipient earns 0.05 IMD, but rankOf returns 0.15 IMD.
Impact: the website's sort isn't affected because featured only returns live placements. Only off-chain readers relying on the "total paid" wording would be misled.
Why it's only info: the brief literally asks for "base plus boost", and an existing test asserts this value. The simplest fix is to correct the comment.

Static-analysis leads, all rejected:

The "strict equality" warnings are ordinary status comparisons.
The "state change after external call" warning in purchase is a read-only call to the fixed registry, inside the reentrancy guard.
The "ignored return value" in configureToken only checks that the token answers a balance query correctly.
The timestamp warnings are the intended 24-hour timing rules.

Coverage: the coverage record answers all 18 entry points (17 hold, none left unchecked), plus rows for the balance rule, the featured totals and rankOf. I didn't write a proof test, since one is only required for critical or high findings.
Everything is in .imd-findings.json in the repository root.

---

Created launch.json with both contracts in dependency order and verified constructor arguments.
Validation passed: manifest checks, offline forge build, and all 61 tests using the supplied fuzz seed. Only launch.json is changed for submission.

---

Review complete. The findings file is written and the scratch test is removed; the tree is otherwise untouched.
Outcome: no defect in the economics of either contract. The conservation rule, the escrow of boosts until closure, pro-rata base refunds, boost forfeiture to the pinned recipient, settlement, recipient pinning, and view/write agreement at the expiry boundary all hold on every path I traced. All 61 existing tests pass, including the invariant run seeded with third-party boosts.
Two low findings recorded in .imd-findings.json, both reproduced with a scratch Foundry test:

Immediate cancel forfeits a third-party boost with zero featured time. Alice buys placement 1, Bob boosts it with 5 IMD, Alice cancels in the same block. Alice gets her full 0.1 IMD back, Bob's 5 IMD goes to the proceeds recipient, and Alice can re-purchase at once. This is exactly what the brief specifies, so it is reported as a design tradeoff for the author to confirm rather than a code error. Any mitigation changes the agreed economics.
Gas-only purchase/cancel loop inflates the placement id space. A cancel at elapsed zero refunds in full and never blocks the next purchase. A helper contract created 200 dead ids for about 308k gas each without spending any IMD. The website's featured scan is linear in placement count forever, so this is a read-path griefing vector inherited from the original design. No funds are at risk.

Coverage: all 18 entry points have a row, plus three invariant rows. Static-analysis leads were checked: the strict-equality and timestamp warnings are the intended status and time-term checks, the unused balance return in configureToken is a probe, and the aderyn reentrancy flag on purchase refers to a view call into the immutable registry inside the guard.
Noted but not filed as findings: the proceeds recipient can boost listings at zero net cost since boosts return as proceeds, and tokens sent directly to the contract are unrecoverable. Both are admin or self-affecting by design.

---

The review is complete and .imd-findings.json holds the result. The tree is unchanged apart from that file, and the scratch test is removed.
Outcome: no permission bypass, trust gap, or asymmetry defect of medium or higher severity in either contract. The full suite passes under the repository seed, and the three pinned files are byte-identical to the upstream commit. The V2 diff contains only the changes the brief lists.
What I traced in the assigned area:

Access control map. Every state-changing entry point has the guard its effect needs. Deposits and proceeds are debitable only by their own holder. The owner has no sweep, pause, admin cancel, or early settle. Factory and pending owner are rejected everywhere. Ownership rotation is two-step and cannot reach zero.
Trust-gap seams. Recipient rotation cannot redirect in-flight value because every placement pins its recipient at purchase, and the payer's expected-recipient check blocks owner front-running. Listing transfers never move a refund away from the original payer. Boosts cannot spend allowances, other deposits, or proceeds.
Asymmetry. Purchase, boost, cancel and settle use the same expiry boundary. Escrow, available and proceeds deltas mirror across every pair, so the conservation rule holds with boosts counted in escrow until closure.

Two items are recorded, each with a concrete reproduction I ran:

Low. The boost function takes no deadline, while purchase does. A boost signed at the start of a placement but included one second before expiry pays in full for one second of ranking. Suggested fix adds a deadline parameter that mirrors purchase.
Info, trust assumption. Cancelling at time zero refunds the full base price but forfeits every boost to the recipient. Because the recipient is the owner's wallet, an owner who also advertises can collect third-party boosts at zero cost by cancelling and re-purchasing in the same block. The brief mandates this forfeiture rule, so it is documented for the requester's decision rather than reported as a defect.

Coverage lists all 18 entry points as holding or tied to those findings, plus three invariant rows. Nothing was left unreached.

---

Added 17 tests covering failure paths, arithmetic and metadata boundaries, pagination, and 24,576 randomized escrow calls.
forge build and forge test pass with the required seed: 78 passed, 0 failed, 0 skipped.
Only test/ changed. No reproducible contract defects found. Live IMD integration remains unverified.

---

The review is complete and .imd-findings.json is written with 2 findings and 21 coverage rows, all 18 listed entry points answered.
Outcome. No critical, high or medium defect in the control flow. The V2 delta is exactly the brief: a diff against the pinned upstream commit shows only the rename, the 24-hour duration, boost and its accounting, rankOf, featured totals, and the #ad label on the three lifecycle events. The three untouched files hash-match upstream. All 61 existing tests pass with the README seed, and the upstream test files differ only by rename and duration constants.
What I traced and confirmed holds. Every custody path keeps accountedBalance equal to available plus escrowed plus proceeds, with boosts in escrow until closure. Cancel refunds the original payer pro rata and sends the whole boost to the pinned recipient. Settle is permissionless and transfer-free, so a hostile recipient cannot block it. The reentrancy guard covers all seven custody entry points, including boost. Owner powers are limited to the two-step handover, one-shot configureToken and setProceedsRecipient, and the constructor makes no external call. I also probed the IMD token the brief names on Robinhood Chain: it has code, 18 decimals, symbol IMD, and no EIP-1967 proxy slots, so the irreversible configureToken and the exact-transfer checks should accept it.
Findings reported.

Low: a purchase and cancel in the same block costs nothing, so one listing owner with 0.1 IMD can mint unlimited placement ids. The featured feed is a dense 100-id scan, so each 100 dead ids cost the website one extra call forever. Verified with 1,000 cycles leaving the payer's balance intact and 10 empty pages. The fix needs a scope decision because pro-rata refunds are a stated requirement.
Info: the pinned proceeds recipient can boost any placement and get the boost back on settle or cancel, so on-chain "total paid" totals are operator-manipulable at zero cost. Recorded as a trust assumption, not a bypass.

Neither finding carries a proof file, since both are below high severity. The scratch test under test/scratch/ that verified the numbers is not part of the submission.

---

Review complete. The findings file is written and validated, and the scratch tests are removed so the tree is clean apart from the required .imd-findings.json.
Outcome: no critical, high or medium defects. All seven specialist findings reproduced against the code and merged into five, three low and two info. My own pass found nothing further.
What I verified

The three unchanged files are byte-identical to the pinned upstream commit, and the FeaturedPlacements to V2 diff contains only the changes the brief asked for.
The full suite passes, including the boost, tie-ranking, forfeiture and boosted-invariant tests the brief requested.
Runtime sizes are about 9 KB each, constructors make no external calls, and launch.json has only the schema keys with arguments in declaration order.
Every entry point has a coverage row, plus three invariant rows (conservation, diff scope, deployability).

Findings kept, all reproduced in a scratch Foundry test that passed on this code

Low, cancel line 201. Same-block purchase and cancel refunds the full price, so one deposit mints unbounded dead ids that featured() must page through. Merged from audit_flow and audit_economics.
Low, cancel line 203. Payer or listing owner can cancel right after a third-party boost: full base refund, whole boost to the recipient, zero ranking delivered. Merged from audit_economics and audit_permissions. Spec-conformant and documented in the README, so flagged as a scope decision.
Low, boost line 182. boost() has no deadline parameter, unlike purchase(), so a late-included boost pays in full for seconds of ranking.
Info, boost line 180. The proceeds recipient can boost any placement at zero net cost, so on-chain totals are operator-manipulable.
Info, rankOf line 252. NatSpec says "Total paid" but cancelled placements report the full nominal base even when refunded.

Static-analysis leads dropped: the aderyn reentrancy line is a staticcall to the immutable registry behind a guard, the slither strict-equality lines are enum comparisons, and the unused-return in configureToken is a deliberate ABI probe whose revert is the check.
