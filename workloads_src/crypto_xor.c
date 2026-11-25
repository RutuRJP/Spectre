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
