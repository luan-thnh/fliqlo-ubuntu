This helper is only for an isolated, disposable GNOME 50 test session. It is not
copied into the Debian package. `FLIQLO_RUNTIME_TEST=1` is required before the
helper will enable Shell.Eval; disabling it restores the prior setting.

The recorded environment used the official ubuntu:26.04 Docker image, GNOME Shell
50.1 / Mutter 50.1, software rendering, `--headless --wayland --no-x11
--virtual-monitor 1920x1080 --force-animations`. No host display or user session was
mounted. The container's empty /run/systemd/seats directory was removed so Shell
used its dummy login manager instead of an unavailable logind service.

Install the app package and this helper into the disposable session's extensions
directory; enable both UUIDs before starting Shell. Run in that same session bus,
with its XDG_RUNTIME_DIR and WAYLAND_DISPLAY:

    FLIQLO_TEST_APP_DIR=/usr/share/fliqlo-ubuntu /usr/bin/python3 tests/preview-button-wayland.py

The test invokes the actual GTK Preferences.preview handler while the extension
is active, confirms the Shell overlay opens, simulates a cached minute mismatch,
and counts compositor `after-paint` progress values. It adds 25 ms of controlled
repaint work to reproduce the old high-priority timeout starvation. It checks at
least two intermediate displayed phases, then closes the overlay.

`tests/gnome-presentation.js` can also be evaluated in that isolated Shell session
to compare the 0.3.1 package against the current package under the same load. The
full recorded comparison is in research/evidence/gnome-frame-clock.json. Stop/remove the
test container afterward; never install this helper as part of a normal setup.
