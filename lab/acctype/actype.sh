#!/bin/bash

if [ "$1" == "51job" -o "$1" == "zhilian" ] ; then
	rm -f a check_result
	cp $1.stats a
	./actype.py $1 || loadpy.sh ./actype.py $1
	mv check_result $1.stats
fi
