#!/usr/bin/env python
# -*- coding:utf8 -*-

import re

from savebin import BinSaver

from spider import Spider


class EchengSpider(Spider):
    def dispatch(self):
        self.bs = BinSaver("echeng.bin")
        for i in range(54300018+1, 56000000):
            self.add_main_job(i)
        self.wait_q()
        self.add_main_job(None)
    def run_job(self, jobid):
        print "job is ", jobid
        url = "http://www.cheng95.com/positions/detail?id=%d" % jobid
        res = self.request_url(url, [])
        print type(res.text)
        if re.search(u'服务器出了点问题',  res.text ):
            print "match..........nothing"
            return
        self.bs.append('echeng.%d' % jobid, res.text)

if __name__ == "__main__":
    s = EchengSpider(20)
    s.run()
