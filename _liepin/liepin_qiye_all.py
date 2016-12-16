#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
import time
from spider.spider import Spider
import re
from spider.savebin import BinSaver
from page_store import PageStoreLP
from spider.httpreq import SpeedControlRequests

# http://m.liepin.com/hjob/1958221/
# http://job.liepin.com/395_3958512/

class LiepinSpider(Spider):

    def __init__(self, thread_cnt):
        super(LiepinSpider, self).__init__(thread_cnt)
        self.page_store = PageStoreLP()
        self.speed_control_requests = SpeedControlRequests()
        self.page_store.testmode = False

    def dispatch(self):

        for i in range(3362419+1, 9999999):
            self.add_main_job(i)
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):

        if isinstance(jobid, int):
            jobid = str(jobid)

        url = "http://job.liepin.com/{}_{}/" .format(jobid[:3], jobid)
        res = self.speed_control_requests.with_sleep_requests(url, 0.1)
        if res is None:
            print "%d failed, sleeping 10 secs." % jobid
            time.sleep(2)
            self.add_job(jobid)
            return

        if re.search(u'您访问的页面不存在或已删除',  res.text ):
            print jobid, "match nothing"
        elif re.search(u'该职位已结束', res.text):
            print jobid, "match ending"
        elif re.search(u'您查看的职位已过期', res.text):
            print jobid, "match timeout"
        else:
            print "saving %s ..." % jobid
            self.page_store.save(int(time.time()), jobid, url, res.text)


if __name__ == "__main__":
    s = LiepinSpider(20)
    s.speed_control_requests.load_proxy('proxy')
    s.run()
