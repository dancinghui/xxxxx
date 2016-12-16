#!/usr/bin/env python
# -*- coding:utf8 -*-
import threading
import urllib2
import re
import sys
import os
import spider.httpreq
from spider.util import htmlfind

def test_proxy(p):
    url = "http://sou.zhaopin.com/jobs/searchresult.ashx?in=210500&jl=%E5%8C%97%E4%BA%AC&p=1&isadv=0"
    o = spider.httpreq.BasicRequests()
    kwargs = {'timeout':6}
    o._set_proxy(kwargs, p)
    con = o.request_url(url, **kwargs)
    flag = False
    if con is None:
        flag = False
    if extract_content(con.text):
        flag = True
    if flag:
        f = open(_file, 'a+')
        print p, '   is OK'
        print >> f, p
        f.close()

def extract_content(doc):
    m = re.search(ur"(?:共|多于)<em>(\d+)</em>个职位满足条件", doc)
    if not m:
        return False
    if int(m.group(1)) == 0:
        return False
    return True

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
    print len(li)
    for i in li:
        t = threading.Thread(target=test_proxy, args=(i,))
        t.start()

