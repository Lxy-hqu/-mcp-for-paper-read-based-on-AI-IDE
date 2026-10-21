"""Check package/install parity, internal links, syntax and installed CLI behavior."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import urllib.parse
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from install_skill import fingerprints


def audit():
    manifest = json.loads((ROOT / 'dist' / 'installation-manifest.json').read_text(encoding='utf-8'))
    source, installed = Path(manifest['source']), Path(manifest['installed'])
    expected = fingerprints(source)
    assert expected == manifest['files'] == fingerprints(installed), 'Installed files differ'
    compiled = []
    for p in source.rglob('*.py'):
        compile(p.read_text(encoding='utf-8'), str(p), 'exec')
        compiled.append(str(p.relative_to(source)))
    checked_links = 0
    for p in source.rglob('*.md'):
        text = re.sub(r'```.*?```', '', p.read_text(encoding='utf-8'), flags=re.S)
        text = re.sub(r'`[^`\n]+`', '', text)
        for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
            parts = urllib.parse.urlsplit(link)
            if parts.scheme or not parts.path:
                continue
            dest = (p.parent / urllib.parse.unquote(parts.path)).resolve()
            assert dest.is_relative_to(source) and dest.is_file(), f'Broken skill reference: {p}: {link}'
            checked_links += 1
    archive = Path(manifest['archive'])
    with zipfile.ZipFile(archive) as z:
        names = set(z.namelist())
        assert names == {source.name + '/' + f for f in expected}, 'Unexpected ZIP contents'
        for f, digest in expected.items():
            assert hashlib.sha256(z.read(source.name + '/' + f)).hexdigest() == digest
    with tempfile.TemporaryDirectory(prefix='mentor-install-smoke-') as temp:
        lib = Path(temp) / 'library'
        paper = Path(temp) / 'example.md'
        paper.write_text('A synthetic control keeps the data split fixed.', encoding='utf-8')
        def cli(*args):
            r = subprocess.run([sys.executable, '-X', 'utf8', str(installed / 'scripts' / 'mentor.py'), '--library', str(lib), *args], capture_output=True, timeout=30)
            assert r.returncode == 0, r.stdout.decode('utf-8', errors='replace') + r.stderr.decode('utf-8', errors='replace')
            return json.loads(r.stdout)
        pid = cli('ingest', str(paper))['paper']['id']
        rid = cli('start', '--papers', pid)['id']
        batch = Path(temp) / 'records.json'
        batch.write_text(json.dumps({'records': [
            {'id': 'E', 'kind': 'evidence', 'paper_id': pid, 'locator': {'page': 1}, 'excerpt': 'data split fixed', 'verification': 'text_checked'},
            {'id': 'C', 'kind': 'checkpoint', 'stage': 'intuition', 'prompt': 'Synthetic pending question'}]}), encoding='utf-8')
        cli('put', '--run', rid, '--file', str(batch))
        assert cli('check', '--run', rid)['ok']
        cli('export', '--run', rid)
        assert cli('check-artifacts', '--run', rid)['ok']
        assert cli('status', '--run', rid)['checkpoints'][0]['understanding'] == 'unverified'
    result = {'ok': True, 'packaged_files': len(expected), 'internal_links_checked': checked_links,
              'compiled_scripts': compiled, 'installed_cli_smoke': 'passed', 'private_sources_in_package': False,
              'limitations': ['Implicit model selection not empirically measured', 'Semantic evidence support and human learning require human/model review']}
    (ROOT / 'validation' / 'final-package-audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    audit()
