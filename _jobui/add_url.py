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
import random
from spider.savebin import FileSaver
from page_store import PageStoreJobUI

class JobuiSpider(Spider):
    """
    jobui增量--爬取直接入库  2016-04-18
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
        self.serial_num = 0

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
        i = 136848805 #134111700
        while i < 150000000:
            i += 1
            job = {"id": i, "retry": 0}
            self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)

    def get_fail_cnt(self, addv, type):
        fc = getattr(self._curltls,type,0)
        if (addv):
            fc += addv
            setattr(self._curltls, type, fc)
        return fc

    def run_job(self, jobid):
        jobid_int = jobid.get("id")
        retry = jobid.get("retry")
        url = "http://www.jobui.com/job/%d/" % (jobid_int)
        tid = self.get_tid()
        proxies = self.proxies_dict[tid]
        res = self.request_url(url, proxies=self.proxies_dict[self.get_tid()])

        self.request_count += 1
        self.serial_num += 1

        if res is None:
            if self.get_fail_cnt(1,'failcount-none') < 10:
                self.re_add_job(jobid)
            else:
                print "id is [ %s ] thread and [ %s ] proxy will be close and drop." % (tid,proxies)
                self.__fail_ids.append(str(jobid_int))
                raise AccountErrors.NoAccountError("Maybe the proxy[ %s ] invalid,failcount = [ %d ]" % (proxies,self.get_fail_cnt(0,'failcount-none')))
            #return
        else:
            setattr(self._curltls,'failcount-none',0)

        if res.code == 407:
            if self.get_fail_cnt(1,'failcount-407') < 10:
                self.re_add_job(jobid)
            else:
                print "id is [ %s ] thread and [ %s ] proxy will be close and drop." % (tid,proxies)
                self.__fail_ids.append(str(jobid_int))
                raise AccountErrors.NoAccountError("Maybe the proxy[ %s ] invalid,failcount = [ %d ]" % (proxies,self.get_fail_cnt(0,'failcount-407')))
            #return
        else:
            setattr(self._curltls,'failcount-407',0)

        if res.code == 404:
            print "%d ======》 404 ---> retry:%d" % (jobid_int, retry)
            if retry < 3:
                self.re_add_job({"id": jobid_int, "retry": (retry+1)})
            else:
                self.__fail_ids.append(str(jobid_int))
            #return
        elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
            print "%d ------> %d " % (jobid_int,res.code)
            self.re_add_job(jobid)
            time.sleep(random.randrange(1, 3, 1))
            #return
        elif res.code == 200:
            self.serial_num = 0
            print "%d ————> will be into database......." % jobid_int
            self.page_store.save(int(time.time()), str(jobid_int), url, res.text)
            self.success_count += 1
        else:
            print "#######################################UNKNOWN ERROR############################################# [ %d ]" % res.code
            if retry < 3:
                self.re_add_job({"id": jobid_int, "retry": (retry+1)})
            else:
                self.__fail_ids.append(str(jobid_int))

        print "serial_number:{},request_count:{},success_count:{},request_speed:{}".format(self.serial_num, self.request_count, self.success_count, self.request_count/(time.time()-self.start_time))


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

    def read_proxy(self,fn):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                self._match_proxy(line)
        print " loaded [ %d ] proxis " % len(self.proxies_dict)


    def _match_proxy(self,line):
        m = re.match('([0-9.]+):(\d+):([a-z0-9]+):([a-z0-9._-]+)$', line, re.I)
        m1 = re.match('([0-9.]+):(\d+):([a-z0-9]+)$', line, re.I)
        if m:
            prstr = '%s:%s@%s:%s' % (m.group(3), m.group(4), m.group(1), m.group(2))
            proxies = {'http': 'http://' + prstr, 'https': 'https://' + prstr}
        elif m1:
            prstr = '%s:%s' % (m1.group(1), m1.group(2))
            proxies = {'http': 'http://' + prstr, 'https': 'https://' + prstr}
        else:
            proxies = {'http': 'http://' + line, 'https': 'https://' + line}
        self.proxies_dict.append(proxies)


if __name__ == "__main__":
    start = time.time()
    s = JobuiSpider()
    s.run()
    end = time.time()
    print "time : {} , success_count : {} ,request_count:{} , request_speed : {}t/s".format((end-start) , s.success_count , s.request_count , s.request_count/(end - start))
