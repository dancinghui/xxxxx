#!/bin/bash

sh extract.sh ../res.csv
sh extract.sh ../res.local.csv
sort -m res.csv.dat res.local.csv.dat | uniq > res.merge.dat
awk -F, '{print $1","$2","$4}' res.merge.dat > res.short.dat
