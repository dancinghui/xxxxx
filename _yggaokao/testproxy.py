#!/usr/bin/env python
# -*- coding:utf8 -*-

import spider.httpreq
import spider.util
import time
import urllib2
import sys
import re
import os
from spider.runtime import Log
from spider.spider import Spider


def test_proxy(p):
    url = "http://gaokao.chsi.com.cn/zsjh/searchZsjh--year-2015,searchType-1,sySsdm-11,start-100.dhtml"
    o = spider.httpreq.BasicRequests()
    kwargs = {'timeout': 6}
    if p:
        o._set_proxy(kwargs, p)
    con = o.request_url(url, **kwargs)
    if con is None or r"403 " in con.text:
        return False
    yxdms = re.findall(r"doDialog\('(\d+)'", con.text, re.S)
    print len(yxdms)
    if len(yxdms) == 20:
        return True
    return False

class TestProxy4zl(Spider):
    def __init__(self, thcnt, fn):
        Spider.__init__(self, thcnt)
        self.tfn = fn
        self.oklist = []

    def dispatch(self):
        with open(self.tfn) as f:
            while True:
                p = f.readline().strip()
                if not p:
                    break
                self.add_job({'type':'testp', 'proxy':p})
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, job):
        p = job['proxy']
        a = time.time()
        tr = test_proxy(p)
        a = time.time()-a
        if not tr:
            Log.errinfo(p, "is BLOCKED")
        elif a>6:
            Log.errinfo(p, "too slow", a)
        else:
            Log.errinfo(p, "OK", a)
            self.oklist.append(p)


def main(fn):
    if test_proxy(None):
        Log.errinfo("I am fine.")
    else:
        Log.errinfo("I am BLOCKED")
    t = TestProxy4zl(30, fn)
    t.run()
    print "========good list:=========="
    t.oklist.sort()
    print "\n".join(t.oklist)
    fd = open("proxy", "w")
    for i in t.oklist:
        fd.write(i + "\n")

if __name__ == '__main__':
    fn = 'curproxy'
    if len(sys.argv) > 1:
        fn = sys.argv[1]
    print fn
    main(fn)

