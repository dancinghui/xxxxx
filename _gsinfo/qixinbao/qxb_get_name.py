#! /usr/bin/env python
# encoding:utf-8


#! /usr/bin/env python
# encoding:utf-8
import re
from urllib import quote

import spider.runtime
from spider.spider import  Spider

#!/usr/bin/env python
# encoding:utf8
from spider.spider import Spider
from spider.httpreq import SessionRequests, CurlReq
import spider.util
import pycurl
import cutil
import json
import abc
import os
from spider.runtime import Log
import time
from spider.spider2 import AioSpider, AioRunner


class MyRunner(AioRunner):
    def __init__(self, a, b,c):
        AioRunner.__init__(self, a, b, c)
        self.baset = time.time()
        self.dstfile = open("corp_name.txt", "a+b")
        self.failfile = open("corp_fail.txt","a+b")
        self.__jsl_clearance = None
        self.__jsluid = None
    def dbg(self, r):
        if '8.8' in self.selproxy:
            Log.error("dbg", r, time.time() - self.baset)
    def prepare_req(self, job, curl, proxies):
        self.dbg('prepare')
        pa = AioRunner.prepare_req(self, job, curl, proxies)
        if pa is not None:
            return pa

        if 'key' in job:
            key = spider.util.utf8str(job['key'])
            url = r"http://www.qixin007.com/search/?key="+quote(key)+"&type=enterprise&source=&isGlobal=Y"
            # url = "http://qichacha.com/search?key=" + quote(key) + "&sType=0"
        else:
            Log.error("Invalid job.===>" + job.__str__())
        print "[%d] prepare %s proxies=" % (self.idx, url), proxies
        headers={}
        if 'ip.cn' in url:
            headers['User-Agent'] = 'curl/7.20.1'
        if self.__jsl_clearance:
            headers["Cookie"] ="__jsl_clearance=" + self.__jsl_clearance+";"
        if self.__jsluid:
            headers["Cookie"]+="__jsluid=" + self.__jsluid
        curl.prepare_req(url, headers=headers, proxies=proxies)
        return True

    def save_name(self, job, corp_name_list):
        for corp_name in corp_name_list:
            if "em" in corp_name:
                corp_name = corp_name.replace(r'<em>', '').replace(r'</em>', '').strip()
            else:
                corp_name = corp_name.strip()
            self.dstfile.write(job["line"].strip() + " " + corp_name + "\n")
            spider.runtime.Log.info("line " + str(job["lineno"]) + ", name===>" + corp_name + " saved...")
            self.dstfile.flush()

    def on_result(self, curl, resp):
        AioRunner.on_result(self, curl, resp)
        con = resp
        if con is None or con.text.strip() == "":
            spider.runtime.Log.error("Request return nothing! Readd...." + self.job.__str__())
            self.master.re_add_job(self.job)
            return
        elif con.code ==521:
            f = open("login.js", "w+b")
            f.write(con.text.replace("<script>","").replace("</script>", "").replace("document.cookie=dc", "console.log(dc)"))
            f.close()
            os.system("nodejs login.js > cookiestr.txt")
            f = open("cookiestr.txt", "r+b")
            self.__jsl_clearance=re.findall(r"__jsl_clearance=(.*?);",f.read(),re.S)[0]
            if "Set-Cookie:" in con.headers:
                setcookie = re.findall(r"Set-Cookie:(.*?)path", con.headers, re.S)[0]
                self.__jsluid = re.findall(r"__jsluid=(.*?);", setcookie, re.S)[0]
            self.master.re_add_job(self.job)
        else:
            corp_name_list = re.findall(r'class="search-result-title"><em>(.*?)</a>', con.text, re.S)
            if len(corp_name_list) == 0:
                spider.runtime.Log.warning("line " + str(self.job["lineno"]) + ", key:" + self.job["key"] + ", no data...")
                self.failfile.write(self.job["line"].strip() + " no data.\n")
                self.failfile.flush()
                return
            else:
                self.save_name(self.job, corp_name_list)
        print resp.request.url, resp.code

    def on_error(self, curl, errcode, errmsg):
        AioRunner.on_error(self, curl, errcode, errmsg)
        print "[%d] error, proxy_errcnt=%d" % (self.idx, self.proxyerr)
        print "with: code=%d msg=%s" % (errcode, errmsg)

class QxbGetName(AioSpider):
    def __init__(self):
        AioSpider.__init__(self, MyRunner)
        self.proxies = []
        f = open("../../_zhilian/curproxy0","rb")
        cnt = 1
        line = f.readline()
        while line is not None and line.strip() != "":
            print "load proxy===>"+line.strip()
            self.proxies.append(line.strip())
            line = f.readline()
            cnt+=1
        f.close()
        spider.runtime.Log.info("total %d proxy...." % (cnt-1))

    def preproc_key(self, key):
        key = key.decode("utf-8")
        all = []
        for i in key:
            if i == "(" or i == ")":
                all.append(i)
            else:
                if ord(i) > 0x400:
                    all.append(i)
        return "".join(all)

    def init_jobs(self):
        f = open(os.environ['HOME']+"/r1.txt", "rb")
        currline = 0
        skip = 0
        endline = 300
        while currline < skip:
            line = f.readline()
            currline += 1

        while currline < endline:
            line = f.readline()
            if line.strip() == "":
                break
            key = line.strip().split(" ")[2].strip()
            key = self.preproc_key(key)
            job = {"key":key, "lineno":currline, "line":line}
            self.add_main_job(job)
            currline += 1



if __name__ == "__main__":
    spider.util.use_utf8()
    q = QxbGetName()
    q.run()

