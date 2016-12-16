#!/usr/bin/env python
# -*- coding:utf8 -*-

import sys
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider, AccountErrors
import re
from spider.savebin import FileSaver
import spider.util
import gs_guangdong
import threading
import random
filter_name = set()

class RunGuangdong(Spider):
    """
    工商网站--广东
    """
    def __init__(self):
        spider.util.use_utf8()
        self.is_debug = False
        if self.is_debug:
            Spider.__init__(self, 1)
            self.gsweb = gs_guangdong.SearchGSWebGuangdong(None)
        else:
            self.proxies_dict = []
            self.read_proxy("../../_ct_proxy/proxy_041209.txt")
            Spider.__init__(self, len(self.proxies_dict))
            self._curltls = threading.local()
        self.gswebs = {}
        self.already = FileSaver("gsinfo_out_spidered_cname1.txt")
        self.success = FileSaver("gsinfo_out.txt")
        self.result_null = FileSaver("gsinfo_out_null.txt")
        #初始化已经爬过的公司
        self.init_cname()
        time.sleep(2)
        self.cnt = 1
        self.run_time = time.time()

    def init_obj(self):
        threadident = str(threading.currentThread().ident)
        gsweb = gs_guangdong.SearchGSWebGuangdong(None)
        if not self.is_debug:
            gsweb.proxies = self.proxies_dict[self.get_tid()]
        self.gswebs[threadident] = gsweb
        setattr(self._curltls, "gsweb", gsweb)
        return gsweb

    def init_cname(self):
        with open("gsinfo_out_spidered_cname1.txt","r") as f:
            for line in f:
                filter_name.add(line.strip())
            print "init already spidered company name finished !"

    def wait_q_breakable(self):
        lt = 0
        while True:
            if not self.job_queue.empty() or not self.job_queue2.empty() or not self.job_queue3.empty():
                time.sleep(5)
            if time.time() < lt + 1 and self._running_count == 0:
                return True
            time.sleep(2)
            lt = time.time()
            if self._worker_count == 0:
                return False

    def dispatch(self):
        with open("guangdong_cname_new.txt", "r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                if line in filter_name:
                    print cnt, line, " ---> already spider!!!"
                    continue
                job = {"name": line, "cnt": cnt, "retry": 0}
                self.add_job(job, True)
                #time.sleep(0.02)
        self.wait_q_breakable()
        self.add_job(None, True)


    def record_spider(self,line):
        """
        已经爬过的,无论成功失败都算爬过.
        """
        filter_name.add(line)
        self.already.append(line)
        self.cnt += 1

    def run_job(self, jobid):
        gsweb = getattr(self._curltls, "gsweb", None)
        if gsweb is None:
            gsweb = self.init_obj()
        cname = jobid.get("name")
        cnt = jobid.get("cnt")
        out = gsweb.search_company(cname)
        if out is None:
            self.job_retry(jobid)
            if self.get_fail_cnt("failcnt", 1) > 10:
                raise AccountErrors.NoAccountError("Maybe the proxy invalid,failcount-none = [ %d ]" % self.get_fail_cnt("failcnt", 0))
        else:
            setattr(self._curltls, "failcnt", 0)

            if len(out) == 0:
                print cnt, "--->", cname, '---> query list result length = 0'
                #self.record_spider(cname)
                self.result_null.append(cname)
                filter_name.add(cname)
            else:
                for oi in out:
                    self.success.append(spider.util.utf8str(oi))
                self.record_spider(cname)

            if time.time() - self.run_time > 20:
                print "speed------> ------> ------> ------> ------> ------>", self.cnt/(time.time() - self.run_time), "t/s"
                self.run_time = time.time()
                self.cnt = 1
        time.sleep(random.randrange(1, 6, 1))

    def job_retry(self, job):
        retry = job.get("retry")
        #if retry < 5:
        retry += 1
        job.update({"retry": retry})
        self.re_add_job(job)
        #else:
            #self.failure.append(job['name'])


    def get_fail_cnt(self, type_key, addv):
        fc = getattr(self._curltls, type_key, 0)
        if addv:
            fc += addv
            setattr(self._curltls, type_key, fc)
        return fc

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "gsinfo_guangdong finished !"
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

    def read_proxy(self, fn):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                self._match_proxy(line)
        self._can_use_proxy_num = len(self.proxies_dict)
        print " loaded [ %d ] proxis " % self._can_use_proxy_num

    def _match_proxy(self, line):
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
    s = RunGuangdong()
    s.run()
    #s.run_job("")
