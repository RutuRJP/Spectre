#!/usr/bin/env python3
"""
Machine Learning Pipeline for Spectre Detection
=================================================
Trains Logistic Regression, Random Forest (with GridSearchCV),
and SVM (RBF) classifiers on the processed dataset.
"""

import pandas as pd
import numpy as np
import os, json, warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, StratifiedKFold
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
import joblib

# ─────────────────────────── Configuration ───────────────────────────
BASE_DIR    = os.path.dirname(__file__)
INPUT_CSV   = os.path.join(BASE_DIR, 'processed_dataset.csv')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
MODELS_DIR  = os.path.join(RESULTS_DIR, 'models')
TEST_SIZE   = 0.3
RANDOM_STATE = 42
CV_FOLDS     = 5

def ensure_dirs():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR,  exist_ok=True)


def load_and_prepare():
    """Load processed dataset, split into train/test with stratification."""
    df = pd.read_csv(INPUT_CSV)
    feature_cols = [c for c in df.columns if c != 'label']

    le = LabelEncoder()
    y = le.fit_transform(df['label'])       # normal=0, spectre=1
    X = df[feature_cols].values

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=TEST_SIZE,
        stratify=y, random_state=RANDOM_STATE
    )

    print(f"[+] Data loaded:  {X_scaled.shape[0]} samples, {X_scaled.shape[1]} features")
    print(f"    Train: {X_train.shape[0]}  |  Test: {X_test.shape[0]}")
    print(f"    Classes: {dict(zip(le.classes_, np.bincount(y)))}")

    return X_train, X_test, y_train, y_test, le, scaler, feature_cols


def build_models():
    """Return dict of model name → estimator (before fitting)."""
    return {
        'Logistic Regression': LogisticRegression(
            max_iter=1000, random_state=RANDOM_STATE
        ),
        'Random Forest': RandomForestClassifier(
            random_state=RANDOM_STATE
        ),
        'SVM (RBF)': SVC(
            kernel='rbf', probability=True, random_state=RANDOM_STATE
        ),
    }


def tune_random_forest(X_train, y_train):
    """GridSearchCV for Random Forest hyperparameters."""
    param_grid = {
        'n_estimators': [50, 100, 200],
        'max_depth':    [None, 10, 20],
    }
    grid = GridSearchCV(
        RandomForestClassifier(random_state=RANDOM_STATE),
        param_grid,
        cv=StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE),
        scoring='f1',
        n_jobs=-1,
        refit=True
    )
    grid.fit(X_train, y_train)
    print(f"    Best RF params: {grid.best_params_}  (F1={grid.best_score_:.4f})")
    return grid.best_estimator_


def run():
    """Execute the full ML training pipeline."""
    print("\n" + "="*70)
    print("PHASE 3: MACHINE LEARNING PIPELINE")
    print("="*70)

    ensure_dirs()
    X_train, X_test, y_train, y_test, le, scaler, feature_cols = load_and_prepare()

    models = build_models()
    trained = {}
    cv_results = {}

    for name, model in models.items():
        print(f"\n--- Training: {name} ---")

        if name == 'Random Forest':
            model = tune_random_forest(X_train, y_train)
        else:
            model.fit(X_train, y_train)

        # 5-fold cross-validation
        cv_scores = cross_val_score(
            model, X_train, y_train, cv=CV_FOLDS, scoring='accuracy'
        )
        cv_results[name] = cv_scores
        print(f"    CV Accuracy: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"    Per-fold:    {[f'{s:.4f}' for s in cv_scores]}")

        trained[name] = model

        # Save model
        model_path = os.path.join(MODELS_DIR, name.replace(' ', '_').replace('(', '').replace(')', '') + '.joblib')
        joblib.dump(model, model_path)

    # Save test data and metadata for the evaluation phase
    joblib.dump({
        'X_train': X_train, 'X_test': X_test,
        'y_train': y_train, 'y_test': y_test,
        'label_encoder': le,
        'scaler': scaler,
        'feature_cols': feature_cols,
    }, os.path.join(RESULTS_DIR, 'test_data.joblib'))

    # Print CV comparison table
    print("\n" + "="*70)
    print(" CROSS-VALIDATION COMPARISON")
    print("="*70)
    print(f"{'Model':<25s} {'Mean Acc':>10s} {'Std':>10s}")
    print("-" * 50)
    for name, scores in cv_results.items():
        print(f"{name:<25s} {scores.mean():>10.4f} {scores.std():>10.4f}")

    return trained, X_test, y_test, le, feature_cols


if __name__ == '__main__':
    run()
