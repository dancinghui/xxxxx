#include<stdio.h>
#include<stdlib.h>
#define ERROR (-1)

unsigned length(const char*p){
    const char *c=p;
    while(*c)c++;
    return p?c-p:0;
}
/*
 * 进制转十进制long long
 * 不处理负数
 */
long long c2i(char*num,int base){
    if (36<base||base<=1){
        return ERROR;
    }else if(NULL==num){
        return 0;
    }
    char * c=num;
    if(base<=10){
        char m='0'+base;
        while(*c){
            if(*c<'0'||*c>=m)return ERROR;
            c++;
        }
    }else{
        char m='A'+base-11;
        while(*c){
            if(!((*c>='0'&&*c<='9')||(*c>='A'&&*c<=m)))return ERROR;
            c++;
        }
    }
    c--;

    long long n=0;
    long long i=1;
    while(c>=num){
        if(*c>='0'&&*c<='9'){
            n+=(*c-'0')*i;
        }else{
            n+=(*c-'A'+10)*i;
        }
        c--;
        i*=base;
    }
    return n;
}
/**
 * 十进制转其他进制
 */
char * i2c(long long n,int base){
    if(base<=1||base>36)return NULL;
    int cnt;
    char *p=NULL;
    char *c;
    // 判断位数
    long long r=base;
    cnt=2;
    while(r<=n){r*=base;cnt++;}
    p=(char*)calloc(sizeof(char),cnt);
    c=p;
    while (n!=0){
        r=n%base;
        n=n/base;
        *c++=r>=10?'A'+r-10:r+'0';
    }
    char *f=p;
    c--;
    while(c>f){
        *c=*c^*f;
        *f=*c^*f;
        *c=*c^*f;
        c--;
        f++;
    }
    return p;

}
void handle(char*in,char*out,int base){
    FILE * fin=fopen(in,"r");
    FILE * fout=NULL;
    if (NULL!=out)fout=fopen(out,"w");
    char ch[100]={0},cc[100]={0};
    long long p,l=0;
    char *pre=NULL,*cur=ch;
    //while(EOF!=!ftell(fin)){
    while(fgets(cur,99,fin)!=NULL){
        //fscanf(fin,"%s\n",cur);
        char *c=cur;
        int error=0;
        while(*c && *c!='\n'){
            if(*c>='a'&&*c<='z'){
                *c-=0x20;
            }else if(*c=='-'){
                char *s=c;
                do{
                    *s=*(s+1);
                    s++;
                }while(*s);
                continue;
            }else if(!(*c>='0'&&*c<='9')&&!(*c>='A'&&*c<='Z')){
                error=1;
                break;
            }
            c++;
        }
        if(*c=='\n'){
            *c='\0';
        }
        if (error){
            continue;
        }
        p=c2i(cur,base);
        if (p>l+1){
            if(NULL!=fout){
                fprintf(fout,"%s,%s,%lld\n",NULL==pre?"00000000":pre,cur,p-l-1);
            }else{
                printf("%s,%s,%lld\n",NULL==pre?"00000000":pre,cur,p-l-1);
            }
        }
        pre=cur;
        cur=ch==cur?cc:ch;
        l=p;
    }
    fclose(fin);
    if (NULL!=fout){
        fclose(fout);
    }
}
void result(char*in,char*out,long long limit,int base){
    FILE * fin=fopen(in,"r");
    FILE * fout=NULL;
    if (NULL!=out)fout=fopen(out,"w");
    char ch[100]={0};
    long long p,l=0;
    char *cur=ch;
    //while(EOF!=!ftell(fin)){
    while(fgets(cur,99,fin)!=NULL){
        //fscanf(fin,"%s\n",cur);
        char *c=cur;
        int error=0;
        while(*c && *c!='\n'){
            if(*c>='a'&&*c<='z'){
                *c-=0x20;
            }else if(*c=='-'){
                char *s=c;
                do{
                    *s=*(s+1);
                    s++;
                }while(*s);
                continue;
            }else if(!(*c>='0'&&*c<='9')&&!(*c>='A'&&*c<='Z')){
                error=1;
                break;
            }
            c++;
        }
        if(*c=='\n'){
            *c='\0';
        }
        if (error){
            continue;
        }
        p=c2i(cur,base);
        if (p>l+1){
            long long count=p-l-1;
            long long start=l+1;
            char *ps=i2c(start,base);
            char *pe=NULL;
            if (count<=limit){
                pe=i2c(p-1,base);
            }else{
                pe=i2c(l+limit,base);
                count=limit;
            }
            if(NULL!=fout){
                fprintf(fout,"%s,%s,%lld\n",ps,pe,count);
            }else{
                printf("%s,%s,%lld\n",ps,pe,count);
            }
            free(ps);
            free(pe);
        }
        l=p;
    }
    fclose(fin);
    if (NULL!=fout){
        fclose(fout);
    }
}
void help(char *name){
    printf("%s mode base input [outupt] [limit]\n",name);
    printf("\twhen mode=1 or mode=2 result interval is paring,otherwise just paring\n");
    printf("\tlimit only use in result mode,defaut is 50\n");
    printf("\tbase will be 2-36\n");
}
int main(int argc,char*argv[]){
    if (argc>3){

        char *out=NULL;
        int limit=-1;
        char mode=argv[1][0];
        int base=atoi(argv[2]);
        if (base<2||base>36){
            fprintf(stderr,"invalid base %s\n",argv[2]);
        }
        if (argc>4){
            out=argv[4];
        }
        if (argc>5){
            limit=atoi(argv[5]);
        }else if (argc==5&& mode=='2'){
            out=NULL;
            limit=atoi(argv[4]);
        }
        if (mode=='1' || mode=='2'){
            limit=limit<0?50:limit;
            result(argv[3],out,limit,base);
        }else{
            handle(argv[3],out,base);
        }
    }else{
        help(argv[0]);
    }
    return 0;
}
