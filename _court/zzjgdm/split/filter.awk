#!/bin/awk -f

BEGIN{
    sum=0;
    limit=100;
 }
{
    if ($3<=limit){
        print "["$1+1","$2-1"]"
        sum+=$3
    }else{
        print "["$1+1","$1+limit"]"
        sum+=limit
    }
}

 END{
    print "sum:",sum
 }

