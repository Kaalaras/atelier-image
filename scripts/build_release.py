"""Developer utility: package tracked sources only, never runtime or local images."""
from pathlib import Path
import subprocess
import sys
import zipfile

root = Path(__file__).resolve().parents[1]
output = Path(sys.argv[1]).resolve()
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode('utf-8').split('\0')
for name in filter(None, tracked):
    if Path(name).parts[0] in {'.runtime', 'app', 'images', 'logs', '.git'}:
        raise SystemExit(f'Refusing to package local data: {name}')
output.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
    for name in filter(None, tracked):
        payload = (root / name).read_bytes()
        if Path(name).suffix in {'.bat', '.ps1'}:
            payload = payload.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
        archive.writestr('Atelier-Image/' + name, payload)
print(f'Archive source créée : {output} ({output.stat().st_size:,} octets)')
