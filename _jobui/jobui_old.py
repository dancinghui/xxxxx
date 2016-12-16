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
class JobuiSpider(Spider):
    """
    jobui读取库内旧ID重爬
    """
    def __init__(self):
        self.proxies_dict = []
        self.read_proxy("proxy_030814.txt")
        Spider.__init__(self, len(self.proxies_dict))
        self.success_count = 0
        self.request_count = 0
        self.__fail_urls = FileSaver("fail_urls.txt")
        self.start_time = time.time()
        self.page_store = PageStoreJobUI()
        self.page_store.testmode = False

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
        with open("db_jobid.txt") as f :
            for url in f:
                job = {"url":url.strip(), "retry": 0}
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
        url = jobid.get("url")
        retry = jobid.get("retry")
        tid = self.get_tid()
        proxies = self.proxies_dict[tid]
        res = self.request_url(url, proxies=self.proxies_dict[self.get_tid()])

        self.request_count += 1

        if res is None:
            if self.get_fail_cnt(1,'failcount-none') < 10:
                self.re_add_job(jobid)
            else:
                print "id is [ %s ] thread and [ %s ] proxy will be close and drop." % (tid,proxies)
                #self.__fail_urls.append(url)
                self.re_add_job(jobid)
                raise AccountErrors.NoAccountError("Maybe the proxy[ %s ] invalid,failcount = [ %d ]" % (proxies,self.get_fail_cnt(0,'failcount-none')))
            return
        else:
            setattr(self._curltls,'failcount',0)

        if res.code == 407:
            if self.get_fail_cnt(1,'failcount-407') < 10:
                print "%s ======》 407  , retry:%d" % (url,retry)
                self.re_add_job(jobid)
            else:
                print "id is [ %s ] thread and [ %s ] proxy will be close and drop." % (tid,proxies)
                self.re_add_job(jobid)
                #self.__fail_urls.append(url)
                raise AccountErrors.NoAccountError("Maybe the proxy[ %s ] invalid,failcount = [ %d ]" % (proxies,self.get_fail_cnt(0,'failcount-407')))
            return
        else:
            setattr(self._curltls,'failcount-407',0)

        if res.code == 404:
            print "%s ======》 404  , retry:%d" % (url,retry)
            if retry < 3:
                self.re_add_job({"id": jobid_int, "retry": (retry+1)})
            else:
                self.__fail_urls.append(url)
            return
        elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
            print "%s ------> %d " % (url, res.code)
            self.add_job(jobid)
            time.sleep(random.randrange(1, 3, 1))
            return
        elif res.code == 200:
            print "%s ————> will be into database......." % url
            m = re.search(ur'http://www.jobui.com/job/(\d+)/', url)
            if m:
                jid = m.group(1)
                self.page_store.save(int(time.time()), jid, url, res.text)
                self.success_count += 1
        else:
            print "#######################################UNKNOWN ERROR############################################# [ %d ] retry:%d" % (res.code, retry)
            if retry < 3:
                self.re_add_job({"id": jobid_int, "retry": (retry+1)})
            else:
                self.__fail_urls.append(url)

            #raise AccountErrors.NoAccountError('fatal error')

        print "request_count:{},success_count:{},request_speed:{}".format(self.request_count,self.success_count,self.request_count/(time.time()-self.start_time))


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "request_count:{},success_count:{},request_speed:{}".format(self.request_count,self.success_count,self.request_count/(time.time()-self.start_time))
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

    def read_proxy(self,fn):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                self._match_proxy(line)
                # m =  re.match(r'(\d+\.\d+\.\d+\.\d+:\d+)', line, re.I)
                # if m:
                #     prstr = m.group(1)
                #     proxies = {'http': 'http://' + prstr+"/", 'https': 'https://' + prstr+"/"}
                #     self.proxies_dict.append(proxies)
                # elif re.match('\s*#', line):
                #     continue
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
