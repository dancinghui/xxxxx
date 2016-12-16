#!/usr/bin/env python
# encoding:utf-8

from qichacha import QccPageStore
import sys
from spider.ipin.savedb import BinReader
import re

def restore(qp, fn):
    r = BinReader(fn)
    while True:
        k, v = r.readone()
        if k is None:
            break
        _, docid, t = re.split(r'\.', k, 2)
        docid = re.sub(r'^.*_', '', docid)
        t = int(t)
        #assert  isinstance(qp, QccPageStore)
        url = "http://qichacha.com/firm_CN_" + docid
        print "saving", docid, t
        qp.save(t, docid, url, v.decode('utf-8'))


if __name__ == '__main__':
    qp = QccPageStore()
    for i in sys.argv[1:]:
        try:
            restore(qp, i)
        except Exception as e:
            print e
