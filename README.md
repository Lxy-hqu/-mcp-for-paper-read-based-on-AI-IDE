<p align="center">
  <img src="docs/assets/hero.png" alt="Paper Research Mentor: an annotated paper becomes connected evidence, independent questions, and experimental ideas" width="100%" />
</p>

<h1 align="center">Paper Research Mentor</h1>

<p align="center"><strong>Read deeply. Think independently. Build with evidence.</strong></p>

<p align="center">
  A Codex skill for deep paper reading, reusable academic writing, and research ideas you can actually test.<br />
  From one paper to a body of literature—with the researcher involved in the reasoning.
</p>

<p align="center">
  <a href="https://github.com/Lxy-hqu/-mcp-for-paper-read-based-on-AI-IDE/actions/workflows/skill-tests.yml"><img src="https://github.com/Lxy-hqu/-mcp-for-paper-read-based-on-AI-IDE/actions/workflows/skill-tests.yml/badge.svg" alt="Skill tests" /></a>
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB" alt="Python 3.10 or newer" />
  <img src="https://img.shields.io/badge/storage-SQLite-0F766E" alt="SQLite storage" />
</p>

<p align="center">
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="#quick-start">Quick start</a> ·
  <a href="docs/usage.md">Usage guide</a> ·
  <a href="docs/example.md">Reading example</a> ·
  <a href="docs/mcp-guide.md">Legacy MCP</a>
</p>

## A paper should leave you with better questions

Paper Research Mentor turns a paper into an explanation of **what was proposed, how it works, what the evidence supports, and how to test a useful idea in your own project**.

Codex does the reading and analysis. Small local scripts preserve page locations, store evidence, check references, and keep discussion history. The skill connects those pieces into a repeatable research workflow.

**Two outcomes stay separate: a finished analysis and demonstrated understanding.** If the reader has not answered a thinking prompt, their understanding stays unverified. The skill examines ideas, competing explanations, and failure conditions without treating agreement as learning.

## What you get

| Output | What makes it useful |
|---|---|
| **A connected deep read** | Rebuild the problem → hypothesis → design → experiment → conclusion, with academic and plain-language explanations. |
| **Equations you can reason through** | Symbols, shapes, assumptions, intermediate steps, toy examples, and explicit parsing limits. |
| **An evidence map** | Link central claims to PDF pages, figures, tables, or equations; distinguish observations from interpretations. |
| **A writing toolkit** | Extract domain terms, useful collocations, sentence patterns, and paragraph structures with conditions for reuse. |
| **Project method suggestions** | Compare your baseline, a small adaptation, and a larger exploration; specify controls, metrics, cost, and stopping criteria. |
| **A literature synthesis** | Compare assumptions and experimental conditions across papers; keep genuine disagreements visible. |
| **A research discussion** | Predict, explain, challenge, revise. Preserve the reader's actual answers and the help they received. |
| **Reusable local records** | Search, resume, add later sources, and export SQLite-backed records to Markdown and JSON. |

The workflow adapts to theoretical, empirical, engineering, and machine-learning papers. Code and training materials are produced when applicable; other disciplines are not forced into a neural-network template.

## Quick start

Requires **Python 3.10+** and a Codex environment with local file/tool access. Git is needed for the clone command. The skill does not require the old MCP server, Node.js, Ollama, or a separate model API key.

```bash
git clone https://github.com/Lxy-hqu/-mcp-for-paper-read-based-on-AI-IDE.git paper-research-mentor
cd paper-research-mentor
python tools/install_skill.py
```

The installer copies the skill to `$CODEX_HOME/skills/paper-research-mentor`, or `~/.codex/skills/paper-research-mentor` when `CODEX_HOME` is unset. It verifies file hashes, preserves a different existing version as a backup, and builds a clean skill ZIP under `dist/`.

Attach a paper in Codex and ask:

```text
Use $paper-research-mentor to deeply read this paper.
Save a source-linked analysis, explain the key equations and experiments,
extract reusable writing patterns, and discuss the most consequential ideas with me.
```

For an automated first pass:

```text
Use $paper-research-mentor to complete the analysis without asking me questions.
Save the thinking prompts separately. Leave my understanding unverified.
```

The skill allows automatic matching for relevant reading requests; naming it explicitly selects the intended workflow. If it is not listed after installation, reopen the chat or restart Codex.

**[Full installation, dependency, and usage instructions →](docs/usage.md)**

## The workflow

```mermaid
flowchart LR
    A[Paper or corpus] --> B[Pages and source evidence]
    B --> C[Mechanisms and scientific critique]
    C --> D[Writing patterns and testable ideas]
    D --> E[Research discussion]
    E --> F[Recorded understanding and open questions]
```

Independent analysis continues while learning prompts await a response. A reader may skip a question or request a direct explanation. Answer exposure and hints are recorded; they do not silently become independent mastery.

### Try a project question

```text
Use $paper-research-mentor to compare these papers against the README,
dataset description, and experiment configuration in my current project.
Compare keeping the baseline, a low-cost adaptation, and a larger exploration.
For each idea, propose the smallest experiment that could disprove it.
```

If no project context is available, suggestions remain conditional. Reading a paper does not automatically authorize editing the project or launching training.

## A concrete example

The reading demonstration uses *Attention Is All You Need*, arXiv v7:

- It keeps the **41.8 in Table 2 vs. 41.0 in the same page's prose** as an unresolved source inconsistency.
- It distinguishes parallel training from autoregressive generation.
- It treats attention visualizations as illustrative evidence, rather than proof of causal explanations.
- It leaves all unanswered learning checkpoints **pending / unverified**.

**[Read the example and its source locations →](docs/example.md)**

The example includes source locations and an explicit record of what was checked.

## Designed to keep scientific boundaries visible

- **Source first:** central claims, numerical results, formulas, and writing patterns need resolvable evidence.
- **Unknown stays unknown:** missing hyperparameters and project facts are not replaced with customary defaults.
- **Reproduction has levels:** a code skeleton, a numerical smoke test, and a reproduced scientific result are different states.
- **Comparisons need conditions:** different datasets, splits, metrics, or budgets are not a universal leaderboard.
- **Data stays out of the skill package:** papers, reading databases, private context, and machine-specific manifests are excluded.

PDF extraction and storage can run locally. That does not imply the Codex model runs offline or that material sent to the host model remains on the computer.

## Validation

The recorded full local test run passes **36 automated tests**, supplemented by a full-paper reading demonstration and an independent forward review. Tests exercise provenance checks, metadata corrections, version handling, discussion-state constraints, later-source attachment, exports, and installation.

Real OCR accuracy, the optional installed-SymPy branch, real Ollama inference, and full WMT/BLEU reproduction have not been validated in that recorded run. Actual human learning outcomes have not been measured.

**[Validation scope and reproducible commands →](docs/validation.md)**

## Repository map

```text
paper-research-mentor/   Installable skill: instructions, references, scripts, template
tools/                  Installer and package audit
tests/                  Behavioral regression tests
docs/                   Usage, examples, validation, and MCP compatibility
src/                    Original TypeScript MCP implementation
```

This project grew from an MCP for AI-powered IDEs. **The original MCP remains available**; Codex users can use the skill directly. See the [compatibility guide](docs/mcp-guide.md) for setup and known implementation limits.

## Contributing

Useful contributions include difficult paper layouts, failures in evidence handling, better disciplinary reading guidance, and concrete examples where an explanation or transfer suggestion overreaches its evidence. See [CONTRIBUTING.md](CONTRIBUTING.md) for a small, reproducible workflow.
