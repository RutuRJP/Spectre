#include <stdio.h>
int main() { long sum=0; for(int i=0;i<50000;i++) sum+=i^0xDEADBEEF; return 0; }
