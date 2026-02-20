# Literature Review Workflow Reference

Extracted from AgentLaboratory.

## PhD Student Literature Review Phase

### Phase Prompt
```
Your goal is to perform a literature review for the presented task and add papers to the literature review.
You have access to arXiv and can perform two search operations:
(1) finding many different paper summaries from a search query
(2) getting a single full paper text for an arXiv paper.
```

### Available Commands

#### SUMMARY — Search for papers
```
```SUMMARY
search query here
```
```
Returns: List of paper summaries matching the query from arXiv.

#### FULL_TEXT — Get complete paper
```
```FULL_TEXT
arXiv_paper_ID
```
```
Returns: Full text of the specified arXiv paper.

#### ADD_PAPER — Add paper to review
```
```ADD_PAPER
arXiv_paper_ID
PAPER_SUMMARY
```
```
Adds the paper with your summary to the official literature review.

### Rules
- Single command per turn
- Use ADD_PAPER when you find a relevant paper
- Don't use SUMMARY too many times (be targeted)
- Include three backticks at top and bottom of commands

## Workflow Pattern

```python
def literature_review(self):
    arx_eng = ArxivSearch()
    resp = self.phd.inference(self.research_topic, "literature review", step=0)

    for _i in range(max_tries):
        feedback = ""

        if "```SUMMARY" in resp:
            query = extract_prompt(resp, "SUMMARY")
            papers = arx_eng.find_papers_by_str(query, N=num_papers)
            feedback = f"Papers related to '{query}':\n{papers}"

        elif "```FULL_TEXT" in resp:
            paper_id = extract_prompt(resp, "FULL_TEXT")
            full_text = arx_eng.retrieve_full_paper_text(paper_id)
            feedback = full_text  # with expiration marker

        elif "```ADD_PAPER" in resp:
            paper_info = extract_prompt(resp, "ADD_PAPER")
            feedback, text = self.phd.add_review(paper_info, arx_eng)

        # Check if enough papers collected
        if len(self.phd.lit_review) >= num_papers_target:
            lit_review_sum = self.phd.format_review()
            return

        resp = self.phd.inference(
            self.research_topic, "literature review",
            feedback=feedback, step=_i + 1
        )
```

## Review Entry Structure

Each paper in the review contains:
```json
{
    "arxiv_id": "2301.12345",
    "title": "Paper Title",
    "summary": "Your summary of the paper and its relevance to the research topic"
}
```

## Integration with Paper Writing

The formatted literature review (`lit_review_sum`) is passed to:
1. **Plan Formulation** — Postdoc uses it to guide experiment planning
2. **Paper Writing** — Provided as context for Related Work and Introduction sections
3. **Result Interpretation** — Used to compare findings with prior work

## Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| num_papers_target | 5-10 | Papers to collect before stopping |
| max_tries | 20 | Maximum search iterations |
| num_papers (per query) | 10 | Papers returned per SUMMARY query |
