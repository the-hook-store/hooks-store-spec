# Promo cut 4 (2026-10-23)

Fourth cut of the Hooks Store promo: 52 s, 1920×1080, 24 fps. Built from screenshots of the live store (taken 2026-10-23 00:45 UTC in a clean headless Chrome, 2× resolution) placed in hard-edged frames with zooms, gold callouts and Press Start 2P captions, cut on the bars of the track.

## Music

"Take this Higher" by Michael Ramir C., Mixkit track 1012 (https://mixkit.co/free-stock-music/tag/edm/), under the Mixkit Stock Music Free License, which allows free use in commercial and non-commercial projects, social media video posts, online marketing ads and YouTube videos, with no attribution required. Not allowed: CDs/DVDs, TV or radio broadcast, video games, remixing into a music-only track. The cut uses the track from 17.84 s to 70.19 s with a 2 s fade. The track runs at 124 BPM; bars in the cut start at 1.524 s and repeat every 1.935 s. Its two bass drops land at 11.20 s and 34.42 s of the video.

Alternates with the same build-and-drop shape, from the same catalogue: "Razor Edge" (1280, drops at 32.4 s, 56.1 s and 87.3 s of the track), "Night Terrors" (334, one big drop at 59.5 s), "Trap Electro Vibes" (126, drum and bass). Swapping the track means re-timing the bar grid in `cut-4-animatic.html` (constants `B0`, `BAR`, `BEAT` and the two `DROPS`).

## Scenes (video time)

| Bar | Start | Scene |
|---|---|---|
| – | 0.00 | Cold open: the pond creature on the real landing page, "Casting" box |
| 0 | 1.52 | Title "The Hooks Store", one word per beat |
| 1 | 3.46 | "Hooks are code." |
| 2 | 5.39 | "You don't have to write it." with three details popping on the beats: a block card, the LIVE pill, "0.5 IMD once" |
| 3 | 7.33 | Landing: the question typed into the real input, zoom onto Describe it during the silence before the drop |
| 5 | 11.20 | Drop 1, flash: the Builder slams in. "Describe it. Or stack blocks." |
| 6 | 13.13 | Shelf, Protection tab: cursor to Add, click on beat 2, card turns ADDED. "52 reviewed blocks. One click each." |
| 7 | 15.07 | The stack of numbered rules. "Every block is an exact rule." |
| 8 | 17.01 | The hook card. "Your hook, as it stands." |
| 9 | 18.94 | The exact-text sheet scrolling. "The swarm gets the exact text." |
| 10 | 20.88 | Findings "Fix before paying · 3", then "Nothing to fix" on beat 2. "Checked before you pay." |
| 11 | 22.81 | Settings with Robinhood Chain chosen. "Robinhood Chain or Ethereum." |
| 12 | 24.75 | Launch review, "What you pay". "Pay 0.5 IMD. Once." |
| 13 | 26.68 | Breakdown: "Written. Tested. Audited. Then deployed." over the real five-step progress bar, highlight sweeping; stats 30–90 minutes, ×4 audits |
| 16 | 32.49 | Riser: "Then it's live." over the hook page rushing in |
| 17 | 34.42 | Drop 2, flash: the hook page, LIVE pill. "Live. On its own page." |
| 18 | 36.36 | Addresses. "Real addresses, read from chain." |
| 19 | 38.29 | Owner controls. "Pause. Resume. Claim fees. Yours." |
| 20 | 40.23 | Open the pool. "Open the pool right there." |
| 21 | 42.16 | My hooks. "All your hooks. One place." |
| 22 | 44.10 | Promotions: deposit typed, cursor to Promote. "Promote it. 0.1 IMD a day." |
| 23 | 46.03 | Featured band with the live placement. "Featured on the store." |
| 24 | 47.97 | Catalog with PROVEN pills. "Proven launches make the next one faster." |
| 25 | 49.90 | Close: pond, "Cast yours.", the URL; music fades |

## Files

- `promo/hooks-store-promo-cut-4.mp4` on the owner's Mac (27 MB; not in this repo).
- `promo/cut-4-animatic.html` here: the cut itself, driven by a master clock; the screenshots it references are not committed (20 MB). The browser version with images: see the artifact link in `jobs/log.md`.
- Render: `cdp-render4.mjs` (headless Chrome, one screenshot per frame) then ffmpeg with the trimmed track.

## Noticed while capturing

- On a cold load the catalog shows "In progress" on live hooks for 10 to 30 seconds while the hook-code verification and placement reads finish; the hook page and My hooks say Live sooner. After 35 s everything read Live and Proven. Candidate for job 14: a "checking…" state instead of "In progress" until the first verification completes.
- With the stand-in wallet, My hooks showed "Could not finish reading Robinhood Chain. Showing what is cached." once (the public RPC rate limit); cropped out of the shot.
