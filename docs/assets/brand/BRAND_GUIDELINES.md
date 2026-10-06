# StackCheck: Brand Guidelines

## 1. Logo and core concept
- **Concept:** An architectural monogram sculpted from three horizontal tech strata with precision 45-degree chamfered cuts. It reflects the three primary layers of modern software stacks (presentation, analytics, and infrastructure).
- **Master Symbol:** Integer geometry on a 256x256 grid without text dependencies.
- **Variants:**
  - **Transparent horizontal lockups (`logo.svg`, `logo-light.svg`, `logo.png`):** Transparent horizontal mark and wordmark without container backgrounds, suitable for dark and light surfaces.
  - **Transparent app icon and favicon (`icon.svg`, `icon.png`, `icon.ico`):** Standalone Strata S symbol in 3-tier blue progression on a transparent canvas for browser tabs, desktop taskbars, and dashboard icons.
  - **Tile and squircle card versions (`stackcheck-app-icon.svg`, `stackcheck-card-logo.svg`):** Boxed versions on obsidian slate (`#0F172A`) tiles.
  - **Monochrome:** Black (`stackcheck-symbol-black.svg`), white (`stackcheck-symbol-white.svg`), and brand cobalt (`stackcheck-symbol-mono.svg`).

---

## 2. Clear space
Keep a clear exclusion zone of at least 1x around the logo on all sides, where X equals the thickness of a single stratum tier (40 px on the 256 grid). No text, borders, or page edges should intrude into this zone.

---

## 3. Minimum sizes
| Format | Digital and screen | Print | Notes |
| :--- | :--- | :--- | :--- |
| **Horizontal lockup (`logo.svg`)** | 160 px width | 40 mm width | Transparent lockup for README, navigation bars, and footers |
| **App icon (`icon.svg`, `icon.png`)** | 24 px | 8 mm | Transparent symbol for dock and taskbar |
| **Favicon (`icon.ico`, `favicon.svg`)** | 16 px | 5 mm | Browser tab icon |

---

## 4. Official color palette

| Color name | Role | HEX | RGB | CMYK | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sky Cyan** | Stratum 1 (UI / Presentation) | `#38BDF8` | `rgb(56, 189, 248)` | `65, 10, 0, 0` | Top tier, highlight, "Check" text accent |
| **Cobalt Sky** | Stratum 2 (Logic / Analytics) | `#0EA5E9` | `rgb(14, 165, 233)` | `75, 25, 0, 0` | Middle spine, telemetry charts |
| **Deep Azure** | Stratum 3 (Infra / Data Base) | `#0284C7` | `rgb(2, 132, 199)` | `85, 45, 0, 0` | Bottom tier, primary brand accent |
| **Obsidian Slate** | Dark Surface Canvas | `#0F172A` | `rgb(15, 23, 42)` | `85, 75, 50, 60` | App icon tile, card background |
| **Crisp White** | Primary Text / Light Mark | `#F8FAFC` | `rgb(248, 250, 252)` | `0, 0, 0, 1` | "Stack" text, dark mode contrast |
| **Muted Slate** | Subtitle / Borders | `#94A3B8` | `rgb(148, 163, 184)` | `40, 25, 20, 0` | Subtitles, secondary metadata |

### Approved background pairings
1. **Dark surfaces (`#0F172A`, `#020617`):** Use `stackcheck-lockup-dark.svg` or `logo.svg`.
2. **Light surfaces (`#FFFFFF`, `#F8FAFC`):** Use `stackcheck-lockup-light.svg` or `logo.svg`.
3. **Monochrome print:** Use `stackcheck-symbol-black.svg` or `stackcheck-lockup-mono.svg`.
4. **App docks:** Use `icon.svg` or `icon.ico`.

---

## 5. Typography
- **Wordmark and display:** Outlined geometric sans derived from Inter and SF Pro Display (Weight: 800 ExtraBold for "Stack", 400 Regular / Cyan 800 for "Check").
- **Code and telemetry:** JetBrains Mono, SF Mono, or Inconsolata for CLI banners, metrics, and tabular reports.

---

## 6. Usage constraints
- Do not apply drop shadows, glows, or 3D skeuomorphism to the mark.
- Do not distort, stretch, slant, or shear the aspect ratio.
- Do not alter the 45-degree chamfer geometry or stratum gap ratios.
- Do not swap the stratum color order (keep the progression from light top to dark bottom).
- Do not place raw white text directly over busy photographic backgrounds without an approved container tile.

---

## 7. Master file directory
```
assets/
├── logo.svg                   # Primary hero card (700x150, for README, index.html, docs)
├── logo.png                   # High-DPI raster logo (1400x300, for Streamlit sidebar)
├── icon.svg                   # Primary app icon (256x256 squircle)
├── icon-transparent.svg       # Standalone color symbol (no background)
├── icon.png                   # High-res app icon (512x512)
├── icon.ico                   # Multi-res Windows executable icon (16-256 px)
└── brand/
    ├── BRAND_GUIDELINES.md    # This brand guide
    ├── presentation.html      # Mockups
    ├── stackcheck-card-logo.svg
    ├── stackcheck-lockup-dark.svg
    ├── stackcheck-lockup-light.svg
    ├── stackcheck-lockup-mono.svg
    ├── stackcheck-symbol-color.svg
    ├── stackcheck-symbol-black.svg
    ├── stackcheck-symbol-white.svg
    ├── stackcheck-symbol-mono.svg
    ├── stackcheck-app-icon.svg
    ├── stackcheck-favicon.svg
    ├── favicon.ico
    ├── icon-192.png / icon-512.png / apple-touch-icon.png
    └── favicon-16.png / favicon-32.png / favicon-48.png
```
