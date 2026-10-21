#!/usr/bin/env python3
"""Source-linked paper reading library: ingest, record, discuss, check, export."""
from __future__ import annotations

import argparse
import json
import sys
import sqlite3
from pathlib import Path

from artifacts import check_artifacts
from library import KINDS, Library, read_json
from pdf_io import doctor, ingest, ocr, parse_pages, render


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--library", default="paper-reading", help="User data directory; never the installed skill")
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Inspect dependencies without installation")
    x = sub.add_parser("ingest", help="Ingest a PDF/text path or public PDF/text URL")
    x.add_argument("source")
    x.add_argument("--title")
    x.add_argument("--source-url")
    x.add_argument("--version")
    x.add_argument("--role", choices=["main", "supplement", "code", "project", "external"], default="main")
    x.add_argument("--backend", choices=["auto", "poppler", "pypdf"], default="auto")
    x = sub.add_parser("metadata", help="Correct known bibliographic fields with history")
    x.add_argument("--paper", required=True)
    x.add_argument("--file", required=True)
    x = sub.add_parser("start", help="Create a run")
    x.add_argument("--papers", nargs="+", required=True)
    x.add_argument("--mode", choices=["full", "batch", "synthesis", "project"], default="full")
    x = sub.add_parser("attach", help="Add newly supplied sources to a run without losing discussions")
    x.add_argument("--run", required=True)
    x.add_argument("--papers", nargs="+", required=True)
    x = sub.add_parser("pages", help="Read source page text/coordinates without truncation")
    x.add_argument("--paper", required=True)
    x.add_argument("--pages", help="One-based range, e.g. 1,3-5; omit for all")
    x.add_argument("--text-only", action="store_true")
    for name in ("render", "ocr"):
        x = sub.add_parser(name)
        x.add_argument("--paper", required=True)
        x.add_argument("--pages", required=True)
        if name == "ocr":
            x.add_argument("--lang", default="eng")
    x = sub.add_parser("put", help="Validate and atomically upsert a records JSON batch")
    x.add_argument("--run", required=True)
    x.add_argument("--file", required=True)
    x = sub.add_parser("checkpoint", help="Append genuine response/help/evaluation events")
    x.add_argument("--run", required=True)
    x.add_argument("--id", required=True)
    x.add_argument("--action", choices=["answer", "hint", "partial_explanation", "answer_exposed", "skip", "evaluate"], required=True)
    x.add_argument("--text", help="For short actual user words; use --text-file for multiline")
    x.add_argument("--text-file")
    x.add_argument("--assessment", choices=["needs_hint", "independent", "transferable"])
    x.add_argument("--answer-event", type=int)
    x.add_argument("--reason")
    x = sub.add_parser("status")
    x.add_argument("--run", required=True)
    x = sub.add_parser("update", help="Update analysis/verification independently; notes are merged")
    x.add_argument("--run", required=True)
    x.add_argument("--analysis", choices=["in_progress", "partial", "complete"])
    x.add_argument("--verification", choices=["pending", "partial", "verified"])
    x.add_argument("--notes-file")
    x = sub.add_parser("search")
    x.add_argument("query")
    x.add_argument("--kind", choices=sorted(KINDS))
    for name in ("check", "export", "check-artifacts"):
        x = sub.add_parser(name)
        x.add_argument("--run", required=True)
    return p


def execute(args):
    if args.command == "doctor":
        return doctor(), 0
    lib = Library(args.library)
    try:
        c = args.command
        if c == "ingest":
            result = ingest(lib, args.source, args.title, args.source_url, args.version, args.role, args.backend)
        elif c == "metadata":
            result = lib.metadata(args.paper, read_json(args.file))
        elif c == "start":
            result = lib.start(args.papers, args.mode)
        elif c == "attach":
            result = lib.attach(args.run, args.papers)
        elif c == "pages":
            pages = lib.pages(args.paper)
            selected = parse_pages(args.pages, len(pages)) if args.pages else range(1, len(pages) + 1)
            result = [{"page": n, "text": pages[n - 1]["text"]} if args.text_only else pages[n - 1] for n in selected]
        elif c in {"render", "ocr"}:
            paper = lib.paper(args.paper)
            if paper["format"] != "pdf":
                raise ValueError("Only PDF sources can be rendered/OCRed")
            pages = parse_pages(args.pages, paper["page_count"])
            out = lib.root / "sources" / args.paper / ("renders" if c == "render" else "ocr")
            result = {"images": render(paper["source_path"], pages, out)} if c == "render" else ocr(paper["source_path"], pages, out, args.lang)
        elif c == "put":
            batch = read_json(args.file)
            if not isinstance(batch, dict):
                raise ValueError("Input must be an object with a records list")
            result = lib.put(args.run, batch.get("records"))
        elif c == "checkpoint":
            if args.text and args.text_file:
                raise ValueError("Choose --text or --text-file")
            text = Path(args.text_file).read_text(encoding="utf-8-sig") if args.text_file else args.text
            result = lib.checkpoint(args.run, args.id, args.action, text, args.assessment, args.answer_event, args.reason)
        elif c == "status":
            result = lib.status(args.run)
        elif c == "update":
            result = lib.update(args.run, args.analysis, args.verification, read_json(args.notes_file) if args.notes_file else None)
        elif c == "search":
            result = lib.search(args.query, args.kind)
        elif c == "check":
            result = lib.check(args.run)
        elif c == "export":
            result = lib.export(args.run)
        elif c == "check-artifacts":
            result = check_artifacts(lib, args.run)
        else:
            raise ValueError("Unknown command")
        return result, 2 if isinstance(result, dict) and result.get("ok") is False else 0
    finally:
        lib.close()


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    try:
        result, code = execute(args)
    except Exception as e:
        # CLI boundary: optional backends can raise their own error types. Never
        # print a success or leak a traceback instead of the documented JSON error.
        result, code = {"ok": False, "error": str(e), "error_type": type(e).__name__}, 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
