#!/usr/bin/env python3
"""
Mitigation Awareness Analysis (Phase 5 helper)
================================================
Compares HPC signatures of mitigated vs unmitigated Spectre executions
and evaluates whether the trained ML models can still detect the attack.
"""

import os, sys
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
RAW_FILE    = os.path.join(BASE_DIR, 'mitigation_perf_data.csv')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
PLOTS_DIR   = os.path.join(RESULTS_DIR, 'plots')

def parse_mitigation_data(path):
    """Parse perf CSV into records with mitigation labels."""
    records = []
    current = {}
    current_label = None
    current_name  = None

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')

            if len(parts) >= 5 and parts[4].strip() in ('spectre', 'spectre_mitigated', 'normal'):
                current_label = parts[4].strip()
                current_name  = parts[5].strip() if len(parts) > 5 else ''
                if len(current) >= 4:
                    current['label'] = current_label
                    current['variant'] = current_name
                    records.append(current)
                current = {}
                continue

            try:
                value = float(parts[0].replace(',', '').strip())
            except (ValueError, IndexError):
                continue
            event = parts[2].strip() if len(parts) > 2 else ''

            if 'cycles' in event and 'instructions' not in event:
                current['cycles'] = value
            elif 'instructions' in event:
                current['instructions'] = value
            elif 'branch-misses' in event:
                current['branch_misses'] = value
            elif 'branches' in event and 'misses' not in event:
                current['branches'] = value
            elif 'cache-misses' in event:
                current['cache_misses'] = value
            elif 'cache-references' in event:
                current['cache_refs'] = value

    return records


def compute_features(records):
    rows = []
    for r in records:
        try:
            rows.append({
                'ipc':              r['instructions'] / r['cycles'],
                'branch_miss_rate': r['branch_misses'] / r['branches'] * 100,
                'cache_miss_rate':  r['cache_misses'] / r['cache_refs'] * 100,
                'cycles':           r['cycles'],
                'label':            r['label'],
                'variant':          r.get('variant', ''),
            })
        except (KeyError, ZeroDivisionError):
            continue
    return pd.DataFrame(rows)


def test_models_on_mitigated(df):
    """Test trained models on mitigated attack data."""
    from sklearn.preprocessing import StandardScaler

    # Load trained models and test data
    test_data = joblib.load(os.path.join(RESULTS_DIR, 'test_data.joblib'))
    feature_cols = test_data['feature_cols']
    scaler = test_data['scaler']
    le = test_data['label_encoder']

    # Add derived features to match training
    df_feat = df.copy()
    df_feat['cpi'] = 1.0 / df_feat['ipc']
    df_feat['cache_mpki'] = df_feat['cache_miss_rate'] * 10.0
    df_feat['branch_mpki'] = df_feat['branch_miss_rate'] * 10.0

    # Ensure columns match
    available_cols = [c for c in feature_cols if c in df_feat.columns]
    if len(available_cols) < len(feature_cols):
        print(f"[!] Warning: only {len(available_cols)}/{len(feature_cols)} features available")

    X = df_feat[available_cols].values
    X_scaled = scaler.transform(X)

    model_files = {
        'Logistic Regression': 'Logistic_Regression.joblib',
        'Random Forest':       'Random_Forest.joblib',
        'SVM (RBF)':           'SVM_RBF.joblib',
    }

    print("\n" + "="*70)
    print(" MITIGATION AWARENESS — MODEL PREDICTIONS")
    print("="*70)

    for variant in df['variant'].unique():
        mask = df['variant'] == variant
        X_var = X_scaled[mask.values]
        print(f"\n--- Variant: {variant} ({mask.sum()} samples) ---")

        for name, fname in model_files.items():
            model_path = os.path.join(RESULTS_DIR, 'models', fname)
            if not os.path.exists(model_path):
                continue
            model = joblib.load(model_path)
            preds = model.predict(X_var)
            # In label encoding: normal=0, spectre=1
            detected = (preds == 1).sum()
            print(f"  {name:<25s}: {detected}/{len(preds)} detected as Spectre "
                  f"({detected/len(preds)*100:.1f}%)")


def plot_mitigation_comparison(df):
    """Plot feature distributions for mitigated vs unmitigated."""
    os.makedirs(PLOTS_DIR, exist_ok=True)

    features = ['ipc', 'cache_miss_rate', 'branch_miss_rate']
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    variants = df['variant'].unique()
    colors = plt.cm.Set2(np.linspace(0, 1, len(variants)))

    for ax, feat in zip(axes, features):
        for variant, color in zip(variants, colors):
            subset = df[df['variant'] == variant][feat]
            ax.hist(subset, bins=15, alpha=0.5, label=variant, color=color, edgecolor='white')
        ax.set_xlabel(feat.replace('_', ' ').title())
        ax.set_title(feat.replace('_', ' ').title())
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    fig.suptitle('Mitigation Awareness — Feature Comparison', fontsize=14, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'mitigation_comparison.png'), dpi=300)
    plt.close(fig)
    print("[+] Saved mitigation_comparison.png")


def main():
    if not os.path.exists(RAW_FILE):
        print(f"[!] {RAW_FILE} not found. Run mitigation_test.sh first.")
        sys.exit(1)

    print("\n" + "="*70)
    print("PHASE 5: MITIGATION AWARENESS ANALYSIS")
    print("="*70)

    records = parse_mitigation_data(RAW_FILE)
    print(f"[+] Parsed {len(records)} runs")

    df = compute_features(records)
    print(f"[+] Computed features for {len(df)} samples")

    # Print statistics
    for variant in df['variant'].unique():
        subset = df[df['variant'] == variant]
        print(f"\n  {variant} (n={len(subset)}):")
        for col in ['ipc', 'branch_miss_rate', 'cache_miss_rate']:
            print(f"    {col:20s}: mean={subset[col].mean():.4f}  std={subset[col].std():.4f}")

    # Test models on mitigated data
    test_models_on_mitigated(df)

    # Generate comparison plots
    plot_mitigation_comparison(df)


if __name__ == '__main__':
    main()
