#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.spider import Spider, MRLManager, AccountErrors
import re
import time
import sys
import random
import spider.util
import spider.runtime
import os
from spider.httpreq import SessionRequests

class check(object):
    def __init__(self):
        self.sessionReq = SessionRequests()
        self.sessionReq.load_proxy('../_51job/proxy')

    def start(self):
        print 'begin crawler!'
        url = r"http://gaokao.chsi.com.cn/zsjh/search.do?ccdm=&jhxzdm=&kldm=&method=majorList&sySsdm=11&year=2016&yxdm=10001"
        header = {"User-Agent":r"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0",
                  "Host": r"gaokao.chsi.com.cn",
                  "Referer": r"http://gaokao.chsi.com.cn/zsjh/"
                  }
        while True:
            i = random.randint(1, 60)
            print i
            con = self.sessionReq.request_url(url, headers=header)
            if con is None or con.text.strip() is "":
                print "Nothing back!readd job"
                time.sleep(i)
                continue
            if r"302 Found" in con.text:
                print "302 Found!"
                time.sleep(i)
                continue
            if r"403 Forbidden" in con.text:
                print "403 Forbidden!"
                time.sleep(i)
                continue
            if "专业名称" not in con.text or "计划数" not in con.text:
                print "阳光高考还没更新！"
                time.sleep(i)
                continue
            if "专业名称" in con.text and "计划数" in con.text:
                print "阳光高考已经更新！"
                break
        spider.util.sendmail(['wangwei@ipin.com'], '阳光高考可以爬了!', "请迅速去抓该网站！")

if __name__ == '__main__':
    spider.util.use_utf8()
    r = check()
    r.start()