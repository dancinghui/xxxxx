# -*- coding:utf8 -*-
import threading
import urllib2
import re
import sys
import os
import spider.httpreq
from spider.util import htmlfind


def test_proxy(p):
    url = "https://company.liepin.com/1362819/"
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
    spans = htmlfind.findTag(doc, 'div', 'class="company-introduction clearfix"')
    if spans:
        ps = re.findall(r'<p[^<>]*>(.*?)</p>', spans[0], re.S)
        for p in ps:
            content += htmlfind.remove_tag(p, True) + "#"
    if isinstance(content, unicode):
        content = content.encode('utf-8')
    return content

if __name__ == '__main__':
    _file = 'proxy'
    if os.path.exists(_file):
        os.remove(_file)
    url = 'http://dev.kuaidaili.com/api/getproxy?orderid=925817981728018&num=1999&protocol=2'
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
