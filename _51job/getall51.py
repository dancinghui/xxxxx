#!/usr/bin/env python
# -*- coding:utf8 -*-

import re

from spider.savebin import BinSaver

from spider.spider import Spider


class Job51Spider(Spider):
    def dispatch(self):
        self.bs = BinSaver("job51.bin")
        for i in range(45000000, 75000000):
            self.add_main_job(i)
        self.wait_q()
        self.add_main_job(None)
    def run_job(self, jobid):
        print "job is ", jobid
        url = "http://search.51job.com/job/%d,c.html" % jobid
        res = self.request_url(url, [])
        if re.search(u'您选择的职位目前已经暂停招聘',  res.text ):
            print jobid, "match nothing"
        else:
            print "saving %d ..." % jobid
            self.bs.append('51job.%d' % jobid, res.text)

if __name__ == "__main__":
    s = Job51Spider(20)
    s.run()
