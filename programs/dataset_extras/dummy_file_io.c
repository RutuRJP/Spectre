#include <stdio.h>
int main() { FILE *f=fopen("/dev/null","w"); for(int i=0;i<50000;i++) fprintf(f, "test"); fclose(f); return 0; }
