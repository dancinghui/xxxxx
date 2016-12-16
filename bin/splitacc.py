#!/usr/bin/env python
# -*- coding:utf8 -*-

import json
import sys
from spider.util import CJSONEncoder, transform


class AccJsonEncoder(CJSONEncoder):
    def __init__(self):
        CJSONEncoder.__init__(self, indent=4)
    def _inclevel(self, dct):
        self.level += 1
        if self.level>1:
            self.indent = None
    def _declevel(self, dct):
        self.level -= 1
        if self.level<=1:
            self.indent = 4


def out_acc(index, mainac, otherac):
    print "====== %d =====" % index
    transform(mainac, lambda c : json.loads(c))
    transform(otherac, lambda c : json.loads(c))
    js = {"main":mainac, "gcv":otherac}
    jstr = AccJsonEncoder().encode(js)
    if isinstance(jstr, unicode):
        jstr = jstr.encode('utf-8')
    with open('acc%d' % index, 'w') as fd:
        fd.write(jstr + "\n")


def split_acc(fn, mainlen, olen):
    list_main = []
    list_other = []
    index = 0
    for line in open(fn, 'r').readlines():
        if 'BROKEN' in line:
            continue
        line = line.strip()
        if '不能搜索' in line:
            list_other.append(line)
        else:
            if len(list_main)*olen < len(list_other) * mainlen:
                list_main.append(line)
            else:
                list_other.append(line)
        if index < 8 and len(list_main)>=mainlen and len(list_other)>=olen:
            index += 1
            out_acc(index, list_main[0:mainlen], list_other[0:olen])
            list_main = list_main[mainlen:]
            list_other = list_other[olen:]

    if len(list_main) + len(list_other) > 0:
        with open('acc_', 'w') as fd:
            for i in list_main:
                fd.write(i + "\n")
            for i in list_other:
                fd.write(i + "\n")


if __name__ == '__main__':
    if len(sys.argv)>1:
        fn = "../lab/acctype/%s.stats" % sys.argv[1]
        split_acc(fn, 10, 10)
    else:
        print "usage:"
        print " %s 51job|zhilian" % sys.argv[0]
