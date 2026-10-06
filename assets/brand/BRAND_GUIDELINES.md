# StackCheck — Brand Guidelines (Compact)

## 1. The Logo & Core Idea
- **Idea:** An architectural **"S"** monogram sculpted from three horizontal tech strata with precision 45° chamfered cuts. It embodies the three fundamental layers of technology stacks (UI / Presentation, Logic / Analytics, Infrastructure / Data) and evokes speed, validation, and multi-tier market intelligence.
- **Master Symbol:** Clean integer geometry on a 256×256 canvas with 0 text dependencies and 100/100 vector production readiness.
- **Versions:**
  - **Transparent Horizontal Lockups (`logo.svg` / `logo-light.svg` / `logo.png`):** Transparent horizontal mark and wordmark without container backgrounds, adaptive for dark and light surfaces.
  - **Transparent App Icon & Favicon (`icon.svg` / `icon.png` / `icon.ico`):** Standalone Strata S symbol in full 3-tier blue progression on a transparent canvas for browser tabs, desktop taskbars, and Streamlit.
  - **Tile / Squircle Card Versions (`stackcheck-app-icon.svg` / `stackcheck-card-logo.svg`):** Optional boxed versions on obsidian slate (`#0F172A`) tiles.
  - **Monochrome & Single-Color:** Black (`stackcheck-symbol-black.svg`), white (`stackcheck-symbol-white.svg`), and brand cobalt (`stackcheck-symbol-mono.svg`).

---

## 2. Clear Space
Keep a clear exclusion zone of at least **1 × $X$** around the logo and mark on all sides, where **$X$** equals the thickness of a single stratum tier ($40\text{ px}$ on the 256 grid, or the cap height of the letterforms). No text, borders, or page edges should intrude into this zone.

---

## 3. Minimum Sizes
| Format | Digital / Screen | Print | Notes |
| :--- | :--- | :--- | :--- |
| **Horizontal Lockup (`logo.svg`)** | 160 px width | 40 mm width | Clean transparent lockup for README, navbar, & footers |
| **App Icon (`icon.svg` / `icon.png`)** | 24 px | 8 mm | Transparent symbol for dock, taskbar, & Streamlit icon |
| **Favicon (`icon.ico` / `favicon.svg`)** | 16 px | 5 mm | Browser tab icon |

---

## 4. Official Color Palette

| Color Name | Role | HEX | RGB | CMYK | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sky Cyan** | Stratum 1 (UI / Presentation) | `#38BDF8` | `rgb(56, 189, 248)` | `65, 10, 0, 0` | Top tier, highlight, "Check" text accent |
| **Cobalt Sky** | Stratum 2 (Logic / Analytics) | `#0EA5E9` | `rgb(14, 165, 233)` | `75, 25, 0, 0` | Middle spine, telemetry charts |
| **Deep Azure** | Stratum 3 (Infra / Data Base) | `#0284C7` | `rgb(2, 132, 199)` | `85, 45, 0, 0` | Bottom tier, primary brand accent |
| **Obsidian Slate** | Dark Surface Canvas | `#0F172A` | `rgb(15, 23, 42)` | `85, 75, 50, 60` | App icon tile, card background |
| **Crisp White** | Primary Text / Light Mark | `#F8FAFC` | `rgb(248, 250, 252)` | `0, 0, 0, 1` | "Stack" text, dark mode contrast |
| **Muted Slate** | Subtitle / Borders | `#94A3B8` | `rgb(148, 163, 184)` | `40, 25, 20, 0` | Subtitles, secondary metadata |

### Approved Background Pairings:
1. **Dark Surfaces (`#0F172A` / `#020617`):** Use `stackcheck-lockup-dark.svg` or `logo.svg`.
2. **Light Surfaces (`#FFFFFF` / `#F8FAFC`):** Use `stackcheck-lockup-light.svg` or `logo.svg` (the hero card is universally readable on white).
3. **Monochrome Print / Laser:** Use `stackcheck-symbol-black.svg` or `stackcheck-lockup-mono.svg`.
4. **App & OS Docks:** Use `icon.svg` or `icon.ico`.

---

## 5. Typography
- **Wordmark & Display:** Outlined modern geometric sans derived from *Inter* and *SF Pro Display* (Weight: 800 ExtraBold for "Stack", 400 Regular / Cyan 800 for "Check").
- **Code & Telemetry:** *JetBrains Mono*, *SF Mono*, or *Fira Code* for CLI banners, metrics, and tabular reports.

---

## 6. Usage Rules ("Don'ts")
- ❌ **Do not** apply drop shadows, glows, or faux-3D isometric skeuomorphism to the mark.
- ❌ **Do not** distort, stretch, slant, or shear the aspect ratio.
- ❌ **Do not** alter the 45° chamfer geometry or stratum gap ratios.
- ❌ **Do not** swap the stratum color order (keep the gradient progressing from light top to dark bottom).
- ❌ **Do not** place raw white text directly over uncontained photographic backgrounds without the approved container tile.

---

## 7. Master File Directory
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
    ├── presentation.html      # Interactive mockups (README, terminal, website, stickers)
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
