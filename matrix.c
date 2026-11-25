#include <stdio.h>
#include <stdlib.h>

#define N 512

int A[N][N], B[N][N], C[N][N];

int main() {
    for(int i=0;i<N;i++)
        for(int j=0;j<N;j++){
            A[i][j]=rand()%100;
            B[i][j]=rand()%100;
        }

    for(int i=0;i<N;i++)
        for(int j=0;j<N;j++)
            for(int k=0;k<N;k++)
                C[i][j]+=A[i][k]*B[k][j];

    printf("done\n");
    return 0;
}
