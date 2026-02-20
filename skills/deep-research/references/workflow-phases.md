# Research Workflow: Detailed Phase Guide

All outputs are organized by phase under the configured output directory: `~/deep-research-output/{slug}/`.

## Phase 1: Frontier

### Objective
Identify the **latest breakthroughs** and trending directions. Understand what the field looks like RIGHT NOW before broadening the search.

### Output Location
`phase1_frontier/`

### Steps

1. **Write config**: `phase1_frontier/paper_finder_config.yaml` targeting the most recent 1-2 years:
   ```yaml
   searches:
     - query: "{topic}"
       num_results: 50
       venues:
         neurips: [2025]
         icml: [2025]
         iclr: [2025, 2026]
         acl: [2025]
   output:
     root: ~/deep-research-output/{slug}/phase1_frontier/search_results
     overwrite: true
   ```

2. **Run paper_finder** (if available): `python <paper_finder_path>/paper_finder.py --mode scrape --config phase1_frontier/paper_finder_config.yaml`

3. **WebSearch for accepted papers**: "{topic} NeurIPS 2025 accepted", "{topic} ICML 2025 oral"

4. **Write frontier notes** → `phase1_frontier/frontier.md`
   - Key recent papers (title, venue, 1-line summary)
   - Trending directions (3-5 themes)
   - Active research groups

### Quality Checks
- At least 10 papers from the latest 1-2 conference cycles
- Clear picture of what's "hot" right now

---

## Phase 2: Survey

### Objective
Build a comprehensive landscape. Discover **35-80 relevant papers** spanning recent and foundational work.

### Output Location
`phase2_survey/`

### Steps

1. **Write config**: `phase2_survey/paper_finder_config.yaml` covering 2023-2025 across all major venues

2. **Search across sources** (save all to `phase2_survey/search_results/`):
   - **paper_finder (primary)**: Broad config, 2023-2025
   - **Semantic Scholar (supplementary)**: `--peer-reviewed-only`, save to `s2_results.jsonl`
   - **arXiv (preprints)**: Save to `arxiv_results.jsonl`

3. **Merge and deduplicate**:
   ```
   python ~/.claude/skills/deep-research/scripts/paper_db.py merge \
     --inputs phase1_frontier/search_results/*.jsonl phase2_survey/search_results/*.jsonl \
     --output paper_db.jsonl
   ```

4. **Filter to 35-80 papers** (critical step):
   ```
   python ~/.claude/skills/deep-research/scripts/paper_db.py filter \
     --input paper_db.jsonl -o paper_db.jsonl \
     --min-score 0.80 --max-papers 70 \
     --keywords agent bio drug protein reason plan
   ```

5. **Cluster and analyze**: Group by methodology, application domain

6. **Write survey notes** → `phase2_survey/survey.md`

### Quality Checks
- 35-80 papers in paper_db.jsonl (NOT more)
- At least 3 distinct themes identified
- Mix of recent and foundational papers

---

## Phase 3: Deep Dive

### Objective
Read 8-15 top papers in detail, extracting methodology, results, and connections.

### Output Location
`phase3_deep_dive/`

### Paper Selection Criteria
Select papers that maximize coverage across:
- **Citation impact**: Top-cited foundational work
- **Recency**: Papers from the last 12 months
- **Diversity**: Cover different themes from Phase 2
- **Methodology**: Different approaches (theoretical, empirical, system)

Write selection with rationale → `phase3_deep_dive/selection.md`

### Reading Each Paper

1. **Download PDFs**: `python ~/.claude/skills/deep-research/scripts/download_papers.py --jsonl paper_db.jsonl --output-dir phase3_deep_dive/papers/ --sort-by-citations --max-downloads 15`

2. **Read**: `Read phase3_deep_dive/papers/{file}.pdf` or `WebFetch https://ar5iv.labs.arxiv.org/html/{arxiv_id}`

3. **Extract structured notes** (per paper):
   - Problem statement
   - Key contributions (3-5 bullet points)
   - Methodology
   - Experiments: Datasets, baselines, metrics, main results
   - Limitations
   - Code/data links
   - Connections to other papers

4. **Write notes** → `phase3_deep_dive/deep_dive.md`

---

## Phase 4: Code & Tools

### Objective
Map the open-source ecosystem: implementations, frameworks, benchmarks, datasets.

### Output Location
`phase4_code/`

### Steps
1. Extract GitHub URLs from deep-dive papers
2. WebSearch: "site:github.com {method name}", "site:paperswithcode.com {topic}"
3. Evaluate: Stars, recency, documentation quality
4. Write → `phase4_code/code_repos.md`

---

## Phase 5: Synthesis

### Objective
Connect insights across papers. Build taxonomy, identify gaps.

### Output Location
`phase5_synthesis/`

### Analysis Steps

1. **Taxonomy of Approaches** — Hierarchical classification
2. **Comparative Table** — Method | Paper | Dataset | Metric | Result | Code
3. **Timeline** — Key developments by year
4. **Gap Analysis** — Open problems, contradictions, missing evaluations, future directions

### Output
- `phase5_synthesis/synthesis.md` — Taxonomy, tables, timeline
- `phase5_synthesis/gaps.md` — Gap analysis and future directions

---

## Phase 6: Compilation

### Objective
Assemble all research into a coherent, well-cited report.

### Output Location
`phase6_report/`

### Report Structure
```
# {Topic}: A Survey
## 1. Introduction
## 2. Background
## 3. Taxonomy of Approaches
## 4. Detailed Analysis
## 5. Applications
## 6. Open Problems and Future Directions
## 7. Conclusion
## References
```

### Steps
1. **Outline**: Draft section outline
2. **Assemble**: Pull content from all phase notes
3. **Citations**: Ensure every claim has `[@key]`
4. **BibTeX**: `python ~/.claude/skills/deep-research/scripts/bibtex_manager.py --jsonl paper_db.jsonl --output phase6_report/references.bib`
5. **Compile**: `python ~/.claude/skills/deep-research/scripts/compile_report.py --topic-dir ~/deep-research-output/{slug}/`
6. **Stats**: `python ~/.claude/skills/deep-research/scripts/paper_db.py stats --input paper_db.jsonl`

### Output
- `phase6_report/report.md` — Final report (2000-5000 words)
- `phase6_report/references.bib` — BibTeX bibliography
