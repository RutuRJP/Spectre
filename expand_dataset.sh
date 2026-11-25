#!/bin/bash
# ============================================================================
# Dataset Expansion Script (Phase 1)
# ============================================================================
# Runs additional workloads under perf stat to expand the dataset.
# Must be executed in a Linux environment with perf and gcc available.
#
# Usage: bash expand_dataset.sh
# Output: expanded_perf_data.csv
# ============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNS=50         # repetitions per workload
OUTPUT="$SCRIPT_DIR/expanded_perf_data.csv"
TEMP_DIR="$SCRIPT_DIR/workloads_bin"
SRC_DIR="$SCRIPT_DIR/workloads_src"

mkdir -p "$TEMP_DIR" "$SRC_DIR"

# ──────────────────── Create Workload Sources ──────────────────────

# 1. AES-like crypto workload (XOR cipher simulation)
cat > "$SRC_DIR/crypto_xor.c" << 'CEOF'
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define SIZE (16*1024*1024)
int main() {
    unsigned char *data = malloc(SIZE);
    unsigned char key[16] = {0x2b,0x7e,0x15,0x16,0x28,0xae,0xd2,0xa6,
                             0xab,0xf7,0x15,0x88,0x09,0xcf,0x4f,0x3c};
    for (long i = 0; i < SIZE; i++) data[i] = (unsigned char)(i & 0xFF);
    for (int round = 0; round < 10; round++)
        for (long i = 0; i < SIZE; i++)
            data[i] ^= key[i % 16];
    long sum = 0;
    for (long i = 0; i < SIZE; i++) sum += data[i];
    printf("%ld\n", sum);
    free(data);
    return 0;
}
CEOF

# 2. SHA-like hashing workload (simple hash chain)
cat > "$SRC_DIR/hash_chain.c" << 'CEOF'
#include <stdio.h>
#include <stdlib.h>
#define ROUNDS 100000000
int main() {
    unsigned long h = 0x6a09e667;
    for (long i = 0; i < ROUNDS; i++) {
        h ^= (h << 13);
        h ^= (h >> 7);
        h ^= (h << 17);
        h += i;
    }
    printf("%lu\n", h);
    return 0;
}
CEOF

# 3. File I/O benchmark
cat > "$SRC_DIR/file_io.c" << 'CEOF'
#include <stdio.h>
#include <stdlib.h>
#define BUF_SIZE (4*1024)
#define ITERATIONS 10000
int main() {
    char buf[BUF_SIZE];
    FILE *f = fopen("/dev/null", "w");
    if (!f) return 1;
    for (int i = 0; i < BUF_SIZE; i++) buf[i] = (char)(i % 256);
    for (int iter = 0; iter < ITERATIONS; iter++)
        fwrite(buf, 1, BUF_SIZE, f);
    fclose(f);
    printf("done\n");
    return 0;
}
CEOF

# 4. Recursive Fibonacci (heavy branch workload)
cat > "$SRC_DIR/fibonacci.c" << 'CEOF'
#include <stdio.h>
long fib(int n) {
    if (n <= 1) return n;
    return fib(n-1) + fib(n-2);
}
int main() {
    printf("%ld\n", fib(42));
    return 0;
}
CEOF

# 5. Quick Sort workload
cat > "$SRC_DIR/quicksort.c" << 'CEOF'
#include <stdio.h>
#include <stdlib.h>
#define N 5000000
int arr[N];
void swap(int *a, int *b) { int t=*a; *a=*b; *b=t; }
int partition(int lo, int hi) {
    int p = arr[hi]; int i = lo-1;
    for (int j = lo; j < hi; j++)
        if (arr[j] <= p) { i++; swap(&arr[i], &arr[j]); }
    swap(&arr[i+1], &arr[hi]);
    return i+1;
}
void qsort_impl(int lo, int hi) {
    if (lo < hi) {
        int pi = partition(lo, hi);
        qsort_impl(lo, pi-1);
        qsort_impl(pi+1, hi);
    }
}
int main() {
    srand(42);
    for (int i = 0; i < N; i++) arr[i] = rand();
    qsort_impl(0, N-1);
    printf("%d\n", arr[N/2]);
    return 0;
}
CEOF

# 6. Linked list traversal (pointer-chasing, cache-unfriendly)
cat > "$SRC_DIR/linkedlist.c" << 'CEOF'
#include <stdio.h>
#include <stdlib.h>
#define N 2000000
struct Node { long val; struct Node *next; };
int main() {
    struct Node *nodes = malloc(N * sizeof(struct Node));
    int *perm = malloc(N * sizeof(int));
    for (int i = 0; i < N; i++) perm[i] = i;
    srand(42);
    for (int i = N-1; i > 0; i--) {
        int j = rand() % (i+1); int t = perm[i]; perm[i] = perm[j]; perm[j] = t;
    }
    for (int i = 0; i < N-1; i++) { nodes[perm[i]].val = perm[i]; nodes[perm[i]].next = &nodes[perm[i+1]]; }
    nodes[perm[N-1]].val = perm[N-1]; nodes[perm[N-1]].next = NULL;
    struct Node *cur = &nodes[perm[0]]; long sum = 0;
    while (cur) { sum += cur->val; cur = cur->next; }
    printf("%ld\n", sum);
    free(nodes); free(perm);
    return 0;
}
CEOF

echo "=== Phase 1: Dataset Expansion ==="
echo "[+] Compiling workloads..."

WORKLOADS=("crypto_xor" "hash_chain" "file_io" "fibonacci" "quicksort" "linkedlist")

for w in "${WORKLOADS[@]}"; do
    gcc -O2 -o "$TEMP_DIR/$w" "$SRC_DIR/$w.c"
    echo "    Compiled $w"
done

# Also ensure Spectre PoC is compiled
SPECTRE_DIR="$SCRIPT_DIR/programs/SpectrePoC"
if [ -f "$SPECTRE_DIR/spectre.c" ]; then
    gcc -O0 -o "$TEMP_DIR/spectre" "$SPECTRE_DIR/spectre.c" 2>/dev/null || true
    echo "    Compiled spectre (unmitigated)"
fi

# Also compile existing workloads
for src in "$SCRIPT_DIR/branch.c" "$SCRIPT_DIR/matrix.c" "$SCRIPT_DIR/memtest.c"; do
    base=$(basename "$src" .c)
    gcc -O2 -o "$TEMP_DIR/$base" "$src"
    echo "    Compiled $base"
done

echo "[+] Collecting perf data ($RUNS runs per workload)..."
echo "" > "$OUTPUT"

collect_perf() {
    local binary="$1"
    local label="$2"
    local name="$3"

    echo "    Collecting: $name ($label)..."
    for i in $(seq 1 $RUNS); do
        perf stat -x , -e cycles,instructions,branches,branch-misses,cache-references,cache-misses \
            "$binary" 2>> "$OUTPUT" > /dev/null
        echo ",,,,$label,$name" >> "$OUTPUT"
    done
}

# Benign workloads
for w in "${WORKLOADS[@]}"; do
    collect_perf "$TEMP_DIR/$w" "normal" "$w"
done

# Existing benign workloads
collect_perf "$TEMP_DIR/branch" "normal" "branch"
collect_perf "$TEMP_DIR/matrix" "normal" "matrix"
collect_perf "$TEMP_DIR/memtest" "normal" "memtest"

# Spectre attack
if [ -f "$TEMP_DIR/spectre" ]; then
    collect_perf "$TEMP_DIR/spectre" "spectre" "spectre"
fi

echo "[+] Raw perf data saved to $OUTPUT"
echo "[+] Processing with Python..."

python3 "$SCRIPT_DIR/process_expanded_data.py"

echo "=== Phase 1 Complete ==="
