"""
Experiment runner for comparing LLM code review quality with and without call-site context.

Conditions:
    A - function body only
    B - function body + call-site examples (AST-extracted)

Models: gpt-4o, claude-3-5-sonnet
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import anthropic
import openai
from dotenv import load_dotenv

from source.llm.code_eval_prompt import generate_code_evaluation_prompt
from source.llm.response_parser import parse_json_response
from source.logic.code_ast_parser import collect_method_usages, get_method_body

load_dotenv()

MODELS = {
    "gpt-4o": "gpt-4o",
    "claude": "claude-sonnet-4-6",
}


def _call_openai(prompt: str) -> str:
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model=MODELS["gpt-4o"],
        messages=[
            {"role": "system", "content": "You are an expert at evaluating Python code."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1500,
        temperature=0.2,
    )
    return response.choices[0].message.content


def _call_claude(prompt: str) -> str:
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    message = client.messages.create(
        model=MODELS["claude"],
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _evaluate(prompt: str) -> Dict[str, Any]:
    results = {}
    for model_name, caller in [("gpt-4o", _call_openai), ("claude", _call_claude)]:
        try:
            raw = caller(prompt)
            results[model_name] = parse_json_response(raw)
        except Exception as e:
            results[model_name] = {"error": str(e)}
    return results


def run_experiment(
    repo_dir: str,
    target_file: str,
    output_dir: str = "outputs/experiment",
    min_call_sites: int = 1,
) -> List[Dict[str, Any]]:
    """
    Run the experiment on all methods in target_file that have at least min_call_sites call sites.

    Args:
        repo_dir: Root directory of the repo (used for AST traversal).
        target_file: Python file whose methods will be evaluated.
        output_dir: Directory to save results.
        min_call_sites: Skip methods with fewer call sites than this.

    Returns:
        List of per-method result dicts.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"Extracting methods from {target_file}...")
    method_usages = collect_method_usages(repo_dir, target_file)
    print(f"Found {len(method_usages)} methods with call sites")

    all_results = []

    for method_pointer, call_site_infos in method_usages.items():
        if len(call_site_infos) < min_call_sites:
            continue

        method_name = method_pointer.method_id.method_name
        print(f"\nEvaluating: {method_name} ({len(call_site_infos)} call sites)")

        # Extract method body and call site text
        method_body = get_method_body(method_pointer.function_node, method_pointer.file_path)
        usage_examples = [get_method_body(cs.function_node, cs.file_path) for cs in call_site_infos]
        usage_text = "\n\n".join(usage_examples)

        # Build prompts for both conditions
        prompt_a = generate_code_evaluation_prompt(method_body, usage_example="")
        prompt_b = generate_code_evaluation_prompt(method_body, usage_example=usage_text)

        print("  Running condition A (no context)...")
        scores_a = _evaluate(prompt_a)

        print("  Running condition B (with call-site context)...")
        scores_b = _evaluate(prompt_b)

        result = {
            "method_name": method_name,
            "file_path": target_file,
            "repo_dir": repo_dir,
            "num_call_sites": len(call_site_infos),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "condition_a": scores_a,
            "condition_b": scores_b,
        }

        all_results.append(result)
        print(f"  Done: {method_name}")

    # Save results
    repo_name = Path(repo_dir).name
    file_stem = Path(target_file).stem
    output_file = Path(output_dir) / f"{repo_name}_{file_stem}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print(f"\nResults saved to {output_file}")
    return all_results


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run call-site context experiment")
    parser.add_argument("--repo", required=True, help="Root directory of the repo")
    parser.add_argument("--file", required=True, help="Target Python file to analyze")
    parser.add_argument("--output", default="outputs/experiment", help="Output directory")
    parser.add_argument("--min-call-sites", type=int, default=1, help="Minimum call sites required")
    args = parser.parse_args()

    results = run_experiment(
        repo_dir=args.repo,
        target_file=args.file,
        output_dir=args.output,
        min_call_sites=args.min_call_sites,
    )
    print(f"\nCompleted. Evaluated {len(results)} methods.")


if __name__ == "__main__":
    main()
