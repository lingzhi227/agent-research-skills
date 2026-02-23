# GitHub Research — Phase Guide

Detailed methodology reference for the github-research skill.

## Phase 1: Intake — Detailed Guide

### Purpose
Extract structured information from deep-research output to seed GitHub discovery.

### Input Requirements
- Deep-research output directory containing:
  - `paper_db.jsonl` (required)
  - `phase4_code/code_repos.md` (optional but valuable)
  - `phase5_synthesis/synthesis.md` (optional)
  - `phase6_report/report.md` (optional)

### Keyword Extraction Strategy
- **Primary keywords**: From paper titles — extract 2-3 word technical phrases
- **Secondary keywords**: From paper tags in paper_db.jsonl
- **Tertiary keywords**: Method names, algorithm names, architecture names from synthesis
- **Author-based**: Search for prolific authors' GitHub profiles

### Expected Output
- 5-20 GitHub URLs directly from papers
- 10-30 search keywords of varying specificity
- Clear mapping: which papers mention which repos

### Edge Cases
- No code_repos.md: rely entirely on paper_db.jsonl keywords
- No paper_db.jsonl: ask user for manual topic keywords
- Non-English papers: extract English technical terms only

---

## Phase 2: Discovery — Detailed Guide

### Search Strategy Matrix
| Strategy | Query Pattern | Sort | When to Use |
|----------|--------------|------|-------------|
| Broad topic | "multi-agent LLM framework" | stars | Always — establishes landscape |
| Paper title | "{exact paper title}" | best-match | For each key paper |
| Method name | "{algorithm name} implementation" | stars | For specific techniques |
| Author search | "{author name}" + topic | updated | For prolific researchers |
| Code pattern | "class {ClassName}" | - | For specific implementations |
| Language-specific | topic + language:python | stars | When language matters |
| Awesome list | "awesome-{topic}" | stars | To find curated lists |

### Rate Limiting
- GitHub search API: 30 requests/minute (unauthenticated), 10 requests/minute (code search)
- Papers With Code API: ~60 requests/minute
- Always set GITHUB_TOKEN for higher limits (5000 req/hr)

### Deduplication
- Primary key: `repo_id` (owner/name, case-insensitive)
- When merging duplicates: keep record with more populated fields; merge paper_ids lists

### Target Numbers
- Aim for 50-200 unique repos before filtering
- Use at least 5 different search queries
- Check Papers With Code for all papers with arxiv_ids

---

## Phase 3: Filtering — Detailed Guide

### Scoring Deep Dive

**Activity Score** (0-1):
- Days since last push: <30d -> 0.9-1.0, 30-90d -> 0.6-0.8, 90-365d -> 0.3-0.5, >365d -> 0.0-0.2
- Frequency weight: pushed_at recency matters most

**Quality Score** (0-1):
- Stars (log-scaled, 30% weight): log(stars+1) normalized across set
- Forks (log-scaled, 20%): log(forks+1) normalized
- Has license (15%): any recognized license = 1.0
- Not archived (20%): archived repos get 0
- Has README (15%): non-empty readme_excerpt = 1.0

**Relevance Score** (0-1, manually assigned):
- 0.9-1.0: Direct implementation of a paper in the literature review
- 0.7-0.89: Closely related technique or framework
- 0.5-0.69: Related but tangential (e.g., general ML framework used by papers)
- 0.3-0.49: Loosely related (e.g., same domain, different approach)
- 0.0-0.29: Unlikely useful

**Composite**: relevance x 0.4 + quality x 0.35 + activity x 0.25

### Selection Criteria
- Always include: repos directly linked to papers
- Prefer: repos with tests, documentation, active maintenance
- Diversity: ensure mix of approaches, not just top-starred
- Minimum: 15 repos; Maximum: 30 repos

---

## Phase 4: Deep Dive — Detailed Guide

### What "Deep Dive" Means
This is NOT a README scan. You must:
1. Clone the repo (shallow)
2. Read the directory structure
3. Open and read key source files (model definitions, training loops, core algorithms)
4. Trace the execution flow from entry point to core logic
5. Evaluate code quality, documentation, test coverage

### Per-Repo Analysis Template
```markdown
# {owner/name} — Deep Dive Analysis

## Overview
- **Purpose**: {one-sentence}
- **Stars**: {N} | **Language**: {lang} | **License**: {license}
- **Last active**: {date} | **Composite score**: {score}

## Architecture
- Entry point: `{file}` -> calls `{function}` -> uses `{module}`
- Core modules: {list key files with purposes}
- Data flow: {how data moves through the system}

## Key Algorithms
- **{Algorithm 1}**: Implemented in `{file}:{lines}`, function `{name}`
  - Matches paper: {yes/no/partially} — {details}
- **{Algorithm 2}**: ...

## Code Quality
- Documentation: {poor/fair/good/excellent}
- Test coverage: {none/minimal/moderate/comprehensive}
- Code style: {consistent/inconsistent}, {patterns used}
- Error handling: {minimal/adequate/thorough}

## Dependencies
- Core: {list key deps}
- ML framework: {pytorch/tensorflow/jax/none}
- Hardware: {CPU only / GPU required / TPU supported}

## Reusability Assessment
- Ease of extraction: {easy/moderate/difficult}
- Tight couplings: {what's hard to separate}
- API surface: {clean/messy}
- Recommended components: {what to reuse}

## Limitations
- {limitation 1}
- {limitation 2}
```

### Prioritization
- Read model/algorithm files first (highest value)
- Then training/evaluation scripts
- Then configuration and entry points
- Skip: CI config, linting config, CHANGELOG

---

## Phase 5: Analysis — Detailed Guide

### Comparison Matrix Dimensions
Build a table comparing all deep-dived repos across:
1. Primary language & ML framework
2. Lines of code & file count
3. Code quality rating (1-5)
4. Paper fidelity (how closely it matches the paper)
5. Reusability rating (1-5)
6. Activity status (active/maintained/stale/archived)
7. Dependency count & overlap
8. License restrictiveness (permissive/copyleft/unknown)
9. Hardware requirements (CPU/GPU/TPU)

### Technique Map Construction
For each significant concept in the deep-research papers:
1. Identify the concept (e.g., "multi-head attention", "reward shaping")
2. Find implementations in analyzed repos
3. Note the specific file, class/function, and line numbers
4. Rate fidelity: faithful / modified / inspired-by / missing
5. Note any improvements or deviations from the paper

### Gap Analysis
Identify:
- Paper concepts with NO implementation found
- Implementations that deviate significantly from papers
- Missing components needed for a complete system
- Opportunities for novel contributions

---

## Phase 6: Blueprint — Detailed Guide

### Integration Plan Structure
1. **Objective**: What system are we building?
2. **Recommended Stack**: Best combination of repos
3. **Architecture Diagram** (text-based): How repos fit together
4. **Step-by-step Plan**:
   - Step 1: Start with {repo} as base
   - Step 2: Extract {component} from {repo}
   - Step 3: Adapt {module} to work with base
   - ...
5. **Risk Assessment**: License conflicts, version incompatibilities, maintenance risk
6. **Estimated Complexity**: Per-step effort estimate (trivial/moderate/significant)

### Reuse Catalog Format
For each extractable component:
- Source repo and file path
- What it does
- Dependencies required
- How to extract (copy files, install deps, adapt imports)
- API surface (key classes/functions, input/output types)
- Caveats and gotchas

### Quality Checklist
Before finalizing:
- [ ] Every paper concept has a code mapping (or explicit "not found")
- [ ] License compatibility checked for recommended stack
- [ ] Dependency conflicts identified between repos
- [ ] At least one "quick start" integration path identified
- [ ] Gaps clearly documented with suggested approaches
