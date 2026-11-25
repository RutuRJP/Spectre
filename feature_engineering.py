#!/usr/bin/env python3
"""
Feature Engineering for Spectre Detection Pipeline
===================================================
Loads the labeled dataset, computes derived features,
applies normalization, and saves the processed data.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
import os
import warnings
warnings.filterwarnings('ignore')

# ─────────────────────────── Configuration ───────────────────────────
INPUT_CSV     = os.path.join(os.path.dirname(__file__), 'labeled_dataset.csv')
OUTPUT_CSV    = os.path.join(os.path.dirname(__file__), 'processed_dataset.csv')
RAW_COLS      = ['ipc', 'branch_miss_rate', 'cache_miss_rate', 'cycles', 'label']

def load_dataset(path: str) -> pd.DataFrame:
    """Load the labeled dataset CSV (auto-detects header)."""
    # Detect whether the CSV has a header row
    with open(path) as f:
        first_line = f.readline().strip()
    if 'ipc' in first_line or 'label' in first_line:
        df = pd.read_csv(path)
        df.columns = RAW_COLS[:len(df.columns)]
    else:
        df = pd.read_csv(path, header=None, names=RAW_COLS)
    # drop any empty trailing rows and filter out stray header rows in body
    df.dropna(subset=['label'], inplace=True)
    df = df[df['label'].isin(['spectre', 'normal'])]
    df['label'] = df['label'].str.strip()
    # Ensure numeric columns
    for col in RAW_COLS[:-1]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df.dropna(inplace=True)
    print(f"[+] Loaded {len(df)} samples from {os.path.basename(path)}")
    print(f"    Class distribution: {dict(df['label'].value_counts())}")
    return df


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add derived features as described in the Planned Evaluation Workflow:
      - CPI = 1 / IPC  (Cycles Per Instruction)
      - Cache MPKI  = cache_miss_rate * 10   (miss-per-kilo-instruction proxy)
      - Branch MPKI = branch_miss_rate * 10
    """
    df = df.copy()
    df['cpi']         = 1.0 / df['ipc']
    df['cache_mpki']  = df['cache_miss_rate'] * 10.0
    df['branch_mpki'] = df['branch_miss_rate'] * 10.0
    print("[+] Derived features added: cpi, cache_mpki, branch_mpki")
    return df


def normalize_features(df: pd.DataFrame):
    """
    Apply StandardScaler to all numeric feature columns.
    Returns: (scaled DataFrame, fitted scaler, feature column names)
    """
    feature_cols = [c for c in df.columns if c != 'label']
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[feature_cols])
    df_scaled = pd.DataFrame(X_scaled, columns=feature_cols, index=df.index)
    df_scaled['label'] = df['label'].values
    print("[+] Features standardized (zero mean, unit variance)")
    return df_scaled, scaler, feature_cols


def print_statistics(df: pd.DataFrame):
    """Print per-class feature statistics."""
    feature_cols = [c for c in df.columns if c != 'label']
    print("\n" + "="*70)
    print("FEATURE STATISTICS (before scaling)")
    print("="*70)
    for label in ['spectre', 'normal']:
        subset = df[df['label'] == label]
        print(f"\n--- {label.upper()} (n={len(subset)}) ---")
        for col in feature_cols:
            vals = subset[col]
            print(f"  {col:20s}:  mean={vals.mean():12.4f}  std={vals.std():12.4f}"
                  f"  min={vals.min():12.4f}  max={vals.max():12.4f}")


def run():
    """Execute the full feature engineering pipeline."""
    print("="*70)
    print("PHASE 2: FEATURE ENGINEERING")
    print("="*70)

    # 1. Load
    df = load_dataset(INPUT_CSV)

    # 2. Derived features
    df = add_derived_features(df)

    # 3. Statistics (pre-scaling)
    print_statistics(df)

    # 4. Normalize
    df_scaled, scaler, feature_cols = normalize_features(df)

    # 5. Save (unscaled, with derived features – scaling applied in ML pipeline)
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"[+] Processed dataset saved to {os.path.basename(OUTPUT_CSV)}")
    print(f"    Columns: {list(df.columns)}")
    print(f"    Shape:   {df.shape}")

    return df, scaler, feature_cols


if __name__ == '__main__':
    run()
