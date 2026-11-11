# Analysis record — supplied Fliqlo 1.9.5

**Runtime update 0.3.2:** Presentation of flip frames and the real GTK preview handler have now been exercised on Ubuntu 26.04 / GNOME 50.1 / headless Wayland, including a controlled slow-paint regression. See [gnome-frame-clock.json](gnome-frame-clock.json). Earlier runtime limitations below describe the original analysis environment.

**Update for Ubuntu 0.3.0:** The additional Windows package exposes the actual HTML renderer. Its verified dimensions, ranges, typography and 330 ms flip duration supersede the early estimates below. See [WINDOWS.md](WINDOWS.md) and [windows-visual-comparison.json](windows-visual-comparison.json).

## Input and tools

- Supplied `Fliqlo 1.9.5.dmg`: 171707 bytes.
- SHA-256: `eac70be43c503997ff5176cfec5a2240d833f9748b5e7375f26ecfd222d03eeb`.
- REA repository: https://github.com/morluto/rea; CLI: `rea-agents 6.8.0`.
- 7-Zip 25.01 from 7-zip.org extracted the LZFSE/APFS image on Linux.
- Rizin 0.9.1, official static Linux build, was invoked through REA. The target was read statically, never launched.

## Observed

`rea-inspect.json` is the original REA DMG inspection. REA itself could hash and identify the container on Linux but could not inventory its children using its macOS adapter.

After external extraction, a temporary ZIP of the saver bundle was inspected by REA (`rea-extracted.json`). It records child identities and inventories the native executable, nib, font and localization resources. That intermediate archive and the original assets are not shipped in this repo or Debian package.

`Info.plist` identifies `com.9031.fliqloSS`, version `1.9.5`, executable `Fliqlo`, and principal class `FliqloView`. This plist was read with Python's plistlib. REA's native plist/Mach-O helpers returned `capability_unavailable` on Linux; those failures are retained in `rea-plist.json` and `rea-macho.json`. A direct REA attempt on the compiled nib was rejected (`rea-settings.json`); it is not a decoded UI graph.

The Vietnamese `ConfigureSheet.strings` and strings embedded in the compiled nib directly establish these controls:

| Original resource control | New implementation |
| --- | --- |
| Time Format: `1-12 AM/PM`, `0-23`, `00-23` | Same three clock formats |
| Scale | Clock scale slider |
| Brightness | Clock brightness slider |
| Background | Card background switch |
| Show on Multiple Displays | All monitors / primary monitor |

REA with Rizin (`rea-rizin-symbols.json`, `rea-rizin-classes.json`) successfully inspected the native Mach-O x86_64 slice. Rizin reports Swift and Objective-C ARC. Recovered Objective-C metadata names `Fliqlo.FliqloView` with superclass `ScreenSaverView`, `Fliqlo.FlapViewModel`, `Fliqlo.ClockViewModel`, `Fliqlo.ConfigureSheet`, and `Fliqlo.Preferences`. Preference fields include `defaultTimeFormat`, `defaultScale`, `defaultBrightness`, `defaultShowBackground` and `defaultAllowMultipleDisplay`. Flap state includes `_oldValue`, `_newValue`, `_animateTop`, `_animateBottom`, `_showBackground`, `brightnessTop`, `brightnessBottom`, `fadeTop`, `fadeBottom` and `flip`. These corroborate two-half flip state and distinct native preferences; they do not establish the complete animation function.

A bounded REA/Rizin disassembly of the Preferences init wrapper and its callee is retained in `rea-rizin-preferences-init.json` and `rea-rizin-defaults.json`. The callee at x86_64 VA `0xe6f0` contains stores of 0 to the default time format (`0xe7bf`), and 100 to the default scale (`0xe7cf`) and brightness (`0xe7df`); the later defaults dictionary also contains TimeFormat=0, Scale=100 and enabled display/background entries. These support the selected initial values, subject to existing stored preferences. It is static evidence, not an execution trace or a full decompilation. Some decoder output includes invalid instructions; no runtime behavior is inferred from them.

The supplied thumbnail has two square cards, a black split seam, narrow gray digits, and an upper-left AM label. The local font has family `Fliqlo`, fixed-width numeric glyphs (450 units at 1000 units/em), and A/M/P glyphs. The original font can be imported only from a user-selected local file; it is not included in the package.

## Reconstruction and remaining differences

The new code implements the observed settings and visual structure with Cairo. The new platform integration is a GNOME Shell 50 extension, plus native GTK preferences, GSettings storage and a Debian installer. This is an independent Linux implementation, not execution of the macOS saver.

The exact scale/brightness mapping, interpolation, animation duration, pixel geometry and all multi-monitor edge cases have not been established by a live run of the original. In the initial 0.2.0 build, a 500 ms two-phase flip and numeric ranges were implementation choices; initial values follow the recovered preference defaults where available. The default font is a condensed rendering of a system font until the user imports their local Fliqlo font.

No macOS session was available to record original behavior. The available Linux environment is Debian 13 with an Xorg dummy display; GNOME Shell 50 and a Wayland compositor session are absent. Native GTK/Cairo tests are real Linux GUI checks. Extension lifecycle checks are a simulation against the actual extension code, not a real Shell load test.

GNOME 50 API usage was checked against upstream `50.0` source (`main.js`, `layout.js`, `sessionMode.js`, `shellDBus.js`, `screenshot.js`), Mutter's backend/grab headers and St's settings header. In particular, the code handles Ubuntu's child session mode, uses the current grab revocation API and actor cursor API, and calls the Shell D-Bus endpoint directly. This source check does not replace running it on Ubuntu 26.04.

The installer has been built, extracted and its schema validated. End-to-end package installation, idle activation, lock transitions and font refresh in a real Ubuntu 26.04 GNOME 50/Wayland session remain unverified. A claim of 100% visual/behavioral equivalence is not supported by the evidence currently available.
