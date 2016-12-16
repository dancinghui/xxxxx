#!/usr/bin/env python
# -*- coding:utf8 -*-
import time

from court.util import save_file
from spider.httpreq import BasicRequests

if __name__ == '__main__':
    count = 100
    req = BasicRequests()
    while count > 0:
        time.sleep(1)
        con = req.request_url('http://egaz.sipo.gov.cn/FileWeb/vci.jpg')
        if con:
            save_file(con.content, './vci/100%s.jpg' % count)
            count -= 1
            print count
