#include <stdlib.h>
struct node { int v; struct node* next; };
int main() { struct node* head=NULL; for(int i=0;i<5000;i++){ struct node* n=malloc(sizeof(*n)); n->v=i; n->next=head; head=n; } return 0; }
