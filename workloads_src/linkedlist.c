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
