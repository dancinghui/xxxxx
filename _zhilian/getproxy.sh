#!/bin/bash

cd /home/xungeng/getjd/_zhilian
./testproxy.py curproxy || loadpy.sh ./testproxy.py curproxy
mv check.result curproxy
