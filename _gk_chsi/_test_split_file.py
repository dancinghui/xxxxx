#!/usr/bin/env python
# -*- coding:utf8 -*-
from chsispider import split_seeds

if __name__ == '__main__':
    split_seeds('spec.seeds.sh', 3, 'spec.seeds.sh.1c', rates=[2, 1, 3, 2])
