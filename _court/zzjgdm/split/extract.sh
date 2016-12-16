#!/bin/bash

 [ ! -f $1 ]&& echo "file $1 dosen't exist" && exit

 out=`echo $1 | awk -F'/' '{print $NF}'`
 
 sort -t, -sf -k1 $1 | uniq | awk -F, '{print $1","$4","$2","$3","$5","$6","$7","$8","$9}' > "${out}.dat"
 
