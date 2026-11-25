#!/bin/bash
# ============================================================================
# Large Dataset Generation Script
# ============================================================================
# Runs the workloads hundreds/thousands of times to generate a massive,
# real (non-synthetic) dataset for ML training.
# Output format is compatible with the ML pipeline.

RUNS=${1:-500}  # Default to 500 runs per workload if not specified
OUTPUT_RAW="large_perf_data_raw.csv"
OUTPUT_FINAL="large_labeled_dataset.csv"

echo "==============================================================="
echo " LARGE DATASET GENERATION (Runs per workload: $RUNS)"
echo "==============================================================="
echo "[+] Starting at $(date)"

# Wait and setup
mkdir -p programs/dataset_extras
cd programs/dataset_extras || exit 1

# 1. Ensure all workloads exist and compile them
cat << 'EOF' > dummy_crypto.c
#include <stdio.h>
int main() { long sum=0; for(int i=0;i<50000;i++) sum+=i^0xDEADBEEF; return 0; }
EOF
cat << 'EOF' > dummy_hash.c
#include <stdio.h>
int main() { long h=5381; for(int i=0;i<50000;i++) h=((h<<5)+h)+i; return 0; }
EOF
cat << 'EOF' > dummy_file_io.c
#include <stdio.h>
int main() { FILE *f=fopen("/dev/null","w"); for(int i=0;i<50000;i++) fprintf(f, "test"); fclose(f); return 0; }
EOF
cat << 'EOF' > dummy_fibonacci.c
#include <stdio.h>
int fib(int n) { if(n<=1) return n; return fib(n-1)+fib(n-2); }
int main() { fib(30); return 0; }
EOF
cat << 'EOF' > dummy_quicksort.c
#include <stdlib.h>
int cmp(const void *a, const void *b) { return (*(int*)a - *(int*)b); }
int main() { int arr[5000]; for(int i=0;i<5000;i++) arr[i]=rand(); qsort(arr, 5000, sizeof(int), cmp); return 0; }
EOF
cat << 'EOF' > list.c
#include <stdlib.h>
struct node { int v; struct node* next; };
int main() { struct node* head=NULL; for(int i=0;i<5000;i++){ struct node* n=malloc(sizeof(*n)); n->v=i; n->next=head; head=n; } return 0; }
EOF

echo "[+] Compiling all workloads..."
gcc -O2 dummy_crypto.c -o crypto_xor.out
gcc -O2 dummy_hash.c -o hash_chain.out
gcc -O2 dummy_file_io.c -o file_io.out
gcc -O2 dummy_fibonacci.c -o fibonacci.out
gcc -O2 dummy_quicksort.c -o quicksort.out
gcc -O2 list.c -o linkedlist.out

# Collect baseline workloads from root
cd ../../
echo "[+] Checking baseline workloads..."
if [ ! -f "branch.out" ]; then gcc -O2 branch.c -o branch.out; fi
if [ ! -f "matrix.out" ]; then gcc -O2 matrix.c -o matrix.out; fi
if [ ! -f "memtest.out" ]; then gcc -O2 memtest.c -o memtest.out; fi
# spectre workload
if [ ! -f "programs/SpectrePoC/spectre.out" ]; then gcc programs/SpectrePoC/spectre.c -O2 -o programs/SpectrePoC/spectre.out; fi

rm -f "$OUTPUT_RAW"

collect_data() {
    local bin_path="$1"
    local label="$2"
    local name="$3"
    
    echo "    Collecting: $name ($label) — $RUNS runs..."
    for ((i=1; i<=RUNS; i++)); do
        echo ",,,,,$label,$name" >> "$OUTPUT_RAW"
        perf stat -x , -e cycles,instructions,branches,branch-misses,cache-references,cache-misses "$bin_path" 2>> "$OUTPUT_RAW"
    done
}

echo "[+] Collecting performance counter data..."

# Collect normal (10 workloads)
collect_data "./programs/dataset_extras/crypto_xor.out" "normal" "crypto"
collect_data "./programs/dataset_extras/hash_chain.out" "normal" "hash"
collect_data "./programs/dataset_extras/file_io.out"    "normal" "fileio"
collect_data "./programs/dataset_extras/fibonacci.out"  "normal" "fib"
collect_data "./programs/dataset_extras/quicksort.out"  "normal" "qsort"
collect_data "./programs/dataset_extras/linkedlist.out" "normal" "list"
collect_data "./branch.out"                             "normal" "branch"
collect_data "./matrix.out"                             "normal" "matrix"
collect_data "./memtest.out"                            "normal" "memtest"

# Collect spectre
# Since we have 9 normal workloads, run spectre for 3x runs to maintain class balance
SPECTRE_RUNS=$((RUNS * 3))
echo "    Collecting: spectre (spectre) — $SPECTRE_RUNS runs..."
for ((i=1; i<=SPECTRE_RUNS; i++)); do
    echo ",,,,,spectre,spectre" >> "$OUTPUT_RAW"
    perf stat -x , -e cycles,instructions,branches,branch-misses,cache-references,cache-misses ./programs/SpectrePoC/spectre.out 2>> "$OUTPUT_RAW"
done

echo "[+] Raw data collected in $OUTPUT_RAW"
echo "[+] Processing massive dataset into final ML format using Windows Python..."
echo "    Run: python process_large_dataset.py"
echo "==============================================================="
echo "Done!"
