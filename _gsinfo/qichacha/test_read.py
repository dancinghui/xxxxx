#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider, AccountErrors
import re
from spider.savebin import BinSaver
import random
import threading
import traceback
import spider.util
from spider.savebin import FileSaver


def test_2():
    filter = set()
    filter_name = set()
    re_self = 0
    new_self = 0
    with open("query_success_name.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                re_self += 1
                print re_self, "自身重复..."
            else:
                new_self += 1
                filter_name.add(line)
    print "自身重复数:", re_self, "成功数量:", new_self
    time.sleep(1)
    re1 = 0
    new = 0
    unnew = 0
    with open("query_success_detail.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                re1 += 1
                print re1, "详情自身重复..."
            else:
                filter.add(line)
                r = eval(line)
                if isinstance(r, list):
                    cname = r[0]
                    if cname in filter_name:
                        new += 1
                        print new, "匹配-----------------"
                    else:
                        unnew += 1
                        filter_name.add(cname)

    print "详情自身重复:", re1, "匹配上的数量:", new, "未匹配上的数量:", unnew


if __name__ == "__main__":
    test_1()
