# Storyboard – StackCheck Launch Video (v1)

## Shot-by-Shot Beat Sheet (30.0s Total)

### Shot 1: The Hook (0.0s – 4.5s)
- **Time:** 0.0s – 4.5s (Duration: 4.5s)
- **VO Line:** "What tech skills are engineering teams actually hiring for right now?"
- **On-Screen Text:** `WHAT TECH SKILLS` / `ARE ENGINEERING TEAMS` / `ACTUALLY HIRING FOR?`
- **Visual:** Obsidian dark background with subtle 40px engineering grid. Soft cyan radial light pool behind text.
- **Motion:** Staggered line entrance (blur 16px -> 0px, y +25px -> 0px, easeOutCubic 400ms). "ACTUALLY HIRING FOR?" scales up with 1.08x overshoot in Stratum Sky Cyan (`#38BDF8`).
- **Transition:** Quick directional blur push (180ms) into Shot 2.
- **SFX:** Soft mechanical key/tick on each word entrance; subtle rising airy whoosh into transition.

---

### Shot 2: The Problem – Market Noise (4.5s – 8.5s)
- **Time:** 4.5s – 8.5s (Duration: 4.0s)
- **VO Line:** "Stop guessing from hype cycles and outdated salary surveys."
- **On-Screen Text:** `HYPE CYCLES` / `BIASED SURVEYS` / `UNVERIFIED STATS`
- **Visual:** Floating translucent tags and red/amber jitter badges randomly adrift in dark space.
- **Motion:** Jittery micro-shake (amp 2px), then an inward gravitational collapse and rapid radial shatter outward as the screen cleanses back to dark obsidian.
- **Transition:** Hard cut on the downbeat of "Meet StackCheck".
- **SFX:** Muffled static hiss; sudden high-pass glitch cut on the shatter; micro sub-drop.

---

### Shot 3: The Reveal – StackCheck & Executive Dashboard (8.5s – 14.5s)
- **Time:** 8.5s – 14.5s (Duration: 6.0s)
- **VO Line:** "Meet StackCheck. The open-source market intelligence engine that turns live job posts into instant competitive insight."
- **On-Screen Text:** `StackCheck` / `MARKET INTELLIGENCE ENGINE`
- **Visual:**
  - 3 horizontal strata monogram tiles (Sky Cyan `#38BDF8`, Cobalt `#0EA5E9`, Azure `#0284C7`) slide in from left with precision 45° chamfer reveals.
  - Wordmark `StackCheck` locks beside the emblem.
  - An isometric 3D card carrying the **Executive Market Overview** dashboard glides into the right half of the frame with a cyan rim light.
- **Motion:** Logo constructs over 450ms (`easeOutExpo`). Dashboard card glides from `scale(0.85)` / `rotateY(14deg)` to `scale(1.0)` / `rotateY(-4deg)` with continuous subtle sine hover.
- **Transition:** Whip-pan right into Shot 4.
- **SFX:** Clean sub-bass impact (-9 dB) on the logo lockup; mechanical snap on monogram settle; glassy swoosh on card arrival.

---

### Shot 4: Deep Telemetry – Compensation & Skill Co-Occurrence (14.5s – 21.0s)
- **Time:** 14.5s – 21.0s (Duration: 6.5s)
- **VO Line:** "Analyze framework dominance, uncover lucrative skill pairings, and benchmark compensation curves across global markets."
- **On-Screen Text:** `REAL-TIME SALARIES` / `SKILL CO-OCCURRENCE` / `CROSS-CORRELATED`
- **Visual:**
  - Split dual-card perspective:
    - **Card A (Left, angled +5°):** Geographic Compensation distribution showing live salary bands ($140k - $240k percentiles).
    - **Card B (Right, angled -5°):** Skill Pairing explorer with glowing neon graph nodes connecting Python, AWS, PostgreSQL, Docker, and Kubernetes.
- **Motion:** Left card enters first (+120ms), right card follows (+240ms). Cyan vector lines between skill nodes draw from source to target. Animated counters tally salary percentiles.
- **Transition:** Vertical tilt down (camera push) into terminal space.
- **SFX:** Dual data chirp; ascending frequency arpeggio as vectors connect; subtle digital chime.

---

### Shot 5: Privacy & Local Execution (21.0s – 25.5s)
- **Time:** 21.0s – 25.5s (Duration: 4.5s)
- **VO Line:** "Zero cloud dependencies. Run the interactive dashboard locally in one command."
- **On-Screen Text:** `ZERO CLOUD` / `100% LOCAL & PRIVATE` / `$ stackcheck`
- **Visual:** Sleek dark glass terminal HUD with glowing cyan top border. Fast terminal stream:
  ```bash
  $ curl -fsSL https://stackcheck.dev/install.sh | bash
  $ stackcheck
  [✓] Local SQLite Engine Loaded
  [✓] 1,420 Live Posts Processed
  [✓] UI Running on http://localhost:8501
  ```
- **Motion:** Terminal snaps down with rubber-band overshoot. Command types out at 30ms/char. Green checkmark badges pop in sequentially (100ms stagger).
- **Transition:** Fast lens zoom-out into hero lockup.
- **SFX:** Rapid mechanical keyboard typing clatter; two sharp success confirmation blips.

---

### Shot 6: Outro & Call to Action (25.5s – 30.0s)
- **Time:** 25.5s – 30.0s (Duration: 4.5s)
- **VO Line:** "Check your stack today. Download free on GitHub."
- **On-Screen Text:**
  - `StackCheck`
  - `TECH STACK MARKET INTELLIGENCE`
  - `github.com/haydermuhib/StackCheck`
- **Visual:**
  - Centered StackCheck horizontal brand lockup.
  - Soft pulsating cyan stratum glow ring behind the emblem.
  - Three pill badges below: `[ Python 3.10+ ]` `[ MIT Licensed ]` `[ Standalone Binary ]`
  - Large glowing CTA button with GitHub icon: `github.com/haydermuhib/StackCheck`
- **Motion:** Logo scales smoothly from 0.94x to 1.0x. Badges pop with 60ms stagger. Subtle light-sweep sheen across the CTA button.
- **Transition:** Slow gentle fade to obsidian black at 29.8s.
- **SFX:** Resonant harmonic outro chord; soft breath out; gentle tail decay.
