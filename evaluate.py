#!/usr/bin/env python3
"""
Evaluation & Metrics for Spectre Detection
============================================
Loads trained models, evaluates on held-out test set,
and computes full classification metrics.
"""

import pandas as pd
import numpy as np
import os, json, warnings
warnings.filterwarnings('ignore')

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_curve, auc
)
import joblib

# ─────────────────────────── Configuration ───────────────────────────
BASE_DIR    = os.path.dirname(__file__)
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
MODELS_DIR  = os.path.join(RESULTS_DIR, 'models')

MODEL_FILES = {
    'Logistic Regression': 'Logistic_Regression.joblib',
    'Random Forest':       'Random_Forest.joblib',
    'SVM (RBF)':           'SVM_RBF.joblib',
}


def load_artifacts():
    """Load test data and trained models."""
    data = joblib.load(os.path.join(RESULTS_DIR, 'test_data.joblib'))
    models = {}
    for name, fname in MODEL_FILES.items():
        path = os.path.join(MODELS_DIR, fname)
        if os.path.exists(path):
            models[name] = joblib.load(path)
    return data, models


def compute_metrics(y_true, y_pred, y_prob):
    """Compute all evaluation metrics for a single model."""
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    fpr_curve, tpr_curve, thresholds = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr_curve, tpr_curve)

    return {
        'accuracy':   accuracy_score(y_true, y_pred),
        'precision':  precision_score(y_true, y_pred),
        'recall':     recall_score(y_true, y_pred),
        'f1':         f1_score(y_true, y_pred),
        'fpr':        fpr,
        'auc':        roc_auc,
        'tp': int(tp), 'fp': int(fp), 'fn': int(fn), 'tn': int(tn),
        'confusion_matrix': cm,
        'roc_fpr':    fpr_curve,
        'roc_tpr':    tpr_curve,
        'thresholds': thresholds,
    }


def run():
    """Execute full evaluation pipeline."""
    print("\n" + "="*70)
    print("PHASE 4: EVALUATION & METRICS")
    print("="*70)

    data, models = load_artifacts()
    X_test   = data['X_test']
    y_test   = data['y_test']
    le       = data['label_encoder']

    all_results = {}

    for name, model in models.items():
        print(f"\n--- {name} ---")
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        metrics = compute_metrics(y_test, y_pred, y_prob)
        all_results[name] = metrics

        # Print classification report
        print(classification_report(y_test, y_pred,
              target_names=le.classes_))

        # Print confusion matrix
        cm = metrics['confusion_matrix']
        print(f"  Confusion Matrix:")
        print(f"                   Pred Normal   Pred Spectre")
        print(f"  Actual Normal      {cm[0,0]:>6d}        {cm[0,1]:>6d}")
        print(f"  Actual Spectre     {cm[1,0]:>6d}        {cm[1,1]:>6d}")
        print(f"\n  FPR = {metrics['fpr']:.4f}  |  AUC = {metrics['auc']:.4f}")

    # Print comparison table
    print("\n" + "="*70)
    print(" MODEL COMPARISON SUMMARY")
    print("="*70)
    header = f"{'Model':<25s} {'Acc':>7s} {'Prec':>7s} {'Recall':>7s} {'F1':>7s} {'FPR':>7s} {'AUC':>7s}"
    print(header)
    print("-" * len(header))
    for name, m in all_results.items():
        print(f"{name:<25s} {m['accuracy']:>7.4f} {m['precision']:>7.4f} "
              f"{m['recall']:>7.4f} {m['f1']:>7.4f} {m['fpr']:>7.4f} {m['auc']:>7.4f}")

    # Save results for visualization
    save_results = {}
    for name, m in all_results.items():
        save_results[name] = {
            k: v for k, v in m.items()
            if k not in ('confusion_matrix', 'roc_fpr', 'roc_tpr', 'thresholds')
        }
    with open(os.path.join(RESULTS_DIR, 'metrics_summary.json'), 'w') as f:
        json.dump(save_results, f, indent=2)

    # Save full results (including ROC curves) for visualization
    joblib.dump(all_results, os.path.join(RESULTS_DIR, 'evaluation_results.joblib'))
    print(f"\n[+] Results saved to {RESULTS_DIR}/")

    return all_results


if __name__ == '__main__':
    run()
