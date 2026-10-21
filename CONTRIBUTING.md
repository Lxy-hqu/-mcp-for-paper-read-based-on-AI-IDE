# Contributing

Useful contributions improve an observable research workflow: a difficult PDF layout, a missing provenance check, a confusing explanation, an unsupported scientific inference, or an interaction that mistakes agreement for understanding.

## Reproduce a problem

Include a public source URL or a minimal synthetic fixture, the relevant source version/page, the request or command, expected behavior, and actual behavior. For a content issue, explain which inference exceeds the evidence. Do not upload private papers, reading databases, credentials, personal paths, or genuine learner histories.

## Make a focused change

```bash
python -m unittest discover -s tests -v
```

PDF fixtures additionally use reportlab and Poppler; pypdf exercises the fallback path. Disclose skipped scenarios. Check skill-relative links if editing references. When changing scripts, add a regression test for an observable behavior rather than matching generated wording.

For packaging checks use an isolated destination:

```bash
python tools/install_skill.py --codex-home ./validation/codex-home
python tools/final_audit.py
```

Keep source observations, model inferences, proposals, reproduction status and real-user participation distinct. A script validating a record does not prove the record's scientific interpretation or the origin of an answer string.

The TypeScript MCP and the Python skill are separate implementations. Changes to one should not imply the other was tested. Do not introduce a model API key or mandatory service when instructions and existing tools already suffice.
