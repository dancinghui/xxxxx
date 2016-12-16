#!/usr/bin/env python
# -*- coding:utf8 -*-

import urllib2
import re
import os
import spider.httpreq
from spider.spider import Spider
from spider.util import htmlfind
from spider.runtime import Log
import time


def test_proxy(p):
    url = "http://www.jobui.com/company/10608979/"
    o = spider.httpreq.BasicRequests()
    kwargs = {'timeout':6}
    o._set_proxy(kwargs, p)
    con = o.request_url(url, **kwargs)

    if con is None:
        return None
    if extract_content(con.text):
        return True

def extract_content(doc):

    find = htmlfind(doc, '<dl class="j-edit hasVist dlli mb10">', 0)
    if find:
        return True


class TestProxy4zl(Spider):
    def __init__(self, thcnt, fn):
        Spider.__init__(self, thcnt)
        self.tfn = fn
        self.oklist = []
        self.push_job = lambda job: self.add_job(job)

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

if __name__ == '__main__':
    _file = 'proxy'
    if os.path.exists(_file):
        os.remove(_file)
    url = 'http://dev.kuaidaili.com/api/getproxy?orderid=925817981728018&num=999&protocol=1&quality=1&sp1=1'
    oper = urllib2.urlopen(url, timeout=20)
    data = oper.read()
    li = re.findall('(\d+\.\d+\.\d+\.\d+:\d+)', data)
    dic = {}
    print len(li)
    for i in li:
        dic[i] = '0'
    li = dic.keys()

    with open(_file, 'wb') as f:
        for i in li:
            print >> f, i

    r = TestProxy4zl(30, _file)
    r.run()

    with open('checked_proxy', 'wb')  as f:
        print "ok number: %d =========== " % len(r.oklist)
        for i in r.oklist:
            print i
            print >> f, i

