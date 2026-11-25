#!/usr/bin/env python3
"""
Master Evaluation Pipeline — Spectre Detection
================================================
Orchestrates the complete evaluation workflow:
  Phase 2: Feature Engineering
  Phase 3: ML Pipeline
  Phase 4: Evaluation & Metrics
  Phase 7: Visualization

Linux-specific phases (1, 5, 6) must be run separately via
their respective shell scripts in a Linux/WSL environment.
"""

import time, os, sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

def banner(text):
    print("\n" + "+" + "="*68 + "+")
    print("|" + text.center(68) + "|")
    print("+" + "="*68 + "+")


def main():
    start = time.time()

    banner("SPECTRE DETECTION — EVALUATION PIPELINE")
    print(f"Working directory: {BASE_DIR}")

    # ─── Phase 2: Feature Engineering ───
    import feature_engineering
    feature_engineering.run()

    # ─── Phase 3: ML Pipeline ───
    import ml_pipeline
    ml_pipeline.run()

    # ─── Phase 4: Evaluation ───
    import evaluate
    evaluate.run()

    # ─── Phase 7: Visualization ───
    import visualize
    visualize.run()

    elapsed = time.time() - start

    banner("PIPELINE COMPLETE")
    print(f"\nTotal execution time: {elapsed:.1f} seconds")
    print(f"\nOutput files:")
    print(f"  processed_dataset.csv     - Feature-engineered dataset")
    print(f"  results/models/           - Trained model files (.joblib)")
    print(f"  results/metrics_summary.json - Metric comparison (JSON)")
    print(f"  results/evaluation_results.joblib - Full results (for viz)")
    print(f"  results/plots/            - All generated plots (PNG)")

    # List generated plots
    plots_dir = os.path.join(BASE_DIR, 'results', 'plots')
    if os.path.isdir(plots_dir):
        print(f"\nGenerated plots:")
        for f in sorted(os.listdir(plots_dir)):
            if f.endswith('.png'):
                print(f"    {f}")

    print("\n" + "-"*70)
    print("Linux-specific phases (run separately in WSL/Linux):")
    print("  Phase 1: bash expand_dataset.sh   (dataset expansion)")
    print("  Phase 5: bash mitigation_test.sh   (mitigation awareness)")
    print("  Phase 6: gcc -O2 -o realtime_detector realtime_detector.c -lm")
    print("           ./realtime_detector <PID> [interval_ms]")
    print("-"*70)


if __name__ == '__main__':
    main()
