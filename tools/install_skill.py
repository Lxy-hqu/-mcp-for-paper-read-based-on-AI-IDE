"""Install only the reusable skill, verify hashes, and build a clean distributable ZIP."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile


def files(folder):
    return sorted(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix != '.pyc')


def fingerprints(folder):
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files(folder)}


def install(home=None):
    root = Path(__file__).resolve().parents[1]
    source = root / 'paper-research-mentor'
    home = Path(home or os.environ.get('CODEX_HOME') or Path.home() / '.codex').resolve()
    target = (home / 'skills' / source.name).resolve()
    if target == source.resolve() or target.parent != (home / 'skills').resolve() or target.name != source.name:
        raise ValueError('Resolved installation target is invalid')
    expected = fingerprints(source)
    if not expected or 'SKILL.md' not in expected:
        raise ValueError('Missing skill source')
    backup = None
    if target.exists() and fingerprints(target) != expected:
        backup = home / 'skill-backups' / (source.name + '-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        if not backup.resolve().is_relative_to(home) or not target.is_relative_to(home):
            raise ValueError('Backup/target must stay inside resolved Codex home')
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(target), str(backup))
    if not target.exists():
        for p in files(source):
            dest = target / p.relative_to(source)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
    if fingerprints(target) != expected:
        raise ValueError('Installed files do not match source hashes')
    dist = root / 'dist'
    dist.mkdir(exist_ok=True)
    archive = dist / 'paper-research-mentor.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for p in files(source):
            z.write(p, Path(source.name) / p.relative_to(source))
    manifest = {'installed_at_utc': datetime.now(timezone.utc).isoformat(), 'source': str(source), 'installed': str(target),
                'backup': str(backup) if backup else None, 'archive': str(archive), 'files': expected,
                'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
    (dist / 'installation-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return manifest


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--codex-home')
    args = p.parse_args()
    result = install(args.codex_home)
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, ensure_ascii=False, indent=2))
