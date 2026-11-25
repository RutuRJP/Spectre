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
