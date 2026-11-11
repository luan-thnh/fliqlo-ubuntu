#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
printf '%s\n' '== Python syntax =='
python3 -m compileall -q native tests scripts
printf '%s\n' '== JavaScript syntax and clock behavior =='
for file in extension/*.js; do node --check "$file"; done
node tests/clock.mjs
node tests/extension-lifecycle.mjs
printf '%s\n' '== Metadata and project checks =='
python3 tests/repository.py
if command -v glib-compile-schemas >/dev/null 2>&1; then
    glib-compile-schemas --strict extension/schemas
else
    printf '%s\n' 'SKIP GSettings compile: install libglib2.0-bin'
fi
if command -v gjs >/dev/null 2>&1; then
    gjs -m tests/gjs-render.js
else
    printf '%s\n' 'SKIP GJS renderer: install gjs'
fi
if /usr/bin/python3 -c 'import cairo, gi; gi.require_version("Gtk", "3.0"); from gi.repository import Gtk' >/dev/null 2>&1; then
    /usr/bin/python3 tests/native.py
    if command -v xvfb-run >/dev/null 2>&1 && command -v dbus-run-session >/dev/null 2>&1; then
        xvfb-run -a dbus-run-session -- /usr/bin/python3 tests/native-ui.py
        xvfb-run -a dbus-run-session -- /usr/bin/python3 tests/native-animation.py
    else
        printf '%s\n' 'SKIP GTK UI runtime: install xvfb and dbus-x11'
    fi
else
    printf '%s\n' 'SKIP GTK/Python runtime: install python3-gi, python3-cairo, gir1.2-gtk-3.0'
fi
