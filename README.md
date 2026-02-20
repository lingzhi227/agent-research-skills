# claude-skills

30 skills for [Claude Code](https://claude.ai/code) covering the full academic research paper lifecycle — from literature search to slide generation.

Extracted from 17 GitHub repos studying LLM-agent-driven research automation. See [SKILLS_DESIGN.md](/Users/lingzhi/Code/research-engine/SKILLS_DESIGN.md) for the original design specifications.

## Installation

### One-line install

```bash
npx skills add lingzhi227/claude-skills -g -a claude-code
```

> Use the `-g` (global) flag. Scripts use `~/.claude/skills/` paths that require global installation.

### Post-install setup

```bash
git clone https://github.com/lingzhi227/claude-skills.git /tmp/claude-skills
/tmp/claude-skills/install.sh
rm -rf /tmp/claude-skills
```

This installs slash commands, checks Python dependencies, and verifies script syntax.

### Optional dependencies

| Package | Required by | Install |
|---------|------------|---------|
| Python 3 | All scripts | `brew install python3` |
| PyMuPDF | `self-review`, `deep-research` (PDF parsing) | `pip install PyMuPDF` |
| numpy + scipy | `data-analysis` (statistical tests) | `pip install numpy scipy` |

### Optional configuration

1. **Semantic Scholar API key** (higher rate limits for literature search):
   - Get one at https://www.semanticscholar.org/product/api#api-key
   - Save in `~/keys.md`: `S2_API_Key: your-key-here`

2. **Output directory**: Deep research outputs go to `~/deep-research-output/` by default.

## Available Skills (30)

### Phase 0: Research Discovery & Planning

| Skill | Description | Scripts |
|-------|-------------|---------|
| **[deep-research](skills/deep-research/)** | 6-phase systematic literature survey (frontier → survey → deep dive → code → synthesis → report) | 7 scripts: search APIs, PDF extraction, paper DB, BibTeX, report compilation |
| **[literature-search](skills/literature-search/)** | Multi-source academic search (Semantic Scholar, arXiv, OpenAlex, CrossRef) with ranking | 4 scripts: `search_crossref.py`, `download_arxiv_source.py`, `search_openalex.py` + shared |
| **[literature-review](skills/literature-review/)** | Multi-perspective dialogue simulation with expert personas for grounded literature review | Shares search scripts |
| **[idea-generation](skills/idea-generation/)** | Generate and score research ideas (Interestingness/Feasibility/Novelty) with iterative refinement | 1 script: `novelty_check.py` |
| **[novelty-assessment](skills/novelty-assessment/)** | Harsh-critic novelty evaluation with up to 10 rounds of literature search | Shares search scripts |
| **[research-planning](skills/research-planning/)** | 4-stage research plan design with task dependency graphs | Prompt-only |

### Phase 1: Method Design

| Skill | Description | Scripts |
|-------|-------------|---------|
| **[atomic-decomposition](skills/atomic-decomposition/)** | Decompose ideas into atomic concepts with bidirectional math ↔ code mapping | Prompt-only |
| **[algorithm-design](skills/algorithm-design/)** | Algorithm pseudocode (LaTeX) + UML diagrams (Mermaid) with consistency verification | Prompt-only |
| **[math-reasoning](skills/math-reasoning/)** | Derivations, proofs, formalization, statistical test selection, notation tables | Prompt-only |
| **[symbolic-equation](skills/symbolic-equation/)** | LLM-guided evolutionary search for scientific equation discovery | Prompt-only |

### Phase 2: Experiment Pipeline

| Skill | Description | Scripts |
|-------|-------------|---------|
| **[experiment-design](skills/experiment-design/)** | 4-stage progressive experiment planning (implement → tune → research → ablate) | 1 script: `design_experiments.py` |
| **[experiment-code](skills/experiment-code/)** | ML training/evaluation pipeline generation with iterative improvement | Prompt-only |
| **[code-debugging](skills/code-debugging/)** | Structured error analysis with categorization and 4-retry fix loop | Prompt-only |
| **[data-analysis](skills/data-analysis/)** | Statistical analysis with 4-round code review and appropriate test selection | 2 scripts: `stat_summary.py`, `format_pvalue.py` |

### Phase 3: Paper Writing

| Skill | Description | Scripts |
|-------|-------------|---------|
| **[paper-writing-section](skills/paper-writing-section/)** | Section-by-section writing with section-specific guidance and two-pass refinement | Prompt-only |
| **[related-work-writing](skills/related-work-writing/)** | Related Work section with thematic organization and compare-and-contrast style | Prompt-only |
| **[survey-generation](skills/survey-generation/)** | Complete survey paper via RAG-based subsection writing with citation validation | Shares search scripts |
| **[paper-to-code](skills/paper-to-code/)** | Convert paper PDF to runnable code repo (Planning → Analysis → Coding pipeline) | Prompt-only |

### Phase 4: Figures, Tables & Citations

| Skill | Description | Scripts |
|-------|-------------|---------|
| **[figure-generation](skills/figure-generation/)** | Publication-quality matplotlib figures with VLM feedback loop (10 figure types) | 1 script: `figure_template.py` |
| **[table-generation](skills/table-generation/)** | JSON/CSV → LaTeX booktabs tables with bold-best, significance stars, multi-dataset | 1 script: `results_to_table.py` |
| **[citation-management](skills/citation-management/)** | BibTeX harvesting, validation, deduplication, and auto-fix | 2 scripts: `harvest_citations.py`, `validate_citations.py` |
| **[backward-traceability](skills/backward-traceability/)** | Every PDF number hyperlinks to the code line that produced it | 1 script: `ref_numeric_values.py` |

### Phase 5: LaTeX & Compilation

| Skill | Description | Scripts |
|-------|-------------|---------|
| **[latex-formatting](skills/latex-formatting/)** | Conference templates (ICML/ICLR/NeurIPS/AAAI/ACL), formatting fixes, pre-submission checks | 2 scripts: `latex_checker.py`, `clean_latex.py` |
| **[paper-compilation](skills/paper-compilation/)** | Full pdflatex+bibtex pipeline with auto-fix error correction loop | 2 scripts: `compile_paper.py`, `fix_latex_errors.py` |
| **[excalidraw-skill](skills/excalidraw-skill/)** | Programmatic Excalidraw diagramming via MCP tools with quality verification | MCP server (7 CJS files) |

### Phase 6: Review & Polish

| Skill | Description | Scripts |
|-------|-------------|---------|
| **[self-review](skills/self-review/)** | 3-persona automated review (NeurIPS form) with reflection and meta-review | 2 scripts: `extract_pdf_text.py`, `parse_pdf_sections.py` |
| **[paper-revision](skills/paper-revision/)** | Map reviewer concerns to sections, apply targeted edits, verify improvements | Prompt-only |
| **[rebuttal-writing](skills/rebuttal-writing/)** | Point-by-point rebuttal with evidence-based responses | Prompt-only |
| **[slide-generation](skills/slide-generation/)** | Paper → Beamer slides (extract elements, generate skeleton, simplify) | 1 script: `extract_paper_elements.py` |
| **[paper-assembly](skills/paper-assembly/)** | End-to-end pipeline orchestrator with 9-phase checkpointing | 1 script: `assembly_checker.py` |

## Usage

### Slash commands

```
/research transformer architectures for long-context reasoning
```

### Natural language (skills activate automatically)

```
"Do a literature review on protein folding with LLMs"
"Write the Methods section of my paper"
"Generate a comparison table from results.json"
"Review my paper draft before submission"
"Make slides from my paper"
"Check if my idea is novel"
"Design experiments for my contrastive learning method"
```

### Direct script usage

```bash
# Search literature
python ~/.claude/skills/literature-search/scripts/search_crossref.py --query "attention mechanism" --rows 10

# Validate citations
python ~/.claude/skills/citation-management/scripts/validate_citations.py --tex paper/main.tex --bib paper/references.bib

# Generate experiment design
python ~/.claude/skills/experiment-design/scripts/design_experiments.py --method "contrastive learning" --task classification --format markdown

# Format p-values
python ~/.claude/skills/data-analysis/scripts/format_pvalue.py --values "0.001 0.05 0.23" --format latex

# Extract paper elements for slides
python ~/.claude/skills/slide-generation/scripts/extract_paper_elements.py --tex main.tex --output slides.tex

# Check paper pipeline completeness
python ~/.claude/skills/paper-assembly/scripts/assembly_checker.py --dir paper/ --verbose
```

## Architecture

All skills follow the same structure:

```
skills/<skill-name>/
├── SKILL.md           # Skill definition (prompt, workflow, rules)
├── scripts/           # Executable tools (optional)
│   └── *.py           # CLI scripts with argparse, docstring headers
└── references/        # Reference docs (optional)
    └── *.md           # Templates, API docs, patterns
```

**Design principles:**
- Scripts are stdlib-only where possible (no heavy dependencies)
- Every script has `--help`, docstring header with usage examples, and argparse CLI
- Skills link to each other via `## Related Skills` sections (upstream/downstream/see-also)
- Prompt-only skills are fully self-contained in SKILL.md

## Requirements

- [Claude Code](https://claude.ai/code)
- Python 3
- Optional: PyMuPDF, numpy, scipy (see installation)
