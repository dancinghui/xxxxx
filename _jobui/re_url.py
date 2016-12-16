#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
#os.environ['PAGESTORE_DB'] = "mongodb://crawler:crawler@192.168.1.81,192.168.1.82,192.168.1.83/gaokao_crawler"
os.environ['PAGESTORE_DB'] = "mongodb://192.168.1.43:27019/jobui"
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider, AccountErrors
import re
import spider.util
import random
from spider.savebin import FileSaver
from page_store import PageStoreJobUI

already_url = set()

class JobuiSpider(Spider):
    """
    jobui数据重爬--爬取直接入库  2016-04-27
    """
    def __init__(self):
        self.is_debug = True
        if self.is_debug:
            Spider.__init__(self, 1)
        else:
            self.proxies_dict = []
            self.read_proxy("../spider/proxy/proxy.txt")
            Spider.__init__(self, len(self.proxies_dict))
        self.success_count = 0
        self.request_count = 0
        self.__fail_ids = FileSaver("fail_url.txt")
        self.start_time = time.time()
        self.page_store = PageStoreJobUI()
        self.page_store.testmode = True
        self.init_time = time.time()
        self.already_url = FileSaver("already_url.txt")
        self.init_already_url()

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

    def init_already_url(self):
        i = 0
        with open("already_url.txt") as f:
            for line in f:
                i += 1
                url = line.strip()
                already_url.add(url)
        print "init already url :", i

    def dispatch(self):
        cnt = 0
        with open("db_export_jobui_url.csv") as f:
            for line in f:
                cnt += 1
                url = line.strip()
                if url in already_url:
                    print "already crawler......ignore..."
                    continue
                m = re.search("http://www\.jobui\.com/job/(\d+)/", url)
                if m:
                    id = int(m.group(1))
                    job = {"cnt": cnt, "id": id, "url": url, "retry": 0}
                    self.add_job(job, True)
                else:
                    print "url error:", line
                    continue
        self.wait_q_breakable()
        self.add_job(None, True)

    def get_fail_cnt(self, addv, type):
        fc = getattr(self._curltls, type, 0)
        if (addv):
            fc += addv
            setattr(self._curltls, type, fc)
        return fc

    def run_job(self, job):
        url = job.get("url")
        id = job.get("id")
        cnt = job.get("cnt")
        retry = job.get("retry")
        tid = self.get_tid()
        proxies = None
        if self.is_debug:
            proxies = {'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'}
        else:
            proxies = self.proxies_dict[tid]
        res = self.request_url(url, proxies=proxies)

        self.request_count += 1

        if res is None or res.code != 200:
            #print "%d --- %d ---> error:", "RES NONE " if res is None else "res.code = %d" % res.code
            self.re_add_job({"id": id, "cnt": cnt, "url": url, "retry": (retry + 1)})
        else:
            if self.page_store.save(int(time.time()), str(id), url, res.text):
                self.success_count += 1
                already_url.add(url)
                self.already_url.append(url)
                print "%d ### %d ###  be into database success......." % (cnt, id)
            else:
                print "%d === %d ===  be into database failure......." % (cnt, id)
                self.re_add_job({"id": id, "cnt": cnt, "url": url, "retry": (retry + 1)})

        if time.time() - self.init_time > 20:
            print "request_count:{},success_count:{},request_speed:{}".format(self.request_count, self.success_count, self.request_count/(time.time()-self.start_time))
            self.init_time = time.time()
            self.request_count = 0
            self.success_count = 0

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "jobui re_url.py is over !"
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

    def read_proxy(self, fn):
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
