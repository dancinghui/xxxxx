#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import time
from spider.spider2 import Spider2
import re
from spider.savebin import BinSaver

#http://m.liepin.com/hjob/1958221/
#http://job.liepin.com/395_3958512/

class LiepinSpider(Spider2):
    def __init__(self, thcnt):
        Spider2.__init__(self, thcnt)
        self._name = 'jd_liepin'
        self.bs = BinSaver("liepin.%d.bin" % os.getpid())

    def init_jobs(self):
        self.add_main_job_range({}, 1, 9999999)

    def run_job(self, job):
        print "job is ", job
        #url = "http://m.liepin.com/hjob/%d/" % (job['value'])
        value = job['value']
        url = "http://job.liepin.com/%03d_%d/" % (int(value)/10000, int(value))
        res = self.request_url(url)
        if re.search(u'您访问的页面不存在或已删除',  res.text ):
            print job, "match nothing"
        elif re.search(u'该职位已结束', res.text):
            print job, "match ending"
        elif re.search(u'您查看的职位已过期', res.text):
            print job, "match timeout"
        else:
            print "saving %d ..." % job['value']
            name = '%s.%d.%d' % (self._name, job['value'], int(time.time()) )
            self.bs.append(name, res.text)

if __name__ == "__main__":
    s = LiepinSpider(50)
    s.run()
