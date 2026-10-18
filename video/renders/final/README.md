# StackCheck — Official Launch Video (v1)

## Master Deliverables
- **Video File:** `StackCheck Launch - Final v1.mp4`
- **Resolution:** 1920×1080 (16:9 Full HD)
- **Framerate:** 30.0 fps progressive
- **Duration:** 31.0 seconds
- **Video Codec:** H.264 (High Profile, YUV420p, CRF 18, Bitrate ~1.3 Mbps)
- **Audio Codec:** AAC 48 kHz mono @ 192 kbps
- **Integrated Loudness:** -19.3 LUFS (True Peak -1.5 dBFS)

## Production Stills
- `still_01_hook.png`: Scene 1 Kinetic Question Hook
- `still_02_reveal.png`: Scene 3 3-Strata Monogram & Executive Dashboard Card
- `still_03_telemetry.png`: Scene 4 Dual Telemetry (Salary Percentiles & Skill Pairings)
- `still_04_outro.png`: Scene 6 Hero Logo, Badges & GitHub CTA

## Narrative Structure & Sound Design
1. **0.0s – 4.1s (The Hook):** Kinetic text stagger with Sky Cyan focus on engineering demand.
2. **4.1s – 8.1s (The Problem):** Unverified buzzword noise shatters into clean dark space.
3. **8.1s – 15.2s (The Reveal):** Architectural 3-strata monogram build with 45° chamfers + floating 3D Executive Dashboard card.
4. **15.2s – 22.5s (Deep Telemetry):** Dual-card perspective with live compensation percentiles and skill co-occurrence network graphs.
5. **22.5s – 27.8s (Local Privacy):** Terminal HUD drop-in with `$ stackcheck` and instant green SQLite and live feed checks.
6. **27.8s – 31.0s (Outro & CTA):** Centered StackCheck hero lockup with glowing radial stratum aura and GitHub link.

## Source Code & Reproducibility
- **Project Memory:** `video/TASTE.md`
- **Timing & Beats:** `video/plan/beats.json`
- **Scenes Source:** `video/src/scenes/`
- **Audio Mix:** `video/assets/audio_mix.wav`
- **Re-render Command:**
  ```bash
  node src/render.js --from 0 --to 31 --fps 30 --scale 1 --out renders/final --name "StackCheck Launch - Final v1" --audio assets/audio_mix.wav
  ```
