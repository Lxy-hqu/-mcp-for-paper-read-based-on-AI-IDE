"""Portable source-linked research library. No model calls or inferred findings."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

KINDS = {"evidence", "claim", "symbol", "experiment", "writing", "transfer", "project", "comparison", "checkpoint", "note"}
ORIGINS = {"author_claim", "source_observation", "model_inference", "external_knowledge", "proposal"}
ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_json(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def required(obj, fields):
    for key in fields:
        if key not in obj or obj[key] is None or obj[key] == "" or obj[key] == [] or (isinstance(obj[key], str) and not obj[key].strip()):
            raise ValueError(f"Missing nonempty field: {key}")


def norm(text):
    return re.sub(r"\s+", "", text.replace("\u00ad", "")).casefold()


class Library:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "papers.db")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        INSERT OR IGNORE INTO meta VALUES('schema_version','1');
        CREATE TABLE IF NOT EXISTS papers(
          id TEXT PRIMARY KEY, sha256 TEXT UNIQUE NOT NULL, title TEXT NOT NULL,
          source_path TEXT NOT NULL, source_url TEXT, version TEXT, role TEXT NOT NULL,
          format TEXT NOT NULL, page_count INTEGER NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS runs(
          id TEXT PRIMARY KEY, mode TEXT NOT NULL, analysis TEXT NOT NULL,
          verification TEXT NOT NULL, notes TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS run_papers(
          run_id TEXT REFERENCES runs(id), paper_id TEXT REFERENCES papers(id),
          PRIMARY KEY(run_id,paper_id));
        CREATE TABLE IF NOT EXISTS records(
          run_id TEXT REFERENCES runs(id), id TEXT, kind TEXT NOT NULL,
          data TEXT NOT NULL, updated_at TEXT NOT NULL, PRIMARY KEY(run_id,id));
        CREATE TABLE IF NOT EXISTS revisions(
          run_id TEXT, record_id TEXT, data TEXT, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS events(
          id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, checkpoint_id TEXT,
          action TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL,
          FOREIGN KEY(run_id,checkpoint_id) REFERENCES records(run_id,id));
        CREATE TABLE IF NOT EXISTS paper_metadata(
          paper_id TEXT PRIMARY KEY REFERENCES papers(id), data TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS metadata_history(
          paper_id TEXT REFERENCES papers(id), before_data TEXT, after_data TEXT, changed_at TEXT);
        """)
        version = self.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0]
        if version != "1":
            raise ValueError(f"Unsupported library schema {version}; refusing to modify it")

    def close(self):
        self.db.close()

    def paper(self, pid):
        row = self.db.execute("SELECT * FROM papers WHERE id=?", (pid,)).fetchone()
        if not row:
            raise ValueError(f"Unknown paper: {pid}")
        out = dict(row)
        extra = self.db.execute("SELECT data FROM paper_metadata WHERE paper_id=?", (pid,)).fetchone()
        out.update(json.loads(extra[0]) if extra else {})
        return out

    def metadata(self, pid, changes):
        old = self.paper(pid)
        allowed = {"title", "source_url", "version", "authors", "year", "abstract", "doi"}
        if not isinstance(changes, dict) or not changes or set(changes) - allowed:
            raise ValueError("Metadata supports title/source_url/version/authors/year/abstract/doi only")
        for key, value in changes.items():
            if key == "year":
                if value is not None and (type(value) is not int or not 1 <= value <= 9999):
                    raise ValueError("year must be an explicit publication year or null")
            elif value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"Metadata {key} must be a nonempty string or null")
        if changes.get("title", "not-set") is None:
            raise ValueError("Title cannot be null; retain a source filename when unknown")
        new = {**old, **changes}
        if new == old:
            return {"paper": old, "metadata_updated": False}
        extra = {k: new[k] for k in ("authors", "year", "abstract", "doi") if k in new}
        with self.db:
            self.db.execute("INSERT INTO metadata_history VALUES(?,?,?,?)", (pid, json.dumps(old, ensure_ascii=False), json.dumps(new, ensure_ascii=False), now()))
            self.db.execute("UPDATE papers SET title=?,source_url=?,version=? WHERE id=?", (new["title"], new["source_url"], new["version"], pid))
            self.db.execute("INSERT INTO paper_metadata VALUES(?,?) ON CONFLICT(paper_id) DO UPDATE SET data=excluded.data", (pid, json.dumps(extra, ensure_ascii=False)))
        return {"paper": self.paper(pid), "metadata_updated": True}

    def pages(self, pid):
        self.paper(pid)
        return read_json(self.root / "sources" / pid / "pages.json")["pages"]

    def source_info(self, pid):
        return read_json(self.root / "sources" / self.paper(pid)["id"] / "pages.json")

    def register(self, original, content, extracted, title=None, source_url=None, version=None, role="main", fmt="text"):
        if role not in {"main", "supplement", "code", "project", "external"}:
            raise ValueError("Invalid source role")
        digest = hashlib.sha256(content).hexdigest()
        pid = "p-" + digest[:20]
        existing = self.db.execute("SELECT * FROM papers WHERE sha256=?", (digest,)).fetchone()
        if existing:
            changes = {k: v for k, v in {"title": title, "source_url": source_url, "version": version}.items() if v is not None}
            result = self.metadata(existing["id"], changes) if changes else {"paper": self.paper(existing["id"]), "metadata_updated": False}
            return {**result, "duplicate": True}
        folder = self.root / "sources" / pid
        folder.mkdir(parents=True, exist_ok=True)
        suffix = ".pdf" if fmt == "pdf" else ".txt"
        source = folder / ("original" + suffix)
        source.write_bytes(content)
        write_json(folder / "pages.json", extracted)
        joined = "\n\n".join(f"=== PDF/page unit {p['page']} ===\n{p['text']}" for p in extracted["pages"])
        (folder / "fulltext.txt").write_text(joined, encoding="utf-8")
        title = title or extracted.get("metadata", {}).get("title") or Path(original).stem
        if not title.strip():
            title = pid
        with self.db:
            self.db.execute("INSERT INTO papers VALUES(?,?,?,?,?,?,?,?,?,?)", (
                pid, digest, title, str(source), source_url, version, role, fmt,
                len(extracted["pages"]), now()))
            author = extracted.get("metadata", {}).get("author")
            self.db.execute("INSERT INTO paper_metadata VALUES(?,?)", (pid, json.dumps({"authors": author, "year": None, "abstract": None, "doi": None}, ensure_ascii=False)))
        return {"paper": self.paper(pid), "duplicate": False, "warnings": extracted.get("warnings", [])}

    def start(self, pids, mode="full"):
        if mode not in {"full", "batch", "synthesis", "project"}:
            raise ValueError("Invalid mode")
        if not pids:
            raise ValueError("At least one source is required")
        for pid in pids:
            self.paper(pid)
        rid = "r-" + uuid.uuid4().hex[:16]
        with self.db:
            self.db.execute("INSERT INTO runs VALUES(?,?,?,?,?,?)", (rid, mode, "in_progress", "pending", "{}", now()))
            self.db.executemany("INSERT INTO run_papers VALUES(?,?)", ((rid, p) for p in dict.fromkeys(pids)))
        (self.root / "runs" / rid).mkdir(parents=True, exist_ok=True)
        return self.status(rid)

    def run(self, rid):
        row = self.db.execute("SELECT * FROM runs WHERE id=?", (rid,)).fetchone()
        if not row:
            raise ValueError(f"Unknown run: {rid}")
        out = dict(row)
        out["notes"] = json.loads(out["notes"])
        out["paper_ids"] = [r[0] for r in self.db.execute("SELECT paper_id FROM run_papers WHERE run_id=? ORDER BY paper_id", (rid,))]
        return out

    def records(self, rid):
        self.run(rid)
        return [json.loads(r[0]) for r in self.db.execute("SELECT data FROM records WHERE run_id=? ORDER BY id", (rid,))]

    def attach(self, rid, pids):
        run = self.run(rid)
        for pid in pids:
            self.paper(pid)
        added = [pid for pid in dict.fromkeys(pids) if pid not in run["paper_ids"]]
        if not added:
            return {"added": [], "run": self.status(rid)}
        notes = run["notes"]
        notes.setdefault("source_additions", []).append({"paper_ids": added, "at": now()})
        with self.db:
            self.db.executemany("INSERT INTO run_papers VALUES(?,?)", ((rid, p) for p in added))
            self.db.execute("UPDATE runs SET analysis='in_progress',verification=?,notes=? WHERE id=?", (
                "partial" if run["verification"] != "pending" else "pending", json.dumps(notes, ensure_ascii=False), rid))
        return {"added": added, "run": self.status(rid)}

    def events(self, rid, cid=None):
        self.run(rid)
        sql = "SELECT * FROM events WHERE run_id=?"
        args = [rid]
        if cid:
            sql += " AND checkpoint_id=?"
            args.append(cid)
        out = []
        for r in self.db.execute(sql + " ORDER BY id", args):
            entry = dict(r)
            entry["data"] = json.loads(entry["data"])
            out.append(entry)
        return out

    def validate_record(self, rec, run, merged):
        required(rec, ["id", "kind"])
        if not isinstance(rec["id"], str) or not ID.fullmatch(rec["id"]):
            raise ValueError("Record ID must be a safe 1-128 character identifier")
        kind = rec["kind"]
        if kind not in KINDS:
            raise ValueError(f"Unsupported kind: {kind}")
        if kind == "evidence":
            required(rec, ["paper_id", "locator", "excerpt", "verification"])
            if rec["paper_id"] not in run["paper_ids"]:
                raise ValueError("Evidence paper is not in this run")
            if not isinstance(rec["excerpt"], str) or len(rec["excerpt"]) > 1600:
                raise ValueError("Evidence excerpt must be a short string (<=1600 chars)")
            if not norm(rec["excerpt"]):
                raise ValueError("Evidence excerpt must contain nonempty normalized source text")
            loc = rec["locator"]
            pages = self.pages(rec["paper_id"])
            page = loc.get("page") if isinstance(loc, dict) else None
            if type(page) is not int or not 1 <= page <= len(pages):
                raise ValueError("locator.page must be a valid one-based PDF/page unit")
            if rec["verification"] not in {"unreviewed", "text_checked", "visual_checked"}:
                raise ValueError("Invalid evidence verification")
            if rec["verification"] == "text_checked" and norm(rec["excerpt"]) not in norm(pages[page - 1]["text"]):
                raise ValueError(f"Excerpt not found on declared page: {rec['id']}; use exact text or visually verify")
            if rec["verification"] == "visual_checked":
                required(rec, ["render_path", "review_note"])
                image_path = (self.root / rec["render_path"]).resolve()
                if not image_path.is_relative_to(self.root) or not image_path.is_file():
                    raise ValueError("Visual evidence needs an existing render inside the library")
                expected = {self.root / "sources" / rec["paper_id"] / name / f"page-{page:04d}.png" for name in ("renders", "ocr")}
                if image_path not in expected:
                    raise ValueError("Visual render must belong to this source and declared page")
                with image_path.open("rb") as handle:
                    header = handle.read(24)
                if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR' or int.from_bytes(header[16:20], 'big') < 1 or int.from_bytes(header[20:24], 'big') < 1:
                    raise ValueError("Visual render is not a PNG with valid dimensions")
        elif kind == "checkpoint":
            required(rec, ["prompt", "stage"])
            if rec["stage"] not in {"intuition", "mechanism", "transfer"}:
                raise ValueError("Invalid checkpoint stage")
            if any(k in rec for k in ("answer", "events", "mastery", "status", "assessment")):
                raise ValueError("Use checkpoint events for responses and evaluations")
        else:
            required(rec, ["origin"])
            if rec["origin"] not in ORIGINS:
                raise ValueError("Invalid provenance origin")
            fields = {
                "claim": ["text"], "symbol": ["symbol", "definition", "expression", "parse_status"],
                "experiment": ["description", "reported", "unreported", "proposed", "validation_level"],
                "writing": ["category", "function", "template", "conditions", "strength", "adaptation"],
                "transfer": ["strategy", "problem", "mechanism", "assumptions", "difference", "minimal_experiment", "metrics_cost", "stop_criteria"],
                "project": ["facts", "unknowns"], "comparison": ["text", "comparability"], "note": ["text"]}
            # Lists/dicts may legitimately be empty when explicitly present (e.g. no unknown settings).
            for key in fields[kind]:
                if key not in rec or rec[key] is None or rec[key] == "" or (isinstance(rec[key], str) and not rec[key].strip()):
                    raise ValueError(f"Missing field for {kind}: {key}")
            if kind == "symbol" and rec["parse_status"] not in {"not_attempted", "parsed", "unsupported", "failed"}:
                raise ValueError("Invalid parse_status")
            if kind == "experiment":
                if not isinstance(rec["reported"], dict) or not isinstance(rec["proposed"], dict) or not isinstance(rec["unreported"], list):
                    raise ValueError("reported/proposed must be objects; unreported a list")
                if set(rec["reported"]) & set(rec["proposed"]):
                    raise ValueError("Reported and proposed settings must not use the same key")
                if rec["validation_level"] not in {"skeleton", "smoke_checked", "reproduced", "not_applicable"}:
                    raise ValueError("Invalid validation_level")
                if rec["validation_level"] in {"smoke_checked", "reproduced"}:
                    required(rec, ["validation_log"])
            if kind == "writing" and rec["category"] not in {"term", "collocation", "sentence", "paragraph"}:
                raise ValueError("Invalid writing category")
            if kind == "transfer":
                if rec["origin"] != "proposal" or rec["strategy"] not in {"baseline", "low_cost", "exploration"}:
                    raise ValueError("Transfer must be a proposal with a valid strategy")
            if kind == "project":
                if not isinstance(rec["facts"], dict) or not isinstance(rec["unknowns"], list):
                    raise ValueError("Project facts must be an object; unknowns a list")
                if not rec["facts"] and (rec.get("context_status") != "unavailable" or not rec["unknowns"]):
                    raise ValueError("Unknown-only project requires context_status=unavailable and actual unknowns")
            refs = rec.get("evidence_ids", [])
            if not isinstance(refs, list) or any(not isinstance(r, str) for r in refs):
                raise ValueError("evidence_ids must be a list of strings")
            unknown_project = kind == "project" and not rec["facts"] and rec.get("context_status") == "unavailable"
            if kind != "note" and not unknown_project and not refs:
                raise ValueError(f"{kind} requires evidence_ids")
            for eid in refs:
                if eid not in merged or merged[eid].get("kind") != "evidence":
                    raise ValueError(f"Unknown evidence ID: {eid}")
            if kind == "project" and rec["facts"] and not any(self.paper(merged[eid]["paper_id"])["role"] == "project" for eid in refs):
                raise ValueError("Project facts need evidence from an ingested project-role source, not an unrelated paper")

    def put(self, rid, records):
        run = self.run(rid)
        if not isinstance(records, list) or not records:
            raise ValueError("records must be a nonempty list")
        old = {r["id"]: r for r in self.records(rid)}
        merged = dict(old)
        seen = set()
        for rec in records:
            if not isinstance(rec, dict):
                raise ValueError("Every record must be an object")
            required(rec, ["id", "kind"])
            if rec["id"] in seen:
                raise ValueError("Duplicate ID in input batch")
            seen.add(rec["id"])
            if rec["id"] in old and old[rec["id"]]["kind"] != rec["kind"]:
                raise ValueError("Cannot change record kind")
            if rec["id"] in old and rec["kind"] == "checkpoint" and old[rec["id"]] != rec:
                raise ValueError("Checkpoint prompts are immutable; create a new checkpoint")
            merged[rec["id"]] = rec
        # Validate the full resulting graph: updates must not invalidate existing dependents.
        for rec in merged.values():
            self.validate_record(rec, run, merged)
        if run["verification"] == "verified" and any(r["kind"] == "evidence" and r["verification"] == "unreviewed" for r in merged.values()):
            raise ValueError("Downgrade run verification before adding unreviewed evidence")
        with self.db:
            for rec in records:
                blob = json.dumps(rec, ensure_ascii=False)
                self.db.execute("INSERT INTO revisions VALUES(?,?,?,?)", (rid, rec["id"], blob, now()))
                self.db.execute("INSERT INTO records VALUES(?,?,?,?,?) ON CONFLICT(run_id,id) DO UPDATE SET data=excluded.data,updated_at=excluded.updated_at", (rid, rec["id"], rec["kind"], blob, now()))
        return {"saved": len(records), "run_id": rid}

    def checkpoint(self, rid, cid, action, text=None, assessment=None, answer_event=None, reason=None):
        records = {r["id"]: r for r in self.records(rid)}
        if records.get(cid, {}).get("kind") != "checkpoint":
            raise ValueError("Unknown checkpoint")
        history = self.events(rid, cid)
        if action not in {"answer", "hint", "partial_explanation", "answer_exposed", "skip", "evaluate"}:
            raise ValueError("Invalid checkpoint event")
        payload = {}
        if action in {"answer", "hint", "partial_explanation", "answer_exposed", "skip"}:
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Event text must be actual answer/help/skip reason")
            payload["text"] = text
        if action == "evaluate":
            if assessment not in {"needs_hint", "independent", "transferable"} or not reason:
                raise ValueError("Evaluation requires assessment and reason")
            answer = next((e for e in history if e["id"] == answer_event and e["action"] == "answer"), None)
            if answer is None:
                raise ValueError("Evaluation must reference a recorded answer event")
            if any(e["action"] == "answer" and e["id"] > answer_event for e in history):
                raise ValueError("Evaluate the latest answer, not an older one")
            if any(e["action"] == "skip" and e["id"] > answer_event for e in history):
                raise ValueError("A later skip invalidates evaluation of this attempt")
            helped = any(e["action"] in {"hint", "partial_explanation", "answer_exposed"} for e in history)
            if helped and assessment in {"independent", "transferable"}:
                raise ValueError("Assisted/exposed checkpoint cannot be independently mastered; use a new question")
            if assessment == "transferable" and records[cid]["stage"] != "transfer":
                raise ValueError("Transfer assessment requires a transfer-stage question")
            payload.update(assessment=assessment, answer_event=answer_event, reason=reason)
        with self.db:
            cur = self.db.execute("INSERT INTO events(run_id,checkpoint_id,action,data,created_at) VALUES(?,?,?,?,?)", (rid, cid, action, json.dumps(payload, ensure_ascii=False), now()))
        return {"event_id": cur.lastrowid, "checkpoint": self.checkpoint_state(rid, cid)}

    def checkpoint_state(self, rid, cid):
        history = self.events(rid, cid)
        state = {"id": cid, "participation": "pending", "understanding": "unverified", "assisted": False}
        for e in history:
            a = e["action"]
            if a == "answer":
                state.update(participation="answered", understanding="unverified")
            elif a == "skip":
                state.update(participation="skipped", understanding="unverified")
            elif a in {"hint", "partial_explanation", "answer_exposed"}:
                state.update(assisted=True, understanding="needs_hint" if state["participation"] == "answered" else "unverified")
            elif a == "evaluate":
                state["understanding"] = e["data"]["assessment"]
        return state

    def status(self, rid):
        out = self.run(rid)
        recs = self.records(rid)
        out["record_counts"] = {k: sum(r["kind"] == k for r in recs) for k in sorted(KINDS) if any(r["kind"] == k for r in recs)}
        out["checkpoints"] = [self.checkpoint_state(rid, r["id"]) for r in recs if r["kind"] == "checkpoint"]
        out["output_directory"] = str(self.root / "runs" / rid)
        return out

    def update(self, rid, analysis=None, verification=None, notes=None):
        run = self.run(rid)
        a, v = analysis or run["analysis"], verification or run["verification"]
        if a not in {"in_progress", "complete", "partial"} or v not in {"pending", "partial", "verified"}:
            raise ValueError("Invalid analysis/verification state")
        n = dict(run["notes"])
        if notes is not None:
            if not isinstance(notes, dict):
                raise ValueError("notes must be an object")
            n.update(notes)
        if a == "complete":
            coverage = n.get("coverage", {})
            for pid in run["paper_ids"]:
                paper = self.paper(pid)
                if paper["role"] in {"main", "supplement"}:
                    actual = coverage.get(pid, [])
                    if not isinstance(actual, list) or any(type(p) is not int for p in actual) or set(actual) != set(range(1, paper["page_count"] + 1)):
                        raise ValueError("Complete analysis needs actual per-page coverage for every main/supplement source")
            required(n, ["report_path"])
            report = (self.root / n["report_path"]).resolve()
            if not report.is_relative_to(self.root) or not report.is_file():
                raise ValueError("Complete analysis needs an existing substantive report inside the library")
            if report.name in {"ledger.md", "records.json"}:
                raise ValueError("A ledger is not a substantive report")
        if v == "verified":
            evidence = [r for r in self.records(rid) if r["kind"] == "evidence"]
            if not evidence or any(e["verification"] == "unreviewed" for e in evidence):
                raise ValueError("Verified needs nonempty reviewed evidence")
            for e in evidence:
                self.validate_record(e, run, {r["id"]: r for r in self.records(rid)})
        with self.db:
            self.db.execute("UPDATE runs SET analysis=?,verification=?,notes=? WHERE id=?", (a, v, json.dumps(n, ensure_ascii=False), rid))
        return self.status(rid)

    def search(self, query, kind=None):
        # Literal substring search: do not interpret user's %/_ as SQL wildcards.
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        pattern = "%" + escaped + "%"
        papers = [self.paper(r[0]) for r in self.db.execute("SELECT DISTINCT p.id FROM papers p LEFT JOIN paper_metadata m ON p.id=m.paper_id WHERE p.title LIKE ? ESCAPE '\\' OR m.data LIKE ? ESCAPE '\\'", (pattern, pattern))]
        sql, args = "SELECT run_id,data FROM records WHERE data LIKE ? ESCAPE '\\'", [pattern]
        if kind:
            if kind not in KINDS:
                raise ValueError("Invalid kind")
            sql += " AND kind=?"
            args.append(kind)
        records = [{"run_id": r[0], "record": json.loads(r[1])} for r in self.db.execute(sql + " ORDER BY run_id,id", args)]
        return {"papers": papers, "records": records}

    def check(self, rid):
        errors, warnings = [], []
        run = self.run(rid)
        recs = {r["id"]: r for r in self.records(rid)}
        for r in recs.values():
            try:
                self.validate_record(r, run, recs)
            except (ValueError, TypeError, KeyError) as e:
                errors.append(f"{r['id']}: {e}")
        for pid in run["paper_ids"]:
            info = self.source_info(pid)
            warnings.extend(f"{pid}: {w}" for w in info.get("warnings", []))
        if any(r["kind"] == "evidence" and r["verification"] == "unreviewed" for r in recs.values()):
            warnings.append("Some evidence is unreviewed")
        if not any(r["kind"] == "claim" for r in recs.values()):
            warnings.append("No substantive claim records yet")
        warnings.append("Structural validation does not establish semantic support or user understanding")
        return {"ok": not errors, "errors": errors, "warnings": warnings}

    def export(self, rid):
        status = self.status(rid)
        data = {"schema_version": 1, "run": status, "papers": [self.paper(p) for p in status["paper_ids"]], "records": self.records(rid), "events": self.events(rid)}
        folder = self.root / "runs" / rid
        write_json(folder / "records.json", data)
        lines = ["# 证据与讨论记录", "", "> 这是结构化记录导出，不替代深读报告；理解状态只来自已记录的真实回答。", "", f"分析：{status['analysis']}；核验：{status['verification']}", ""]
        evidence = {r["id"]: r for r in data["records"] if r["kind"] == "evidence"}
        for rec in data["records"]:
            lines += [f"<a id=\"{rec['id']}\"></a>", f"## {rec['id']} · {rec['kind']}", ""]
            if rec["kind"] == "evidence":
                paper = self.paper(rec["paper_id"])
                source_rel = Path(paper["source_path"]).relative_to(self.root).as_posix()
                from urllib.parse import quote
                label = f"{paper['title']} · PDF/page {rec['locator']['page']}"
                lines += [f"[{label}](../../{quote(source_rel)}#page={rec['locator']['page']})", "", rec["excerpt"], ""]
            else:
                for eid in rec.get("evidence_ids", []):
                    if eid in evidence:
                        lines.append(f"[{eid}](#{eid})")
            lines += ["```json", json.dumps(rec, ensure_ascii=False, indent=2), "```", ""]
        lines += ["## 参与状态", "", "```json", json.dumps(status["checkpoints"], ensure_ascii=False, indent=2), "```", "", "## 原始事件", "", "```json", json.dumps(data["events"], ensure_ascii=False, indent=2), "```", ""]
        (folder / "ledger.md").write_text("\n".join(lines), encoding="utf-8")
        return {"json": str(folder / "records.json"), "ledger": str(folder / "ledger.md")}
