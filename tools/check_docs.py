"""Check public documentation links and local images without contacting remote sites."""
from pathlib import Path
import re
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]


def main():
    paths = [ROOT / 'README.md', ROOT / 'README.zh-CN.md', ROOT / 'CONTRIBUTING.md', *sorted((ROOT / 'docs').rglob('*.md'))]
    errors, count = [], 0
    for path in paths:
        text = path.read_text(encoding='utf-8')
        text = re.sub(r'```.*?```', '', text, flags=re.S)
        text = re.sub(r'`[^`\n]+`', '', text)
        links = re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text) + re.findall(r'(?:src|href)="([^"]+)"', text)
        for link in links:
            url = urllib.parse.urlsplit(link)
            if url.scheme:
                continue
            target = (path.parent / urllib.parse.unquote(url.path)).resolve() if url.path else path
            count += 1
            if not target.is_relative_to(ROOT) or not target.is_file():
                errors.append(f'{path.relative_to(ROOT)}: missing link {link}')
                continue
            if url.fragment and target.suffix.lower() == '.md':
                headings = re.findall(r'^#{1,6}\s+(.+)$', target.read_text(encoding='utf-8'), re.M)
                slugs = {re.sub(r'[^\w -]', '', h.lower()).replace(' ', '-') for h in headings}
                if urllib.parse.unquote(url.fragment) not in slugs:
                    errors.append(f'{path.relative_to(ROOT)}: missing heading {link}')
        if re.search(r'(?:[GD]:[\\/](?:CodexData|paper_read_skill))', text):
            errors.append(f'{path.relative_to(ROOT)}: private machine path in public documentation')
    image = ROOT / 'docs' / 'assets' / 'hero.png'
    if not image.is_file() or image.read_bytes()[:8] != b'\x89PNG\r\n\x1a\n':
        errors.append('Cover is missing or not a PNG')
    print({'documents': len(paths), 'local_links': count, 'errors': errors})
    return 2 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
