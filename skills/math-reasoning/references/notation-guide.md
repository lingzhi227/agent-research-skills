# Standard Mathematical Notation for ML/AI Papers

## Spaces and Sets

| Concept | Notation | LaTeX |
|---------|----------|-------|
| Real numbers | ℝ | `\mathbb{R}` |
| Natural numbers | ℕ | `\mathbb{N}` |
| Integers | ℤ | `\mathbb{Z}` |
| d-dimensional reals | ℝ^d | `\mathbb{R}^d` |
| Input space | 𝒳 | `\mathcal{X}` |
| Output/label space | 𝒴 | `\mathcal{Y}` |
| Hypothesis space | 𝒫 | `\mathcal{H}` |
| Parameter space | Θ | `\Theta` |
| Dataset | 𝒟 | `\mathcal{D}` |
| Loss function | ℒ | `\mathcal{L}` |
| Model family | ℱ | `\mathcal{F}` |

## Probability and Statistics

| Concept | LaTeX |
|---------|-------|
| Expectation | `\mathbb{E}[\cdot]` or `\mathbb{E}_{p(x)}[\cdot]` |
| Probability | `\mathbb{P}(\cdot)` or `p(\cdot)` |
| Variance | `\mathrm{Var}[\cdot]` |
| Covariance | `\mathrm{Cov}[\cdot, \cdot]` |
| KL divergence | `D_{\mathrm{KL}}(p \| q)` |
| Mutual information | `I(X; Y)` |
| Entropy | `H(X)` or `\mathcal{H}(X)` |
| Normal distribution | `\mathcal{N}(\mu, \sigma^2)` |
| Indicator function | `\mathbb{1}[\cdot]` |

## Optimization

| Concept | LaTeX |
|---------|-------|
| Argmin | `\arg\min_{\theta \in \Theta}` |
| Argmax | `\arg\max_{\theta \in \Theta}` |
| Optimal params | `\theta^*` |
| Gradient | `\nabla_\theta \mathcal{L}` |
| Hessian | `\nabla^2 \mathcal{L}` |
| Learning rate | `\eta` or `\alpha` |

## Linear Algebra

| Concept | LaTeX |
|---------|-------|
| Vectors (bold lowercase) | `\mathbf{x}` or `\bm{x}` |
| Matrices (bold uppercase) | `\mathbf{W}` or `\bm{W}` |
| Transpose | `\mathbf{W}^\top` |
| Inverse | `\mathbf{W}^{-1}` |
| Norm | `\|\mathbf{x}\|` or `\|\mathbf{x}\|_2` |
| Inner product | `\langle \mathbf{x}, \mathbf{y} \rangle` |
| Trace | `\mathrm{tr}(\mathbf{A})` |
| Determinant | `\det(\mathbf{A})` or `|\mathbf{A}|` |
| Frobenius norm | `\|\mathbf{A}\|_F` |
| Hadamard product | `\mathbf{A} \odot \mathbf{B}` |

## Common ML Operations

| Concept | LaTeX |
|---------|-------|
| Softmax | `\mathrm{softmax}(\mathbf{z})_i = \frac{e^{z_i}}{\sum_j e^{z_j}}` |
| Sigmoid | `\sigma(x) = \frac{1}{1 + e^{-x}}` |
| ReLU | `\mathrm{ReLU}(x) = \max(0, x)` |
| Cross-entropy | `-\sum_i y_i \log \hat{y}_i` |
| MSE | `\frac{1}{n}\sum_i (y_i - \hat{y}_i)^2` |
| Attention | `\mathrm{Attention}(Q, K, V) = \mathrm{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V` |

## Useful LaTeX Declarations

```latex
\DeclareMathOperator*{\argmin}{arg\,min}
\DeclareMathOperator*{\argmax}{arg\,max}
\DeclareMathOperator{\tr}{tr}
\DeclareMathOperator{\diag}{diag}
\DeclareMathOperator{\rank}{rank}
\DeclareMathOperator{\softmax}{softmax}
\DeclareMathOperator{\sigmoid}{\sigma}

\newcommand{\R}{\mathbb{R}}
\newcommand{\E}{\mathbb{E}}
\newcommand{\Prob}{\mathbb{P}}
\newcommand{\bx}{\mathbf{x}}
\newcommand{\by}{\mathbf{y}}
\newcommand{\bW}{\mathbf{W}}
\newcommand{\btheta}{\boldsymbol{\theta}}
\newcommand{\norm}[1]{\left\| #1 \right\|}
\newcommand{\abs}[1]{\left| #1 \right|}
\newcommand{\inner}[2]{\langle #1, #2 \rangle}
\newcommand{\KL}[2]{D_{\mathrm{KL}}\left( #1 \| #2 \right)}
```

## Statistical Tests Decision Tree

### Comparing two groups
- Normal data → **paired/unpaired t-test**
- Non-normal → **Wilcoxon signed-rank / Mann-Whitney U**

### Comparing >2 groups
- Normal + equal variance → **one-way ANOVA + post-hoc Tukey HSD**
- Otherwise → **Kruskal-Wallis + post-hoc Dunn**

### Correlation
- Linear → **Pearson's r**
- Monotonic → **Spearman's ρ**

### Categorical data
- 2×2 → **Fisher's exact test / χ² test**
- Larger → **χ² test of independence**

### Multiple comparisons
- Always apply **Bonferroni correction** or **Benjamini-Hochberg FDR**
- Report: `α_corrected = α / k` where k = number of comparisons

### Reporting convention
```latex
The improvement is statistically significant
($p < 0.01$, paired $t$-test, $t(4) = 5.23$, Cohen's $d = 1.87$).
Results reported as mean $\pm$ std over $N = 5$ random seeds.
```
