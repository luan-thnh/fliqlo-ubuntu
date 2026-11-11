"""Read a user-selected font from the Windows package without executing its code."""
import base64
import io
from pathlib import Path
import re
import struct
import zipfile

MAX_APP = 16 * 1024 * 1024
MAX_FONT = 1024 * 1024


def windows_html(path):
    path = Path(path)
    if path.stat().st_size > MAX_APP:
        raise ValueError('Gói Windows vượt giới hạn 16 MiB.')
    if path.suffix.lower() == '.zip':
        with zipfile.ZipFile(path) as archive:
            entries = [entry for entry in archive.infolist()
                       if entry.filename.rsplit('/', 1)[-1].lower() == 'fliqlo.scr']
            if len(entries) != 1 or entries[0].file_size > MAX_APP:
                raise ValueError('ZIP phải có đúng một Fliqlo.scr, tối đa 16 MiB.')
            with archive.open(entries[0]) as source:
                data = source.read(MAX_APP + 1)
    else:
        with path.open('rb') as source:
            data = source.read(MAX_APP + 1)
    if len(data) > MAX_APP or data[:2] != b'MZ':
        raise ValueError('Không phải gói Fliqlo Windows được hỗ trợ.')
    start = data.find('<!DOCTYPE html>'.encode('utf-16le'))
    end = data.find('</html>'.encode('utf-16le'), max(0, start))
    if start < 0 or end < start or end - start > 1024 * 1024:
        raise ValueError('Không tìm thấy renderer HTML trong bản Windows này.')
    html = data[start:end + 14].decode('utf-16le')
    return html


def windows_font(path):
    html = windows_html(path)
    match = re.search(r'base64,([A-Za-z0-9+/=]+)', html)
    if not match:
        raise ValueError('Không tìm thấy font nhúng trong renderer.')
    font = base64.b64decode(match.group(1), validate=True)
    if len(font) < 20 or font[:4] != b'wOF2' or len(font) > MAX_FONT or struct.unpack_from('>I', font, 16)[0] > MAX_FONT:
        raise ValueError('Font WOFF2 không hợp lệ hoặc quá lớn.')
    from fontTools.ttLib import TTFont
    try:
        decoded = TTFont(io.BytesIO(font))
        decoded.flavor = None
        output = io.BytesIO()
        decoded.save(output)
    except Exception as error:
        raise ValueError('Không giải mã được font WOFF2 trong bản Windows.') from error
    if output.tell() > MAX_FONT:
        raise ValueError('Font đã giải mã quá lớn.')
    return output.getvalue()
