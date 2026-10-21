"""Structural checks for analysis Markdown. No semantic grading claims."""
from __future__ import annotations
import re
import urllib.parse
from pathlib import Path


def anchors(text):
    result = set(re.findall(r'<a\s+id=["\']([^"\']+)', text))
    for heading in re.findall(r"^#{1,6}\s+(.+)$", text, re.M):
        slug = re.sub(r"[^\w\- ]", "", heading.strip().lower()).replace(" ", "-")
        result.add(slug)
    return result


def check_artifacts(lib, rid, directory=None):
    folder = Path(directory).resolve() if directory else lib.root / "runs" / rid
    if not folder.is_relative_to(lib.root):
        raise ValueError("Artifact checks must stay inside the user library")
    evidence = {r["id"] for r in lib.records(rid) if r["kind"] == "evidence"}
    errors, warnings, checked = [], [], []
    for path in sorted(folder.rglob("*.md")):
        text = path.read_text(encoding="utf-8-sig")
        checked.append(str(path))
        fence, visible = None, []
        for number, line in enumerate(text.splitlines(), 1):
            m = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
            if m:
                token = m[1]
                if fence is None:
                    fence = token
                elif token[0] == fence[0] and len(token) >= len(fence):
                    fence = None
                continue
            if fence is None:
                visible.append((number, line))
        if fence:
            errors.append(f"{path.name}: unclosed code fence")
        prose = "\n".join(line for _, line in visible)
        if len(re.findall(r"(?m)^\s*\$\$\s*$", prose)) % 2:
            errors.append(f"{path.name}: unbalanced display-math delimiters")
        for number, line in visible:
            for eid in re.findall(r"\[EVID:([^\]]+)\]", line):
                if eid not in evidence:
                    errors.append(f"{path.name}:{number}: unknown evidence {eid}")
            for link in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", line):
                link = link.strip("<>")
                parts = urllib.parse.urlsplit(link)
                if parts.scheme in {"http", "https", "mailto", "codex"}:
                    continue
                target = path if not parts.path else (path.parent / urllib.parse.unquote(parts.path)).resolve()
                if not target.is_relative_to(lib.root):
                    errors.append(f"{path.name}:{number}: local link escapes library")
                elif not target.is_file():
                    errors.append(f"{path.name}:{number}: missing local link {link}")
                elif parts.fragment and target.suffix.lower() == ".md":
                    if urllib.parse.unquote(parts.fragment) not in anchors(target.read_text(encoding="utf-8-sig")):
                        errors.append(f"{path.name}:{number}: missing Markdown anchor {link}")
        if re.search(r"\{\{.+?\}\}|\bTODO\b|待填写", prose):
            warnings.append(f"{path.name}: possible unfinished template")
    if not checked:
        warnings.append("No Markdown artifacts found")
    warnings.append("Checks cover structure, links and evidence IDs, not mathematical rendering or semantic correctness")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "files_checked": checked}
