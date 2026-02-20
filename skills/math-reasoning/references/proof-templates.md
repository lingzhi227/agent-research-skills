# Proof Templates for Research Papers

## Theorem Environment

```latex
\begin{theorem}[Name]
\label{thm:name}
Let $f: \mathcal{X} \to \mathcal{Y}$ be a continuous function. Then ...
\end{theorem}

\begin{proof}
We prove by [technique]. ...

[Step 1] ...
[Step 2] ...
Therefore, ... \qed
\end{proof}
```

## Supporting Environments

```latex
\begin{lemma}[Helper result]
\label{lem:helper}
For all $x \in \mathcal{X}$, ...
\end{lemma}

\begin{proposition}
\label{prop:name}
Under Assumption~\ref{asm:name}, ...
\end{proposition}

\begin{corollary}
\label{cor:name}
As a direct consequence of Theorem~\ref{thm:name}, ...
\end{corollary}

\begin{definition}[Concept Name]
\label{def:name}
We define ... as ...
\end{definition}

\begin{assumption}
\label{asm:name}
We assume that ...
\end{assumption}

\begin{remark}
Note that this result implies ...
\end{remark}
```

## Proof Techniques

### Direct Proof
```latex
\begin{proof}
Assume the premises hold. We have:
\begin{align}
    f(x) &= ... \label{eq:step1} \\
    &\leq ... \tag{by Lemma~\ref{lem:helper}} \\
    &= ... \nonumber
\end{align}
which completes the proof.
\end{proof}
```

### Proof by Contradiction
```latex
\begin{proof}
Suppose for contradiction that $\neg P$. Then ...
This contradicts the assumption that ..., completing the proof.
\end{proof}
```

### Proof by Induction
```latex
\begin{proof}
We prove by induction on $n$.

\textbf{Base case} ($n = 1$): ...

\textbf{Inductive step}: Assume the statement holds for $n = k$.
We show it holds for $n = k + 1$:
\begin{align}
    f(k+1) &= f(k) + g(k) \\
    &\leq ... \tag{by inductive hypothesis} \\
    &= ...
\end{align}
By the principle of mathematical induction, the result holds for all $n \geq 1$.
\end{proof}
```

### Convergence Proof (common in ML)
```latex
\begin{theorem}[Convergence Rate]
\label{thm:convergence}
Under Assumptions~\ref{asm:smoothness} and~\ref{asm:bounded_var}, Algorithm~\ref{alg:method}
with step size $\eta = \frac{1}{\sqrt{T}}$ satisfies:
\begin{equation}
    \frac{1}{T} \sum_{t=1}^{T} \mathbb{E}\left[\|\nabla f(\theta_t)\|^2\right] \leq \frac{2(f(\theta_1) - f^*)}{\sqrt{T}} + \frac{L\sigma^2}{\sqrt{T}}
\end{equation}
\end{theorem}
```

### Generalization Bound (common in learning theory)
```latex
\begin{theorem}[Generalization Bound]
\label{thm:generalization}
Let $\mathcal{F}$ be a function class with Rademacher complexity $\mathfrak{R}_n(\mathcal{F})$.
For any $\delta > 0$, with probability at least $1 - \delta$ over the draw of $n$ samples:
\begin{equation}
    \sup_{f \in \mathcal{F}} \left| \hat{R}(f) - R(f) \right| \leq 2\mathfrak{R}_n(\mathcal{F}) + \sqrt{\frac{\log(2/\delta)}{2n}}
\end{equation}
\end{theorem}
```

## Complexity Analysis Template
```latex
\begin{proposition}[Computational Complexity]
\label{prop:complexity}
Algorithm~\ref{alg:method} has time complexity $\mathcal{O}(nd^2)$ and
space complexity $\mathcal{O}(nd)$, where $n$ is the number of samples
and $d$ is the input dimension.
\end{proposition}
```
