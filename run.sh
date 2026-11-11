#!/bin/sh
set -eu
APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
glib-compile-schemas --strict "$APP_DIR/extension/schemas"
exec /usr/bin/python3 "$APP_DIR/native/app.py" "$@"
