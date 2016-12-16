#!/bin/bash
#coding=utf-8

my_python=`which python`

function print_usage(){

    echo "Usage: run.sh  [genq | searchId | getCV] process_cnt"
}

function check_int(){
    echo $1
    expr $1 + 0 &>/dev/null
    if [ $? -ne 0 ]; then
        print_usage;
        echo $1" is not digit "
        exit 1;
    fi

}


if [ $# != 2 ]; then
    print_usage;
    exit 1;
fi
check_int $2;


echo $1

for((i=0;i<$2;i++))
do
    cmd="screen -LdmS cv_liepin_v2.py_process_$i $my_python cv_liepin_v2.py $1 $i $2"
    echo ${cmd}
    $cmd
done