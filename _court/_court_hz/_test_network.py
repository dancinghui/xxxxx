#!/usr/bin/env python
# -*- coding:utf8 -*-
from spider.httpreq import BasicRequests

if "__main__" == __name__:
    rq = BasicRequests()
    rq.set_proxy('106.75.134.190:18888:ipin:ipin1234')
    con = rq.request_url('http://www.zjsfgkw.cn/document/JudgmentDetail/4062962')
    if con:
        print con.text
