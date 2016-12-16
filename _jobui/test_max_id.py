#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
import time
from spider.spider import Spider, AccountErrors
import re
from spider.savebin import BinSaver
import random
import threading
from spider.util import Log
import spider.util


#http://www.jobui.com/job/132971013/
class JobuiSpider(Spider):
    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        self._savelock = threading.RLock()
        self.num_count = 0

    def dispatch(self):
        self.bs = BinSaver("jobui_job.bin")
        for i in range(133002626, 133002636,1) :
            self.add_job(i, True)
        self.wait_q()
        self.add_job(None, True)

    def run_job(self, jobid):
        self.num_count += 1
        #print "job is ", jobid
        url = "http://www.jobui.com/job/%d/" % (jobid)
        # url = 'http://www.jobui.com/job/1962956760/'
        res = self.request_url(url)
        print "id:{}  , Page status: {} ".format(jobid , res.code)
        if res is None:
            print "%d failed, sleeping 10 secs." % jobid
            time.sleep(5)
            self.add_job(jobid)
            return
        elif res.code == 404:
            time.sleep(3)
            return
        elif res.code == 503:
            print "maybe speed too fast..."
            time.sleep(5)
            self.add_job(jobid)
            return
        elif res.code == 200:
            print "saving %d ..." % jobid
            with self._savelock:
                with open("jobid.txt","a+b") as f:
                    f.write("%s\n" % jobid)
                    #f.flush()
                    #fn = 'jobui_job.%d.%d' % (jobid, int(time.time()))
                    #self.bs.append(fn, res.text)
            time.sleep(5)
        else:
            Log.error("unknown xxxxx")
            Log.errorbin("%s"%jobid, res.text)
            raise AccountErrors.NoAccountError('fatal error')

    #send email to me
    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

if __name__ == "__main__":
    start = time.time()
    s = JobuiSpider(20)
    #s.load_proxy("../_zhilian/curproxy")
    s.run()
    end = time.time()
    print "time : {} , count : {} ,speed : {}t/s".format((end-start) , s.num_count ,s.num_count/(end - start))
