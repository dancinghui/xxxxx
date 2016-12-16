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
    url = "http://jobs.51job.com/all/co3043977.html"
    o = spider.httpreq.BasicRequests()
    kwargs = {'timeout':6}
    o._set_proxy(kwargs, p)
    con = o.request_url(url, **kwargs)
    flag = False
    if con is None:
        flag = False
    if extract_content(con.text) != '':
        flag = True
    if flag:
        f = open(_file, 'a+')
        print p, '   is OK'
        print >> f, p
        f.close()


def extract_content(doc):
    content = ''
    divs = htmlfind.findTag(doc, 'div', 'class="in"')
    if divs:
        ps = re.findall(r'<p[^<>]*>(.*?)</p>', divs[0], re.S)
        for p in ps:
            content += htmlfind.remove_tag(p, True) + "#"
    if isinstance(content, unicode):
        content = content.encode('utf-8')
    return content

if __name__ == '__main__':
    _file = 'proxy.txt'
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

