# Job 7 notes (explorer, 2026-10-21)

### build_website
Implemented job 7 and all carry-over fixes. Source, dist/, SPEC 1.25, documentation and test results are complete.
Passed: build/typecheck, 495 unit tests, nine relay tests, 160 browser tests, and both live checks. Seven optional browser cases skipped. Bundle: 6.08 MB; protected files unchanged.
Results and limitations.


### design_critic
AreaResult
Requirements22 met; 6 missing; 0 faked
Broken features6 bugs: 5 high, 1 medium
First screen, 390pxProduct and main action visible
taste@113/16 passed
Copy0 findings
Share cardPresent; image returns HTTP 200
Revision needed. Six verified findings, with exact fixes, inputs and source citations, are recorded in .imd-findings.json:
- High — bug: conflicting catalog rules pass the consistency gate.
- High — bug: “paid in ETH” bypasses the IMD settlement guard.
- High — bug: a payee address satisfies a missing service-address check.
- High — bug: “Send swap fees to Bob” passes without an address.
- High — bug: a conflicting fixed pool allocation leaves continuation unlocked.
- Medium — bug: the supplied Buy back and burn example is rejected as contradicting itself.
Explicit requirementStatusEvidence
Pair currency in Swap fee, Different buy/sell fees, Whale fee, Volatility fee, Buyback jar, Prize pot, Fee that fades and other fee clausesMetcatalog.json, compose.ts
IMD conversion and other-pool opt-outMetIMD_FEE_OPT_OUT, composer
“My wallet” becomes the paying addressMetcontext()
IMD’s treasury label and exact supplied addressMetCatalog options, IMD_TREASURY
Updated composer fixturesMettests/fixtures/compose-{A,B,C}.txt
Composer tests for every block, type and pairingMettests/safety.test.mjs
Consistency check before free check and LaunchMetuseSwarmCheck.ts, chain/launch.ts
Red notice names offending sentencesMetSafetyNotice.tsx; recognized failures
Reject mismatched fee side or settlementMissingFinding 2
Reject recipients without addressesMissingFinding 4
Reject dependencies without deploy-chain addressesMissingFinding 3
Reject contradictory rulesMissingFinding 1
Unit-test consistency on every composed block/type/pairingMet420-case matrix
Show conflicting fixed facts and lock until explicit opt-outMissingFinding 5
Blocked question under Needs attention, through relay GET /jobs/:id, using both reason fieldsMetRelayTimeline.tsx, relay.ts; live blocked launch
Fix in Builder restores draft with question beside itMetHook.tsx, draft.ts, Builder.tsx
Preserve original request for corrected relaunchMetSubmitted-draft archive and previous-request disclosure
Known questions become checker rulesMetknown-questions.json, safety.ts
First known question records launch 2’s conversion-pool problemMetFirst JSON entry
Fee table and Launch page explain stopped requests spend the fee and checks make that rareMetLaunchReview.tsx
Remove hat; retain far boat and birdsMetsrc/scene/pond.ts
Confirmed cancelled Launch fails with working retryMetCancellation browser test
Confirmed replaced Launch fails with working retryMetReplacement browser test
Reorg removes ticker announcement and ageMetLanding.tsx; reorg browser test
SPEC refreshed to 1.25MetSPEC.md:3
Preserve remaining job-6 behaviorMissingFinding 6 introduces an example regression
Deliver source and dist/MetBoth present; export exercised
Job-7 unit, relay, all-route width and live-RPC resultsMettests/results/job7/
The visual idea remains coherent: a Uniswap v4 hook storefront carried by a monochrome fishing pond and pixel interface. The three remaining probe flags follow that specified style.
Independent checks passed: 495 unit tests, nine relay tests, 39 job-7 Chromium tests, and all 21 route-width layouts. Live RPC reads settled in 1.7 seconds. WebKit could not launch. No real transaction was sent; implementation files remain unchanged


### build_website
Fixed all six findings, rebuilt dist/, and wrote .imd-responses.json.
Validation passed: 643 unit tests, 9 relay tests and 188 browser cases; seven optional cases skipped. Live RPC settled in 8.9 seconds. Bundle remains below 8 MiB.
Results and limitations.


### design_critic
AreaResult
Requirements30 met; 0 missing; 0 faked
Broken features0; all six previous findings resolved
First screen, 390pxProduct and main action visible
taste@113/16; three required pixel-style exceptions
Copy0 findings
Share cardPresent
Saved .imd-findings.json as {"findings":[]}. Source and export remain unchanged.
Each previous finding is fixed:
Previous findingVerified result
Conflicting catalog rulesBoth reported pairs quote their conflicts and lock Check and Launch; removing either rule restores continuation.
“Paid in ETH” bypassRejected for IMD pairing; matching currency passes.
Payout address satisfying a service dependencyVRF with an unrelated payee and the unaddressed pricing pool remain blocked.
Named fee recipient“Send swap fees to Bob” and “fees go to Bob” are rejected; addressed equivalents pass.
Fixed token allocation conflictRecorded 50% fact conflicts with 65%, survives reload, and requires explicit opt-out plus recheck.
Buy back and burn examplePasses with sell-only fees; same-direction contradictions remain blocked.
Requirement coverage:
RequirementStatus and evidence
Named fee blocks use pair currency for side and settlementMet — src/blocks/catalog.json; composed matrix
Other ETH-side/settlement sentences follow pairingMet — catalog templates and composer
IMD request forbids conversion and other poolsMet — compose.ts, IMD_FEE_OPT_OUT
“My wallet” becomes the paying addressMet — composer and wallet browser case
“IMD’s treasury” writes the supplied addressMet — IMD_TREASURY; recipient tests
Update fixturesMet — composer fixture comparisons
Composer tests cover every block/type/pairingMet — compose.test.mjs, safety.test.mjs
Check consistency before free checkMet — useSwarmCheck.ts, relay.ts
Check consistency before LaunchMet — launch serializer and signing guard
Wrong fee side produces quoted red lockMet — SafetyNotice; browser cases
Wrong settlement produces quoted red lockMet — settlement regressions
Unresolved recipients lock continuationMet — recipient regressions
Unaddressed dependencies lock continuationMet — service/pool tests and disabled Yield
Contradictory rules lock continuationMet — pairwise regressions and recovery
Safety tests inspect every composed block/type/pairingMet — 420-case block matrix
Conflicting fixed facts appear in understood panelMet — SwarmPanel.tsx; allocation regression
Conflict remains locked until explicit opt-out/recheckMet — navigation, stale-result and reload cases
Composer supplies IMD opt-out automaticallyMet — composer matrix
Blocked question appears under Needs attentionMet — blocked Hook browser cases
Relay reads both reported question fieldsMet — RelayTimeline.tsx, jobAttention()
Fix in Builder restores draft/question and preserves requestMet — saved and reconstructed draft cases
Known questions apply launch 2’s conversion ruleMet — known-questions.json; rule tests
Fee table explains stopped requests spend the feeMet — LaunchReview.tsx fee table
Launch page explains purpose of checksMet — Check before paying panel
Remove hat; retain distant boat and birdsMet — pond.ts; scene regressions
Cancelled/replaced launch has working retryMet — receipt replacement browser cases
Reorg removes ticker announcement and ageMet — reorg regression, including another minute
Refresh SPEC to 1.25Met — SPEC.md
Preserve job 6 behaviorMet — full regression suite
Deliver source, dist and requested test resultsMet — dist/, tests/results/job7/; all routes at three widths
Independent checks pass
