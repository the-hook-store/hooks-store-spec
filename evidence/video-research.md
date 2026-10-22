# Promo video research (2026-10-22)

IMD sells video as an ordinary job: `job.open@job-1` with `skill: create-video` and named `outputs` (0.5 IMD once; "Images, video and audio: any model with an image, video or audio tool"). Three completed examples, pulled from the explorer and the API:

| Job | Brief | Output | Time from payment |
|---|---|---|---|
| a308c304 (OG explainer) | 30 s, pixel-art, project's own on-chain art only, on-screen text per 4-7 s beat, no voiceover | 1920×1080, 15 fps, H.264 + AAC, 30.0 s, 654 KB | 3 min |
| a5c1da37 (pepe2pepe promo) | 38-42 s, creative direction, brand sources, a timed storyboard, guardrails, no narration | 1920×1080, 30 fps, 40.0 s, 2.1 MB + 1920×1080 poster | 13 min |
| ab959afd ("video that best represent imd") | one line | 1280×720, 24 fps, 20 s, 1.3 MB | 8 min |

What they look like (frames in video-example-*-frames.png): motion-graphics explainers built from the project's brand assets, typed captions, diagrams, counting numbers, light music; not generated live-action footage. A separate "raw footage pack" job (43f063f9) asked for image-to-video photoreal clips and got eleven 4-5 s vertical clips in 55 minutes, which shows the workers also have generative video models when a brief asks for them.

Our brief (jobs/video-1-promo.json) follows the pepe2pepe shape: creative direction, brand and sources, a timed storyboard, guardrails, named outputs (artifacts/hooks-store-promo.mp4, artifacts/poster.png). Free check 2026-10-22: zero blockers, plan "Make the video" (create-video), facts subject, style, length and words all stated (evidence/check-video-1.*).

Outside IMD (for reference only): Google Veo 3.1, Runway Gen-4.5 and Kling 3.0 make generated footage from text or stills on monthly plans, with watermarks on cheap tiers; Sora was shut down in 2026. None is needed for a motion-graphics promo of a user interface.
