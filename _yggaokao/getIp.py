#!/usr/bin/env python
# -*- coding:utf8 -*-
import urllib2
import re
import sys
import os
if __name__ == '__main__':
    _file = 'curproxy'
    if os.path.exists(_file):
        os.remove(_file)
    #proxy = urllib2.ProxyHandler({'http': 'ipin:ipin1234@106.75.134.192:18888'})
    #opener = urllib2.build_opener(proxy)
    #urllib2.install_opener(opener)
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
    f = open(_file,'w')
    for i in li:
        print >>f,  i
    f.close()
