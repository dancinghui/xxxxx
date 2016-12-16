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
import gs_guangdong_new
import threading
import random
import os
filter_name = set()
filter_query_name = set()
#深圳:QyxyDetail
#广州:entityShow
#广东其他地区:GSpublicityList

class RunGuangdong(Spider):

    class Saver(object):
        def __init__(self):
            self.bs = BinSaver("gsinfo_Guangdong_html.bin")
            self.pic = BinSaver("gsinfo_Guangdong_pic.bin")
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
            Spider.__init__(self, 100)
            #self.proxies_dict = [{'http': 'http://ipin:helloipin@106.75.134.189:18889', 'https': 'https://ipin:helloipin@106.75.134.189:18889'}]
            self.proxies_dict = [{'http': 'http://192.168.1.39:3428', 'https': 'https://192.168.1.39:3428'}]
        else:
            self.proxies_dict = []
            self.read_proxy("/home/windy/develop/getjd/_ct_proxy/proxy_all_filter.txt")
            Spider.__init__(self, len(self.proxies_dict))
        self._curltls = threading.local()
        self.gswebs = {}
        #已经获取详情成功的关键字
        self.success_name = FileSaver("已经查询过的关键字.txt")
        #已经获取详情成功的查询到的公司名
        self.succes_query_name = FileSaver("已经拿到详情的公司名.txt")
        #页面提示无法显示的公司列表信息out[]
        self.not_show_save = FileSaver("页面提示无法显示的公司列表out.txt")
        #查不到内容的关键字
        self.query_none_kw = FileSaver("查询内容为空的关键字.txt")

        #初始化已经爬过的链接
        self.init_spider_url()
        self.lock = threading.Lock()
        #速度记录
        self.run_time = time.time()
        self.cnt = 1
        self.proxy_error_cnt = 0
        #广州系统555返回被封掉的 out
        #self.query_out = FileSaver("query_out_un_spider2.txt")


    def init_obj(self):
        threadident = str(threading.currentThread().ident)
        gsweb = gs_guangdong_new.SearchGSWebGuangdong(self.saver)
        if self.is_debug:
            gsweb.proxies = self.proxies_dict[0]
        else:
            gsweb.proxies = self.proxies_dict[self.get_tid()]
        self.gswebs[threadident] = gsweb
        setattr(self._curltls, "gsweb", gsweb)
        return gsweb


    def init_spider_url(self):
        with open("已经查询过的关键字.txt", "r") as f:
            i = 0
            for name in f:
                filter_name.add(name.strip().decode("utf-8"))
                i += 1
            print "初始化　已经查询过的关键字.txt 完毕　", i

        with open("查询内容为空的关键字.txt", "r") as f:
            i = 0
            for name in f:
                filter_name.add(name.strip().decode("utf-8"))
                i += 1
            print "初始化　查询内容为空的关键字.txt 完毕　", i

        with open("已经拿到详情的公司名.txt", "r") as f:
            i = 0
            for name in f:
                filter_query_name.add(name.strip().decode("utf-8"))
                i += 1
            print "初始化　已经拿到详情的公司名.txt 完毕　", i




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
        with open("guangdong_tiqu_all_cname.txt", "r") as f:
            cnt = 0
            for qname in f:
                qname = qname.strip()
                cnt += 1
                if qname in filter_name:
                    #print cnt, qname, " ---> already spider!!!"
                    continue
                job = {"cnt": cnt, "retry": 0, "qname": qname, "type": "query"}
                self.add_job(job, True)
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

    def record_spider(self, name):
        """
        记录已经爬过的:写入到已经成功的文本 - 添加到过滤列表
        """
        filter_name.add(name)
        self.success_name.append(name)
        self.cnt += 1
        #setattr(self._curltls, "failcnt", 0)
        with self.lock:
            self.proxy_error_cnt = 0

    def record_spider_query(self, name):

        filter_query_name.add(name)
        self.succes_query_name.append(name)
        self.cnt += 1
        # setattr(self._curltls, "failcnt", 0)
        with self.lock:
            self.proxy_error_cnt = 0

    def run_job(self, jobid):

        tid = self.get_tid()
        gsweb = getattr(self._curltls, "gsweb", None)
        if gsweb is None:
            gsweb = self.init_obj()

        #gsweb.select_user_agent("=Mozilla/5.0 (Windows NT "+str(random.randrange(1, 99, 1))+".0; WOW64; rv:"+str(random.randrange(1, 99, 1))+") AppleWebKit/"+str(random.randrange(100, 999, 1))+"."+str(random.randrange(1, 99, 1))+" (KHTML, like Gecko) Chrome/"+str(random.randrange(1, 99, 1))+".0.2311."+str(random.randrange(100, 999, 1))+" Safari/"+str(random.randrange(100, 999, 1))+"."+str(random.randrange(1, 99, 1)))
        tp = jobid["type"]
        cnt = jobid.get("cnt")

        qname = jobid.get("qname")
        if qname.decode("utf-8") in filter_name or qname.decode("utf-8") in filter_query_name:
            #print cnt, "已经查询过:", qname
            return
        #qname = "广州白云机场"
        out = gsweb.search_company(qname)
        if out is None:
            self.job_retry(jobid, 1)
            return
        else:
            setattr(self._curltls, "failcnt", 0)
        if "PROXY-ERROR" in out or "OPERATION-FAST" in out:
            #self.proxy_error_cnt += 1
            self.error_add()
            self.job_retry(jobid, 1)
            return
        elif "QUERY-NONE" in out:
            self.query_none_kw.append(qname)
            filter_name.add(qname)
            return
        elif len(out) == 0:
            self.job_retry(jobid, 1)
            return
        else:
            print tid, cnt, "get#############:", qname, len(out), "------>", spider.util.utf8str(out)
            scs = 0
            for oi in out:
                cname = oi["name"].strip()
                if cname.decode("utf-8") in filter_query_name or cname.decode("utf-8") in filter_name:
                    #print "qname=", qname, "查到的公司名:", cname, "已经爬过...忽略!!!"
                    scs += 1
                    continue
                if self.get_detail(gsweb, oi, cnt, qname=qname):
                    scs += 1

            if len(out) == scs:
                self.record_spider(qname)


        if time.time() - self.run_time > 20:
            print cnt, "====================== speed =====================", self.cnt/(time.time() - self.run_time), "t/s"
            self.run_time = time.time()
            self.cnt = 1



    def error_add(self):
        pass
        # with self.lock:
        #     self.proxy_error_cnt += 1
        #     print "错误数:", self.proxy_error_cnt
        #     if self.proxy_error_cnt > 80:
        #         self.restart_jb()

    def restart_jb(self):
        if self.proxy_error_cnt < 80:
            return
        self.proxy_error_cnt = 0
        print "=============================重新启动拨号脚本================================="
        result = os.system("sshpass -p 'helloipin' ssh ipin@192.168.2.90 /home/ipin/bin/redial")
        time.sleep(10)
        ip = os.system("sshpass -p 'helloipin' ssh ipin@192.168.2.90 /home/ipin/bin/getip")
        print "=============================重新启动拨号脚本成功=============================="


    def get_detail(self, gsweb, oi, cnt, qname=None):
        #time.sleep(2)
        tid = self.get_tid()
        cname = oi["name"]
        url = oi["url"]
        regist_code = oi["regcode"]
        gd = "gsxt.gdgs.gov.cn/aiccips/GSpublicity/GSpublicityList.html"
        sz = "szcredit.com.cn/web/GSZJGSPT/QyxyDetail.aspx"
        gz1 = "gsxt.gzaic.gov.cn/search/search!entityShow"
        gz2 = "gsxt.gzaic.gov.cn/aiccips/GSpublicity/GSpublicityList.html"
        flg = None
        if gd in url:
            #return True
            flg = gsweb.get_GSpublicityList(cnt, cname, url, regist_code, qname=qname)
        elif sz in url:
            #return True
            flg = gsweb.get_QyxyDetail(cnt, cname, url, regist_code, tid=tid)
        elif gz1 in url:
            #return True
            flg = gsweb.get_entityShow(cnt, cname, url, regist_code)
            # 此链接跑完需重新初始化对象
            self.init_obj()
        elif gz2 in url:
            flg = gsweb.get_guangzhou(cnt, cname, url, regist_code, qname=qname)
        else:
            print "未知的链接类型--->", url
            Log.error("UNKNOWN LINK TYPE," + url)
            return True #未知链接类型 暂时跳过 算成功

        if flg == "success":
            self.record_spider_query(cname.strip())
            return True
        elif flg == "proxy_error":
            self.error_add()
            time.sleep(5)
            return self.get_detail(gsweb, oi, cnt, qname=qname)
        elif flg == "notdisplay":
            oi["error"] = "notdisplay"
            self.not_show_save.append(spider.util.utf8str(oi))
            return True
        elif flg == "return_error":
            oi["error"] = "return_page_error"
            self.not_show_save.append(spider.util.utf8str(oi))
            return True
        elif flg == "page_error":
            time.sleep(10)
            return self.get_detail(gsweb, oi, cnt, qname=qname)
        elif flg == "521":
            gsweb = self.init_obj()
            return self.get_detail(gsweb, oi, cnt, qname=qname)
        else:
            return False

    def job_retry(self, job, addv):
        retry = job.get("retry")
        retry += 1
        job.update({"retry": retry})
        self.re_add_job(job)
        # if self.get_fail_cnt("failcnt", addv) > 15:
        #     if not self.is_debug:
        #         raise AccountErrors.NoAccountError("Maybe the proxy invalid,failcount-none = [ %d ]" % self.get_fail_cnt("failcnt", 0))


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
    #s.run_job({"type": "query", "cnt": 1, "qname": "111"})
