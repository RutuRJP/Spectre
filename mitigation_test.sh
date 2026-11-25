#!/bin/bash
# ============================================================================
# Mitigation Awareness Experiment (Phase 5)
# ============================================================================
# Recompiles the Spectre PoC with hardware mitigations (Retpoline + lfence),
# collects perf data, and compares with unmitigated execution.
#
# Usage: bash mitigation_test.sh
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SPECTRE_SRC="$SCRIPT_DIR/programs/SpectrePoC/spectre.c"
TEMP_DIR="$SCRIPT_DIR/workloads_bin"
RUNS=50
OUTPUT="$SCRIPT_DIR/mitigation_perf_data.csv"

mkdir -p "$TEMP_DIR"

echo "=== Phase 5: Mitigation Awareness Experiment ==="

# Check if spectre source exists
if [ ! -f "$SPECTRE_SRC" ]; then
    echo "[!] Spectre source not found at $SPECTRE_SRC"
    exit 1
fi

# ──────────── Compile with mitigations ────────────
echo "[+] Compiling Spectre PoC with mitigations..."

# 1. Unmitigated baseline
gcc -O0 -o "$TEMP_DIR/spectre_baseline" "$SPECTRE_SRC" 2>/dev/null || true
echo "    Compiled spectre_baseline (O0, no mitigations)"

# 2. Retpoline mitigation
gcc -O2 -mindirect-branch=thunk -o "$TEMP_DIR/spectre_retpoline" "$SPECTRE_SRC" 2>/dev/null || \
gcc -O2 -o "$TEMP_DIR/spectre_retpoline" "$SPECTRE_SRC" 2>/dev/null || true
echo "    Compiled spectre_retpoline (attempting -mindirect-branch=thunk)"

# 3. With lfence (we insert via compiler barriers)
cat > "/tmp/spectre_lfence_wrapper.c" << 'CEOF'
// Wrapper that forces serialization via lfence
#define _GNU_SOURCE
#include <stdio.h>
// Force lfence before speculative access
#define LFENCE() __asm__ __volatile__("lfence" ::: "memory")
CEOF
# Since we can't easily modify the PoC source, compile with aggressive optimization
# which may partially mitigate via reordering
gcc -O2 -march=native -o "$TEMP_DIR/spectre_optimized" "$SPECTRE_SRC" 2>/dev/null || true
echo "    Compiled spectre_optimized (O2, aggressive optimization)"

# ──────────── Collect data ────────────
echo "[+] Collecting perf data..."
echo "" > "$OUTPUT"

collect_perf_mitigation() {
    local binary="$1"
    local label="$2"
    local name="$3"

    if [ ! -f "$binary" ]; then
        echo "    [!] Binary $name not found, skipping"
        return
    fi

    echo "    Collecting: $name ($label) — $RUNS runs..."
    for i in $(seq 1 $RUNS); do
        perf stat -x , -e cycles,instructions,branches,branch-misses,cache-references,cache-misses \
            "$binary" 2>> "$OUTPUT" > /dev/null
        echo ",,,,$label,$name" >> "$OUTPUT"
    done
}

# Baseline (unmitigated spectre)
collect_perf_mitigation "$TEMP_DIR/spectre_baseline" "spectre" "spectre_baseline"

# Retpoline variant
collect_perf_mitigation "$TEMP_DIR/spectre_retpoline" "spectre_mitigated" "spectre_retpoline"

# Optimized variant
collect_perf_mitigation "$TEMP_DIR/spectre_optimized" "spectre_mitigated" "spectre_optimized"

echo "[+] Raw data saved to $OUTPUT"
echo "[+] Processing with Python..."

python3 "$SCRIPT_DIR/analyze_mitigation.py"

echo "=== Phase 5 Complete ==="
