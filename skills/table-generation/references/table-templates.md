# LaTeX Table Templates Reference

## Template 1: Simple Comparison Table (booktabs)

```latex
\begin{table}[htbp]
\centering
\caption{Performance comparison on benchmark datasets.}
\label{tab:main_results}
\begin{tabular}{lccc}
    \toprule
    Method & Dataset 1 & Dataset 2 & Dataset 3 \\
    \midrule
    Baseline 1 & 82.3$\pm$0.6 & 71.8$\pm$0.7 & 76.8$\pm$0.6 \\
    Baseline 2 & 83.5$\pm$0.4 & 73.3$\pm$0.5 & 80.1$\pm$0.7 \\
    Baseline 3 & 84.0$\pm$0.4 & 73.1$\pm$0.3 & 81.0$\pm$0.4 \\
    \midrule
    \textbf{Ours} & \textbf{84.2$\pm$0.4} & \textbf{73.4$\pm$0.4} & \textbf{81.1$\pm$0.4} \\
    \bottomrule
\end{tabular}
\end{table}
```

## Template 2: Grouped Comparison with multirow

```latex
\begin{table}[htbp]
\centering
\caption{Experiment results for node classification. Accuracy (\%) reported.}
\label{tab:node_clf}
\begin{threeparttable}
\renewcommand\tabcolsep{10pt}
\renewcommand\arraystretch{1.05}
\begin{tabular}{c|c|ccc}
    \toprule
    & Method & Cora & CiteSeer & PubMed \\
    \midrule
    \multirow{2}{*}{Supervised}
    & GCN & 81.5 & 70.3 & 79.0 \\
    & GAT & 83.0$\pm$0.7 & 72.5$\pm$0.7 & 79.0$\pm$0.3 \\
    \midrule
    \multirow{4}{*}{Self-supervised}
    & DGI & 82.3$\pm$0.6 & 71.8$\pm$0.7 & 76.8$\pm$0.6 \\
    & MVGRL & 83.5$\pm$0.4 & 73.3$\pm$0.5 & 80.1$\pm$0.7 \\
    & CCA-SSG & \underline{84.0$\pm$0.4} & 73.1$\pm$0.3 & \underline{81.0$\pm$0.4} \\
    & \textbf{Ours} & \textbf{84.2$\pm$0.4} & \textbf{73.4$\pm$0.4} & \textbf{81.1$\pm$0.4} \\
    \bottomrule
\end{tabular}
\begin{tablenotes}
    \footnotesize
    \item Best results in \textbf{bold}, second best \underline{underlined}.
\end{tablenotes}
\end{threeparttable}
\end{table}
```

## Template 3: Ablation Study

```latex
\begin{table}[htbp]
\centering
\caption{Ablation study on model components.}
\label{tab:ablation}
\begin{tabular}{lccc}
    \toprule
    Variant & Acc. (\%) & F1 (\%) & Params (M) \\
    \midrule
    Full model & \textbf{84.2} & \textbf{83.7} & 12.3 \\
    \quad w/o Component A & 82.1 & 81.5 & 10.1 \\
    \quad w/o Component B & 83.0 & 82.3 & 11.8 \\
    \quad w/o Component C & 81.5 & 80.9 & 9.5 \\
    \quad w/o A + B & 80.2 & 79.6 & 8.7 \\
    \bottomrule
\end{tabular}
\end{table}
```

## Template 4: Ablation with Checkmarks

```latex
\begin{table}[htbp]
\centering
\caption{Component ablation analysis.}
\label{tab:component_ablation}
\begin{tabular}{ccc|cc}
    \toprule
    Comp. A & Comp. B & Comp. C & Accuracy & F1 \\
    \midrule
    \checkmark & \checkmark & \checkmark & \textbf{84.2} & \textbf{83.7} \\
    & \checkmark & \checkmark & 82.1 & 81.5 \\
    \checkmark & & \checkmark & 83.0 & 82.3 \\
    \checkmark & \checkmark & & 81.5 & 80.9 \\
    & & & 78.3 & 77.1 \\
    \bottomrule
\end{tabular}
\end{table}
```

## Template 5: Wide Table (two-column, table*)

```latex
\begin{table*}[htbp]
\centering
\caption{Performance comparison across 4 datasets with multiple metrics.}
\label{tab:full_results}
\scriptsize
\begin{tabular}{l|cc|cc|cc|cc}
    \toprule
    & \multicolumn{2}{c|}{Dataset 1} & \multicolumn{2}{c|}{Dataset 2} & \multicolumn{2}{c|}{Dataset 3} & \multicolumn{2}{c}{Dataset 4} \\
    Method & R@20 & N@20 & R@20 & N@20 & R@20 & N@20 & R@20 & N@20 \\
    \midrule
    Baseline 1 & 0.0466 & 0.0395 & 0.0944 & 0.0522 & 0.1763 & 0.2101 & 0.0211 & 0.0154 \\
    Baseline 2 & 0.0526 & 0.0444 & 0.1030 & 0.0623 & 0.1833 & 0.2205 & 0.0327 & 0.0249 \\
    \textbf{Ours} & \textbf{0.0793} & \textbf{0.0668} & \textbf{0.1578} & \textbf{0.0935} & \textbf{0.2613} & \textbf{0.3106} & \textbf{0.0585} & \textbf{0.0436} \\
    \bottomrule
\end{tabular}
\end{table*}
```

## Template 6: Table with Notes (threeparttable)

```latex
\begin{table}[htbp]
\centering
\begin{threeparttable}
\caption{Statistical analysis of treatment effects.}
\label{tab:stats}
\begin{tabular}{lcccc}
    \toprule
    Variable & Coef. & SE & 95\% CI & $p$-value \\
    \midrule
    Treatment & 0.42 & 0.08 & (0.26, 0.58) & $<$0.001*** \\
    Age & $-$0.03 & 0.01 & ($-$0.05, $-$0.01) & 0.012* \\
    Gender (M) & 0.15 & 0.12 & ($-$0.09, 0.39) & 0.214 \\
    \bottomrule
\end{tabular}
\begin{tablenotes}
    \footnotesize
    \item \textbf{CI}: Confidence Interval. \textbf{SE}: Standard Error.
    \item Significance: * $p < 0.05$, ** $p < 0.01$, *** $p < 0.001$.
\end{tablenotes}
\end{threeparttable}
\end{table}
```

## Template 7: Dataset Statistics

```latex
\begin{table}[htbp]
\centering
\caption{Dataset statistics.}
\label{tab:datasets}
\begin{tabular}{lrrrr}
    \toprule
    Dataset & \#Train & \#Val & \#Test & \#Classes \\
    \midrule
    CIFAR-10 & 45,000 & 5,000 & 10,000 & 10 \\
    CIFAR-100 & 45,000 & 5,000 & 10,000 & 100 \\
    ImageNet & 1.2M & 50,000 & 100,000 & 1,000 \\
    \bottomrule
\end{tabular}
\end{table}
```

## Template 8: Hyperparameter Table

```latex
\begin{table}[htbp]
\centering
\caption{Hyperparameter settings.}
\label{tab:hyperparams}
\begin{tabular}{ll}
    \toprule
    Hyperparameter & Value \\
    \midrule
    Learning rate & 0.001 \\
    Batch size & 64 \\
    Optimizer & AdamW \\
    Weight decay & 0.01 \\
    Epochs & 100 \\
    Warmup steps & 1,000 \\
    Hidden dim & 256 \\
    \# Layers & 6 \\
    Dropout & 0.1 \\
    \bottomrule
\end{tabular}
\end{table}
```

## Formatting Rules

1. **Bold best results**: `\textbf{84.2}` for the best in each column
2. **Underline second best**: `\underline{83.5}` for runner-up
3. **Standard deviations**: Use `$\pm$` (e.g., `84.2$\pm$0.4`)
4. **Alignment**: `l` for text, `c` or `r` for numbers
5. **Required packages**: `booktabs`, `multirow`, `threeparttable`
6. **Use `table*`** for wide tables in two-column layouts
7. **Notes**: Use `threeparttable` + `tablenotes` for footnotes
8. **Thousands separator**: Use commas (1,000 not 1000)
9. **Negative numbers**: Use `$-$0.03` not `-0.03` for proper minus sign
