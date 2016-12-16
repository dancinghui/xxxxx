#!/usr/bin/env python
# encoding:utf-8
import time
from spider.savebin import BinReader, BinSaver
from qichacha import QccPageStore
import getopt
import sys
import random


class PageChecker(object):
    def __init__(self, check_file):
        self.check_file = check_file
        pass

    def random_check(self, start=0, limit=10):
        binreader = BinReader(self.check_file)
        opts, args = getopt.getopt(sys.argv[1:], "n:")
        if len(opts) is 0 or opts[0][1] is "":
            randomindex = random.randint(start, start+limit)
        else:
            randomindex = int(opts[0][1])
        line = binreader.readone()
        i = 1
        while i < randomindex and line[0] is not None:
            line = binreader.readone()
            i += 1
        if line[0] is None:
            print "None!!!"
            return
        f = open(line[0] + ".html", "w+b")
        f.write(line[1])
        f.close()

if __name__ == "__main__":
    pc = PageChecker("/home/peiyuan/data/qichacha/old/qichacha.130_140w.bin")
    pc.random_check(0, 100)


# binreader = BinReader("/home/peiyuan/data/sum/qichacha_sum_1451891706.02.bin")
# opts,args = getopt.getopt(sys.argv[1:],"n:")
# if len(opts) is 0 or opts[0][1] is "":
#     randomindex = random.randint(0,10000)
# else:
#     randomindex = int(opts[0][1])
# line = binreader.readone()
# i = 1
# while i< randomindex:
#     line = binreader.readone()
#     i+=1
#
# f = open(line[0]+".html","w+b")
# f.write(line[1])
# f.close()
# exit()
