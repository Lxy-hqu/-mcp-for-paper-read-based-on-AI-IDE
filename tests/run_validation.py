"""Persist actual unittest evidence, including skips, interpreter and capabilities."""
import io
import json
from pathlib import Path
import sys
import unittest
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'paper-research-mentor' / 'scripts'))
from pdf_io import doctor

suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_*.py')
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
out = ROOT / 'validation'
out.mkdir(exist_ok=True)
name = 'tests-bundled' if doctor()['packages']['pypdf'] else 'tests-stdlib'
(out / f'{name}.txt').write_text(stream.getvalue(), encoding='utf-8')
summary = {'executed_at_utc': datetime.now(timezone.utc).isoformat(), 'tests': result.testsRun,
           'failures': len(result.failures), 'errors': len(result.errors), 'skips': [(str(test), reason) for test, reason in result.skipped],
           'ok': result.wasSuccessful(), 'capabilities': doctor()}
(out / f'{name}.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k: summary[k] for k in ['tests', 'failures', 'errors', 'skips', 'ok']}))
sys.exit(0 if result.wasSuccessful() else 1)
