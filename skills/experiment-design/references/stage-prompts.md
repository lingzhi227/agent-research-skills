# Experiment Design Stage Prompts

Extracted from AI-Scientist-v2 (agent_manager.py) and AI-Researcher (exp_analyser.py).

## 4-Stage Progressive Experiment Framework (AI-Scientist-v2)

### Stage 1: Initial Implementation
**Goal**: Get a working baseline on a simple dataset.

```
Stage 1 - Initial Implementation:
- Implement the core method on the simplest dataset
- Ensure training converges (check training curves)
- Establish baseline metrics
- Verify code runs without errors

Completion criteria:
- Training loss decreases
- Validation metrics are reasonable (not random)
- Code executes end-to-end without errors
```

### Stage 2: Baseline Tuning
**Goal**: Optimize hyperparameters and test on multiple datasets.

```
Stage 2 - Baseline Tuning:
- Tune learning rate, batch size, and key hyperparameters
- Test on at least 2 datasets
- Compare against published baselines
- Run 3 seeds for statistical significance

Completion criteria:
- Results competitive with or better than baselines
- Consistent across multiple seeds
- Training curves show stable convergence
```

### Stage 3: Creative Research
**Goal**: Novel improvements and comprehensive evaluation.

```
Stage 3 - Creative Research:
- Implement novel improvements to the method
- Test on 3+ datasets
- Compare against 3+ baselines
- Ablation of key design choices
- Generate publication-quality figures

Completion criteria:
- Clear improvement over baselines on most datasets
- Ablation supports contribution claims
- Figures are informative and well-designed
```

### Stage 4: Ablation Studies
**Goal**: Systematic component analysis.

```
Stage 4 - Ablation Studies:
- Remove/modify each key component one at a time
- Measure impact on performance
- Sensitivity analysis for key hyperparameters
- Report statistical significance (mean ± std over 3+ seeds)

Completion criteria:
- Every claimed contribution verified by ablation
- Hyperparameter sensitivity is reasonable
- Results table is complete with all comparisons
```

## VLM-Based Stage Completion Check (AI-Scientist-v2)

```
Examine the training curves and results:
1. Is the training loss decreasing?
2. Is validation performance improving?
3. Has the model converged or does it need more epochs?
4. Are there signs of overfitting?
5. Is the performance competitive with baselines?

Based on this analysis, determine if the current stage is complete
or if more experiments are needed.
```

## Best-Node Selection (AI-Scientist-v2)

```
Given the following experiment results and their training curves,
holistically select the best experiment considering:
1. Final test performance (primary metric)
2. Training stability (smooth loss curves)
3. Consistency across seeds
4. Generalization (train-test gap)

Experiment results:
{results_json}

Select the best experiment and justify your choice.
```

## Ablation Study Design (AI-Researcher)

```
Given the experimental results:
{results}

Design an ablation study to verify each component's contribution:
1. List all key components of the method
2. For each component, propose a variant where it is removed/replaced
3. Predict expected impact of each removal
4. Prioritize: test the most impactful ablations first
```

## Sensitivity Analysis (AI-Researcher)

```
Design a sensitivity analysis for these hyperparameters:
{hyperparameters}

For each hyperparameter:
1. Define a reasonable range to test
2. Specify the number of values to try
3. Identify which metrics to track
4. Note any interactions between hyperparameters
```
