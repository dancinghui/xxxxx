#!/usr/bin/env python
# -*- coding:utf8 -*-

import sys
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider
import re
from spider.savebin import FileSaver, BinSaver
import spider.util
import gs_guangdong
import threading
filter_url = set()

#深圳:QyxyDetail
#广州:entityShow
#广东其他地区:GSpublicityList

class RunGuangdong(Spider):

    class Saver(object):
        def __init__(self):
            self.bs = BinSaver("gsinfo_Guangdong_html.bin")
            self.fs_QyxyDetail = FileSaver("gsinfo_guangdong_QyxyDetail.txt")
            self.fs_GSpublicityList = FileSaver("gsinfo_guangdong_GSpublicityList.txt")
            self.fs_entityShow = FileSaver("gsinfo_guangdong_entityShow.txt")
            self.fs_guangzhou = FileSaver("gsinfo_guangdong_guangzhou.txt")
    """
    工商网站--广东
    """
    def __init__(self):
        spider.util.use_utf8()
        self.saver = RunGuangdong.Saver()
        self.is_debug = False
        if self.is_debug:
            Spider.__init__(self, 1)
            self.proxies_dict = [{'http': 'http://ipin:helloipin@106.75.134.189:18889', 'https': 'https://ipin:helloipin@106.75.134.189:18889'}]
        else:
            Spider.__init__(self, 30)
            self.proxies_dict = []
            self.get_proxy_from_api()
        self._curltls = threading.local()  #
        self.gswebs = {}
        #已经访问成功的URL
        self.success_url = FileSaver("gsinfo_guangdong_success_url.txt")
        #初始化已经爬过的链接
        self.init_spider_url()
        self.cnt = 1
        self.run_time = time.time()
        self.lock = threading.Lock()

        self.not_show_save = FileSaver("not_show_error_out.txt")


    def init_obj(self):
        threadident = str(threading.currentThread().ident)
        gsweb = gs_guangdong.SearchGSWebGuangdong(self.saver)
        if self.is_debug:
            gsweb.proxies = self.proxies_dict[0]
        else:
            gsweb.proxies = self.select_proxy()
        self.gswebs[threadident] = gsweb
        setattr(self._curltls, "gsweb", gsweb)
        return gsweb

    def select_proxy(self):
        """获取proxy"""
        with self.lock:
            if len(self.proxies_dict) > 0:
                proxy = self.proxies_dict[0]
                self.proxies_dict.remove(proxy)
                print "------------------------------------ 切换代理:", proxy, "现有数量:", len(self.proxies_dict)
                return proxy
            else:
                self.get_proxy_from_api()
                proxy = self.proxies_dict[0]
                self.proxies_dict.remove(proxy)
                print "------------------------------------ 切换代理:", proxy, "现有数量:", len(self.proxies_dict)
                return proxy

    def get_proxy_from_api(self):
        url = "http://dev.kuaidaili.com/api/getproxy/?orderid=925817981728018&num=600&b_pcchrome=1&b_pcie=1&b_pcff=1&b_iphone=1&protocol=1&method=2&an_an=1&an_ha=1&sp1=1&quality=1&sort=2&format=json&sep=1"
        res = self.request_url(url)
        if res.code == 200:
            jsn = eval(res.text)
            proxy_list = jsn["data"]["proxy_list"]
            for p in proxy_list:
                self._match_proxy(p)
            print "======================================== 新获取代理完毕,代理个数:", len(proxy_list)

    def init_spider_url(self):
        with open("gsinfo_guangdong_success_url.txt", "r") as f:
            i = 0
            for url in f:
                filter_url.add(url.strip())
                i += 1
            print "init already spidered commpany url finished !", i

        with open("not_show_error_out.txt", "r") as f:
            i = 0
            for line in f:
                oi = eval(line)
                if "error" in oi:
                    del oi["error"]
                filter_url.add(spider.util.utf8str(oi))
                i += 1
            print "init already not_show_error_out finished !", i

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
        with open("gsinfo_out.txt","r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                if line in filter_url:
                    #print cnt, " ---> already spider!!!"
                    continue
                if not self.select_run(line): continue
                job = {"cnt": cnt, "retry": 0, "line": line}
                self.add_job(job, True)
                time.sleep(0.02)
        self.wait_q_breakable()
        self.add_job(None, True)

    def select_run(self, line):
        tag = [
                "gsxt.gdgs.gov.cn/aiccips/GSpublicity/GSpublicityList.html",
                # 广东 -- 系统无法显示 封IP -- 可能是没有数据
                "szcredit.com.cn/web/GSZJGSPT/QyxyDetail.aspx",
                #深圳  -- 请稍后再查  -- 封IP + UA  -- 一般有数据
                #"gsxt.gzaic.gov.cn/search/search!entityShow"
                "gsxt.gzaic.gov.cn/aiccips/GSpublicity/GSpublicityList.html"
                 #广州 -- 封IP + UA  --系统无法显示 -- 可能是没有数据
                ]
        oi = eval(line)
        url = oi["url"]
        for t in tag:
            if t in url:
                return True
        return False

    def record_spider_url(self, line):
        """
        记录已经爬过的
        """
        filter_url.add(line)
        self.success_url.append(line)
        self.cnt += 1
        setattr(self._curltls, "failcnt", 0)

    def run_job(self, jobid):
        tid = self.get_tid()
        gsweb = getattr(self._curltls, "gsweb", None)
        if gsweb is None:
            gsweb = self.init_obj()

        line = jobid.get("line")
        retry = jobid.get("retry")
        cnt = jobid.get("cnt")
        oi = {}
        try:
            oi = eval(line)
        except Exception as e:
            print e, "run_job eval exception,line=", line
            return
        cname = oi["name"]
        url = oi["url"]
        #url = "http://gsxt.gzaic.gov.cn/aiccips/GSpublicity/GSpublicityList.html?service=entInfo_v0aMi7tSLsoEDkCy7V3bR0OgZSlziwda/oQqfoB0GjE=-50aS1uze1DaXd8Gk5PFw0A=="
        regist_code = oi["regcode"]
        t1 = "gsxt.gdgs.gov.cn/aiccips/GSpublicity/GSpublicityList.html"
        t2 = "szcredit.com.cn/web/GSZJGSPT/QyxyDetail.aspx"
        t3 = "gsxt.gzaic.gov.cn/search/search!entityShow"
        t4 = "gsxt.gzaic.gov.cn/aiccips/GSpublicity/GSpublicityList.html"
        flg = ""
        if t1 in url:
            flg = gsweb.get_GSpublicityList(cnt, cname, url, regist_code)
        elif t2 in url:
            flg = gsweb.get_QyxyDetail(cnt, cname, url, regist_code, tid=tid)
        elif t3 in url:
            flg = gsweb.get_entityShow(cnt, cname, url, regist_code)
            #此链接跑完需重新初始化对象
            self.init_obj()
        elif t4 in url:
            flg = gsweb.get_guangzhou(cnt, cname, url, regist_code)
        else:
            print "unknown url type ---> ", url

        if flg == "success":
            self.record_spider_url(spider.util.utf8str(oi))
        elif flg == "proxy_error":
            self.job_retry(jobid, gsweb, 1)
        elif flg == "notdisplay":
            oi["error"] = "notdisplay"
            self.not_show_save.append(spider.util.utf8str(oi))
        elif flg == "return_error":
            oi["error"] = "return_page_error"
            self.not_show_save.append(spider.util.utf8str(oi))
        elif flg == "":
            pass
        else:
            self.job_retry(jobid, gsweb, 0)


        if time.time() - self.run_time > 20:
            print cnt, "speed------> ------> ------> ------> ------> ------>", self.cnt/(time.time() - self.run_time), "t/s"
            self.run_time = time.time()
            self.cnt = 1


    def job_retry(self, job, gsweb, addv):
        retry = job.get("retry")
        retry += 1
        job.update({"retry": retry})
        self.re_add_job(job)
        if self.get_fail_cnt("failcnt", addv) > 5:
            if not self.is_debug:
                gsweb.proxies = self.select_proxy()
                setattr(self._curltls, "gsweb", gsweb)
            #raise AccountErrors.NoAccountError("Maybe the proxy invalid,failcount-none = [ %d ]" % self.get_fail_cnt("failcnt", 0))


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
    s = RunGuangdong()
    s.run()
    #s.run_job("")
