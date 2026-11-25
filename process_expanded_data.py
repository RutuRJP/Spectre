#!/usr/bin/env python3
"""
Process Expanded Perf Data (Phase 1 helper)
=============================================
Parses the expanded_perf_data.csv collected by expand_dataset.sh,
extracts features, and merges with the existing labeled_dataset.csv.
"""

import os, re, sys
import pandas as pd
import numpy as np

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
RAW_FILE  = os.path.join(BASE_DIR, 'expanded_perf_data.csv')
OLD_CSV   = os.path.join(BASE_DIR, 'labeled_dataset.csv')
OUT_CSV   = os.path.join(BASE_DIR, 'labeled_dataset.csv')  # overwrite with merged

def parse_perf_csv(path):
    """Parse perf stat -x , output into structured records."""
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

            # Label marker line: ,,,,,label,name
            if len(parts) >= 6 and parts[4].strip() in ('normal', 'spectre'):
                current_label = parts[4].strip()
                current_name  = parts[5].strip() if len(parts) > 5 else ''
                if len(current) >= 6:
                    current['label'] = current_label
                    current['workload'] = current_name
                    records.append(current)
                current = {}
                continue

            # perf stat line: value,,event,...
            if len(parts) < 3:
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
    """Convert raw perf records to feature vectors."""
    rows = []
    for r in records:
        try:
            ipc = r['instructions'] / r['cycles']
            bmr = r['branch_misses'] / r['branches'] * 100
            cmr = r['cache_misses'] / r['cache_refs'] * 100
            rows.append({
                'ipc':              ipc,
                'branch_miss_rate': bmr,
                'cache_miss_rate':  cmr,
                'cycles':           r['cycles'],
                'label':            r['label'],
            })
        except (KeyError, ZeroDivisionError):
            continue
    return pd.DataFrame(rows)


def main():
    if not os.path.exists(RAW_FILE):
        print(f"[!] {RAW_FILE} not found. Run expand_dataset.sh first.")
        sys.exit(1)

    print("[+] Parsing expanded perf data...")
    records = parse_perf_csv(RAW_FILE)
    print(f"    Parsed {len(records)} runs")

    df_new = compute_features(records)
    print(f"    Computed features for {len(df_new)} valid samples")
    print(f"    New class distribution: {dict(df_new['label'].value_counts())}")

    # Load existing dataset
    if os.path.exists(OLD_CSV):
        # Check if it has a header
        with open(OLD_CSV) as f:
            first_line = f.readline().strip()
        if 'ipc' in first_line or 'label' in first_line:
            df_old = pd.read_csv(OLD_CSV)
        else:
            df_old = pd.read_csv(OLD_CSV, header=None,
                                 names=['ipc', 'branch_miss_rate', 'cache_miss_rate', 'cycles', 'label'])
        df_old.dropna(subset=['label'], inplace=True)
        df_old['label'] = df_old['label'].str.strip()
        print(f"[+] Existing dataset: {len(df_old)} samples")
    else:
        df_old = pd.DataFrame()

    # Merge
    df_merged = pd.concat([df_old, df_new], ignore_index=True)
    df_merged.dropna(subset=['label'], inplace=True)
    print(f"[+] Merged dataset: {len(df_merged)} total samples")
    print(f"    Class distribution: {dict(df_merged['label'].value_counts())}")

    # Save (with header for consistency)
    df_merged.to_csv(OUT_CSV, index=False)
    print(f"[+] Saved merged dataset to {os.path.basename(OUT_CSV)}")


if __name__ == '__main__':
    main()
