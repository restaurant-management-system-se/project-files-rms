"""Check local documentation links and preserve original formal-source hashes."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = ['README.md', 'backend/docs/RMS-32-delivery-status.md',
             'Issues/Backlog/DEVIATION_REGISTER.md']
errors = []
links = 0
for relative in DOCUMENTS:
    source = ROOT / relative
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', source.read_text()):
        url = urlsplit(target)
        if url.scheme or url.netloc or not url.path:
            continue
        path = (source.parent / unquote(url.path)).resolve()
        if not path.is_relative_to(ROOT) or not path.exists():
            errors.append(f'{relative}: broken or escaping local target {target}')
        links += 1
manifest = json.loads((ROOT / 'backend/docs/source-document-hashes.json').read_text())
for relative, expected in manifest['sha256'].items():
    actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
    if actual != expected:
        errors.append(f'Formal source changed without recorded revision: {relative}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'Documentation check passed: {links} local links; {len(manifest["sha256"])} formal source hashes unchanged.')
