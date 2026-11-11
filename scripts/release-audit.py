#!/usr/bin/env python3
"""Non-destructive pre-publication checks for release candidates."""
from pathlib import Path
import json
import sys
import zipfile
import subprocess

root = Path(__file__).resolve().parents[1]
version = (root / 'VERSION').read_text().strip()
zip_path = root / 'dist' / f'fliqlo-ubuntu@luan-thnh-v{version}.zip'
deb = root / 'dist' / f'fliqlo-ubuntu_{version}_all.deb'
errors = []
blockers = []

if not zip_path.is_file():
    errors.append('Missing extension ZIP (run ./scripts/build-extension.sh).')
else:
    with zipfile.ZipFile(zip_path) as bundle:
        names = set(bundle.namelist())
        needed = {'metadata.json', 'extension.js', 'clock.js', 'prefs.js',
                  'schemas/gschemas.compiled',
                  'schemas/org.gnome.shell.extensions.fliqlo-ubuntu.gschema.xml'}
        missing = needed - names
        if missing:
            errors.append(f'Extension ZIP lacks: {sorted(missing)}')
        unexpected = [name for name in names if name.endswith(('.py', '.deb', '.scr', '.dmg', '.otf'))]
        if unexpected:
            errors.append(f'Unexpected files in extension ZIP: {unexpected}')
        if not missing:
            metadata = json.loads(bundle.read('metadata.json'))
            if metadata.get('uuid') != 'fliqlo-ubuntu@luan-thnh':
                errors.append('Metadata UUID mismatch.')
if not deb.is_file():
    errors.append('Missing Debian package (run ./scripts/build-deb.sh).')
else:
    result = subprocess.run(['dpkg-deb', '--field', str(deb), 'Version'], capture_output=True, text=True)
    if result.returncode or result.stdout.strip() != version:
        errors.append('Debian version mismatch.')

if not any((root / item).exists() for item in ['LICENSE', 'LICENSE.md', 'COPYING']):
    blockers.append('Choose a source license and add a LICENSE/COPYING file.')
blockers.append('A maintainer must review generated/changed GJS before EGO upload.')
blockers.append('Real GNOME Shell 50 Wayland testing, artwork rights and repo ownership require verification.')
print('Artifact checks:', 'PASSED' if not errors else 'FAILED')
for item in errors:
    print('ERROR:', item)
print('Pre-publication blockers (manual):')
for item in blockers:
    print(' -', item)
sys.exit(bool(errors))
