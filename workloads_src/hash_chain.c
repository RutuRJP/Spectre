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
