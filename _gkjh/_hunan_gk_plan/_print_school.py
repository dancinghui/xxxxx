#!/usr/bin/env python
# -*- coding:utf8 -*-
from school import schools as sch

if __name__ == '__main__':
    for c in sch:
        print c
    print 'size', len(sch)
