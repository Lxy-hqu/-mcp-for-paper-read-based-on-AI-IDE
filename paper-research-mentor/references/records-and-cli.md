# Record contract and executable interface

Run all commands with an available Python. `<skill>` is this skill folder, `<lib>` is a USER output folder. Global `--library` goes before the subcommand. CLI returns JSON; exit 2 means invalid input/check failure. No external model calls occur.

```text
python <skill>/scripts/mentor.py doctor
python <skill>/scripts/mentor.py --library <lib> ingest <PDF-or-text-path-or-public-URL> --title <verified-title> --version <known-version>
python <skill>/scripts/mentor.py --library <lib> ingest <project.md> --role project
python <skill>/scripts/mentor.py --library <lib> metadata --paper <id> --file <known-metadata.json>
python <skill>/scripts/mentor.py --library <lib> start --papers <paper-id> [other-id ...] --mode full
python <skill>/scripts/mentor.py --library <lib> attach --run <existing-run> --papers <new-project-or-paper-id>
python <skill>/scripts/mentor.py --library <lib> pages --paper <id> --pages 1,3-5
python <skill>/scripts/mentor.py --library <lib> render --paper <id> --pages 3-4
python <skill>/scripts/mentor.py --library <lib> ocr --paper <id> --pages 2 --lang eng
python <skill>/scripts/mentor.py --library <lib> put --run <run-id> --file <batch.json>
python <skill>/scripts/mentor.py --library <lib> search "attention" --kind claim
python <skill>/scripts/mentor.py --library <lib> check --run <run-id>
python <skill>/scripts/mentor.py --library <lib> export --run <run-id>
python <skill>/scripts/mentor.py --library <lib> check-artifacts --run <run-id>
python <skill>/scripts/mentor.py --library <lib> update --run <run-id> --analysis complete --verification partial --notes-file <notes.json>
python <skill>/scripts/mentor.py --library <lib> status --run <run-id>
```

`ingest --backend pypdf` tests fallback; `--source-url` attaches provenance to saved readable text. URL HTML must first be resolved/extracted through browsing. Text split on form-feed uses page UNITS, not invented PDF pagination; use paragraph/section labels in the locator too. Source extraction lives at `sources/<id>/pages.json` and the original at `original.pdf` or `original.txt`. Printed PDF page labels may be unknown. Coordinates are PDF points with top-left origin from Poppler.

## Batch shape

`{"records": [record, ...]}`. Safe IDs match letters/digits plus `_.:-`; IDs are local to a run. All references are resolved in the resulting batch, so evidence may follow its claims. Invalid batches are atomic. Updating a record retains its previous revision. Checkpoint prompts cannot be overwritten.

Evidence example (replace with the ACTUAL source, passage and location):

```json
{
  "id": "E1", "kind": "evidence", "paper_id": "p-actual-id",
  "locator": {"page": 3, "section": "3.2.1", "equation": "1", "printed_page": "3"},
  "excerpt": "A short exact passage from that page",
  "verification": "text_checked"
}
```

`locator.page` is always a valid one-based extracted unit. `verification` is `unreviewed`, `text_checked` (short excerpt must match that page, whitespace/case normalized), or `visual_checked`. For visual review add `render_path` relative to the library and substantive `review_note`; the image must exist AND Codex must actually view it. For equations whose extraction is corrupt use a visually verified transcription and describe the discrepancy. A parser cannot judge semantic entailment.

All non-evidence/non-checkpoint records have `origin`: `author_claim`, `source_observation`, `model_inference`, `external_knowledge`, `proposal`. Every substantive record has `evidence_ids`; a note can explicitly lack support.

| kind | Required additional fields |
|---|---|
| claim | `text` |
| symbol | `symbol`, `definition`, `expression`, `parse_status` (`not_attempted`, `parsed`, `unsupported`, `failed`) |
| experiment | `description`, `reported` object, `unreported` list, `proposed` object, `validation_level` (`skeleton`, `smoke_checked`, `reproduced`, `not_applicable`) |
| writing | `category` (`term`, `collocation`, `sentence`, `paragraph`), `function`, `template`, `conditions`, `strength`, `adaptation` |
| transfer | `strategy` (`baseline`, `low_cost`, `exploration`), `problem`, `mechanism`, `assumptions`, `difference`, `minimal_experiment`, `metrics_cost`, `stop_criteria`; origin must be proposal |
| project | `facts`, `unknowns` |
| comparison | `text`, `comparability` |
| note | `text` |
| checkpoint | `prompt`, `stage` (`intuition`, `mechanism`, `transfer`); no origin, invented answer or mastery field |

Additional analytical fields are allowed. `reported` and `proposed` cannot duplicate a setting key. An actually run experiment level needs `validation_log`; the script checks its presence, while Codex must verify its content.

For no project context use `facts: {}`, a nonempty `unknowns` list, `context_status: "unavailable"` and `evidence_ids: []`. Do not cite paper passages as evidence of nonexistent project facts. A populated project profile requires actual project-source evidence.

`metadata --file` takes an object with known corrections: `title`, `authors`, publication `year`, `abstract`, `doi`, `source_url`, `version`. Unknowns may be null except title. Changes retain history. Duplicate ingestion keeps the source ID and applies explicitly supplied title/version/URL corrections, never inferred defaults. File creation year is not publication year.

## Discussion events

```text
python <skill>/scripts/mentor.py --library <lib> checkpoint --run <run> --id C1 --action answer --text-file <actual-user-answer.txt>
python <skill>/scripts/mentor.py --library <lib> checkpoint --run <run> --id C1 --action hint --text "The hint actually shown"
python <skill>/scripts/mentor.py --library <lib> checkpoint --run <run> --id C1 --action evaluate --assessment needs_hint --answer-event <event-id> --reason "Specific observed missing link"
```

Other actions: `partial_explanation`, `answer_exposed`, `skip` (requires real wording/reason). Do not use these commands to simulate a conversation outside a labeled test. Evaluation must reference the latest answer, include a reason, and respect help/exposure. A new answer resets its assessment to unverified. A skip removes any active mastery claim.

## Completion and export

When the user supplies project notes, a supplement or another paper later, ingest it, then `attach` it to the existing run. Genuine new sources reset analysis to in_progress and verification to pending/partial, preserving all previous checkpoints/events/coverage. Re-read relevant outputs and re-export after updating, rather than creating a disconnected run.

Notes JSON example: `{"coverage":{"p-actual-id":[1,2,3]},"report_path":"runs/r-actual-id/overview.md","limitations":["Unverified supplementary code"]}`. `complete` requires actual coverage of all main/supplement pages and an existing report, not a ledger. This is an honesty declaration, not automatic proof of reading. `verified` additionally requires nonempty reviewed evidence. Keep pending/partial whenever appropriate.

Export produces `records.json` (portable snapshot with events and sources) and `ledger.md`. Create substantive reports yourself alongside them. Cite evidence with `[EVID:E1]` and, when useful, `[E1](ledger.md#E1)`. Artifact checks validate local file links, explicit anchors, evidence IDs, fences and display-math pairing; they do not certify Mermaid or mathematical rendering.
