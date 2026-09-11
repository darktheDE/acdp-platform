#!/usr/bin/env python3
"""
compute_ragas_scorecard.py - Deterministic calculation of Ragas RAG evaluation metrics and scorecard generation.
Part of the experiment-evaluator skill in ACDP.
"""

import argparse
import json
import statistics
import sys
from pathlib import Path


def compute_scorecard(input_file: Path) -> int:
    if not input_file.exists():
        print(f"[FAIL] Input evaluation file not found: {input_file}")
        return 1

    try:
        data = json.loads(input_file.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[FAIL] JSON parsing error: {e}")
        return 1

    records = data if isinstance(data, list) else data.get("results", [])
    if not records:
        print("[FAIL] No evaluation records found in input data.")
        return 1

    metrics = ["faithfulness", "answer_relevance", "context_precision", "context_recall"]
    targets = {
        "faithfulness": 0.90,
        "answer_relevance": 0.85,
        "context_precision": 0.85,
        "context_recall": 0.80,
    }

    summary = {}
    for m in metrics:
        values = [r.get(m) for r in records if r.get(m) is not None]
        if values:
            summary[m] = {
                "mean": statistics.mean(values),
                "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                "count": len(values),
            }

    print(f"\n=== RAG Evaluation Scorecard ({len(records)} test queries) ===")
    print("| Metric | Target | Achieved Mean | Std Dev | Status |")
    print("| :--- | :---: | :---: | :---: | :---: |")

    all_passed = True
    for m in metrics:
        if m in summary:
            mean = summary[m]["mean"]
            std = summary[m]["stdev"]
            target = targets[m]
            passed = mean >= target
            if not passed:
                all_passed = False
            status_str = "PASS [OK]" if passed else "FAIL [BELOW TARGET]"
            print(f"| **{m}** | $\\ge {target:.2f}$ | **{mean:.4f}** | $\\pm {std:.4f}$ | {status_str} |")
        else:
            print(f"| **{m}** | $\\ge {targets[m]:.2f}$ | N/A | N/A | MISSING |")
            all_passed = False

    print("\nOverall Status:", "PASS" if all_passed else "ATTENTION NEEDED")
    return 0 if all_passed else 1


def main():
    parser = argparse.ArgumentParser(description="Compute Ragas RAG Evaluation Scorecard")
    parser.add_argument("--input", required=True, help="Path to evaluation results JSON file")
    args = parser.parse_args()

    sys.exit(compute_scorecard(Path(args.input)))


if __name__ == "__main__":
    main()
