#include <stdio.h>
int main() { long h=5381; for(int i=0;i<50000;i++) h=((h<<5)+h)+i; return 0; }
