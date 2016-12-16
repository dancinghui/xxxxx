#!/bin/bash

i=1
while [ $i -le 8 ]
do
    echo "====< $i >===" >> $2
    cut -c $i $1 |  sort | uniq -c >> $2
    i=$((i+1))
done

