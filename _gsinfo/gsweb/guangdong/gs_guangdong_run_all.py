#!/usr/bin/env python
# -*- coding:utf8 -*-

import sys
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider, AccountErrors
from spider.runtime import Log
import re
from spider.savebin import FileSaver, BinSaver
import spider.util
import gs_guangdong
import threading
filter_name = set()
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
        self.is_debug = True
        if self.is_debug:
            Spider.__init__(self, 1)
            self.proxies_dict = [{'http': 'http://ipin:helloipin@106.75.134.190:18889', 'https': 'https://ipin:helloipin@106.75.134.190:18889'}]
        else:
            self.proxies_dict = []
            self.read_proxy("../../_ct_proxy/proxy_041309.txt")
            Spider.__init__(self, len(self.proxies_dict))
        self._curltls = threading.local()
        self.gswebs = {}
        #已经获取详情成功的公司名
        self.success_name = FileSaver("guangdong_success_spider_cname.txt")
        #根据关键字查到的公司名再写入到这里面,防止丢失
        self.un_spider_name = FileSaver("guangdong_temp_un_spider_cname.txt")
        #页面提示无法显示的公司列表信息out[]
        self.not_show_save = FileSaver("guangdong_not_show_out.txt")

        #初始化已经爬过的链接
        self.init_spider_url()
        self.lock = threading.Lock()
        #速度记录
        self.run_time = time.time()
        self.cnt = 1


    def init_obj(self):
        threadident = str(threading.currentThread().ident)
        gsweb = gs_guangdong.SearchGSWebGuangdong(self.saver)
        if self.is_debug:
            gsweb.proxies = {}#self.proxies_dict[0]
        else:
            gsweb.proxies = self.proxies_dict[self.get_tid()]
        self.gswebs[threadident] = gsweb
        setattr(self._curltls, "gsweb", gsweb)
        return gsweb


    def init_spider_url(self):
        with open("guangdong_success_spider_cname.txt", "r") as f:
            i = 0
            for name in f:
                filter_name.add(name.strip())
                i += 1
            print "init success spidered commpany name finished !", i


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
        with open("guangdong_un_spider_cname.txt", "r") as f:
            cnt = 0
            for qname in f:
                qname = qname.strip()
                cnt += 1
                if qname in filter_name:
                    #print cnt, " ---> already spider!!!"
                    continue
                job = {"cnt": cnt, "retry": 0, "qname": qname, "type": "query"}
                self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)

    def select_run(self, line):
        tag = [
                "gsxt.gdgs.gov.cn/aiccips/GSpublicity/GSpublicityList.html",
                # 广东 -- 系统无法显示 封IP -- 可能是没有数据
                #"szcredit.com.cn/web/GSZJGSPT/QyxyDetail.aspx"
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

    def record_spider(self, name):
        """
        记录已经爬过的
        """
        filter_name.add(name)
        self.success_name.append(name)
        self.cnt += 1
        setattr(self._curltls, "failcnt", 0)

    def run_job(self, jobid):
        tid = self.get_tid()
        gsweb = getattr(self._curltls, "gsweb", None)
        if gsweb is None:
            gsweb = self.init_obj()

        tp = jobid["type"]
        cnt = jobid.get("cnt")
        if tp == "query":
            qname = jobid.get("qname")
            if qname in filter_name:
                print cnt, "已经查询过:", qname
                return
            out = gsweb.search_company(qname)
            if out is None:
                self.job_retry(jobid, 1)
                return
            else:
                setattr(self._curltls, "failcnt", 0)
            if "PROXY-ERROR" in out:
                raise AccountErrors.NoAccountError("Maybe the proxy invalid - PROXY-ERROR ")
            elif len(out) == 0:
                print cnt, qname, ' 查询公司列表为空...'
                self.record_spider(qname)
                return
            else:
                for oi in out:
                    cname = oi["name"]
                    if cname in filter_name:
                        print cnt, "已经爬取过:", cname
                        return
                    job = {"oi": oi, "type": "detail", "cnt": cnt, "retry": 0}
                    self.add_main_job(job)
                    self.un_spider_name.append(cname)
                self.record_spider(qname)

        elif tp == "detail":
            oi = jobid["oi"]
            cname = oi["name"]
            url = oi["url"]
            regist_code = oi["regcode"]
            gd = "gsxt.gdgs.gov.cn/aiccips/GSpublicity/GSpublicityList.html"
            sz = "szcredit.com.cn/web/GSZJGSPT/QyxyDetail.aspx"
            gz1 = "gsxt.gzaic.gov.cn/search/search!entityShow"
            gz2 = "gsxt.gzaic.gov.cn/aiccips/GSpublicity/GSpublicityList.html"
            flg = None
            if gd in url:
                flg = gsweb.get_GSpublicityList(cnt, cname, url, regist_code)
            elif sz in url:
                flg = gsweb.get_QyxyDetail(cnt, cname, url, regist_code, tid=tid)
            elif gz1 in url:
                flg = gsweb.get_entityShow(cnt, cname, url, regist_code)
                #此链接跑完需重新初始化对象
                self.init_obj()
            elif gz2 in url:
                flg = gsweb.get_guangzhou(cnt, cname, url, regist_code)
            else:
                print "未知的链接类型--->", url
                Log.error("UNKNOWN LINK TYPE,"+url)
                return

            if flg == "success":
                self.record_spider(cname)
            elif flg == "proxy_error":
                self.job_retry(jobid, 1)
            elif flg == "notdisplay":
                oi["error"] = "notdisplay"
                self.not_show_save.append(spider.util.utf8str(oi))
                #self.job_retry(jobid, 0)
            elif flg == "return_error":
                oi["error"] = "return_page_error"
                self.not_show_save.append(spider.util.utf8str(oi))
                #self.job_retry(jobid, 0)
            else:
                self.job_retry(jobid, 0)


        if time.time() - self.run_time > 20:
            print cnt, "====================== speed =====================", self.cnt/(time.time() - self.run_time), "t/s"
            self.run_time = time.time()
            self.cnt = 1


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
    s = RunGuangdong()
    s.run()
    #s.run_job("")
