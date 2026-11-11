"""Checks packaging contract without requiring a desktop session."""
from pathlib import Path
import json
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

class RepositoryTests(unittest.TestCase):
    def test_extension_metadata(self):
        metadata = json.loads((ROOT / 'extension/metadata.json').read_text())
        self.assertEqual(metadata['uuid'], 'fliqlo-ubuntu@luan-thnh')
        self.assertIn('50', metadata['shell-version'])
        self.assertNotIn('version', metadata)  # EGO assigns extension upload versions.

    def test_schema_keys(self):
        root = ET.parse(ROOT / 'extension/schemas/org.gnome.shell.extensions.fliqlo-ubuntu.gschema.xml').getroot()
        keys = {entry.attrib['name'] for entry in root.iter('key')}
        self.assertTrue({'scale','brightness','background','flip-animation','idle-seconds','idle-enabled','multiple-displays','preview-token','font-family','time-format'} <= keys)

    def test_standalone_preferences(self):
        js = (ROOT / 'extension/prefs.js').read_text()
        self.assertIn("title: 'Appearance'", js)
        self.assertIn("title: 'Screensaver'", js)
        self.assertNotIn('Gio.Subprocess.new', js)
        self.assertNotIn('Gio.Subprocess', js)

    def test_gtk_layout(self):
        source = (ROOT / 'native/app.py').read_text()
        css = (ROOT / 'native/style.css').read_text()
        self.assertIn('Gtk.StackSwitcher', source)
        self.assertIn('class Preferences(Gtk.ApplicationWindow)', source)
        self.assertIn('status-banner', css)
        self.assertIn('@theme_bg_color', css)

    def test_release_files(self):
        version = (ROOT / 'VERSION').read_text().strip()
        self.assertRegex(version, r'^\d+\.\d+\.\d+$')
        self.assertTrue((ROOT / 'scripts/build-extension.sh').is_file())
        self.assertTrue((ROOT / 'docs/RELEASING.md').is_file())
        self.assertTrue((ROOT / 'native/style.css').is_file())
        self.assertIn('style.css', (ROOT / 'scripts/build-deb.sh').read_text())

if __name__ == '__main__':
    unittest.main()
