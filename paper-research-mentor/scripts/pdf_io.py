"""Page-preserving extraction, bounded public downloads and explicit rendering/OCR."""
from __future__ import annotations

import importlib.util
import ipaddress
import json
import re
import shutil
import socket
import subprocess
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

MAX_BYTES = 40 * 1024 * 1024


def doctor():
    return {"python": __import__("sys").executable, "stdlib_library": True,
            "commands": {c: shutil.which(c) for c in ("pdftotext", "pdfinfo", "pdftoppm", "tesseract")},
            "packages": {p: importlib.util.find_spec(p) is not None for p in ("pypdf", "fitz", "sympy")}}


def command(args, timeout=90):
    proc = subprocess.run([str(a) for a in args], capture_output=True, timeout=timeout)
    if proc.returncode:
        raise ValueError(f"{Path(str(args[0])).name} failed: {proc.stderr.decode('utf-8', errors='replace')[:1200]}")
    return proc.stdout.decode("utf-8", errors="replace")


def validate_url(url):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("Only public HTTP(S) URLs without embedded credentials are supported")
    try:
        addresses = socket.getaddrinfo(parts.hostname, parts.port or (443 if parts.scheme == "https" else 80), type=socket.SOCK_STREAM)
    except OSError as e:
        raise ValueError(f"Cannot resolve source host: {e}") from e
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("Source URL resolves to a non-public address")


class PublicRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(url):
    validate_url(url)
    opener = urllib.request.build_opener(PublicRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": "PaperResearchMentor/1.0 (research reading)"})
    with opener.open(request, timeout=45) as response:
        validate_url(response.url)
        size = response.headers.get("Content-Length")
        if size and int(size) > MAX_BYTES:
            raise ValueError("Source exceeds 40 MiB limit")
        content = response.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise ValueError("Source exceeds 40 MiB limit")
        mime = response.headers.get_content_type()
        final_url = response.url
    if content.lstrip().startswith(b"%PDF-"):
        fmt = "pdf"
    elif mime in {"text/plain", "text/markdown"} and not re.search(br"<(?:html|!doctype)\b", content[:1000], re.I):
        fmt = "text"
    else:
        raise ValueError("URL is not PDF/plain text. Resolve the primary full text with browsing and save readable UTF-8 text with --source-url")
    return content, fmt, final_url


def section_hints(text):
    pattern = re.compile(r"^\s*(?:\d+(?:\.\d+)*[.)]?\s+)?(?:abstract|introduction|background|related work|methods?|methodology|results?|experiments?|discussion|conclusions?|references|appendix|摘要|引言|方法|结果|讨论|结论|参考文献|附录)\b.{0,65}$", re.I)
    return [{"line": i + 1, "heading": line.strip()} for i, line in enumerate(text.splitlines()) if pattern.match(line)]


def page_record(number, text, blocks=None, printed_label=None):
    warnings = []
    chars = sum(not c.isspace() for c in text)
    if chars < 40:
        warnings.append("sparse_or_scanned_page: OCR or visual inspection needed")
    if text.count("\ufffd") > 3 or (text and text.count("\ufffd") / len(text) > .01):
        warnings.append("replacement_characters: extraction may be corrupt")
    if sum(bool(re.search(r"\S {8,}\S", line)) for line in text.splitlines()) >= 4:
        warnings.append("possible_columns_or_table: verify visual reading order")
    return {"page": number, "printed_label": printed_label, "text": text, "blocks": blocks or [],
            "section_hints": section_hints(text), "warnings": warnings}


def extract_text(content):
    text = content.decode("utf-8-sig")
    units = text.split("\f")
    if units and not units[-1].strip() and len(units) > 1:
        units.pop()
    return {"backend": "utf8", "metadata": {}, "warnings": ["Text units are not inferred PDF page numbers; locator labels must say page unit"],
            "pages": [page_record(i + 1, t) for i, t in enumerate(units)]}


def extract_pdf(path, backend="auto"):
    path = Path(path).resolve()
    if backend not in {"auto", "poppler", "pypdf"}:
        raise ValueError("Invalid PDF backend")
    caps = doctor()
    poppler = caps["commands"]["pdftotext"]
    if backend == "poppler" and not poppler:
        raise ValueError("pdftotext is unavailable")
    if backend == "poppler" or (backend == "auto" and poppler):
        text = command([poppler, "-layout", "-enc", "UTF-8", path, "-"])
        units = text.split("\f")
        if units and not units[-1].strip():
            units.pop()
        pages = [page_record(i + 1, t) for i, t in enumerate(units)]
        warnings = []
        metadata = {}
        if caps["commands"]["pdfinfo"]:
            info = command([caps["commands"]["pdfinfo"], path])
            m = re.search(r"^Pages:\s+(\d+)", info, re.M)
            if m:
                count = int(m[1])
                if len(pages) > count:
                    raise ValueError("Extracted page count disagrees with pdfinfo")
                while len(pages) < count:
                    pages.append(page_record(len(pages) + 1, ""))
            for key in ("Title", "Author", "CreationDate"):
                m = re.search(rf"^{key}:[ \t]*(.*)$", info, re.M)
                if m:
                    metadata[key.lower()] = m[1].strip()
            # CreationDate is a file timestamp, NOT the publication year.
        try:
            xml = command([poppler, "-bbox-layout", "-enc", "UTF-8", path, "-"])
            root = ET.fromstring(xml)
            xmlpages = [e for e in root.iter() if e.tag.split("}")[-1] == "page"]
            for page, xp in zip(pages, xmlpages):
                for block in xp.iter():
                    if block.tag.split("}")[-1] != "line":
                        continue
                    words = ["".join(w.itertext()) for w in block if w.tag.split("}")[-1] == "word"]
                    page["blocks"].append({"text": " ".join(words), "bbox": [float(block.attrib[k]) for k in ("xMin", "yMin", "xMax", "yMax")]})
        except (ValueError, ET.ParseError, KeyError) as e:
            warnings.append(f"Coordinates unavailable; page text retained: {e}")
        used = "poppler"
    else:
        if not caps["packages"]["pypdf"]:
            raise ValueError("PDF text requires pdftotext or pypdf; text-only library still works")
        from pypdf import PdfReader
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ValueError("Encrypted PDF: supply an accessible copy")
        labels = reader.page_labels
        pages = [page_record(i + 1, page.extract_text() or "", printed_label=labels[i] if labels else None) for i, page in enumerate(reader.pages)]
        metadata = {"title": str(reader.metadata.title or ""), "author": str(reader.metadata.author or "")} if reader.metadata else {}
        warnings = ["pypdf fallback has no coordinates; inspect layout visually"]
        used = "pypdf"
    if not pages:
        raise ValueError("No pages found")
    for p in pages:
        warnings.extend(f"page {p['page']}: {w}" for w in p["warnings"])
    return {"backend": used, "metadata": metadata, "pages": pages, "warnings": warnings}


def parse_pages(value, count):
    result = set()
    for part in value.split(","):
        if "-" in part:
            lo, hi = map(int, part.split("-", 1))
            if lo > hi:
                raise ValueError("Page range must be ascending")
            result.update(range(lo, hi + 1))
        else:
            result.add(int(part))
    if not result or min(result) < 1 or max(result) > count:
        raise ValueError("Render/OCR page range outside the source")
    return sorted(result)


def render(path, pages, output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    caps = doctor()
    images = []
    if caps["commands"]["pdftoppm"]:
        for page in pages:
            prefix = output / f"page-{page:04d}"
            command([caps["commands"]["pdftoppm"], "-f", page, "-l", page, "-singlefile", "-scale-to", "1800", "-png", Path(path).resolve(), prefix])
            image = prefix.with_suffix(".png")
            if not image.is_file():
                raise ValueError("Renderer returned without an image")
            images.append(str(image))
    elif caps["packages"]["fitz"]:
        import fitz
        with fitz.open(path) as doc:
            for page in pages:
                image = output / f"page-{page:04d}.png"
                doc[page - 1].get_pixmap(matrix=fitz.Matrix(2, 2)).save(image)
                images.append(str(image))
    else:
        raise ValueError("Rendering requires pdftoppm or PyMuPDF; cannot claim visual verification")
    return images


def ocr(path, pages, output, language="eng"):
    tess = shutil.which("tesseract")
    if not tess:
        raise ValueError("OCR unavailable: tesseract not found; original transcript remains unchanged")
    if not re.fullmatch(r"[a-zA-Z0-9_+.-]+", language):
        raise ValueError("Invalid language identifier")
    images = render(path, pages, output)
    results = []
    for page, image in zip(pages, images):
        text = command([tess, image, "stdout", "-l", language])
        results.append({"page": page, "text": text, "status": "unreviewed_ocr", "image": image})
    result = {"warning": "OCR is an alternative unverified transcript; check formulas and numbers on the original", "pages": results}
    dest = Path(output) / "ocr.json"
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"ocr_path": str(dest), **result}


def ingest(lib, source, title=None, source_url=None, version=None, role="main", backend="auto"):
    is_url = source.startswith(("https://", "http://"))
    if is_url:
        content, fmt, resolved = download(source)
        source_url = resolved
    else:
        p = Path(source).resolve()
        if not p.is_file():
            raise ValueError(f"Source not found: {p}")
        if p.stat().st_size > MAX_BYTES:
            raise ValueError("Source exceeds 40 MiB limit")
        content = p.read_bytes()
        fmt = "pdf" if content.lstrip().startswith(b"%PDF-") else "text"
        if fmt == "text" and p.suffix.lower() not in {".txt", ".md", ".tex", ".py", ".json", ".yaml", ".yml", ".csv", ".ts", ".bib"}:
            raise ValueError("Unsupported source; use PDF or explicit UTF-8 text")
    if fmt == "pdf":
        with tempfile.TemporaryDirectory(prefix="paper-mentor-") as temp:
            tmp = Path(temp) / "source.pdf"
            tmp.write_bytes(content)
            extracted = extract_pdf(tmp, backend)
    else:
        extracted = extract_text(content)
    if not content.strip():
        raise ValueError("Empty source")
    return lib.register(source, content, extracted, title, source_url, version, role, fmt)
