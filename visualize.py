#!/usr/bin/env python3
"""
Visualization for Spectre Detection Evaluation
================================================
Generates all required plots: ROC curves, confusion matrices,
feature importance, scatter plots, and feature distributions.
"""

import pandas as pd
import numpy as np
import os, warnings
warnings.filterwarnings('ignore')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import joblib

# ─────────────────────────── Configuration ───────────────────────────
BASE_DIR    = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
PLOTS_DIR   = os.path.join(RESULTS_DIR, 'plots')

# Colour palette
COLORS = {
    'Logistic Regression': '#e74c3c',
    'Random Forest':       '#2ecc71',
    'SVM (RBF)':           '#3498db',
}
LABEL_COLORS = {'normal': '#3498db', 'spectre': '#e74c3c'}


def ensure_dirs():
    os.makedirs(PLOTS_DIR, exist_ok=True)


# ──────────────────────── 1. ROC Curves ────────────────────────
def plot_roc_curves(results):
    """Overlay ROC curves for all models on one plot."""
    fig, ax = plt.subplots(figsize=(8, 6))

    for name, m in results.items():
        ax.plot(m['roc_fpr'], m['roc_tpr'],
                label=f"{name} (AUC={m['auc']:.3f})",
                color=COLORS.get(name, '#333'), linewidth=2)

    ax.plot([0, 1], [0, 1], 'k--', alpha=0.4, label='Random Baseline')
    ax.set_xlabel('False Positive Rate', fontsize=12)
    ax.set_ylabel('True Positive Rate', fontsize=12)
    ax.set_title('ROC Curves — Spectre Detection Models', fontsize=14, fontweight='bold')
    ax.legend(loc='lower right', fontsize=10)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'roc_curves.png'), dpi=300)
    plt.close(fig)
    print("[+] Saved roc_curves.png")


# ──────────────────── 2. Confusion Matrices ─────────────────────
def plot_confusion_matrices(results):
    """Side-by-side confusion matrix heatmaps."""
    n = len(results)
    fig, axes = plt.subplots(1, n, figsize=(5*n, 4.5))
    if n == 1:
        axes = [axes]

    for ax, (name, m) in zip(axes, results.items()):
        cm = m['confusion_matrix']
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                    xticklabels=['Normal', 'Spectre'],
                    yticklabels=['Normal', 'Spectre'],
                    ax=ax, cbar=False,
                    annot_kws={'size': 14, 'fontweight': 'bold'})
        ax.set_title(name, fontsize=12, fontweight='bold')
        ax.set_xlabel('Predicted', fontsize=10)
        ax.set_ylabel('Actual', fontsize=10)

    fig.suptitle('Confusion Matrices', fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'confusion_matrices.png'), dpi=300,
                bbox_inches='tight')
    plt.close(fig)
    print("[+] Saved confusion_matrices.png")


# ──────────────────── 3. Feature Importance ─────────────────────
def plot_feature_importance(feature_cols):
    """Bar chart of Random Forest feature importances."""
    rf_path = os.path.join(RESULTS_DIR, 'models', 'Random_Forest.joblib')
    if not os.path.exists(rf_path):
        print("[!] Random Forest model not found, skipping feature importance plot")
        return

    rf = joblib.load(rf_path)
    importances = rf.feature_importances_
    indices = np.argsort(importances)[::-1]

    fig, ax = plt.subplots(figsize=(10, 5))
    colors_bar = plt.cm.viridis(np.linspace(0.3, 0.9, len(feature_cols)))

    ax.bar(range(len(feature_cols)),
           importances[indices],
           color=colors_bar,
           edgecolor='white',
           linewidth=0.5)
    ax.set_xticks(range(len(feature_cols)))
    ax.set_xticklabels([feature_cols[i] for i in indices], rotation=30, ha='right')
    ax.set_ylabel('Importance', fontsize=12)
    ax.set_title('Random Forest — Feature Importance', fontsize=14, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'feature_importance.png'), dpi=300)
    plt.close(fig)
    print("[+] Saved feature_importance.png")


# ──────────────── 4. IPC vs Cache Miss Scatter ─────────────────
def plot_ipc_vs_cachemiss():
    """Scatter plot of IPC vs Cache Miss Rate, colored by class."""
    df = pd.read_csv(os.path.join(BASE_DIR, 'processed_dataset.csv'))

    fig, ax = plt.subplots(figsize=(8, 6))
    for label, color in LABEL_COLORS.items():
        subset = df[df['label'] == label]
        ax.scatter(subset['ipc'], subset['cache_miss_rate'],
                   c=color, label=label.capitalize(),
                   alpha=0.7, edgecolors='white', s=60)

    ax.set_xlabel('IPC (Instructions Per Cycle)', fontsize=12)
    ax.set_ylabel('Cache Miss Rate (%)', fontsize=12)
    ax.set_title('IPC vs Cache Miss Rate — Class Separation', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'ipc_vs_cachemiss.png'), dpi=300)
    plt.close(fig)
    print("[+] Saved ipc_vs_cachemiss.png")


# ──────────────── 5. Feature Distributions ─────────────────────
def plot_feature_distributions():
    """Box plots for key features split by class."""
    df = pd.read_csv(os.path.join(BASE_DIR, 'processed_dataset.csv'))
    key_features = ['ipc', 'branch_miss_rate', 'cache_miss_rate', 'cpi']

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, feat in zip(axes.flatten(), key_features):
        data_normal  = df[df['label'] == 'normal'][feat]
        data_spectre = df[df['label'] == 'spectre'][feat]

        bp = ax.boxplot([data_normal, data_spectre],
                        labels=['Normal', 'Spectre'],
                        patch_artist=True,
                        widths=0.5)
        bp['boxes'][0].set_facecolor(LABEL_COLORS['normal'])
        bp['boxes'][1].set_facecolor(LABEL_COLORS['spectre'])
        for box in bp['boxes']:
            box.set_alpha(0.6)

        ax.set_title(feat.replace('_', ' ').title(), fontsize=12, fontweight='bold')
        ax.grid(axis='y', alpha=0.3)

    fig.suptitle('Feature Distributions by Class', fontsize=14, fontweight='bold')
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'feature_distributions.png'), dpi=300)
    plt.close(fig)
    print("[+] Saved feature_distributions.png")


# ──────────────── 6. Model Comparison Bar Chart ─────────────────
def plot_model_comparison(results):
    """Grouped bar chart comparing model metrics."""
    metrics_to_plot = ['accuracy', 'precision', 'recall', 'f1', 'auc']
    model_names = list(results.keys())

    x = np.arange(len(metrics_to_plot))
    width = 0.22

    fig, ax = plt.subplots(figsize=(10, 5))

    for i, name in enumerate(model_names):
        vals = [results[name][m] for m in metrics_to_plot]
        bars = ax.bar(x + i * width, vals, width,
                      label=name, color=COLORS.get(name, '#666'),
                      alpha=0.85, edgecolor='white')
        for bar, v in zip(bars, vals):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{v:.2f}', ha='center', va='bottom', fontsize=8)

    ax.set_xticks(x + width)
    ax.set_xticklabels([m.upper() for m in metrics_to_plot], fontsize=10)
    ax.set_ylim(0, 1.15)
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('Model Performance Comparison', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOTS_DIR, 'model_comparison.png'), dpi=300)
    plt.close(fig)
    print("[+] Saved model_comparison.png")


def run():
    """Generate all visualization plots."""
    print("\n" + "="*70)
    print("PHASE 7: VISUALIZATION")
    print("="*70)

    ensure_dirs()

    # Load evaluation results
    results = joblib.load(os.path.join(RESULTS_DIR, 'evaluation_results.joblib'))

    # Load feature columns from test data
    test_data = joblib.load(os.path.join(RESULTS_DIR, 'test_data.joblib'))
    feature_cols = test_data['feature_cols']

    # Generate all plots
    plot_roc_curves(results)
    plot_confusion_matrices(results)
    plot_feature_importance(feature_cols)
    plot_ipc_vs_cachemiss()
    plot_feature_distributions()
    plot_model_comparison(results)

    print(f"\n[+] All plots saved to {PLOTS_DIR}/")


if __name__ == '__main__':
    run()
