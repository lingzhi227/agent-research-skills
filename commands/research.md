---
description: Conduct a deep academic literature review on a topic
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, WebSearch, WebFetch, Task
---

# Deep Research: $ARGUMENTS

You are conducting a systematic academic literature review on: **$ARGUMENTS**

## Paper Quality Policy

**Peer-reviewed conference papers take priority over arXiv preprints.** arXiv papers have not undergone peer review and may contain unverified claims. Always prefer published conference/journal papers.

### Source Priority
1. **Top AI conferences**: NeurIPS, ICLR, ICML, ACL, EMNLP, NAACL, AAAI, IJCAI, CVPR, KDD (highest trust)
2. **Peer-reviewed journals**: JMLR, TACL, Nature, Science
3. **Workshop papers**: NeurIPS/ICML workshops
4. **arXiv with high citations**: Supplementary only
5. **Recent arXiv preprints**: Use cautiously, always mark as `(preprint)`

## Setup

1. Read `~/.claude/skills/deep-research/SKILL.md` for the workflow overview
2. Create output directory: `~/deep-research-output/{slug}/` with phase subdirectories
3. Read Semantic Scholar API key from `~/keys.md` (field `S2_API_Key`)

## Scripts (all at `~/.claude/skills/deep-research/scripts/`)

| Script | Purpose |
|--------|---------|
| `search_arxiv.py` | Search arXiv API, output JSONL |
| `search_semantic_scholar.py` | Search Semantic Scholar API |
| `download_papers.py` | Download PDFs from JSONL |
| `extract_pdf.py` | Extract text from PDFs (PyMuPDF) |
| `paper_db.py` | JSONL database management (merge, filter, dedup, tag, stats) |
| `bibtex_manager.py` | Generate BibTeX from JSONL |
| `compile_report.py` | Compile notes into final report with citations |

Invoke as: `python ~/.claude/skills/deep-research/scripts/<name>.py <args>`

## Output Structure

```
~/deep-research-output/{slug}/
├── paper_db.jsonl                    # Master database (accumulated across phases)
├── phase1_frontier/
│   ├── paper_finder_config.yaml
│   ├── search_results/
│   └── frontier.md
├── phase2_survey/
│   ├── paper_finder_config.yaml
│   ├── search_results/
│   └── survey.md
├── phase3_deep_dive/
│   ├── papers/
│   ├── selection.md
│   └── deep_dive.md
├── phase4_code/
│   └── code_repos.md
├── phase5_synthesis/
│   ├── synthesis.md
│   └── gaps.md
└── phase6_report/
    ├── report.md
    └── references.bib
```

## Execution

### Phase 1: Frontier
- Write `~/deep-research-output/{slug}/phase1_frontier/paper_finder_config.yaml` targeting latest 1-2 years
- Run paper_finder if available (see SKILL.md for setup)
- **WebSearch**: "{topic} NeurIPS 2025 accepted", "{topic} ICML 2025 oral"
- Identify trending directions and key recent breakthroughs
- Write `~/deep-research-output/{slug}/phase1_frontier/frontier.md`

### Phase 2: Survey
1. Write `~/deep-research-output/{slug}/phase2_survey/paper_finder_config.yaml` covering 2023-2025
2. **paper_finder (primary)**: Run scrape with broader config (if available)
3. **Semantic Scholar (supplementary)**: `python ~/.claude/skills/deep-research/scripts/search_semantic_scholar.py --query "..." --peer-reviewed-only --max-results 100 --api-key <key> -o ~/deep-research-output/{slug}/phase2_survey/search_results/s2_results.jsonl`
4. **arXiv (preprints)**: `python ~/.claude/skills/deep-research/scripts/search_arxiv.py --query "..." --max-results 50 -o ~/deep-research-output/{slug}/phase2_survey/search_results/arxiv_results.jsonl`
5. Merge: `python ~/.claude/skills/deep-research/scripts/paper_db.py merge --inputs ~/deep-research-output/{slug}/phase1_frontier/search_results/*.jsonl ~/deep-research-output/{slug}/phase2_survey/search_results/*.jsonl --output ~/deep-research-output/{slug}/paper_db.jsonl`
6. Filter to 35-80 papers: `python ~/.claude/skills/deep-research/scripts/paper_db.py filter --input ~/deep-research-output/{slug}/paper_db.jsonl -o ~/deep-research-output/{slug}/paper_db.jsonl --min-score 0.80 --max-papers 70`
7. Write `~/deep-research-output/{slug}/phase2_survey/survey.md`

### Phase 3: Deep Dive
- Select 8-15 papers, write rationale to `~/deep-research-output/{slug}/phase3_deep_dive/selection.md`
- Download PDFs: `python ~/.claude/skills/deep-research/scripts/download_papers.py --jsonl ~/deep-research-output/{slug}/paper_db.jsonl --output-dir ~/deep-research-output/{slug}/phase3_deep_dive/papers/ --sort-by-citations --max-downloads 15`
- Read via `Read` tool (PDFs) or `WebFetch` (ar5iv HTML: `https://ar5iv.labs.arxiv.org/html/{arxiv_id}`)
- Write structured notes to `~/deep-research-output/{slug}/phase3_deep_dive/deep_dive.md`

### Phase 4: Code & Tools
- Extract GitHub URLs from notes, web search for implementations
- Write `~/deep-research-output/{slug}/phase4_code/code_repos.md`

### Phase 5: Synthesis
- Cross-paper analysis: taxonomy, comparative tables, timeline
- **Weight peer-reviewed findings higher** in analysis
- Write `~/deep-research-output/{slug}/phase5_synthesis/synthesis.md`, `~/deep-research-output/{slug}/phase5_synthesis/gaps.md`

### Phase 6: Compilation
- Run: `python ~/.claude/skills/deep-research/scripts/compile_report.py --topic-dir ~/deep-research-output/{slug}/`
- Mark preprint citations with `(preprint)` suffix
- Structure: Introduction → Background → Taxonomy → Deep Analysis → Applications → Open Problems → References

## Key Rules
- **Peer-reviewed papers first**, arXiv as supplement
- Save after each phase (incremental progress)
- Use `[@key]` citation format; mark `(preprint)` for non-reviewed papers
- Read `~/.claude/skills/deep-research/references/workflow-phases.md` for detailed methodology
