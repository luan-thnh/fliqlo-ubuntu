"""Optional integration check: pass a locally owned Fliqlo DMG. Requires a display and 7zz."""
import hashlib
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

source = Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory() as temporary:
    os.environ['XDG_DATA_HOME'] = temporary + '/data'
    os.environ['XDG_CACHE_HOME'] = temporary + '/cache'
    os.environ['GSETTINGS_BACKEND'] = 'memory'
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'native'))
    from app import App, Preferences, settings
    from gi.repository import Gtk
    app = App()
    app.register(None)
    config = settings()
    window = Preferences(app, config)
    class Selection:
        path = source
        def __init__(self, **_kwargs): pass
        def add_buttons(self, *_args): pass
        def add_filter(self, *_args): pass
        def run(self): return Gtk.ResponseType.OK
        def get_filename(self): return str(self.path)
        def destroy(self): pass
    with patch.object(Gtk, 'FileChooserDialog', Selection):
        window.import_font(None)
        installed = Path(temporary) / 'data/fonts/fliqlo-ubuntu/Fliqlo.otf'
        assert installed.exists(), window.status.get_text()
        assert config.get_string('font-family') in ('Fliqlo', 'Fliqlo Bold')
        digest = hashlib.sha256(installed.read_bytes()).hexdigest()
        invalid = Path(temporary) / 'invalid.otf'
        invalid.write_bytes(b'invalid')
        Selection.path = invalid
        window.import_font(None)
        assert hashlib.sha256(installed.read_bytes()).hexdigest() == digest
        assert 'Không nhập được font' in window.status.get_text()
        invalid_zip = Path(temporary) / 'invalid.zip'
        invalid_zip.write_bytes(b'not a ZIP')
        Selection.path = invalid_zip
        window.import_font(None)
        assert hashlib.sha256(installed.read_bytes()).hexdigest() == digest
        assert 'Không nhập được font' in window.status.get_text()
    window.destroy()
print('Font import: Archive extraction, family validation and preservation on invalid input passed.')
