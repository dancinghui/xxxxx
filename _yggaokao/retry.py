#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import PageStoreBase
from spider.spider import Spider, MRLManager, AccountErrors
import re
import time
from spider.httpreq import ProxyError
import sys
import spider.util
from spider.runtime import Log
import os
import hashlib
from spider.httpreq import SessionRequests

class YggaokaoRetry(Spider):
    def __init__(self, threadcnt):
        super(Yggaokao, self).__init__(threadcnt)
        self.sessionReq = SessionRequests()

    def dispatch(self):
        f = open("prov_list","r+b")
        currline = 0
        skipto = 0
        endline = 10000

        for line in f:
            currline += 1
            if currline >= skipto:
                sySsdm = line.split(" ")[0].strip()
                job = {"sySsdm": sySsdm, "year": "2014", "start":0, "type":"u1"}
                self.add_main_job(job)
            if currline >= endline:
                break
        self.wait_q()
        self.add_job(None, True)

    def retry(self, con, job):
        if re.search(u'<h1>An error occurred.</h1>', con.text) or re.search(u'Tinyproxy was unable to', con.text):
            #should reload this page.
            if int(job["retrycnt"]) < 5:
                job["retrycnt"] = int(job["retrycnt"]) + 1
                self.add_job(job)
                return True
        return False

    def save_sch_list(self, job, res):
        with self.locker:
            fr = open("prov/"+job["sySsdm"]+".txt", "r+b")
            f = open("prov/"+job["sySsdm"]+".txt", "a+b")
            schlist = re.findall(r'<tr bgcolor="#FFFFFF" onMouseOver="this.style.background=\'#FFFFEE\'" onMouseOut=\"this.'
                                 r'style.background=\'#ffffff\'">(.*?)</tr>' , res , re.S)

            for schinfo in schlist:
                schstr = ""
                tds = re.findall(r"<td.*?>(.*?)</td>", schinfo, re.S)
                if len(tds) is 0:
                    spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " match error! No td tag! Readd..\n")
                    self.re_add_job(job)
                    ferr = open("errors/" + job["sySsdm"]+ "_"+str(job["start"])+".html", "w+b")
                    ferr.write(res)
                    ferr.close()
                    f.close()
                    return
                schnamelist = re.findall(r'dhtml">(.*?)</a>', tds[0], re.S)
                if len(schnamelist) is 0:
                    schnamelist = []
                    schnamelist.append(tds[0].strip())
                    if schnamelist[0] is "":
                        spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " match error! No school name! Readd..\n")
                        self.re_add_job(job)
                        ferr = open("errors/" + job["sySsdm"]+ "_"+str(job["start"])+".html", "w+b")
                        ferr.write(res)
                        ferr.close()
                        f.close()
                        return
                schname = schnamelist[0]
                if schname in fr.read():
                    print 'skip...', schname, ", in", job["sySsdm"], ".txt"
                    fr.close()
                    f.close()
                    return
                schstr += schname
                if r'span985">985</span>' in tds[0]:
                    schstr += " 985"
                if r'span211">211</span>' in tds[0]:
                    schstr += " 211"
                if r'spanyan">研</span>' in tds[0]:
                    schstr += " 研"

                for i in range(len(tds))[1:(len(tds)-1)]:
                    schstr += " "+tds[i]
                stucnt =  re.findall(r"doDialog.*?\">(.*?)</a>", tds[len(tds) - 1], re.S)[0].strip()
                schstr += " " + stucnt
                f.write(schstr+"\n")
                f.flush()
            f.close()

    def save_sch_detail(self, job, res):
        if not os.path.exists("detail/"+job["sySsdm"]):
                    os.makedirs("detail/"+job["sySsdm"])
        f = open("detail/"+job["sySsdm"]+"/"+job["yxdm"]+".html", "w+b")
        f.write(res)
        f.flush()
        f.close()

    def check_should_fetch(self, job):
        if(job["type"] is "u1"):
             return True
        else:
            if os.path.exists("detail/"+job["sySsdm"]+r"/"+job["yxdm"]+".html"):
                return False
            else:
                return True


    def run_job(self, job):
        if job["type"] is "u1":
            print "searching %s, start at %d" % (job["sySsdm"], job["start"])
            url = "http://gaokao.chsi.com.cn/zsjh/searchZsjh.do?ccdm=&jhxzdm=&kldm=&searchType=1&ssdm=&" \
                  "sySsdm=%s&year=%s&yxmc=&start=%d" % (job["sySsdm"], job["year"], job["start"])
            header = {"User-Agent":r"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.73 Safari/537.36",
                      "Referer":r"http://gaokao.chsi.com.cn/zsjh/zsjh2014.jsp",
                      "Origin":r"http://gaokao.chsi.com.cn",
                      "X-Requested-With":r"XMLHttpRequest",
                      "Pragma":r"no-cache"}
            con = self.sessionReq.request_url(url, headers=header)

            if con is None or con.text.strip() == "":
                spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " nothing return ! Readd..\n")
                time.sleep(10)
                self.re_add_job(job)
                return
            res = con.text
            if r"302 Found" in res:
                spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " 302 Found ! Readd..\n")
                self.re_add_job(job)
                firstCraw = True
                setattr(self._curltls, 'firstCraw', firstCraw)
                return

            elif re.search(u'无查询结果', res):
                spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " no data! Readd..\n")
                self.re_add_job(job)
                return
            elif re.search(ur'<H1>错误</H1>', res):
                time.sleep(3)
                spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " error occur ! Readd..\n")
                self.re_add_job(job)
                firstCraw = True
                setattr(self._curltls, 'firstCraw', firstCraw)
                return
            else:
                if int(job["start"]) is 0:
                    m = re.search(r"if \(Num > (\d+)", res)
                    if m:
                        pgcnt = int(m.group(1))
                        while pgcnt > 1:
                            jobb = {"sySsdm": job["sySsdm"], "year": job["year"], "start": (pgcnt-1)*20, "type":"u1"}
                            self.add_job(jobb)
                            pgcnt -= 1
                    else:
                        spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " no more page! Readd!\n")
                        self.re_add_job(job)
                        return


                yxdms = re.findall(r"doDialog\('(\d+)'", res, re.S)
                if len(yxdms) == 0:
                    spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " no url! Readd.\n")
                    self.re_add_job(job)
                    return
                for yxdm in yxdms:
                    job2 = {"yxdm": yxdm, "sySsdm": job["sySsdm"], "year": "2014", "type":"u2"}
                    if not self.check_should_fetch(job2):
                        print "skip...", job['sySsdm'], "/", job["yxdm"]
                    else:
                        self.add_job(job2)
                self.save_sch_list(job, res)
        elif job["type"] is "u2":
            url = r"http://gaokao.chsi.com.cn/zsjh/search.do?" \
                  r"ccdm=&jhxzdm=&kldm=&method=majorList&sySsdm=%s&year=%s&yxdm=%s" % (job["sySsdm"], job["year"], job["yxdm"])
            header = {"User-Agent":r"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.73 Safari/537.36"}
            con = self.sessionReq.request_url(url, headers=header)
            if con is None or con.text.strip() is "":
                print "Nothing back!readd job" + job.__str__()
                time.sleep(10)
                self.re_add_job(job)
                return
            if r"302 Found" in con.text:
                spider.runtime.Log.error(job.__str__()+" 302 Found ! Readd..\n")
                self.re_add_job(job)
                return
            res = con.text
            self.save_sch_detail(job, res)

    def run_job_desp(self, job):

        firstCraw = getattr(self._curltls, 'firstCraw', None)
        if firstCraw is None or firstCraw is True:
                setattr(self._curltls, 'curl', None)
                time.sleep(3)
                con = self.request_url("http://gaokao.chsi.com.cn/zsjh/zsjh2014.jsp", allow_redirects=False)
                t = re.findall(r"aliyungf_tc=(.*?);", con.headers)
                if len(t) is 0:
                    tt = re.findall(r"alicdn_sec=(.*?);", con.headers)
                    if len(tt) is 0:
                        spider.runtime.Log.error("No setCookie in headers\n")
                        self.re_add_job(job)
                        return
                    alicdn_sec = tt[0]
                    setattr(self._curltls, 'alicdn_sec', alicdn_sec)
                else:
                    aliyungf_tc = t[0]
                    setattr(self._curltls, 'aliyungf_tc', aliyungf_tc)
                firstCraw = False
                setattr(self._curltls, 'firstCraw', firstCraw)

        if job["type"] is "u1":
            print "searching %s, start at %d" % (job["sySsdm"], job["start"])
            url = "http://gaokao.chsi.com.cn/zsjh/searchZsjh.do?ccdm=&jhxzdm=&kldm=&searchType=1&ssdm=&" \
                  "sySsdm=%s&year=%s&yxmc=&start=%d" % (job["sySsdm"], job["year"], job["start"])
            # con = self.qcclogin.request_url(url)
            timestr = str(int(time.time()))
            # hashStr = hashlib.md5(str(timestr)).hexdigest()
            aliyungf_tc = getattr(self._curltls, 'aliyungf_tc', "AQAAAKT4VTBf8wsAW6o8OlSGFDVN4M5Y")
            alicdn_sec = getattr(self._curltls, 'alicdn_sec', "568cf0c77249af9b25b2b76cd6b2ab8ccff136f3")
            header = {"Cookie": r"alicdn_sec="+alicdn_sec+r"; aliyungf_tc="+aliyungf_tc,
                      "User-Agent":r"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.73 Safari/537.36",
                      "Referer":r"http://gaokao.chsi.com.cn/zsjh/zsjh2014.jsp",
                      "Origin":r"http://gaokao.chsi.com.cn",
                      "X-Requested-With":r"XMLHttpRequest",
                      "Pragma":r"no-cache"}
            con = self.request_url(url, headers=header, allow_redirects=False)
            res = con.text
            if r"302 Found" in res:
                spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " 302 Found ! Readd..\n")
                self.re_add_job(job)
                firstCraw = True
                setattr(self._curltls, 'firstCraw', firstCraw)
                return
            if res.strip() == "":
                spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " nothing return ! Readd..\n")
                time.sleep(10)
                self.re_add_job(job)
                return
            elif re.search(u'无查询结果', res):
                spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " no data! Readd..\n")
                self.re_add_job(job)
                return
            elif re.search(ur'<H1>错误</H1>', res):
                time.sleep(3)
                spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " error occur ! Readd..\n")
                self.re_add_job(job)
                firstCraw = True
                setattr(self._curltls, 'firstCraw', firstCraw)
                return
            else:
                if int(job["start"]) is 0:
                    m = re.search(r"if \(Num > (\d+)", res)
                    if m:
                        pgcnt = int(m.group(1))
                        while pgcnt > 1:
                            jobb = {"sySsdm": job["sySsdm"], "year": job["year"], "start": (pgcnt-1)*20, "type":"u1"}
                            self.add_job(jobb)
                            pgcnt -= 1
                    else:
                        spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " no more page! Readd!\n")
                        self.re_add_job(job)
                        return


                yxdms = re.findall(r"doDialog\('(\d+)'", res, re.S)
                if len(yxdms) == 0:
                    spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " no url! Readd.\n")
                    self.re_add_job(job)
                    return
                for yxdm in yxdms:
                    job2 = {"yxdm": yxdm, "sySsdm": job["sySsdm"], "year": "2014", "type":"u2"}
                    self.add_job(job2)
                self.save_sch_list(job, res)
        elif job["type"] is "u2":
            url = r"http://gaokao.chsi.com.cn/zsjh/search.do?" \
                  r"ccdm=&jhxzdm=&kldm=&method=majorList&sySsdm=%s&year=%s&yxdm=%s" % (job["sySsdm"], job["year"], job["yxdm"])
            timestr = str(int(time.time()))
            aliyungf_tc = getattr(self._curltls, 'aliyungf_tc', "AQAAAKT4VTBf8wsAW6o8OlSGFDVN4M5Y")
            alicdn_sec = getattr(self._curltls, 'alicdn_sec', "568cf0c77249af9b25b2b76cd6b2ab8ccff136f3")
            header = {"Cookie": r"alicdn_sec="+aliyungf_tc+r"; aliyungf_tc="+alicdn_sec,
                      "User-Agent":r"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.73 Safari/537.36"}
            con = self.request_url(url, headers=header, allow_redirects=False)
            if con is None or con.text.strip() is "":
                print "Nothing back!readd job" + job.__str__()
                time.sleep(10)
                self.re_add_job(job)
                return
            if r"302 Found" in con.text:
                spider.runtime.Log.error(job.__str__()+" 302 Found ! Readd..\n")
                self.re_add_job(job)
                return
            res = con.text
            self.save_sch_detail(job, res)



    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail(['wangwei@ipin.com'], '%s DONE' % sys.argv[0], msg)
            pass
        elif evt == 'STARTED':
            #spider.misc.stacktracer.trace_start('res.trace.html')
            pass

if __name__ == '__main__':
    spider.util.use_utf8()
    r = Yggaokao(5)
    r.load_proxy('../_zhilian/curproxy0')
    r.run()
