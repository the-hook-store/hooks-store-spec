# Job 9 reviews, copied from https://explorer.imd.fun/jobs/0543f750-a284-4783-a62f-1ae098fbff5a on 2026-10-22

Implemented job 9, refreshed SPEC 1.34 and rebuilt dist/.
Build/typecheck passed, along with 1,145 unit tests and 234 browser tests; seven optional tests were skipped. Adversarial review findings were fixed.
Bundle: 8,370,362 bytes, within 8 MiB. Validation and limitations.

---

Review complete. Six findings are in .imd-findings.json, each verified by running the real compose(), body(), validate() and checkConsistency() against the tree (in a temp copy, since the root package.json here is an empty, git-excluded file that breaks Node's module resolution for the repo in place). No repository file was changed.
What held up. Owner, remainder, fee recipient and every address in the objective arrive lowercase with a checksummed wallet, and the consistency check refuses non-lowercase body fields. The seven phrasings named in the brief ("owner receives 1%", "goes to the owner", "2% commission", "toll", "route", "divert", "accrues"), spelled amounts ("one percent", "half a percent", "one per cent"), "payable to IMD's treasury" flowing into footer and deployer constructor, a rate-less fee raising a finding, and the per-direction cap (4% buys plus 4% sells accepted, 3% swap plus 3% buy refused) all behave as specified. Proven matching ignores parameters, words and Custom, is overridden by an own repository, the instruction lands after the first sentence for type B with the deployer check still passing, the relay import is compared against the pinned entry, and contracts-only Live requires Completed status 0 plus a live record with the hook address never a condition.
Findings, by severity

High, src/lib/compose.ts:247. The proven instruction is spliced at the first .  in line one. A token name like "Dr. Pond" (free text, allowed by the catalog) is cut in half, the request opens with "Launch Dr.", and the consistency check raises a false "pairing" finding that locks Launch while the index matches the stack.
High, src/lib/writtenFees.ts:68. "Swappers pay 1 percent." and "Every buyer pays 1%." produce "Hook fee rate: 0%" with no fee facts and no finding. "pay" is not a charge verb and agent nouns are not trade words, so the detector is still an allowlist for this class.
Medium, src/lib/writtenFees.ts:130. "Take 1% of every swap for IMD's treasury and the owner." drops the second payee silently and composes a treasury-only recipient with no finding.
Medium, src/lib/writtenFees.ts:80. "Collect a 2% fee on sells and no fee on buys." is classed as a prohibition, writes 0%, and then triggers two false "contradiction" findings. The reversed order fixed in the prior review passes.
Low, src/lib/compose.ts:261. "Collect 1% for the treasury." leaves "Fee recipient: the treasury." and a generic recipient block, although the spec defines treasury as IMD's address.
Low, src/lib/proven.ts:33. A words-only draft matches any index entry with an empty or Custom-only block list. Latent today, since the live index has one four-block type B entry.

Not covered. No browser inspection of the summary line, Copy link or the notification prompt at the three widths, and no live relay or IMD check was called. The job 9 unit file could not run in this tree because web/node_modules and viem are not installed here, so I relied on direct probes rather than the shipped test run.

---

The build is close: one high bug remains. Carry-over (a), the structural written-fee detector, is still partly a word list. A request whose words name 1% can still go out saying "Hook fee rate: 0%" and pass every check. It's the only finding, and it's in .imd-findings.json. I changed no files; scratch scripts and screenshots are under test/scratch/ only.
AreaCountBrief requirements22 met, 1 missing (carry-over a), 0 faked, 0 after review, 0 need the requesterBroken features1: the written-fee detectorProduct on the first screen at 390yestaste@1 checks passed12 of 16. The 4 failures come from the mockup the owner fixed on purpose (SPEC 14.9), so they aren't findingsCopy findings0Share cardyes (title, favicon, og:title, og:image)
Requirements

Owner lowercased (carry-over): met. body() lowercases the owner and remainderTo (src/lib/compose.ts:274, :277). I confirmed it with a checksummed wallet; there's a unit test in tests/job9.test.mjs.
Consistency check refuses non-lowercase addresses: met (src/lib/safety.ts:68-73).
Contracts-only launches read Live from the launch record, hook() and Completed status 0: met (web/src/chain/decode.ts, tests/results/job9/hook-live-zero-390.webp). I didn't run it in a browser myself; I'm relying on the builder's tests and the second seat's review.
(a) Written-fee detector made structural: missing. Verbs like "receives", "route", "divert", "toll" and "commission" now work. But payer words ("swappers", "buyers", "sellers", "pay") still write 0%.
(b) Recipient named in words flows into the deployer sentence and footer: met. "payable to IMD's treasury" puts 0x3f25…1f22 in both.
(c) Spelled thresholds don't count as a fee rate: met. "Charge a small hook fee once the price moves one percent" raises the fee-rate finding.
(d) 5% cap per direction: met. "Take 3% of every buy. Take 3% of every sell." counts 3% each way.
Proven-launch index fetched at load, never bundled, a failure means none: met (src/lib/proven.ts:4, fetchProvenLaunches).
Match on type, block set and chain, with Custom allowed: met (matchProvenLaunch). It matches against the live index entry PondsideGuard.
One summary line on the Builder, the Launch page and the hook page: met (web/src/Builder.tsx:269, LaunchReview.tsx:156, Hook.tsx:79).
The creator's own repository overrides the match, with no other control: met.
repoUrl and baseCommit checked through the relay's /import, with a silent fallback: met (web/src/relay.ts:53, ProvenLaunches.tsx).
"Start from the audited source…" sentence after the first sentence, every other sentence kept: met. I checked it on Type B: the inserted sentence is the only change and the consistency check passes.
The wait copy on the Builder and the Launch page: met (LAUNCH_WAIT).
Copy link on the hook page: met (Hook.tsx:80).
Ask once for browser notifications: met (LaunchNotifications.tsx).
Tests and results: met. Composer and import tests exist, Playwright covers the summary and fallback at 320, 390 and 1440, and results are under tests/results/job9.
SPEC refreshed to 1.34: met. Upstream is now at 1.37; the brief asked for 1.34.
Second-seat review: met (tests/results/job9/ADVERSARIAL-REVIEW.md).

The idea: a hook store you read in a pixel pond, carried by the live ASCII canvas.
The finding
High, bug: a written amount paid by "swappers", "buyers" or "sellers" still writes "Hook fee rate: 0%".

Where: src/lib/writtenFees.ts:66 (tradePattern).
Repro (no browser): Type B, Describe it, chain 4663, prompt "Swappers pay one percent to the owner."

The request says "Hook fee rate: 0%." and has no fee sentences.
The consistency check returns nothing, so the request passes.


Second repro: "Buyers and sellers pay 1% to the owner." also writes 0%.

---

All five findings from last round are fixed. I re-ran each of my original reproductions against the revised code, and I found nothing new that I can reproduce, so .imd-findings.json holds {"findings":[]}. I changed no other file.
Settled findings


[high] Token name containing ". " breaks the proven-launch request — fixed. The first sentence is now cut at the length it was built to (firstSentence, src/lib/compose.ts), not at the first ". " in the line. With 'Dr. Pond' and 'St. Croix', line 1 is now the whole "Launch Dr. Pond (DRP) … paired with IMD." sentence. The "Start from the audited source…" instruction comes next, then the token sentence. checkConsistency(b) and validate(d, wallet) both return [].


[high] 'pay' phrasing with a trader noun wrote a zero fee — fixed.

Fee composed correctly: 'Swappers pay 1 percent.' gives {buy:1, sell:1}. 'Every buyer pays 1%.' gives {buy:1, sell:0}. Both get the fee-side and recipient sentences. 'Buyers pay 2% to the owner.', '1% of each trade goes to the owner.' and 'The owner receives 1% of every swap.' also compose with the right rate and recipient and no finding.
Rate not attached, but flagged: 'Sellers are charged 2%.' and 'Buyers pay the owner 1%.' raise a fee-rate finding instead of silently writing zero, which is the clarification behaviour job 9 asked for.



[medium] 'for IMD's treasury and the owner' dropped the second destination — fixed. Both targets are now read. The request says "Fee recipient: the unresolved written fee recipient." and checkConsistency reports recipient and fee-recipient.


[medium] 'Collect a 2% fee on sells and no fee on buys.' was read as a prohibition — fixed. The rates are now {buy:0, sell:2} and the fee-side sentences are composed, with no findings.


[low] 'the treasury' was not resolved — fixed. 'Collect 1% for the treasury.' now gives "Fee recipient: 0x3f252e859a277a86a3967c11d4e054b2f07a1f22." with no findings.


[low] Words-only drafts matched proven entries — fixed. matchProvenLaunch now returns undefined for a words-only draft against entries with blocks [], ['custom'] or (type A) ['token'].


Extra probes on the revised code, all correct

'Sellers pay 2% and buyers pay 1%' gives {buy:1, sell:2}, and 'Buyers and sellers pay 1%' gives 1% each way.
'Sellers pay 4% and buyers pay 4%' passes, so the 5% cap is applied per direction.
'Swappers pay 1 percent to IMD's treasury.' sends the fee to the treasury.
'Charge 1% on buys and no fee on sells, paid to the owner.' composes cleanly.
'Take 1% of every swap, or no fee on buys.' raises a contradiction finding, which is correct for a self-contradicting rule.
A type B proven launch puts the instruction right after the deployer sentence and keeps the rest. The body carries repoUrl and baseCommit.

Test run: 634 of 635 tests pass. The one failure is tests/job9.test.mjs, which could not load at all: it imports viem from web/node_modules, which isn't installed here. I didn't install it because that would write into the repository, so this review did not run that file's tests.

---

AreaPrevious reportThis reviewRequirements—35 met, 1 missing, 0 faked, 1 after reviewBroken features1 highPrevious fixed; 1 new highProduct/action on first screen, 390px—Yestaste@1—13/16 passedCopy findings—0Share card—Present
The previously reported zero-fee bug is fixed. Both original prompts now compose the required fee sentences; 48 variants passed across launch types, chains, pairings and editors.
High — bug: a passive written owner payment selects the payer as fee recipient. With a distinct owner, “The owner is paid 1% of every swap.” puts the payer in both the deployer sentence and fee footer. Validation and consistency checks return no findings. Chromium at 390 × 844 also lets this contradictory request reach Launch review. Recognize the passive payee and resolve it to the owner, or require clarification before proceeding. The exact inputs, measured output and source snippet are recorded in .imd-findings.json, citing writtenFees.ts:135.
Explicit requirementStatus and evidenceLowercase owner, remainderTo and every carried addressMet — src/lib/compose.tsUnit test using a checksummed walletMet — tests/job9.test.mjsConsistency rejects invalid or nonlowercase address fieldsMet — src/lib/safety.tsRead contracts-only launches through relay GET /launches/:idMet — web/src/chain/store.tsUse artifact addresses and attestation contract namesMet — web/src/chain/decode.tsRead deployer hook() and show both addressesMet — store, Hook and browser testsShow “hook not deployed yet” for zero hook()Met — web/src/Hook.tsx, browser testsLive requires Completed status 0 plus live record, independently of hook addressMet — decode and browser testsRecognize written percentages, basis points and fractions near trade wordsMet — writtenFees.ts, regression testsCompose correct fee-side, settlement, recipient and partial-fill sentencesMissing correctness for passive named recipients — finding aboveUnattached amounts require clarification instead of zeroMet — composer consistency testsWritten “payable to IMD’s treasury” reaches deployer and footerMet — job-9 testsSpelled thresholds cannot substitute for a missing fee rateMet — job-9 testsApply the combined 5% cap per directionMet — composer and consistency testsFetch the specified proven index at load; never bundle itMet — proven.ts, ProvenLaunches.tsxFailed index fetch means no proven launchesMet — unit and browser fallback testsMatch type, block-id set and chain; allow parameters, words and Custom ruleMet — matching testsApply matches automatically in the backgroundMet — useProvenSource, rendered summaryShow the exact provenance line in the summaryMet — browser testsCarry the same provenance onto the hook pageMet — Hook browser testsAdvanced own repository overrides matching; no additional controlMet — browser override testCarry entry repoUrl and baseCommitMet — composer testsResolve proven source through relay /import firstMet — mocked import testsFailed import or absent relay silently composes from scratchMet — fallback tests at all three widthsInsert the specified audited-source instruction after the first sentenceMet — composer and revision testsRetain other composed request sentencesMet — fresh/proven output comparisonShow the exact wait estimate in Builder and LaunchMet — both rendered surfacesOffer Copy linkMet — actual clipboard browser assertionAsk once abo

---

I reproduced the reported bug, fixed it, and wrote the answer to .imd-responses.json with the verdict "fixed".
What was wrong: the fee-destination reader in src/lib/writtenFees.ts didn't treat "The owner is paid 1% of every swap." as naming a destination. With an owner different from the paying wallet, the request named the owner as owner but named the payer as fee recipient, in both the deployer sentence and the fee footer. Neither check caught it. "The owner gets 1%…" and "The owner takes 1%…" failed the same way.
The fix: when a known destination (the owner, my wallet, the treasury or a full address) is followed by a payment verb, it now counts as the written destination. That covers passive forms like "is paid", "is credited" or "is owed" and active ones like "receives", "gets", "earns", "takes", "keeps" or "collects". The existing code already turns "the owner" into the owner's address, so the deployer sentence and the footer now both name the owner. If the payee has no address, as in "Alice is paid 1% of every swap.", the request is refused with a "recipient" finding rather than quietly paying the wallet. Sentences like "The fee is paid in ETH." still don't name anyone.
Tests added in tests/job9-revision.test.mjs:

Four owner-payee wordings across launch types A, B and C, using different payer and owner addresses.
The unknown-payee case, which must be refused.

Results, recorded in tests/results/job9/revision/:
CheckResultTypecheck and production buildpassed (the old large-chunk warning is still there)Unit tests1,155 of 1,155 passedPlaywright234 passed, 7 optional skipsThe real launchBody()owner in both fee-recipient spots; refuses the "Alice" promptExport integritycomplete metadata, no missing or absolute asset links8 MiB bundle budgetpassed, about 600 KB to spare
The screens didn't change, so I didn't rerun the design probe. dist/ was rebuilt; only the bundle's file name changed.
Things to know:

The reorg tests in tests/chain.test.mjs sometimes miss their 1-second timing window on this machine, with or without my change. In about half of full runs one of the four fails; they passed in the recorded run. I noted this in tests/results/job9/REVIEW.md and left those tests alone.
I installed dependencies and the Playwright browser locally to run the checks. Running Playwright overwrote screenshots from earlier jobs, so I restored them, and I deleted web/node_modules afterwards.
I haven't committed anything.

Not delivered: artifacts/builder-1440.png, artifacts/builder-320.png, artifacts/builder-390.png, artifacts/cast-frames.json, artifacts/hook-1440.png, artifacts/hook-320.png, artifacts/hook-390.png, artifacts/hook-manage-1440.png and 11 more. Under artifacts/, only this step's named outputs leave the machine.

---

Your earlier high finding is mostly fixed. It still fails in one case, so I've kept it open as one high finding in .imd-findings.json. I changed no other file.
AreaThis roundBrief requirements (met / missing / faked)Only carry-over (b), "the recipient named in words flows into both", re-checked: still missing for one kind of wording (below)Broken features1 (the payee issue below)Product on the first screen at 390Not re-measured; this round only settles the composer findingtaste@1 checks passedProbe not re-run this roundCopy findings0 newShare cardNot re-checked
What the fix gets right. I re-ran your reproduction: draft type B, owner 0x9a50…0ab0, paying wallet 0x6cba…8a34. The deployer constructor and the Fee recipient: footer now both name the owner when the prompt says:

"The owner is paid 1% of every swap."
"The owner gets 1% of every swap."
"The owner will be paid 1% of every swap."
"The owner is credited 1% of each trade."

Types A and B give no findings. Type C only asks for the existing token, as it should. In type A the paying wallet still appears, but only as the token's remaining-supply recipient, which is by design. "Alice is paid 1% of every swap." and "1% of every swap goes to Bob." now raise recipient, and launchBody() in web/src/chain/launch.ts refuses the request. tests/job9-revision.test.mjs passes 10 of 10.
Why it doesn't fully hold (src/lib/writtenFees.ts:138). The new rule only catches an unknown payee followed by "is paid / credited / owed / given / sent". An unknown payee followed by "receives", "gets" or "earns" still defaults to the paying wallet, with no finding. For "Alice receives 1% of every swap.":

The body quotes the creator's words: <description>Alice receives 1% of every swap.</description>.
The same body also says $owner and the fee recipient 0x6cba4751742f6989fa224b2dc5d5d52fcef98a34 and Fee recipient: 0x6cba4751742f6989fa224b2dc5d5d52fcef98a34.
validate() and checkConsistency() both return nothing, so the payment gate lets it through.

"The marketing wallet receives…", "Bob earns…" and "The dev fund gets 1% of every swap." behave the same way. A builder reading this request would have to guess who gets paid. That is the half of the original finding that asked for "require recipient clarification rather than defaulting to the payer".
Fix: extend passivePayee's verb group to also accept receives? | accrues? | gets? | earns? | keeps? | collects?. The existing notPayee filter already excludes fee words, traders and "it/them". Then add those four prompts to the revision test.
I reported nothing else new.

---

I found four defects, ranked below. The most serious is that the proven-launch feature (SPEC 4.17) never turns on against the real relay, even though every test passes. The findings are written to .imd-findings.json, and no project files were changed.


High: the proven-launch import always fails in production (web/src/relay.ts:58). IMD's /import sends back the repository URL with .git on the end. importProvenSource requires the returned URL to match the entry's URL exactly.

I confirmed this with a live /import call for launch 2424 (PondsideGuard), the same read-only call the site makes. It returned …-pondsideguard.git, and the function returned null when given that exact response. The job 5 evidence shows the same .git behaviour.
Effect: a draft with exactly the proven block set is always composed from scratch. There is no "Built from a proven launch" line, no repoUrl/baseCommit in the body, and no "Start from the audited source" sentence.
The tests miss this because both the Playwright and unit mocks send the requested URL straight back instead of IMD's real response.



Medium: the written-fee detector still writes a 0% fee for some amounts (src/lib/writtenFees.ts:83). These three descriptions each produce Hook fee rate: 0%, with no fee sentences and no finding from either check:

1/100 of every swap goes to the owner.
1 pct of every swap goes to the owner.
One in every hundred tokens traded goes to the owner.



Low: Type A drafts can only match an entry that also lists the token block (src/lib/proven.ts:32). The only published entry lists behaviour blocks alone. If the owner adds a Type A entry the same way, no Type A draft can ever match it. No Type A entry exists yet, so the open question is which format entries should use.


Low: notifications go out for other people's launches (web/src/LaunchNotifications.tsx:16). After a visitor grants permission once, every in-progress hook page they open is added to the watch list. They then get "Your launch is confirmed" for launches they only browsed.


What I checked and found correct:

Owner and address lowercasing: a checksummed wallet, owner or remainder comes out lowercase in the body and the text. The consistency check refuses mixed case anywhere in the body and refuses an empty owner.
Composed text with a proven launch: the "Start from the audited source" sentence sits right after the first sentence, the rest of the text is kept, and both checks pass.
Which drafts match: changing the chain or adding a block removes the match, and the creator's own repository overrides it.
Brief's fee examples: the phrasings listed in the brief now produce fee intent, or a clarification finding where no rate can be attached. This includes "toll", "commission", "accrues", the spelled thresholds and "payable to IMD's treasury" (the treasury flows into both the deployer sentence and the footer).
5% cap: it is applied per direction. For example, a 5% buy fee from a block plus a written 1% sell fee is allowed.
Live reading for contracts-only launches: it matches the real relay record for launch 2424. The deployer is recognised by its name, and a zero hook() gives "hook not deployed yet".

Not covered:

I did not open the site in a browser, so the 320/390/1440 layouts are unchecked.
The live SPEC.md upstream is now version 1.37, ahead of the 1.34 the task names. I did not compare the two.
