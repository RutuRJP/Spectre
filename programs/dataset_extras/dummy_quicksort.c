#include <stdlib.h>
int cmp(const void *a, const void *b) { return (*(int*)a - *(int*)b); }
int main() { int arr[5000]; for(int i=0;i<5000;i++) arr[i]=rand(); qsort(arr, 5000, sizeof(int), cmp); return 0; }
