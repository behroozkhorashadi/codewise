"""
Analysis module for the call-site context experiment.

Loads experiment results and computes:
    1. Score delta (condition B - condition A) per dimension
    2. Inter-model agreement (Claude vs GPT-4o correlation)
    3. Score consistency (variance across criteria)
    4. Summary statistics for thesis reporting
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

CRITERIA = [
    "separation_of_concerns",
    "documentation",
    "logic_clarity",
    "understandability",
    "efficiency",
    "error_handling",
    "testability",
    "reusability",
    "code_consistency",
    "dependency_management",
    "security_awareness",
    "side_effects",
    "scalability",
    "resource_management",
    "encapsulation",
    "readability",
]

MODELS = ["gpt-4o", "claude"]


def load_results(results_dir: str = "outputs/experiment") -> List[Dict[str, Any]]:
    all_results = []
    for path in Path(results_dir).glob("*.json"):
        if "progress" in path.name:
            continue
        with open(path) as f:
            data = json.load(f)
        if isinstance(data, list):
            all_results.extend([r for r in data if isinstance(r, dict) and "condition_a" in r])
    return all_results


def _get_scores(condition: Dict[str, Any], model: str) -> Dict[str, int]:
    model_result = condition.get(model, {})
    if "error" in model_result:
        return {}
    scores = model_result.get("criteria_scores", {})
    overall = model_result.get("overall_score")
    if overall is not None:
        scores["overall"] = overall
    return scores


def score_delta(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Compute mean score delta (B - A) per criterion per model.
    Positive delta = context improved the score.
    """
    deltas: Dict[str, Dict[str, List[int]]] = {model: {c: [] for c in CRITERIA + ["overall"]} for model in MODELS}

    for r in results:
        for model in MODELS:
            scores_a = _get_scores(r["condition_a"], model)
            scores_b = _get_scores(r["condition_b"], model)
            if not scores_a or not scores_b:
                continue
            for criterion in CRITERIA + ["overall"]:
                if criterion in scores_a and criterion in scores_b:
                    deltas[model][criterion].append(scores_b[criterion] - scores_a[criterion])

    return {
        model: {criterion: round(sum(vals) / len(vals), 3) if vals else None for criterion, vals in criteria.items()}
        for model, criteria in deltas.items()
    }


def inter_model_agreement(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Compute Pearson correlation between GPT-4o and Claude scores per condition per criterion.
    Higher correlation = models agree more.
    """
    from math import sqrt

    def pearson(x: List[float], y: List[float]) -> float:
        n = len(x)
        if n < 2:
            return None
        mx, my = sum(x) / n, sum(y) / n
        num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
        den = sqrt(sum((xi - mx) ** 2 for xi in x)) * sqrt(sum((yi - my) ** 2 for yi in y))
        return round(num / den, 3) if den else None

    agreement = {}
    for condition_key in ["condition_a", "condition_b"]:
        agreement[condition_key] = {}
        for criterion in CRITERIA + ["overall"]:
            gpt_scores, claude_scores = [], []
            for r in results:
                g = _get_scores(r[condition_key], "gpt-4o")
                c = _get_scores(r[condition_key], "claude")
                if criterion in g and criterion in c:
                    gpt_scores.append(g[criterion])
                    claude_scores.append(c[criterion])
            agreement[condition_key][criterion] = pearson(gpt_scores, claude_scores)

    return agreement


def score_variance(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """
    Compute mean variance across criteria scores per condition per model.
    Lower variance = more consistent scoring.
    """
    from statistics import variance

    var: Dict[str, Dict[str, List[float]]] = {f"{model}_{cond}": [] for model in MODELS for cond in ["a", "b"]}

    for r in results:
        for model in MODELS:
            for cond_key, cond_label in [("condition_a", "a"), ("condition_b", "b")]:
                scores = _get_scores(r[cond_key], model)
                vals = [scores[c] for c in CRITERIA if c in scores]
                if len(vals) >= 2:
                    var[f"{model}_{cond_label}"].append(variance(vals))

    return {key: round(sum(vals) / len(vals), 3) if vals else None for key, vals in var.items()}


def summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute all metrics and return a single summary dict."""
    return {
        "total_methods": len(results),
        "score_delta": score_delta(results),
        "inter_model_agreement": inter_model_agreement(results),
        "score_variance": score_variance(results),
    }


def print_report(results_dir: str = "outputs/experiment") -> None:
    results = load_results(results_dir)
    if not results:
        print("No results found.")
        return

    s = summary(results)

    print(f"\n{'='*60}")
    print(f"EXPERIMENT ANALYSIS  ({s['total_methods']} methods)")
    print(f"{'='*60}")

    print("\n--- Score Delta (B - A, positive = context helped) ---")
    for model in MODELS:
        print(f"\n  {model}:")
        deltas = s["score_delta"][model]
        overall = deltas.get("overall")
        print(f"    overall: {overall:+.3f}" if overall is not None else "    overall: n/a")
        for c in CRITERIA:
            val = deltas.get(c)
            if val is not None:
                print(f"    {c}: {val:+.3f}")

    print("\n--- Inter-Model Agreement (Pearson r, higher = more agreement) ---")
    for cond in ["condition_a", "condition_b"]:
        label = "A (no context)" if cond == "condition_a" else "B (with context)"
        overall = s["inter_model_agreement"][cond].get("overall")
        print(f"  {label} — overall r: {overall:.3f}" if overall is not None else f"  {label} — overall r: n/a")

    print("\n--- Score Variance (lower = more consistent) ---")
    for key, val in s["score_variance"].items():
        print(f"  {key}: {val}" if val is not None else f"  {key}: n/a")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze experiment results")
    parser.add_argument("--results-dir", default="outputs/experiment", help="Directory with result JSON files")
    args = parser.parse_args()
    print_report(args.results_dir)
