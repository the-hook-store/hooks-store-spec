# Job 8 notes (explorer, 2026-10-22)

### build_website
Implemented SPEC 1.31 §4.16, refreshed the Builder, and rebuilt dist/.
Build and typecheck passed; 1,096 unit tests and 195 browser tests passed, with 7 optional skips. Four live free checks passed. Bundle checks fit under 8 MiB.
Validation records results and limitations, including unavailable WebKit libraries. The independent review documents four specification-policy risks for the owner’s next job.


### adversarial_review
I found four defects and reproduced each one by running the real compose.ts and safety.ts from scripts in /tmp. They are in .imd-findings.json, most severe first. No repository file other than .imd-findings.json was changed. None of the findings has a Foundry proof, because none is in Solidity.
- 
High: a fee written in words is missed, and the composer adds "Hook fee rate: 0%." (src/lib/compose.ts:220). The fee detector only recognises a number followed by %, IMD or ETH.
- Input: a type B request in words mode, chain 4663, no blocks, with the description "Charge a fee of 30 basis points on every swap and send it to 0x6cba…8a34." "Take half a percent of every swap as a fee for the owner." fails the same way.
- Result: the request contains both that description and "Hook fee rate: 0%.". validate() and checkConsistency() both return nothing, so a builder would get two contradictory fee rules after payment.
- 
Medium: a fee written in words gets no pair-currency sentence (compose.ts:219). The sentence naming the fee side, settlement and recipient is only written when a fee block is stacked.
- Input: a type B request in words mode with "Take 1% of every swap as a fee."
- Result: the request names no fee side, no settlement currency and no recipient, and the check passes. Rule 4 of 4.16 and section 6.7 require all three.
- 
Medium: the 5% fee cap ignores Fee that fades and Volatility fee (compose.ts:122).
- Input: Swap fee 0.1%, Buyback jar 4.9%, Fee that fades starting at 30% (the catalog allows up to 30), Volatility fee 3%.
- Result: rateTotal() returns 5 and nothing flags it, although the first swap pays 34.9% and a volatile period 7.9%.
- 
Low: the Builder allows block pairs that the consistency check then rejects (src/blocks/catalog.json, Max buy per wallet sentence).
- Input: Max buy per wallet with Pause, Trading hours or Circuit breaker, or Liquidity lock with Pause or Circuit breaker.
- Result: the Builder offers Add and validate() passes, but checkConsistency() reports a contradiction and Launch stays locked. The block menu gives no warning, so the user only finds out at Launch.
What came out clean:
- IMD pairing: for every block in a type A request paired with IMD, "ETH" appears only in the "do not convert" sentence, and the check raises nothing (apart from Split the fee's empty second address, which is meant to be flagged).
- Required sentences: the deployer, factory, ETH-only pool, token definition, references, owner and no-outside-dependency sentences are all present and checked as 4.16 asks.
- Excludes: the excludes lists are enforced in both directions.
- Words mode: a saved block stack is left out of the request, and the summary still shows the words in Stack blocks mode.
Not covered, because time ran out: I did not run Playwright at the three widths, and I did not compare against the evidence files for the free check or IMD's fixed facts.


### design_critic
AreaResult
Requirements32 met · 4 missing · 0 faked · 1 after review
Broken features3 high findings
First screen at 390Product and main action visible
taste@113/16 passed; remaining flags match prescribed styling
Copy3 request/example defects
Share cardPresent
Three defects still allow contradictory requests through:
- bug: Writing “1 percent” produces both the requested positive fee and Hook fee rate: 0%.
- fidelity: The supplied Price reading and Owner pause examples omit required PoolId arguments.
- bug: B/C written fee requests name the payer as constructor recipient even when the description names another address.
Exact inputs, source citations, expected changes and measured reproductions are saved in .imd-findings.json.
The requirement accounting below marks partially fulfilled requirements missing where a confirmed gap remains.
RequirementStatusEvidence
4.16.1 Constructor-mined deployer, forwarding, hook() and zero-hook stateMissingDeployment wording and zero-hook handling exist; written recipient can disagree with constructor
4.16.2 Type A factory-only initializationMetsrc/lib/compose.ts factory gate and constructor arguments
4.16.3 ETH pool restrictions, token definition and PoolId scopeMissingCatalog complies; supplied words examples omit PoolId
4.16.4 Pair-currency sides, settlement, thresholds and IMD exceptionsMetCatalog/composer matrix
4.16.5 No outside dependencies; both referencesMetComposer footer and body()
4.16.6 Factory exception only for AMetComposer branches
4.16.7 Owner always matches bodyMetbody() and consistency tests
4.16.8 Actual-traded fees and partial-fill revertsMetCharging block sentences
4.16.9 Explicit zero fee without charging blocksMetComposer footer; written-fee contradiction reported separately
4.16.10 One rate/destination and resolved fee choicesMissingBlock combinations comply; written B/C destination can conflict
4.16.11 Buyback execution, price limit and token retention/burningMetBuyback catalog sentence and token context
4.16.12 LP-share empty-liquidity fallbackMetLP-share sentence
4.16.13 Prize withdrawal, periods and bounded lookupMetPrize-pot sentence and claimPrize signature
4.16.14 Anti-sandwich wording and LP donationMetAnti-sandwich sentence
4.16.15 Windows begin at first swapMetTiming and fee sentences
4.16.16 tx.origin identity and limitationMetShared wallet-limit wording
4.16.17 Seconds and chain-local block numberMetVolatility, breaker, JIT and anti-sandwich sentences
4.16.18 Token-amount-only Max swap sizeMetMax-swap sentence
4.16.19 Position keys and own-position exemptionsMetLiquidity sentences and management ABI tests
4.16.20 Sunset precedence and withdrawalsMetSunset sentence
4.16.21 Donation options and hook exceptionsMetOption-specific sentences and conditional controls
4.16.22 Exclusion lists and incompatible combinationsMetCatalog lists and exhaustive exclusion tests
4.16.23 Batch auctions unavailableMetDisabled catalog entry and Builder
4.16.24 Dynamic-fee flag, mapping and pool initializationMetCatalog and pool-call encoding tests
4.16.25 Yield remains unavailableMetDisabled entry on both chains
4.16.26 Warning, checklist, visible rules, owner grants and precedenceMetBuilder and composer carry-over tests
4.16.27 Six-block/24 KB noticeMetBuilder and Launch summary
4.16.28 mulDiv and own-token supply capMetComposer, catalog and validation
4.16.29 Verify poolBps denominatorMetRecorded receipt research and total-supply wording
4.16.30 Post-fix laun


### build_website
Fixed all seven findings and rebuilt dist/.
Build and typecheck passed, plus 1,104 unit tests, 9 relay tests and 202 browser tests. Seven optional checks were skipped.
Finding responses · Validation and limitations


### adversarial_review
Three of my four earlier findings are fixed. The first one (high) is only partly fixed, and I found one new medium issue. Both are in .imd-findings.json. I changed no repository files; the scripts I ran were in /tmp/rv.
Earlier findings:
- 
[high] 418c451b, a written fee gets a contradictory "Hook fee rate: 0%." line: partly fixed.
- What now works: I ran the original inputs ("30 basis points", "half a percent"). The 0% line is gone, the pair-currency fee sentence and recipient are written, and the checks pass.
- What still fails: the detector at src/lib/writtenFees.ts:25 only counts a fee if the clause contains the word fee, jar or pot, or a verb like take, charge or collect. Many common ways of writing a fee have neither:
- "1% of every swap goes to the owner."
- "Add a 2% tax on sells for the owner."
- "Skim 1% of every swap for the owner." / "Keep 1% of each swap for the owner."
- For each of these, the request still gets "Hook fee rate: 0%.", with no fee side or recipient sentence, and both validate() and checkConsistency() return nothing. This happens in Describe it mode and with a Custom rule, under types A, B and C. The final consistency guard (safety.ts:189) uses the same detector, so it misses these too. I filed this again as high.
- 
[medium] f77fb0a9, a written fee has no fee-side, settlement or recipient sentence: fixed. For "Take 1% of every swap as a fee." the request now names the ETH side, ETH settlement, the recipient address and the amount-traded rule.
- 
[medium] 1f896273, the 5% cap ignored Fee that fades and Volatility fee: fixed. The reported stack now totals 34.9%, and both checks refuse it. The fade start is capped at 5%.
- 
[low] 505680786, block pairs that contradict each other were allowed: fixed. I ran every allowed pair of blocks under types A (ETH and IMD pairs), B and C, 1,014 combinations in all. Every pair the palette allows passes both checks with no finding.
New finding:
- [medium] A written fee and a block fee are checked against the 5% cap separately (safety.ts:165). Example: type B with a Swap fee block at 3%, plus a Custom rule saying "Also charge a 4% fee on every swap for the owner." Together that is 7%, over the 5% cap. Yet rateTotal() returns 3, and both checks return nothing. The builder also has to guess whether the 4% is added to the 3% or overridden by the numbered rule.
Neither finding is in Solidity code, so neither has a Foundry proof attached. Each one names the exact input and the actual output of compose(), validate() and checkConsistency().


### design_critic
AreaPrevious reviewThis review
Requirements trackedNot recorded33 met, 3 missing, 0 faked, 1 needs requester
Broken features3 high2 high
Product/action on first screen at 390Not recordedYes
taste@1Not recorded13/16
Editorial copy findingsNot recorded0
Share cardNot recordedPresent
All three original reproductions are fixed. Two related safety defects remain, recorded in .imd-findings.json:
- High — bug: “payable to [treasury]” leaves the payer in the deployer and fee footer, contradicting the written destination.
- High — bug: a price threshold of “1 percent” lets “charge a small hook fee” pass without an actual fee rate.
Both reproduce for B/C, both written editors, and all three widths. Each passes the local consistency gate and enables Continue after a mocked successful free check.
Requirement dispositions below use the numbered rules in SPEC 4.16. Evidence names identify the source file and relevant element.
RequirementStatusEvidence
1. Constructor-mined deployer, unchanged arguments, hook() and zero stateMissing: written recipient can disagree; remaining behavior metcompose.ts, writtenFees.ts, Hook.tsx; finding 1
2. Type A factory authorization and constructor argumentsMetcompose.ts: Type A opening
3. Native-ETH scope, token definition and PoolId interfacesMetcompose.ts, catalog signatures, Builder examples
4. Pair currency, conversion opt-out and currency orderMetcompose.ts, catalog templates
5. No outside dependencies; both referencesMetcompose.ts: footer and body()
6. Factory named only for AMetcompose.ts: launch-type branches
7. Owner in body and textMetcompose.ts: body()
8. Actual-traded fees and partial-fill revertMetcompose.ts: feeBasis
9. Explicit zero-fee defaultMetcompose.ts, percent regressions
10. One rate/destination, distribution ordering, no burn destinationMissing: payable destination remains contradictorywrittenFees.ts; finding 1
11. Buyback timing, price limit and token-specific retention/burningMetCatalog jar, own-token; composer context
12. LP sharing fallbackMetCatalog lp-share
13. Prize withdrawal, rollover and bounded lookupMetCatalog pot
14. Anti-sandwich wordingMetCatalog anti-sandwich
15. First-swap windowsMetCatalog window/period sentences
16. tx.origin and limitationMetComposer walletLimit
17. Seconds and chain-specific block numberMetCatalog volatility, breaker, JIT, anti-sandwich
18. Token-amount-only maximum swapMetCatalog max-swap
19. Position keys and hook-position exemptionsMetCatalog liquidity rules
20. Sunset precedence and withdrawalsMetCatalog sunset
21. Donation options and own-donation exceptionMetCatalog donate.optionSentences
22. Exclusion listsMetCatalog excludes; combination tests
23. Batch auctions unavailableMetCatalog async.disabled
24. Dynamic fee flag and initializationMetCatalog lp-fee, web/src/chain/pool.ts
25. Yield remains dimmedMetCatalog yield.disabled
26. Written warning/checklist, visible rules, owner powers and precedenceMetBuilder.tsx, compose.ts
27. Six-block noticeMetBuilder.tsx: .block-count
28. mulDiv and supply capMetComposer footer, catalog own-token
29. Verify pool allocation basisMettests/results/job8/pool-allocation-research.md
30. Paid launches and subsequent owner follow-throughNeeds requester: authorized signed launchesFuture operational verification
Composer tests across blocks/types/pairingsMettests/job8.test.mjs, revision


### build_website
Fixed all four findings and rebuilt dist/.
Build, typecheck, 1,130 unit tests and 215 Chromium tests pass. Seven optional tests skipped; WebKit unavailable. Bundle fits under 8 MiB.
Finding responses · Validation report


### build_website
Of the two findings from last round, the price-threshold one is fixed. The "payable to" one is fixed for that spelling, but the same defect still gets through with other ordinary wording, so I've raised it again with a new reproduction. .imd-findings.json holds that one finding, and no other file was changed.
AreaLast roundThis round
Prior findings settled0 of 21 fixed, 1 still reproduces with other wording
Brief requirements (met / missing / faked)not re-countednot re-counted (this round only settles the raised findings)
Broken features2 (high)1 (high)
Product on the first screen at 390—not re-checked
taste@1 checks passed—not run this round
Copy findings00
Share card—not re-checked
1. Price threshold accepted as the fee rate (src/lib/safety.ts:162): fixed.
- I ran the exact sentence again ("When the pool price moves by 1 percent… charge a small hook fee…") for types B and C, in both Describe it and Custom rule. The consistency check now returns fee-rate ("Name an exact fee amount…"), and the request no longer gets the "Hook fee rate: 0%." line.
- That finding locks the Builder's Check and Continue buttons (web/src/useSwarmCheck.ts:29, web/src/Builder.tsx:283-284) and the Launch step (web/src/LaunchReview.tsx:179).
- Two nearby wordings are also caught: a 2 percent liquidity trigger with no fee amount, and "a modest hook fee, capped at 5 percent".
2. "Payable to" treasury fee still paid to the payer (src/lib/writtenFees.ts): fixed for that wording only.
- The exact reported sentence now puts the treasury 0x3f25…1F22 in the deployer constructor and the "Fee recipient:" footer, for B and C in both editors. "paid to" works too.
- The address lookup only knows each destination verb in its base form plus sent, paid and payable. So "transferred to", "forwarded to", "routed to", "remitted to" and "with proceeds transferred to" find no address.
- In each of those cases the constructor and footer fall back to the payer 0x1111…1111, while the description still sends the fee to the treasury. Both validation and the consistency check return nothing, so the free check and Continue stay unlocked.
- The shipped bundle (dist/assets/index-BY4Eg384.js) carries the same address-matching pattern. I reproduced this through the composer functions the Builder calls, not by clicking through the browser this round.
- It stays high, as a bug at src/lib/writtenFees.ts:65, because it breaks SPEC 4.16 items 1 and 10 and 6.7 the same way the original did.
- The fix in the finding: accept the past-tense forms of those verbs, and have the consistency check flag a 0x address in fee wording that differs from the constructor's recipient. Add these spellings to the regression tests for B and C in both editors.
I found nothing else new that I could reproduce.


### adversarial_review
Review complete. Both findings I raised last round are fixed as stated, and the findings file at .imd-findings.json records two residuals, one medium and one low.
Prior high finding (written fee with no fee word, b02b0a7c): fixed. I ran the author's reproduction for all four phrasings in Describe it and Custom rule, types A and B, chain 4663, wallet 0x6cba…4a34. Each now composes the pair-side, settlement, recipient and partial-fill sentences, omits the zero line, and passes validation with no findings. The rebuilt bundle under dist/ contains the new detector.
Prior medium finding (written fee not counted toward the 5% cap, ffcbc178): fixed. Swap fee 3% plus the written 4% now totals 7% in rateTotal, blocks in validate, and blocks again in the consistency check, for A on both pairings, B and C. The boundary cases pass and fail as the author describes.
Residual, reported as medium. The written-fee detector remains a word allowlist, and one-word synonyms still get the silent zero line with no finding. The following prompts each compose Hook fee rate: 0%. with no fee-side sentence and empty checks, in both editors and types A and B:
- "The owner receives 1% of every swap."
- "1% of each trade goes to the owner."
- "2% commission on every swap to the owner."
- "Buyers pay a 1% toll to the owner.", "Route 1% …", "Divert 1% …", "1% … accrues to the owner."
I lowered this from high because the stated inputs are fixed and the author's review already says the guards cover tested forms only. The finding suggests a structural fix: any written amount next to a trade word with no fee block should count as fee intent, and an amount the parser cannot attach to a charge should raise the existing clarification finding instead of writing zero.
Residual, reported as low. The combined cap adds the written maximum to the block maximum across directions rather than per direction. Buy 2% / sell 4% plus a written 2% on buys only is blocked as 6% although no direction exceeds 4%. This is conservative and blocks a legal request rather than letting one through.
No files in the tree were changed other than the findings file. The untracked dotfiles shown by git are environment files, not mine.
