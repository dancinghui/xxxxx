#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
os.environ['PAGESTORE_DB'] = "mongodb://crawler:crawler@192.168.1.81,192.168.1.82,192.168.1.83/gaokao_crawler"
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider, AccountErrors
import re
#from spider.runtime import Log
from spider.savebin import BinSaver
import random
import threading
import traceback
import spider.util
from spider.savebin import FileSaver
from page_store import PageStoreJobUI

#http://www.jobui.com/job/132925988/
#thread count mapping to proxy number
class JobuiSpider(Spider):
    """
    jobui增量--爬取直接入库
    """
    def __init__(self):
        self.proxies_dict = []
        self.read_proxy("../spider/proxy/proxy.txt")
        Spider.__init__(self, len(self.proxies_dict))
        self.success_count = 0
        self.request_count = 0
        self.__fail_ids = FileSaver("fail_ids.txt")
        self.start_time = time.time()
        self.page_store = PageStoreJobUI()
        self.page_store.testmode = True

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
        i = 130000000
        while i < 140000000 :
            job = {"id":i}
            self.add_job(job, True)
            i += 1
        self.wait_q_breakable()
        self.add_job(None, True)

    def get_fail_cnt(self, addv):
        fc = getattr(self._curltls,'failcount',0)
        if (addv):
            fc += addv
            setattr(self._curltls, 'failcount', fc)
        return fc

    def run_job(self, jobid):
        jobid_int = jobid.get("id")
        url = "http://www.jobui.com/job/%d/" % (jobid_int)
        tid = self.get_tid()
        proxies = self.proxies_dict[tid]
        res = self.request_url(url, proxies=self.proxies_dict[self.get_tid()])

        self.request_count+=1

        if res is None:
            if self.get_fail_cnt(1) < 10:
                self.add_job(jobid)
            else:
                print "id is [ %s ] thread and [ %s ] proxy will be close and drop." % (tid,proxies)
                self.__fail_ids.append(str(jobid_int))
                raise AccountErrors.NoAccountError("Maybe the proxy[ %s ] invalid,failcount = [ %d ]" % (proxies,self.get_fail_cnt(0)))
            return
        else:
            setattr(self._curltls,'failcount',0)

        if res.code == 404:
            print "%d ======》 404" % jobid_int
            return
        elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
            print "%d ------> %d " % (jobid_int,res.code)
            self.add_job(jobid)
            time.sleep(1)
            return
        elif res.code == 200:
            print "%d ————> will be into database......." % jobid_int
            self.page_store.save(int(time.time()), str(jobid_int), url, res.text)
            self.success_count += 1
        else:
            print "#######################################UNKNOWN ERROR############################################# [ %d ]" % res.code
            self.__fail_ids.append(str(jobid_int))
            #raise AccountErrors.NoAccountError('fatal error')

        #if self.request_count % 10000 == range(0,9):
        print "request_count:{},success_count:{},request_speed:{}".format(self.request_count,self.success_count,self.request_count/(time.time()-self.start_time))


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "request_count:{},success_count:{},request_speed:{}".format(self.request_count,self.success_count,self.request_count/(time.time()-self.start_time))
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

    def read_proxy(self,fn):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                m =  re.match(r'(\d+\.\d+\.\d+\.\d+:\d+)', line, re.I)
                if m:
                    prstr = m.group(1)
                    proxies = {'http': 'http://' + prstr+"/", 'https': 'https://' + prstr+"/"}
                    self.proxies_dict.append(proxies)
                elif re.match('\s*#', line):
                    continue
        print " loaded [ %d ] proxis " % len(self.proxies_dict)



if __name__ == "__main__":
    start = time.time()
    s = JobuiSpider()
    s.run()
    end = time.time()
    print "time : {} , success_count : {} ,request_count:{} , request_speed : {}t/s".format((end-start) , s.success_count , s.request_count , s.request_count/(end - start))
