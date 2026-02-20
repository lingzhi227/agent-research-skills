# API Reference Guide

## arXiv API

### Base URL
```
http://export.arxiv.org/api/query
```

### Query Parameters
| Parameter | Description | Example |
|-----------|-------------|---------|
| `search_query` | Search terms with field prefixes | `all:transformer+AND+cat:cs.AI` |
| `start` | Offset for pagination | `0` |
| `max_results` | Results per page (max 100) | `50` |
| `sortBy` | Sort field | `relevance`, `lastUpdatedDate`, `submittedDate` |
| `sortOrder` | Sort direction | `descending`, `ascending` |

### Query Syntax
- **Field prefixes**: `ti:` (title), `au:` (author), `abs:` (abstract), `all:` (all fields), `cat:` (category)
- **Boolean operators**: `AND`, `OR`, `ANDNOT`
- **Grouping**: parentheses `()`
- **Examples**:
  - `all:transformer AND cat:cs.CL` — transformers in CL
  - `au:vaswani AND ti:attention` — Vaswani papers about attention
  - `(cat:cs.AI OR cat:cs.CL) AND all:"language model"` — LM papers in AI or CL

### Common Categories
| Category | Field |
|----------|-------|
| `cs.AI` | Artificial Intelligence |
| `cs.CL` | Computation and Language (NLP) |
| `cs.LG` | Machine Learning |
| `cs.CV` | Computer Vision |
| `cs.MA` | Multiagent Systems |
| `cs.SE` | Software Engineering |
| `q-bio.BM` | Biomolecules |
| `q-bio.GN` | Genomics |
| `q-bio.QM` | Quantitative Methods |
| `stat.ML` | Machine Learning (Statistics) |

### Rate Limits
- **1 request per 3 seconds** (be conservative)
- Results are Atom XML format
- Max 100 results per request, paginate for more

### Script Usage
```bash
python ~/.claude/skills/deep-research/scripts/search_arxiv.py \
  --query "long context reasoning LLM" \
  --max-results 50 \
  --categories cs.AI cs.CL \
  --sort-by relevance \
  --start-date 2023-01-01 \
  -o results.jsonl
```

### WebFetch Usage
```
WebFetch http://export.arxiv.org/api/query?search_query=all:transformer+AND+cat:cs.AI&max_results=10&sortBy=relevance
```
Parse the Atom XML response to extract paper entries.

---

## Semantic Scholar Graph API

### Base URL
```
https://api.semanticscholar.org/graph/v1
```

### Authentication
- API key from your configured keys file (field `S2_API_Key`)
- Header: `x-api-key: <key>`
- Without key: 100 requests/5 min. With key: 1 request/second sustained.

### Endpoints

#### Paper Search
```
GET /paper/search?query=...&fields=...&offset=0&limit=100
```

| Parameter | Description |
|-----------|-------------|
| `query` | Search string |
| `fields` | Comma-separated field list |
| `offset` | Pagination offset |
| `limit` | Results per page (max 100) |
| `year` | Year range filter (e.g., `2020-2026`, `2024-`, `-2020`) |
| `fieldsOfStudy` | Filter by field (e.g., `Computer Science`) |
| `venue` | Filter by venue |

#### Paper Details
```
GET /paper/{paper_id}?fields=...
```
`paper_id` can be: Semantic Scholar paperId, `arxiv:2401.12345`, `DOI:10.xxx`, `PMID:xxx`

#### Citations
```
GET /paper/{paper_id}/citations?fields=...&limit=1000
```
Returns papers that cite the given paper.

#### References
```
GET /paper/{paper_id}/references?fields=...&limit=1000
```
Returns papers referenced by the given paper.

#### Batch Paper Details
```
POST /paper/batch?fields=...
Body: {"ids": ["paper_id_1", "arxiv:2401.12345", ...]}
```
Get details for up to 500 papers at once.

### Useful Fields
```
title,authors,abstract,year,venue,citationCount,referenceCount,
externalIds,url,publicationDate,tldr,isOpenAccess,openAccessPdf
```

### Rate Limits
- **Public**: 100 requests per 5 minutes (burst)
- **Authenticated**: 1 request/second sustained, 10/second burst
- On 429: exponential backoff (2s, 4s, 8s)

### Script Usage
```bash
python ~/.claude/skills/deep-research/scripts/search_semantic_scholar.py \
  --query "long horizon reasoning LLM agent" \
  --max-results 100 \
  --min-citations 10 \
  --year-range 2022-2026 \
  --api-key <key> \
  -o results.jsonl
```

### WebFetch Usage
```
WebFetch https://api.semanticscholar.org/graph/v1/paper/search?query=long+horizon+reasoning&fields=title,authors,abstract,year,citationCount,externalIds&limit=20
```

For a specific paper:
```
WebFetch https://api.semanticscholar.org/graph/v1/paper/arxiv:2401.12345?fields=title,authors,abstract,year,citationCount,references
```

---

## ar5iv (HTML Paper Access)

### Overview
ar5iv renders arXiv papers as HTML5 pages. Use this when you need to read a paper without downloading the PDF, especially in WebFetch-only mode.

### URL Pattern
```
https://ar5iv.labs.arxiv.org/html/{arxiv_id}
```

### Examples
```
https://ar5iv.labs.arxiv.org/html/2401.12345
https://ar5iv.labs.arxiv.org/html/1706.03762
```

### WebFetch Usage
```
WebFetch https://ar5iv.labs.arxiv.org/html/1706.03762
Prompt: "Extract the abstract, introduction, methodology, and key results from this paper"
```

### Notes
- Not all papers render perfectly (LaTeX edge cases)
- Figures may not display but captions are usually available
- Math renders as MathML/text, readable but sometimes imperfect
- Very recent papers (< 24h) may not yet be available
- For papers that don't render, fall back to PDF via Read tool

---

## OpenReview API

### Base URL
```
https://api.openreview.net
```

### Paper Search by Venue
```
GET /notes?content.venue=ICLR+2024&limit=50
```

### WebFetch Usage
```
WebFetch https://api.openreview.net/notes?content.venue=NeurIPS+2024&content.title=reasoning&limit=20
Prompt: "Extract paper titles, authors, and ratings"
```

### Notes
- Useful for finding accepted papers at top venues with review scores
- Rate limiting is generous but be polite
- Reviews and scores available for many venues

---

## PDF Access Patterns

### Direct PDF Download (arXiv)
```
https://arxiv.org/pdf/{arxiv_id}
```

### Claude Code Read Tool
Claude Code's `Read` tool can natively read PDF files:
```
Read /path/to/downloaded/paper.pdf
```
This extracts text directly — no scripts needed for individual papers.

### Batch PDF Processing
For multiple papers, use the scripts:
```bash
python ~/.claude/skills/deep-research/scripts/download_papers.py \
  --jsonl paper_db.jsonl \
  --output-dir papers/ \
  --max-downloads 20 \
  --sort-by-citations

python ~/.claude/skills/deep-research/scripts/extract_pdf.py \
  --input papers/ \
  --output-dir texts/ \
  --sections
```
