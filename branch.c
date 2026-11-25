#include <stdio.h>
#include <stdlib.h>

int main(){
    long sum=0;
    for(long i=0;i<500000000;i++){
        if(rand()%2)
            sum++;
        else
            sum--;
    }
    printf("%ld\n", sum);
}
