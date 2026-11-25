#include <stdio.h>
#include <stdlib.h>

#define SIZE (256*1024*1024)

int main() {
    char *arr = malloc(SIZE);

    for(long i=0;i<SIZE;i++)
        arr[i] = i;

    long sum=0;
    for(long i=0;i<SIZE;i++)
        sum += arr[i];

    printf("%ld\n", sum);
    return 0;
}
