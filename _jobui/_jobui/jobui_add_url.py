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

class JobuiSpiderUrlAdd(Spider):
    """
    jobui增量--爬取直接入库
    """
    def __init__(self):
        self.proxies_dict = []
        self.read_proxy("../spider/proxy/proxy.txt")
        Spider.__init__(self, len(self.proxies_dict))
        self.success_count = 0
        self.request_count = 0
        self.__fail_add_url = FileSaver("fail_add_url.txt")
        self.start_time = time.time()
        self.domain = self.read_domain()
        self.domain_file = FileSaver("domains.txt")
        #self.page_store = PageStoreJobUI()
        #self.page_store.testmode = True

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
        with open('job_url.txt','r') as f:
            while True:
                line = f.readline().strip()
                if line is None:
                    break
                job = {"url":line}
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
        url = jobid.get("url")
        tid = self.get_tid()
        proxies = self.proxies_dict[tid]
        res = self.request_url(url, proxies=self.proxies_dict[self.get_tid()])

        self.request_count+=1

        if res is None:
            if self.get_fail_cnt(1) < 10:
                self.add_job(jobid)
            else:
                print "id is [ %s ] thread and [ %s ] proxy will be close and drop." % (tid,proxies)
                self.__fail_add_url.append(url)
                raise AccountErrors.NoAccountError("Maybe the proxy[ %s ] invalid,failcount = [ %d ]" % (proxies,self.get_fail_cnt(0)))
            return
        else:
            setattr(self._curltls,'failcount',0)

        if res.code == 404:
            print "%s ======》 404" % url
            return
        elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
            print "%s ------> %d " % (url,res.code)
            self.add_job(jobid)
            time.sleep(1)
            return
        elif res.code == 200:
            print "%s ————> will be into database......." % url
            #http://www.jobui.com/job/92336088/
            m = re.search(ur'http://www.jobui.com/job/(\d+)/',url)
            if m:
                jid = m.group(1)
                #self.page_store.save(int(time.time()), jid, url, res.text)
                self.success_count += 1
                self.parseDomain(res.text)
        else:
            print "#######################################UNKNOWN ERROR############################################# [ %d ]" % res.code
            self.__fail_add_url.append(url)
            #raise AccountErrors.NoAccountError('fatal error')

        #if self.request_count % 10000 == range(0,9):
        print "request_count:{},success_count:{},request_speed:{}".format(self.request_count,self.success_count,self.request_count/(time.time()-self.start_time))


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg+= "jobui_add_url.py -- execute result : success_count : {} ,request_count:{}".format(self.success_count, self.request_count)
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)
        if evt == 'STARTED':
            msg = 'jobui_add_url.py start execute...'
            spider.util.sendmail('chentao@ipin.com', '%s STARTED' % sys.argv[0], msg)

    def parseDomain(self,content):
        m = re.search(ur'<em class="sourceWeb common-icon"></em>(.*)</dd>',content)
        if m:
            dm_str = m.group(1)
            m1 = re.search(ur'<a class="no-style fwb " rel="nofllow" target="_blank" href="(.*)" onclick="_hmt.push\(\[\'_trackEvent\', \'jobInfo\', \'jobInfo_info\',\'jobInfo_info_jobSourceWeb\'\]\);">(.*)</a>',dm_str)
            if m1:
                dm_str = m1.group(2)
            dm = '"' + dm_str + '"'
            if dm in self.domain:
                print '[%s] already in domains...'%dm_str
            else:
                self.domain.append(dm)
                self.domain_file.append(dm)
                print '[%s] add to domains...'%dm_str
        else:
            print 'no match domain...'

    def read_domain(self):
        domain = []
        with open('domains.txt','r') as f:
            for line in f:
                domain.append(line.strip())
        return domain

    def read_proxy(self,fn):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                m = re.match(r'(\d+\.\d+\.\d+\.\d+:\d+)', line, re.I)
                if m:
                    prstr = m.group(1)
                    proxies = {'http': 'http://' + prstr+"/", 'https': 'https://' + prstr+"/"}
                    self.proxies_dict.append(proxies)
                elif re.match('\s*#', line):
                    continue
        print " loaded [ %d ] proxis " % len(self.proxies_dict)

if __name__ == "__main__":
    start = time.time()
    s = JobuiSpiderUrlAdd()
    s.run()
    end = time.time()
    print "time : {} , success_count : {} ,request_count:{} , request_speed : {}t/s".format((end-start) , s.success_count , s.request_count , s.request_count/(end - start))
