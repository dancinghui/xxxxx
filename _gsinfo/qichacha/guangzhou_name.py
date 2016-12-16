#!/usr/bin/env python
# -*- coding:utf8 -*-

import sys
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider, AccountErrors
import re
from spider.savebin import FileSaver, BinSaver
import spider.util
import threading
from lxml import html
filter_name = set()

#深圳:QyxyDetail
#广州:entityShow
#广东其他地区:GSpublicityList

class GuangzhouName(Spider):
    def __init__(self):
        spider.util.use_utf8()
        self.is_debug = True
        if self.is_debug:
            Spider.__init__(self, 1)
        else:
            self.proxies_dict = []
            self.read_proxy("../../_ct_proxy/proxy_all_filter.txt")
            Spider.__init__(self, len(self.proxies_dict))
        self._curltls = threading.local()
        self.success_name = FileSaver("query_success_name.txt")
        self.success_detail = FileSaver("query_success_detail.txt")
        #初始化已经爬过的链接
        self.init_spider_url()
        self.cnt = 1
        self.run_time = time.time()
        self.lock = threading.Lock()


    def init_obj(self):
        threadident = str(threading.currentThread().ident)


    def init_spider_url(self):
        with open("query_success_name.txt", "r") as f:
            i = 0
            for url in f:
                filter_name.add(url.strip())
                i += 1
            print "init already query commpany name finished !", i


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
        with open("../qiyecxb-ct/guangzhou.txt", "r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                if line in filter_name:
                    #print cnt, line, " ---> already queried!!!"
                    continue
                job = {"cnt": cnt, "retry": 0, "kw": line}
                self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)

    def record_spider_url(self, line):
        """
        记录已经爬过的
        """
        filter_name.add(line)
        self.success_name.append(line)
        self.cnt += 1
        setattr(self._curltls, "failcnt", 0)

    def run_job(self, job):
        #tid = self.get_tid()
        key = job["kw"]
        cnt = job["cnt"]
        kw = spider.util.utf8str(key)
        url = "http://qichacha.com/search?key=" + kw + "&sType=0"
        headers = {"Referer": "http://qichacha.com/", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0"}
        res = None
        if self.is_debug:
            res = self.request_url(url, headers=headers, proxies={'http': 'http://ipin:helloipin@192.168.1.45:3428', 'https': 'https://ipin:helloipin@192.168.1.45:3428'}, timeout=10)
        else:
            res = self.request_url(url, headers=headers)
        if res is None:
            self.job_retry(job, 1)
            print kw, "res 为空..."
            return
        if res.code == 200 and res.text is not None:
            if u"请登陆后再查询" in res.text:
                print "请登陆后再查询>..."
                return
            if u"小查还没找到数据" in res.text:
                print kw, "查不到数据..."
                self.record_spider_url(key)
                return
            doc = html.fromstring(res.text)
            lst = doc.xpath("//section[@id='searchlist']")
            all = 0
            for l in lst:
                try:
                    content = l.text_content()
                    arry = content.split("\t")
                    r_arry = []
                    for arr in arry:
                        if arr.strip() == "":
                            continue
                        s = arr.strip().replace("\r", "").replace("\n", "")
                        s_ary = s.split(" ")
                        r_arry.append(s_ary[0].strip())
                    self.success_detail.append(spider.util.utf8str(r_arry))
                    all += 1
                    print cnt, "===>", spider.util.utf8str(r_arry)
                except Exception as e:
                    print cnt, key, "---> 发生异常 --->", e
                    self.job_retry(job, 0)
                    return
            if all != 0 and len(lst) == all:
                self.record_spider_url(key)
        else:
            print kw, "res或text为空 , res.code:", res.code
            self.job_retry(job, 1)


        # if time.time() - self.run_time > 20:
        #     print "speed------> ------> ------> ------> ------> ------>", self.cnt/(time.time() - self.run_time), "t/s"
        #     self.run_time = time.time()
        #     self.cnt = 1


    def job_retry(self, job, addv):
        retry = job.get("retry")
        retry += 1
        job.update({"retry": retry})
        self.re_add_job(job)
        if self.get_fail_cnt("failcnt", addv) > 15:
            if not self.is_debug:
                raise AccountErrors.NoAccountError("Maybe the proxy invalid,failcount-none = [ %d ]" % self.get_fail_cnt("failcnt", 0))


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
    spider.util.use_utf8()
    s = GuangzhouName()
    s.run()
    #s.run_job({"kw": "广州爱拼"})
