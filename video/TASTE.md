# TASTE – StackCheck Launch Video
<!--
  TASTE MEMORY of this motion-graphics project. Written and kept up to date by the AI agent.
  PURPOSE: a brand-new chat (any agent, any model) must be able to read ONLY this file
  (+ PROGRESS.md) and continue making scenes that look, move and sound exactly like the
  approved ones — same theme, same concept, same design system, same feel.
-->
Updated: 2026-10-18 21:15 · by: Antigravity Motion Director · current version: draft
Status of this file: draft (awaiting VO & plan approval)
Visual version for the user: plan/design.html

## 1. Brief, concept & story (what we are making and why)
- **One-line concept:** "From raw job postings to razor-sharp market telemetry: how top engineers and analysts benchmark tech demand, salaries, and skill pairings with StackCheck."
- **Video type / platform / format:** SaaS Product Launch Teaser, 16:9 1920×1080, 30 fps, 30 s duration
- **Audience & goal / CTA:** Software engineers, engineering managers, tech recruiters, and analysts. Goal: demonstrate authority, data depth, and local ease-of-use; CTA: "Run in seconds. Free on GitHub."
- **Brand inputs:** Official StackCheck 3-strata logo, dashboard screenshots, obsidian slate dark canvas. Assets in `video/assets/brand/` and `video/assets/screenshots/`.
- **Narrative structure:**
  - 0.0s – 4.5s: Hook — What skills are actually paying right now?
  - 4.5s – 8.5s: Problem — Stop guessing from hype and biased surveys.
  - 8.5s – 14.5s: Reveal — Meet StackCheck (3-strata monogram build + 3D floating executive dashboard).
  - 14.5s – 21.0s: Feature Showcase — Telemetry depth (Compensation curves & skill pairing graph).
  - 21.0s – 25.5s: Local / Privacy — Zero cloud bloat. One command standalone binary.
  - 25.5s – 30.0s: Outro & CTA — Hero lockup, GitHub URL, live command.
- **Pipeline:** Pipeline A/B Hybrid (Code-drawn Canvas/WebGL 2D & 3D cards + authentic UI screenshots + kinetic typography).

## 2. Theme & feel (the "sense" of the video)
- **Mood words (4):** Precision · Authoritative · High-Velocity · Modern-SaaS
- **Theme / visual world:** Obsidian dark canvas (`#0B0F19` to `#0F172A`) illuminated by vivid cyan-to-azure strata glows (`#38BDF8`, `#0EA5E9`, `#0284C7`), subtle grid lines (40px grid), floating 3D glass cards, and crisp micro-animations.
- **Intensity level:** 3.5 (Linear/Raycast aesthetic — rhythmic, tight, high craft without sensory overload).
- **Feels like (references):** Recipe C (SaaS Product Launch, Slack/Linear style) with Recipe D kinetic precision.
- **Must NOT feel like:** Slow enterprise slideshow, cheesy 3D corporate template, generic AI video slop.

## 3. Visual design system
- **Palette (hex + role, 60-30-10):**
  - Background (60%): Obsidian Slate (`#0B0F19` base, `#0F172A` cards)
  - Primary / Text (30%): Crisp White (`#F8FAFC`), Slate Gray (`#94A3B8`), Border Slate (`#1E293B`)
  - Accent / Hero (10%): Stratum Sky Cyan (`#38BDF8`), Cobalt Sky (`#0EA5E9`), Deep Azure (`#0284C7`)
- **Typography:**
  - Display / Hero: Inter / SF Pro Display, 800 ExtraBold, sizes: 64px to 84px
  - Subheadings / UI: Inter, 500 Medium / 600 SemiBold, 28px to 36px
  - Telemetry / Code: JetBrains Mono / SF Mono, 600 SemiBold, 24px to 32px
- **Text treatment:** Crisp white fill with subtle negative tracking (-0.03em), cyan accent highlights on key action verbs and telemetry numbers.
- **Layout:** 1920×1080 canvas, 120px safe area margins on all sides. Center-weighted visual balance with floating perspective cards angled at rotateY(-8deg) to rotateY(8deg).
- **Textures & finish:** 2.5% subtle film noise, faint cyan radial vignette (blur 180px, opacity 0.15), 1px border glows (`rgba(56, 189, 248, 0.25)`).

## 4. Motion language
- **Easing family:**
  - Entrances: `easeOutCubic` / `easeOutExpo` (duration 350ms - 500ms)
  - Exits: `easeInCubic` (duration 250ms)
  - Card float: Gentle sine wave hover (period 4.0s, amplitude 6px)
- **Text animation:** Word-staggered cascade (stagger 45ms), blur-to-sharp (12px blur -> 0px), scale overshoot (1.06 -> 1.00).
- **Signature devices:**
  - 3-strata logo assembly: 3 horizontal bars slide into place with precision 45-degree chamfer reveals.
  - Floating 3D tilt cards: Dashboard screenshots housed in rounded dark glass cards (`border-radius: 16px`, `box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7)`).
  - Telemetry pulse: Glowing cyan data points expand along graph coordinates on the spoken beat.
- **Transitions:** Fast directional whip-push (200ms) and cinematic hard cuts precisely matched to VO phrase boundaries.

## 5. Sound identity
- **Text SFX:** Clean, dry acoustic clicks and mechanical micro-ticks (40ms - 90ms) on text reveals.
- **Hero / impact sounds:** Low sub-bass hit (-9 dB) on "StackCheck" logo lockup, followed by an airy riser.
- **Telemetry SFX:** Subtle digital data chirp / high-frequency chime on graph node connections.
- **Music:** Sleek, driving electronic minimal tech bed (~110-120 BPM), ducked -12 dB under voiceover.
- **Mix targets:** SFX 6–10 dB under VO; Voiceover at -14 LUFS integrated, True Peak ≤ -1.5 dBTP.
- **Banned sounds:** Long cartoony whooshes, arcade laser bleeps, cheesy corporate acoustic guitar.

## 6. Voice
- **VO Profile:** Confident, articulate, modern tech narrator (American/Neutral, crisp and dynamic).
- **ElevenLabs Model:** Eleven v3 or Eleven v4
- **Recommended Voice:** "Adam" (Deep, authoritative American) or "Brian" (Crisp, technical narrator) or "Rachel" (Direct, clear tech founder).
- **Settings:** Stability 45%, Similarity 75%, Style 15%, Speed 1.0.

## 7. Technical setup
- **Render engine:** Deterministic Canvas 2D/WebGL rendering with Playwright frame stepping + FFmpeg mux.
- **Directory:** `video/`
- **Preview command:** `node ../scripts/preview.mjs <from> <to> --name "StackCheck Launch" --version 1`
- **Render contract:** `node src/render.js --from <start> --to <end> --fps 30 --scale 1 --out renders/previews`

## 8. Do / Don't
- **DO:** Keep text concise, impactful, and synchronized to the millisecond with VO cues.
- **DO:** Let actual dashboard data (real salaries, real skill percentages) take the spotlight.
- **DON'T:** Use low-contrast text or illegible small fonts (< 22px).
- **DON'T:** Overcrowd scenes; every frame must have a clear visual hierarchy.

## 9. Feedback rules log (append-only)
| Date | Version | User said | Rule we keep from now on |
|---|---|---|---|
| 2026-10-18 | v1 | Preferred 16:9, 30s duration, narrated voiceover, Modern SaaS style | Strict 30s duration, 16:9 1920x1080 canvas, Linear/SaaS aesthetic |

## 10. Decision history
- 2026-10-18 · v1 · Initialized StackCheck launch video configuration based on user intake.
