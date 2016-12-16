#!/bin/bash

help(){
    echo "ncsum a sum calculator for nacao"
    echo "usage: ncsum input"
}
[ -z "$1" ] && help && exit 0

awk -F, 'BEGIN{sum=0}{sum+=$3}END{print sum}' $1
