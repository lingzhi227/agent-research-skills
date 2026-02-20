#!/usr/bin/env python3
"""Generate experiment design from a research plan.

Takes a research plan (JSON or text description) and generates
a structured experiment design with baselines, ablation matrix,
hyperparameter grid, and evaluation metrics.

Self-contained: uses only stdlib.

Usage:
    python design_experiments.py --plan research_plan.json --output experiment_design.json
    python design_experiments.py --method "contrastive learning" --task "image classification" --output design.json
    python design_experiments.py --plan plan.json --format markdown
"""

import argparse
import json
import os
import sys


DEFAULT_HYPERPARAMS = {
    "learning_rate": [1e-4, 3e-4, 1e-3],
    "batch_size": [16, 32, 64],
    "epochs": [50, 100],
    "weight_decay": [0, 1e-4, 1e-2],
    "dropout": [0.0, 0.1, 0.3],
}

DEFAULT_METRICS = {
    "classification": ["accuracy", "f1_macro", "precision", "recall", "auroc"],
    "regression": ["mse", "mae", "r2", "rmse"],
    "generation": ["bleu", "rouge_l", "meteor", "perplexity"],
    "detection": ["map", "map50", "precision", "recall", "f1"],
    "segmentation": ["iou", "dice", "pixel_accuracy"],
    "retrieval": ["mrr", "ndcg", "recall_at_k", "precision_at_k"],
    "general": ["accuracy", "f1", "loss"],
}

STAGE_TEMPLATES = [
    {
        "name": "initial_implementation",
        "description": "Get a basic working implementation",
        "goals": [
            "Implement core method",
            "Run on simplest dataset",
            "Verify training loop works",
        ],
        "max_iterations": 5,
        "completion_criteria": "Working implementation with non-trivial performance",
    },
    {
        "name": "baseline_tuning",
        "description": "Tune hyperparameters and establish baselines",
        "goals": [
            "Tune learning rate and batch size",
            "Compare against at least 2 baselines",
            "Test on at least 2 datasets",
        ],
        "max_iterations": 10,
        "completion_criteria": "Stable training, improvement over baselines",
    },
    {
        "name": "creative_research",
        "description": "Explore novel improvements",
        "goals": [
            "Try architectural modifications",
            "Explore loss function variants",
            "Test on at least 3 datasets",
        ],
        "max_iterations": 15,
        "completion_criteria": "Demonstrated novel improvement",
    },
    {
        "name": "ablation_studies",
        "description": "Systematic component analysis",
        "goals": [
            "Ablate each proposed component",
            "Test sensitivity to hyperparameters",
            "Run with multiple random seeds",
        ],
        "max_iterations": 10,
        "completion_criteria": "All planned ablations completed",
    },
]


def generate_ablation_matrix(components: list[str]) -> list[dict]:
    """Generate ablation study matrix from component list."""
    ablations = [{"name": "Full Model", "components": {c: True for c in components}}]
    for comp in components:
        ablation = {
            "name": f"w/o {comp}",
            "components": {c: (c != comp) for c in components},
        }
        ablations.append(ablation)
    return ablations


def generate_design(plan: dict) -> dict:
    """Generate a full experiment design from a research plan."""
    method = plan.get("method", "proposed method")
    task_type = plan.get("task_type", "general")
    components = plan.get("components", ["component_A", "component_B", "component_C"])
    baselines = plan.get("baselines", [])
    datasets = plan.get("datasets", [])
    custom_metrics = plan.get("metrics", [])
    num_seeds = plan.get("num_seeds", 3)

    # Select metrics
    metrics = custom_metrics or DEFAULT_METRICS.get(task_type, DEFAULT_METRICS["general"])

    # Generate hyperparameter grid
    hp_grid = plan.get("hyperparameter_grid", {})
    if not hp_grid:
        hp_grid = {
            "learning_rate": DEFAULT_HYPERPARAMS["learning_rate"],
            "batch_size": DEFAULT_HYPERPARAMS["batch_size"],
        }

    # Generate ablation matrix
    ablations = generate_ablation_matrix(components)

    # Compute total experiments estimate
    n_hp_configs = 1
    for vals in hp_grid.values():
        n_hp_configs *= len(vals)
    n_datasets = max(len(datasets), 1)
    n_ablations = len(ablations)
    n_baselines = max(len(baselines), 1)
    total_runs = (n_hp_configs + n_ablations + n_baselines) * n_datasets * num_seeds

    design = {
        "method": method,
        "task_type": task_type,
        "stages": STAGE_TEMPLATES,
        "baselines": baselines,
        "datasets": datasets,
        "metrics": metrics,
        "primary_metric": metrics[0] if metrics else "accuracy",
        "components": components,
        "ablation_matrix": ablations,
        "hyperparameter_grid": hp_grid,
        "num_seeds": num_seeds,
        "estimated_total_runs": total_runs,
        "evaluation_protocol": {
            "report_mean_std": True,
            "statistical_test": "paired_ttest" if num_seeds >= 3 else "none",
            "significance_level": 0.05,
        },
    }

    return design


def format_markdown(design: dict) -> str:
    """Format experiment design as markdown."""
    lines = [f"# Experiment Design: {design['method']}\n"]

    lines.append(f"## Task Type: {design['task_type']}\n")

    lines.append("## Stages\n")
    for i, stage in enumerate(design["stages"], 1):
        lines.append(f"### Stage {i}: {stage['name']}")
        lines.append(f"{stage['description']}\n")
        for goal in stage["goals"]:
            lines.append(f"- {goal}")
        lines.append(f"- Completion: {stage['completion_criteria']}\n")

    if design["baselines"]:
        lines.append("## Baselines\n")
        for b in design["baselines"]:
            lines.append(f"- {b}")
        lines.append("")

    if design["datasets"]:
        lines.append("## Datasets\n")
        for d in design["datasets"]:
            lines.append(f"- {d}")
        lines.append("")

    lines.append("## Metrics\n")
    lines.append(f"Primary: **{design['primary_metric']}**\n")
    for m in design["metrics"]:
        lines.append(f"- {m}")
    lines.append("")

    lines.append("## Ablation Matrix\n")
    comps = design["components"]
    header = "| Variant | " + " | ".join(comps) + " |"
    sep = "|" + "|".join(["---"] * (len(comps) + 1)) + "|"
    lines.append(header)
    lines.append(sep)
    for ab in design["ablation_matrix"]:
        row = f"| {ab['name']} | "
        row += " | ".join("Y" if ab["components"][c] else "N" for c in comps)
        row += " |"
        lines.append(row)
    lines.append("")

    lines.append("## Hyperparameter Grid\n")
    for param, vals in design["hyperparameter_grid"].items():
        lines.append(f"- {param}: {vals}")
    lines.append("")

    lines.append(f"## Summary\n")
    lines.append(f"- Seeds: {design['num_seeds']}")
    lines.append(f"- Estimated total runs: {design['estimated_total_runs']}")
    lines.append(f"- Statistical test: {design['evaluation_protocol']['statistical_test']}")

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Generate experiment design from research plan")
    parser.add_argument("--plan", help="Research plan JSON file")
    parser.add_argument("--method", help="Method name (if no plan file)")
    parser.add_argument("--task", help="Task type: classification, regression, generation, etc.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json",
                        help="Output format (default: json)")
    parser.add_argument("--output", "-o", help="Output file")
    args = parser.parse_args()

    if args.plan and os.path.exists(args.plan):
        with open(args.plan, encoding="utf-8") as f:
            plan = json.load(f)
    elif args.method:
        plan = {
            "method": args.method,
            "task_type": args.task or "general",
        }
    else:
        print("Error: specify --plan or --method", file=sys.stderr)
        sys.exit(1)

    design = generate_design(plan)

    if args.format == "markdown":
        output = format_markdown(design)
    else:
        output = json.dumps(design, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Design written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
