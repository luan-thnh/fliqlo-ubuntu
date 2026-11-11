# Windows reference: Fliqlo 1.6.1

The user supplied `FliqloScr.zip` (814536 bytes), SHA-256 `d2ce5a7e37d7aa1ebd0b873a715938b822b7f81ccd2509a794f24fad3039fa22`. Its `Fliqlo.scr` is 950328 bytes, SHA-256 `c2b7339da0f5dbe3c93e9a8b6dbb597238a467bc0365d63a96212627591d8fb2`.

REA 6.8.0 successfully inspected the ZIP and managed executable with `inspect-artifact` and `inspect-managed-artifact`. Evidence is retained as `rea-windows-archive.json` and `rea-windows-managed.json`. It observes .NET Framework CIL, Windows Forms, WebView2-related references and embedded resources. No Windows application code was executed during extraction.

A UTF-16 literal in the managed executable contains the complete 28510-character HTML/CSS/JavaScript renderer, including an embedded WOFF2 font. Its recovered UTF-8 HTML SHA-256 is `467aef770179626feff3a24d9d9a9c4b8fd58a297c9994320708fc6a85d62fa7`. The payload remains outside the repository. The ZIP ReadMe describes version 1.6.1 and WebView2; its installation instructions were treated as documentation, not commands to execute.

## Observed renderer facts

| Item | Actual shipped value | Correction in Ubuntu 0.3.0 |
| --- | --- | --- |
| Landscape outer canvas | 1350 × 700 | Fit with the same formula |
| Portrait outer canvas | 700 × 1350 | Stack hours over minutes |
| Card / inter-card gap | 600 / 50 units | Replace estimated percentages |
| Card radius | 50 units | Match base radius |
| Top / bottom flap | 297 px content + 1 px border; 6 px seam | Explicit clipped halves and seam |
| Card backgrounds | Outer gradient #161616 → #0c0c0c; inner #111 → #0b0b0b | Same two gradients |
| Foreground | White with alpha .711 | Alpha compositing over actual card background |
| Digits | Font size 600; line height 758; baseline 523 | Same baseline and proper Pango shaping |
| AM / PM | Upper-left / lower-left, 60-unit font | Correct positions, not both at bottom or both at top |
| Digit adjustments | Text-indent −.025em for 1; .04em for 11; .08em for other values ending in 1 | Centered-line half-indent offsets; font GPOS kerning via Pango |
| 3D projection | CSS perspective 4000 px; top/bottom rotateX about their own hinges | Inverse projective raster mapping, replacing vertical-only scaling |
| Flip duration | .165 s per half | Total .330 s, replacing .500 s |
| Flip easing | CSS ease-in for top, ease-out for bottom | Invert cubic Bézier x to calculate easing |
| Flip brightness | Top 100%→40%, bottom 200%→100%, background fade states | Corresponding phase shading and additive highlight compositing |
| Scale / brightness | Minimum 50, maximum 100 | Verified ranges instead of guessed 25–150 / 10–100 |
| Format IDs | Windows 0=12h, 1=padded 24h, 2=unpadded 24h | Preserve Ubuntu's existing IDs by semantic mapping in comparison harness |

The Windows font has family aliases `Fliqlo` / `Fliqlo Bold`, version 2.1, and kerning pairs. Ignoring those pairs gives visibly wrong placement, especially `11`. The user-selectable ZIP/SCR importer decodes only the embedded WOFF2 font to the local font directory. It bounds input size, validates the font family and preserves the existing font on invalid input. It never installs or launches the `.scr` executable.

## Reproducible visual comparison

`node scripts/compare-reference.cjs /path/FliqloScr.zip /path/scratch --animated`:

1. Extract the HTML and font locally from the original user-provided file.
2. Render ten fixed-date, fixed-viewport original HTML frames plus four explicitly paused animation frames (45/120/210/290 ms during 11:59 AM → 12:00 PM) using Linux Chromium. Disable only the optional WebView2 host bridge, and seed the original setting keys with semantically matching values. The clock's HTML/CSS/JS is unchanged.
3. Render the independent Python Cairo/Pango implementation with the same local font, time, viewport, orientation and settings.
4. Retain raw per-channel image errors and a symmetric 1-pixel-neighborhood raster comparison. This tolerance is explicit: it accommodates different edge rasterizers and is not pixel identity.

The measured Python report is `windows-visual-comparison.json`. The same 14 cases were rendered by the actual extension drawing module under GJS 1.82.3 / Pango / Cairo, not a mock (`windows-gjs-comparison.json`). Both renderers produced identical pixels in the tested cases. This exercises real GJS drawing APIs, but does not load the extension lifecycle into GNOME Shell. Cases cover midnight/noon, 12h and both 24h formats, `1`/`11`/`01`/`21`/`31`/`41`/`51`, portrait/landscape, 50–100% scale and brightness, backgrounds on/off, and viewport widths 640–1920.

Worst mean absolute channel error on the full image: 0.8378/255. Worst structural mismatch after the stated edge tolerance: 0.0441% of active clock pixels. Raw mismatches are retained too; at some settings the fraction of active pixels with >10/255 raw error is materially larger because of edge rasterization. No aggregate percentage is a claim of 100% application equivalence.

## Still not established

These are original **HTML frames rendered on Linux**, not recordings from a live Windows WebView2 session. The image comparison does not cover the actual Windows/macOS host, all preferences, startup or input behavior. The St.DrawingArea host and compositor integration are not tested by the headless GJS/Python screenshot harness. The extension lifecycle test remains a simulation; GNOME 50/Wayland installation and idle/lock behavior still need a real session.

The animation uses the recovered phase duration, easing, brightness and CSS perspective distance of 4000. A per-pixel-row inverse rotateX/perspective mapping renders the trapezoidal flap, replacing the earlier vertical-only approximation. Four paused animation frames passed the same image comparison in both Python and GJS. This is not a full temporal/video comparison, a check of every DPI/setting, or exact pixel identity with Windows GPU rendering. macOS 1.9.5 and Windows 1.6.1 are distinct reference versions; this report does not assert they behave identically.

A bounded local CPU check at 1920×1080, two changing cards and 20 animation phases measured about 12.4 ms/frame in Python and 18.8 ms/frame in GJS after a warm-up. These are measurements of this cloud CPU renderer, not a frame-rate guarantee for the user’s GNOME session.

Runtime update for 0.3.2: the compositor after-paint path and installed GTK preview handler have since been tested on Ubuntu 26.04 / GNOME 50.1 / headless Wayland. The old timeout starvation was reproduced under controlled repaint load and corrected with actor frame-clock timelines. See gnome-frame-clock.json. Physical monitors, GPU drivers and every user DPI configuration remain outside that test.
