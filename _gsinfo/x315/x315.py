#! /usr/bin/env python
# encoding:utf-8
from spider.spider import Spider
from spider.httpreq import SessionRequests
from spider.runtime import Log
import spider.util
import urllib
import re
import os
import time
from spider.util import utf8str


class X315Spider(Spider):
    def init_req(self):
        self.sesnreq.load_proxy("../gongshangju/proxy_all.txt")
        self.sesnreq.select_user_agent("firefox")
        self.sesnreq.request_url("http://www.x315.com/index")
        con = self.sesnreq.request_url("http://s4.cnzz.com/stat.php?id=1256666136&show=pic1")
        jsessionid = con.cookies[0].split("\t")[-1]
        jsscript = "var document={};var window = {};"+con.text+"console.log(document.cookie);"
        f = open("login.js","w+b")
        f.write(jsscript)
        f.close()
        os.system("nodejs login.js>cookie.txt")
        f = open("cookie.txt", "r+b")
        cookiestr = f.read()
        self.cookiestr = urllib.unquote(re.search("(CNZZDATA.*?;)", cookiestr).group(1)+"JSESSIONID="+jsessionid+";")
        print self.cookiestr

    def __init__(self, threadcnt):
        Spider.__init__(self,threadcnt)
        self.sesnreq = SessionRequests()
        self.sesnreq.load_proxy("../gongshangju/proxy1.txt", 0 ,False)
        self.sesnreq.select_user_agent("firefox")
        # self.init_req()



    def dispatch(self):
        currline = 0
        skipto = 0
        endline = 100000
        with open(os.environ["HOME"]+"/r1.txt", "rb") as f:
            while currline<skipto:
                line = f.readline()
                currline+=1
            while currline<endline:
                line = f.readline().strip()
                key = line.split(" ")[2]
                job = {"type":"t1", "key":key, "line":line, "lineno":currline}
                self.add_main_job(job)
                currline+=1
        self.add_main_job(None)

    def jobrunner1(self,job):
        con = self.sesnreq.request_url("http://www.x315.com/", headers={"Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3"})
        # self.sesnreq.request_url("http://s4.cnzz.com/stat.php?id=1256666136&show=pic1")
        url = r"http://www.x315.com/quicksearch?qk=%s&t=1&z=&timestamp=%s"%("富士康", str(time.time()).split(".")[0]+str(time.time()).split(".")[1][:3])
        header = {"Accept":r"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                  "Connection":"Keep-alive",
                  "Content-Type":"application/x-www-form-urlencoded",
                  "Accept-Language":"zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                  "Referer":"http://www.x315.com/",
                  "X-Requested-With":"XMLHttpRequest"
                 }
        con = self.sesnreq.request_url(url, headers=header)
        print con.text
        if ur"查询过于频繁" in con.text:
            if not self.re_add_job(job):
                Log.error("readd job failed.==>"+utf8str())
            Log.info("查询过于频繁,sleep 10 s.")
            time.sleep(10)

    def jobrunner2(self,job):
        pass
    def run_job(self, job):
        Log.info("running job:"+utf8str(job))
        if job["type"] == "t1":
            self.jobrunner1(job)
        elif job["type"] == "t2":
            self.jobrunner2(job)


if __name__ == "__main__":
    x315 = X315Spider(1)
    x315.select_user_agent("firefox")
    x315.load_proxy("../gongshangju/proxy_all.txt")
    x315.run()
