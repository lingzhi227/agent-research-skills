# Rebuttal Writing Prompts Reference

Extracted from ChatReviewer.

## System Prompt (Verbatim from ChatReviewer)

```
You are the author, you submitted a paper, and the reviewers gave the review comments.
Please reply with what we have done, not what we will do.
You need to extract questions from the review comments one by one, and then respond point-to-point to the reviewers' concerns.
Please answer in {language}. Follow the format of the output later:
- Response to reviewers
#1 reviewer
Concern #1: xxxx
Author response: xxxxx

Concern #2: xxxx
Author response: xxxxx
...

#2 reviewer
Concern #1: xxxx
Author response: xxxxx

Concern #2: xxxx
Author response: xxxxx
...

#3 reviewer
Concern #1: xxxx
Author response: xxxxx

Concern #2: xxxx
Author response: xxxxx
...
```

## Review Format (for parsing input)

```
* Overall Review
Please briefly summarize the main points and contributions of this paper.

* Paper Strength
Please provide a list of the strengths of this paper.
(1) xxx
(2) xxx

* Paper Weakness
Please provide a numbered list of your main concerns regarding this paper.
(1) xxx
(2) xxx

* Questions To Authors And Suggestions For Rebuttal
Please provide a numbered list of specific and clear questions.

* Overall score (1-10)
```

## Output Format Template

```markdown
# Response to Reviewers

We thank all reviewers for their thoughtful and constructive feedback.
Below we address each concern point by point.
All changes in the revised manuscript are highlighted in blue.

## Summary of Major Changes

1. [Brief description of change 1]
2. [Brief description of change 2]
3. [Brief description of change 3]

---

## Reviewer #1

We thank Reviewer #1 for [brief positive acknowledgment].

**Concern #1:** [Extracted concern verbatim or accurately paraphrased]

**Author Response:** [Detailed response]
- [Specific evidence: "As shown in Table X / Section Y / Equation Z..."]
- [If new experiment was run: "We have conducted additional experiments..."]
- [Reference to revised manuscript: "We have clarified this in Section X (page Y)."]

**Concern #2:** [Extracted concern]

**Author Response:** [Detailed response]

---

## Reviewer #2

[Same structure as Reviewer #1]

---

## Reviewer #3

[Same structure as Reviewer #1]
```

## Response Strategies by Concern Type

### Missing Baselines / Comparisons
```
We appreciate this suggestion. We have added comparisons with [Method X] and [Method Y].
As shown in the updated Table Z, our method achieves [metric] of [value], which is [X%] higher than [Method X] ([value]) and [Y%] higher than [Method Y] ([value]).
These results have been added to Table Z in the revised manuscript.
```

### Insufficient Ablations
```
We agree that this analysis is important. We have conducted the requested ablation study.
As shown in the new Table Z:
- Removing Component A leads to a [X%] drop in [metric], confirming its contribution to [aspect].
- Removing Component B results in a [Y%] decrease, demonstrating its role in [aspect].
These results are now included in Section X.Y of the revised paper.
```

### Clarity / Writing Quality
```
We thank the reviewer for pointing this out. We have revised [Section X] to clarify [specific point].
Specifically, we have:
- Added a formal definition of [concept] in Section X.Y
- Included a figure (Figure Z) illustrating [process]
- Rewritten the paragraph on [topic] for improved clarity
```

### Theoretical Concerns
```
We appreciate this insightful question. [Formal response addressing the theoretical point]
We have added [Theorem/Proposition/Remark X] in Section Y to formally address this concern.
The key insight is that [explanation], which ensures [property].
```

### Scalability / Efficiency
```
We have conducted additional experiments to evaluate scalability.
- On [large dataset]: our method achieves [metric] in [time], compared to [baseline] which takes [time].
- Memory usage: [X] GB vs [Y] GB for [baseline].
- We have added a complexity analysis in Section X.Y showing that our method has [O(n)] complexity.
```

### Missing Related Work
```
We thank the reviewer for pointing us to this relevant work. We have added a discussion
of [Paper X] and [Paper Y] in the Related Work section. Our method differs from [Paper X]
in that [key difference]. Compared to [Paper Y], our approach [advantage].
```

## Key Principles

1. **Past tense / present perfect**: "We have added..." not "We will add..."
2. **Quantitative evidence**: Always include specific numbers, tables, figures
3. **Reference the manuscript**: "See Section X.Y, Table Z, Figure W"
4. **Acknowledge valid points**: "We agree with the reviewer that..."
5. **Be concise but thorough**: Each response should be self-contained
6. **Highlight changes**: Use blue text or clearly mark what changed in the revision
