#!/bin/bash

find . -name '*.so' | xargs rm -f
python setup.py build
find . -name '*.so' | xargs -I {} cp {} .
./test.py
