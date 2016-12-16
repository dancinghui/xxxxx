#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
sys.path.append(sys.path[0]+"/..")
print sys.path

os.environ['PAGESTORE_DB'] = "mongodb://crawler:crawler@192.168.1.81,192.168.1.82,192.168.1.83/gaokao_crawler"
import time
from spider.spider import Spider, AccountErrors
import re
from spider.savebin import BinSaver
import random
import threading
import traceback
import spider.util
from spider.savebin import BinReader
from page_store import PageStoreJobUI

#http://www.jobui.com/job/131298184/
#thread count mapping to proxy number
class JobuiBin2DB(Spider):
    """
    bin文件读取并写入到库里面去
    """
    def __init__(self,thcnt):
        Spider.__init__(self,thcnt)
        self.num_count = 0
        self.page_store = PageStoreJobUI()
        self.page_store.testmode = False
        self.bin_list = ['jobui_job_data1.bin','jobui_job_bu.bin','jobui_job_data2.bin']

    def wait_q_breakable(self):
        lt = 0
        while True:
            if not self.job_queue.empty() or not self.job_queue2.empty() or not self.job_queue3.empty():
                time.sleep(5)
            if time.time() < lt + 1 and self._running_count==0:
                return True
            time.sleep(2)
            lt = time.time()
            if self._worker_count == 0:
                return False

    def dispatch(self):
        for binname in self.bin_list:
            bin = BinReader("./jobdata/"+binname)
            while True:
                (a,b) = self.bs.readone()
                if a is None:
                    break
                job = {"index":a,"html":b}
                self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)

    def get_fail_cnt(self, addv):
        fc = getattr(self._curltls,'failcount',0)
        if (addv):
            fc += addv
            setattr(self._curltls, 'failcount', fc)
        return fc


    def run_job(self, jobid):
        #jobui_job.131298184.1451893899
        #http://www.jobui.com/job/131298184/
        id = jobid.get("index").split(".")[1]
        url = "http://www.jobui.com/job/%s/" % (id)
        html = jobid.get("html")
        self.page_store.save(int(time.time()), id, url, html)
        self.num_count += 1


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

if __name__ == "__main__":
    start = time.time()
    s = JobuiBin2DB(1)
    s.run()
    end = time.time()
    print "time : {} , count : {} ,speed : {}t/s".format((end-start) , s.num_count ,s.num_count/(end - start))
