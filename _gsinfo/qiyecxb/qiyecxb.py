#! /usr/bin/env python
# encoding:utf-8
import re

from spider.spider import Spider, SessionRequests
from spider.savebin import BinSaver
from spider import spider, util
from spider.runtime import Log
import threading
import os
import time
import json
from urllib import quote


class QycxbReq(SessionRequests):
    def __init__(self):
        SessionRequests.__init__(self)
        self._proxy_use_times = {}
        self.proxy_limit = 20
        self.curproxy = ""

    def load_proxy(self, fn, index=-1, auto_change=True):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                line = re.sub('\s*#.*', '', line)
                if line == '':
                    break
                self._proxy_use_times[line] = 0
                self.sp_proxies[line] = 0
        self._cur_proxy_index = index
        self._auto_change_proxy = auto_change
        print "==== %d proxies loaded ====" % len(self.sp_proxies.keys())

    def request_url(self, url, **kwargs):
        if len(self.sp_proxies.keys())!=0 and self._cur_proxy_index != -1:
            if self._proxy_use_times[self.curproxy] < self.proxy_limit:
                self._proxy_use_times[self.curproxy] += 1
            else:
                self.remove_curproxy()
        try:
            ret = super(SessionRequests, self).request_url(url, **kwargs)
            return ret
        except RuntimeError as e:
            if "no proxy" in e.message:
                Log.error("No proxy...Exit.")
                exit()

    def remove_curproxy(self):
        with self.locker:
            self._proxy_use_times[self.curproxy] = self.proxy_limit + 1

    def _replace_proxy(self, kwargs, memo):
        with self.locker:
            if not isinstance(self.sp_proxies, dict) or len(self.sp_proxies.keys()) == 0:
                return False
            if self._auto_change_proxy:
                oldproxy = memo.get('proxy')
                if oldproxy in self.sp_proxies:
                    self.sp_proxies[oldproxy] += 1
                prs = self.sp_proxies.keys()
                prs.sort()
                for i in range(0, len(prs)):
                    self._cur_proxy_index = (self._cur_proxy_index + 1) % len(prs)
                    selproxy = prs[self._cur_proxy_index]
                    if self.sp_proxies.get(selproxy, 0) <= 10 and self._proxy_use_times.get(selproxy,
                                                                                            0) <= self.proxy_limit:
                        memo['proxy'] = selproxy
                        self._set_proxy(kwargs, selproxy)
                        self.curproxy = selproxy
                        return True
                    elif self._proxy_use_times.get(selproxy,0) > self.proxy_limit:
                        Log.error("This proxy has run too many times.==>"+ self.curproxy)
                    else:
                        Log.error("This proxy has made too many errors.==>" + self.curproxy)
            elif self._cur_proxy_index < 0:
                # don't auto change proxy, and the index < 0, no proxy is used.
                # but don't report an error.
                return True
            else:
                prs = self.sp_proxies.keys()
                prs.sort()
                selproxy = prs[self._cur_proxy_index % len(prs)]
                self._set_proxy(kwargs, selproxy)
                return True
        return False


class QycxbSpider(Spider):
    def __init__(self, threadcnt):
        Spider.__init__(self, threadcnt)
        self.sqs = {}
        self.binsaver = BinSaver("Qycxb" + str(time.time()).split(".")[0] + ".bin")

    def init_req(self):
        with self.locker:
            threadident = str(threading.currentThread().ident)
            sq = QycxbReq()
            # sq.load_proxy("../../_zhilian/curproxy0")
            # sq.load_proxy("../_zhilian/curproxy")
            # sq.select_user_agent("firefox")
            sq.default_headers = {"Connection": "keep-alive",
                                  "Accept": r"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                                  "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                                  "Accept-Encoding": "gzip, deflate",
                                  "Referer":"http://qiye.qianzhan.com/",
                                  "X-Requested-With":"XMLHttpRequest",
                                  "User-Agent": r"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0",
                                  "Pragma":"no-cache",
                                  "Cache-Control":"no-cache",
                                  "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8"}
            # con = sq.request_url("http://qiye.qianzhan.com/")
            con1 = sq.request_url(r"http://qiye.qianzhan.com/orgcompany/searchList",
                                  data=r"oc_name=%E5%B9%BF%E5%B7%9E%E5%B8%82%E5%8D%97%E6%B2%99%E5%8D%8E%E5%B7%A5%E7%A0%94%E7%A9%B6%E9%99%A2&oc_area=&sh_searchType=1&od_orderby=0&page=1&pageSize=10")
            self.sqs[threadident] = sq
            setattr(self._curltls, "sq", sq)
            return sq

    def dispatch(self):
        f = open("/home/peiyuan/r1.txt", "rb")
        currline = 0
        skip = 0
        endline = 1000
        while currline < skip:
            line = f.readline()
            currline += 1

        while currline < endline:
            line = f.readline()
            key = line.strip().split(" ")[-1].strip()
            job = {"key": key, "type": "u1", "lineno": currline}
            self.add_main_job(job)
            currline += 1
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, job):
        time.sleep(5)
        threadident = str(threading.currentThread().ident)
        sq = getattr(self._curltls, "sq",None)
        if sq is None:
            sq = self.init_req()
        Log.info("Running job:" + util.utf8str(job.__str__()))
        if job["type"] == "u1":
            Log.info("Searching line %d" % job["lineno"])
            con = sq.request_url(r"http://qiye.qianzhan.com/orgcompany/searchList",
                                 data={"oc_name": job["key"], "od_orderby": 0, "page": 1,
                                       "pageSize": 10, "oc_area": "",
                                       "sh_searchType": 1})
            if con is None or con.text.strip() == "" or con.code != 200:
                Log.error("[u1]Bad connect or empty content return.. JOB=>" + util.utf8str(job.__str__()))
                self.re_add_job(job)
                return
            else:
                jsonobj = ""
                try:
                    jsonobj = json.loads(con.text.strip())
                except ValueError as e:
                    Log.error("Json decode error. String is %s" % con.text)
                    return
                if not jsonobj["succ"]:
                    Log.warning(jsonobj.__str__())
                    time.sleep(1)
                    Log.error("[u1]Request fail, succ flag is False. JOB=>" + util.utf8str(job.__str__()))
                    if 'status' in jsonobj and jsonobj['status'] == '4':
                        Log.error("Remove current proxy...Used %d times....." % sq._proxy_use_times[sq.curproxy])
                        sq.remove_curproxy()
                    self.re_add_job(job)
                else:
                    corplist = jsonobj["lst"]
                    if len(corplist) == 0:
                        Log.error("Search return nothing. %d:%s, no data." % (job["lineno"], job["key"]))
                        return
                    else:
                        for corp in corplist:
                            jobb = {"type": "u2", "orgCode": corp["oc_orgCode"], "name": corp["oc_name"]}
                            self.add_job(jobb)

        if job["type"] == "u2":
            Log.info("Getting detail info about %s" % job["name"])
            timestr = "%f" % time.time()
            con0 = sq.request_url(r"http://qiye.qianzhan.com/orgcompany/GetJsVerfyCode?t=0.%s&_=%s" % (
                timestr.split(".")[1], timestr.split(".")[0]))
            if con0 is None or con0.text.strip() == "" or con0.code != 200:
                Log.error("[u2]Bad connect or empty content return.. JOB=>" + util.utf8str(job.__str__()))
                self.re_add_job(job)
                return
            if not os.path.exists(threadident):
                os.mkdir(threadident)
            f = open(threadident + "/qycxb.js", "w+b")
            f.write(r'var window = {document : {cookie :"qznewsite.uid=' + sq.get_cookie(
                    "qznewsite.uid").strip() +'"}};  ' + con0.text + "console.log(window.__qzmcf())")
            f.flush()
            os.system("nodejs " + threadident + "/qycxb.js > " + threadident + "/mcfcode.txt")
            mcfcode = open(threadident + "/mcfcode.txt", "rb").read().strip()
            con1 = sq.request_url("http://qiye.qianzhan.com/orgcompany/SearchItemDtl",
                                  data={"mcfCode": mcfcode, "orgCode": job["orgCode"]})
            if con1 is None or con1.text.strip() == "" or con1.code != 200:
                Log.error("[u2]Bad connect or empty content return.. JOB=>" + util.utf8str(job.__str__()))
                self.re_add_job(job)
                return
            else:
                jsonobj = json.loads(con1.text.strip())
                if not jsonobj["succ"]:
                    Log.warning(jsonobj.__str__())
                    time.sleep(1)
                    Log.error(
                            "[u2]Request fail, succ flag is False.Check the orgcode and mcfcode. JOB=>" + util.utf8str(
                                    job.__str__()))
                    if 'status' in jsonobj and jsonobj['status'] == '4':
                        Log.error("Remove current proxy...Used %d times....." % sq._proxy_use_times[sq.curproxy])
                        sq.remove_curproxy()
                    self.re_add_job(job)
                else:
                    self.binsaver.append(job["name"] + job["orgCode"], con1.text.strip())
                    Log.info("%s,%s,saved." % (job["name"], job["orgCode"]))
                    return


if __name__ == "__main__":
    spider.util.use_utf8()
    # sq = SessionRequests()
    qxbspider = QycxbSpider(1)
    qxbspider.run()
    # for i in range(10):
    #     con = sq.request_url(r"http://qiye.qianzhan.com/orgcompany/searchList",
    #                          data={"oc_name": "广州市南沙华工研究院", "od_orderby": 0, "page": 1, "pageSize": 10, "oc_area": "",
    #                                "sh_searchType": 1})
    #     print con.text.strip()
    #     jsonobj = json.loads(con.text.strip())
        # print jsonobj["succ"] is True
        # timestr = "%f"%time.time()
        # con0 = sq.request_url(r"http://qiye.qianzhan.com/orgcompany/GetJsVerfyCode?t=0.%s&_=%s"%(timestr.split(".")[1], timestr.split(".")[0]))
        # f = open("qycxb.js", "w+b")
        # f.write(r'var window = {document : {cookie : "qznewsite.uid=' + sq.get_cookie(
        #     "qznewsite.uid") + r'"},};' + con0.text + "console.log(window.__qzmcf())")
        # f.flush()
        # os.system("nodejs qycxb.js > mcfcode.txt")
        # mcfcode = open("mcfcode.txt", "rb").read().strip()
        # con1 = sq.request_url("http://qiye.qianzhan.com/orgcompany/SearchItemDtl",
        #                       data={"mcfCode": mcfcode, "orgCode": "zzmZStBCzH0H2x6hJU0ekA=="})
        # print con1.text
