#!/usr/bin/env python
# -*- coding:utf8 -*-

import sys
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider, AccountErrors
import re
from spider.savebin import FileSaver,BinSaver
import spider.util
import gs_beijing
import threading
import random
filter_url = set()
filter_queries = set()
class RunBeijing(Spider):

    class Saver(object):
        def __init__(self):
            self.bs = BinSaver("gsinfo_Beijing_html.bin")
            self.fs = FileSaver("gsinfo_beijing.txt")
    """
    工商网站--北京
    """
    def __init__(self):
        spider.util.use_utf8()
        self.saver = RunBeijing.Saver()
        self.is_debug = True
        if self.is_debug:
            Spider.__init__(self, 1)
            self.gsweb = gs_beijing.SearchGSWebBeijing(self.saver)
        else:
            self.proxies_dict = []
            self.read_proxy("../../../_ct_proxy/proxy_all_filter.txt")
            Spider.__init__(self, len(self.proxies_dict))
            self._curltls = threading.local()
        self.gswebs = {}
        #已经访问成功的URL
        self.success_kw = FileSaver("gsinfo_beijing_success_kw.txt")
        #对于查到的列表信息,爬取成功就写入到这个文本,防止重复爬取
        self.success_queries = FileSaver("gsinfo_beijing_success_queries.txt")
        #初始化已经爬过的链接
        self.init_spider_url()
        #time.sleep(2)
        self.cnt = 0
        self.run_time = time.time()
        self.cnt_q = 0
        self.new_object_time = time.time()


    def init_obj(self):
        threadident = str(threading.currentThread().ident)
        gsweb = gs_beijing.SearchGSWebBeijing(self.saver)
        if not self.is_debug:
            gsweb.proxies = self.proxies_dict[self.get_tid()]
        self.gswebs[threadident] = gsweb
        setattr(self._curltls, "gsweb", gsweb)
        return gsweb

    def init_spider_url(self):
        with open("gsinfo_beijing_success_kw.txt", "r") as f:
            for url in f:
                filter_url.add(url.strip())
            print "init already spidered commpany url finished !"

        with open("gsinfo_beijing_success_queries.txt", "r") as f:
            for name in f:
                filter_queries.add(name.strip().decode("utf-8"))
            print "init already spidered commpany queries finished !"

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
        with open("/home/windy/develop/getjd/_gsinfo/gsweb/beijing/beijing_cname_backhalf.txt", "r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                if line in filter_url:
                    print cnt, line, " --->kw already spider!!!"
                    continue
                job = {"cnt": cnt, "retry": 0, "kw": line}
                self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)

    def record_spider_kw(self, kw):
        """
        记录已经爬过的关键字
        """
        filter_url.add(kw)
        self.success_kw.append(kw)
        self.cnt += 1
        #setattr(self._curltls, "failcnt", 0)

    def record_spider_queries(self, line):
        """记录已经爬取成功的查询列表某一条"""
        filter_queries.add(line)
        self.success_queries.append(line)
        self.cnt_q += 1
        setattr(self._curltls, "failcnt", 0)

    def run_job(self, job):
        gsweb = getattr(self._curltls, "gsweb", None)
        if time.time() - self.new_object_time > 120:
            #每隔2分钟重新初始化一次对象
            gsweb = self.init_obj()
        else:
            if gsweb is None:
                gsweb = self.init_obj()

        gsweb.select_user_agent(
            "=Mozilla/5.0 (Windows NT " + str(random.randrange(1, 99, 1)) + ".0; WOW64) AppleWebKit/" + str(
                random.randrange(100, 999, 1)) + "." + str(
                random.randrange(1, 99, 1)) + " (KHTML, like Gecko) Chrome/" + str(
                random.randrange(1, 99, 1)) + ".0.2311." + str(random.randrange(100, 999, 1)) + " Safari/" + str(
                random.randrange(100, 999, 1)) + "." + str(random.randrange(1, 99, 1)) + " LBBROWSER")

        kw = job.get("kw")
        #kw = "腾讯科技（北京）有限公司"
        retry = job.get("retry")
        cnt = job.get("cnt")
        out = gsweb.search_company(kw)
        if out is None:
            self.job_retry(job)
            return
        if len(out) != 0 and out[0] == "stop":
            self.job_retry(job)
            return
            #raise AccountErrors.NoAccountError("The proxy invalid , IP stop !!!")
        all = len(out)
        scs_cnt = 0
        for oi in out:
            cname = oi["name"]
            url = oi["url"]
            regcode = oi["regcode"]
            entid = oi["entid"]
            s = cname+","+str(regcode)
            if s in filter_queries:
                #如果已经爬取过了,略过
                all -= 1
                continue
            retry2 = 0
            while True:
                flag = gsweb.get_detail(entid, cname, regcode, url)
                if flag:
                    self.record_spider_queries(s)
                    time.sleep(random.randrange(1, 5, 1))
                    scs_cnt += 1
                    break
                else:
                    retry2 += 1
                    if retry2 > 5:
                        break

        if scs_cnt == all:
            self.record_spider_kw(kw)
        else:
            self.job_retry(job)

        if time.time() - self.run_time > 20:
            print "query speed------> ------> ------> ------> ------> ------>", self.cnt/(time.time() - self.run_time), "t/s"
            print "detail speed------> ------> ------> ------> ------> ------>", self.cnt_q / (time.time() - self.run_time), "t/s"
            self.run_time = time.time()
            self.cnt = 0
            self.cnt_q = 0

    def job_retry(self, job):
        retry = job.get("retry")
        cnt = job.get("cnt")
        kw = job.get("kw")
        retry += 1
        print "第%d行 - 关键字:%s 将要重试第%d次 ... "%(cnt, kw, retry)
        job.update({"retry": retry})
        self.re_add_job(job)
        # if self.get_fail_cnt("failcnt", 1) > 10:
        #     time.sleep(60*60)
            #raise AccountErrors.NoAccountError("Maybe the proxy invalid,failcount-none = [ %d ]" % self.get_fail_cnt("failcnt", 0))


    def get_fail_cnt(self, type_key, addv):
        fc = getattr(self._curltls, type_key, 0)
        if addv:
            fc += addv
            setattr(self._curltls, type_key, fc)
        return fc

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "gsinfo_beijing finished !"
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
    s = RunBeijing()
    s.run()
    #s.run_job("")
