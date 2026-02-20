# NeurIPS Review Form

> Extracted verbatim from AI-Scientist `perform_review.py`.

## Review Form Instructions

Below is a description of the questions you will be asked on the review form for each paper and some guidelines on what to consider when answering these questions.

1. **Summary**: Briefly summarize the paper and its contributions. This is not the place to critique the paper; the authors should generally agree with a well-written summary.

2. **Strengths and Weaknesses**: Please provide a thorough assessment of the strengths and weaknesses of the paper, touching on each of the following dimensions:
   - **Originality**: Are the tasks or methods new? Is the work a novel combination of well-known techniques? Is it clear how this work differs from previous contributions? Is related work adequately cited?
   - **Quality**: Is the submission technically sound? Are claims well supported (e.g., by theoretical analysis or experimental results)? Are the methods used appropriate? Is this a complete piece of work or work in progress?
   - **Clarity**: Is the submission clearly written? Is it well organized? Does it adequately inform the reader?
   - **Significance**: Are the results important? Are others likely to use the ideas or build on them? Does it advance the state of the art in a demonstrable way?

3. **Questions**: Please list and carefully describe any questions and suggestions for the authors.

4. **Limitations**: Have the authors adequately addressed the limitations and potential negative societal impact of their work?

5. **Soundness**: 1-4 scale (poor, fair, good, excellent)

6. **Presentation**: 1-4 scale (poor, fair, good, excellent)

7. **Contribution**: 1-4 scale (poor, fair, good, excellent)

8. **Overall**: 1-10 scale:
   - 10: Award quality
   - 9: Very Strong Accept
   - 8: Strong Accept
   - 7: Accept
   - 6: Weak Accept
   - 5: Borderline accept
   - 4: Borderline reject
   - 3: Reject
   - 2: Strong Reject
   - 1: Very Strong Reject

9. **Confidence**: 1-5 scale (low to absolute certainty)

10. **Decision**: Accept or Reject (binary only)

## Review JSON Format

```json
{
  "Summary": "...",
  "Strengths": ["..."],
  "Weaknesses": ["..."],
  "Originality": 3,
  "Quality": 3,
  "Clarity": 3,
  "Significance": 3,
  "Questions": ["..."],
  "Limitations": ["..."],
  "Ethical Concerns": false,
  "Soundness": 3,
  "Presentation": 3,
  "Contribution": 3,
  "Overall": 6,
  "Confidence": 4,
  "Decision": "Accept"
}
```

## Scoring Weights (from AgentLaboratory)

| Dimension | Weight | Scale |
|-----------|--------|-------|
| Overall | 1.0 | /10 |
| Contribution | 0.4 | /4 |
| Presentation | 0.2 | /4 |
| Soundness | 0.1 | /4 |
| Confidence | 0.1 | /5 |
| Originality | 0.1 | /4 |
| Significance | 0.1 | /4 |
| Clarity | 0.1 | /4 |
| Quality | 0.1 | /4 |

Weighted score formula: `(sum of weight × normalized_score) / sum_of_weights × 10`

NeurIPS acceptance bar: ~5.9/10. Workshop acceptance: ~6.0/10 (60-70% acceptance rate).

## Three Reviewer Personas (from AgentLaboratory)

1. **Harsh but fair**: Expects good experiments that lead to insights
2. **Harsh and critical**: Looking for impactful ideas in the field
3. **Open-minded**: Looking for novel ideas not proposed before

## Reflection Prompt (up to 5 rounds)

```
Round {N}/{total}.
In your thoughts, first carefully consider the accuracy and soundness of the review you just created.
Include any other factors that you think are important in evaluating the paper.
Ensure the review is clear and concise, and the JSON is in the correct format.
Do not make things overly complicated.
In the next attempt, try and refine and improve your review.
Stick to the spirit of the original review unless there are glaring issues.

If there is nothing to improve, simply repeat the previous JSON EXACTLY and include "I am done" at the end of the thoughts.
```
