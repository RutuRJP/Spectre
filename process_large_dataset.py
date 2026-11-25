#!/usr/bin/env python3
"""
Process Massive Dataset
=========================
Parses the large_perf_data_raw.csv collected by generate_large_dataset.sh
and outputs the 'large_labeled_dataset.csv' ready for ML training.
"""

import os, sys
import pandas as pd

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
RAW_FILE  = os.path.join(BASE_DIR, 'large_perf_data_raw.csv')
OUT_CSV   = os.path.join(BASE_DIR, 'large_labeled_dataset.csv')

def parse_perf_csv(path):
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

            if len(parts) >= 6 and parts[4].strip() in ('normal', 'spectre'):
                current_label = parts[4].strip()
                current_name  = parts[5].strip() if len(parts) > 5 else ''
                if len(current) >= 6:
                    current['label'] = current_label
                    current['workload'] = current_name
                    records.append(current)
                current = {}
                continue

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
        print(f"[!] {RAW_FILE} not found. Run bash generate_large_dataset.sh first.")
        sys.exit(1)

    print("[+] Parsing massive raw perf data...")
    records = parse_perf_csv(RAW_FILE)
    print(f"    Parsed {len(records)} runs.")

    df = compute_features(records)
    print(f"[+] Computed features for {len(df)} samples.")
    print(f"    Class distribution: {dict(df['label'].value_counts())}")

    df.to_csv(OUT_CSV, index=False)
    print(f"[+] Saved massive dataset to {os.path.basename(OUT_CSV)}")


if __name__ == '__main__':
    main()
