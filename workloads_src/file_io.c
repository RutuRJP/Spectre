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
