# Data Analysis Review Prompts

Extracted from data-to-paper (hypothesis_testing/coding/analysis/coding.py) and AgentLaboratory.

## 4-Round Code Review System (data-to-paper)

### Round 1: Fundamental Code Flaws

```
### CHECK FOR FUNDAMENTAL FLAWS:
Check for any fundamental mathematical or statistical flaws in the code.

### CHECK FOR WRONG CALCULATIONS:
Explicitly list all key calculations and assess them.

### CHECK FOR MATH TRIVIALITIES:
Check for any mathematically trivial assessments / statistical tests.
For example, testing whether a value is different from zero when it is
defined as a sum of positive values.

### OTHER ISSUES:
Any other issues you find in the code.
```

### Round 2: Data Handling Issues

```
### DATASET PREPARATIONS:
- Missing values: Are missing values handled correctly?
- Units: Are units consistent and correctly converted?
- Data restriction: Is data appropriately filtered/restricted?

### DESCRIPTIVE STATISTICS:
Check for issues in descriptive statistics calculations.

### PREPROCESSING:
Review data preprocessing steps:
- Normalization / standardization
- Feature encoding
- Train/test split methodology

### ANALYSIS:
Check data analysis issues:
- Correct statistical test selection
- Assumptions met (normality, independence, etc.)
- Multiple comparisons correction

### STATISTICAL TESTS:
Check choice and implementation of statistical tests:
- Is the test appropriate for the data type?
- Are assumptions validated?
- Are p-values correctly computed and interpreted?
```

### Round 3: Per-Table Individual Review

```
### SENSIBLE NUMERIC VALUES:
Check each numeric value in the table:
- Are values within expected ranges?
- Do percentages sum to 100% where expected?
- Are decimal places appropriate?

### MEASURES OF UNCERTAINTY:
Does the table report measures of uncertainty?
- p-values for statistical tests
- Confidence intervals for estimates
- Standard deviations for means

### MISSING DATA:
Are we missing key variables or important results?

### OTHER ISSUES:
Any other issues you find in the table.
```

*Note: This round runs individually for each output file (df_*.pkl).*

### Round 4: Cross-Table Completeness

```
### COMPLETENESS OF TABLES:
Does the code create all needed results for the hypothesis testing plan?

### CONSISTENCY ACROSS TABLES:
Are tables consistent in:
- Variable naming conventions
- Measures of uncertainty reported
- Decimal precision
- Statistical test choices

### MISSING DATA:
Are we missing key variables or measures of uncertainty
that should be reported for a complete analysis?
```

## Allowed Packages Whitelist (data-to-paper)

```python
ALLOWED_PACKAGES = [
    'pandas',
    'numpy',
    'scipy',
    'statsmodels',
    'sklearn',
    'pingouin',     # For ANOVA and post-hoc tests
    'matplotlib',   # For diagnostic plots only
]
```

## Statistical Test Selection Guide

```
Select the appropriate statistical test based on:

| Data Type | Groups | Test |
|-----------|--------|------|
| Continuous, normal, 2 groups | Independent | Independent t-test |
| Continuous, normal, 2 groups | Paired | Paired t-test |
| Continuous, non-normal, 2 groups | Independent | Mann-Whitney U |
| Continuous, normal, 3+ groups | Independent | One-way ANOVA |
| Continuous, non-normal, 3+ groups | Independent | Kruskal-Wallis |
| Categorical, 2 variables | Independent | Chi-square test |
| Continuous, 2 variables | Correlation | Pearson/Spearman |
| Binary outcome | Multiple predictors | Logistic regression |

Always check assumptions before applying parametric tests:
1. Normality (Shapiro-Wilk test)
2. Homogeneity of variance (Levene's test)
3. Independence of observations
```

## Results Interpretation Dialogue (AgentLaboratory)

```
Postdoc guides PhD to extract insights:

1. "What are the key findings from the results?"
2. "Are there any surprising or unexpected results?"
3. "How do results compare to baselines?"
4. "What is the statistical significance of improvements?"
5. "Are there any failure cases or limitations?"
6. "What patterns do you observe across datasets?"
```
