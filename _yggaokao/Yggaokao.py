#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import PageStoreBase
from spider.spider import Spider, MRLManager, AccountErrors
import re
import time
from spider.httpreq import ProxyError
import sys
import spider.util
import random
import spider.runtime
import os
import hashlib
from spider.httpreq import SessionRequests

class Yggaokao(Spider):
    def __init__(self, threadcnt):
        super(Yggaokao, self).__init__(threadcnt)
        self.sessionReq = SessionRequests()
        self.sessionReq.load_proxy('proxy')

    def dispatch(self):
        f = open("prov_list","r+b")
        currline = 0
        skipto = 0
        endline = 100

        for line in f:
            currline += 1
            if currline >= skipto:
                sySsdm = line.split(" ")[0].strip()
                job = {"sySsdm": sySsdm, "year": "2015", "start":0, "type":"u1"}
                self.add_main_job(job)
            if currline >= endline:
                break
        self.wait_q()
        self.add_job(None, True)

    def check_sch_list(self, url, flag=True):
        if not os.path.exists("prov"):
            os.makedirs("prov")
        if not os.path.exists("prov/check.txt"):
            f = open('prov/check.txt', 'w')
            f.close()
        if(flag):
            with open("prov/check.txt") as file_:
                for line in file_:
                    if url in line:
                        return False
            return True
        f = open("prov/check.txt", "a+")
        f.write(url+"\n")
        f.close()

    def check_sch_detail(self, job):
        if not os.path.exists("detail/" + job["sySsdm"]):
            os.makedirs("detail/" + job["sySsdm"])
            return True
        files = os.listdir("detail/" + job["sySsdm"])
        if files.count(job["yxdm"]+".html") == 0:
            return True
        return False

    def retry(self, con, job):
        if re.search(u'<h1>An error occurred.</h1>', con.text) or re.search(u'Tinyproxy was unable to', con.text):
            #should reload this page.
            if int(job["retrycnt"]) < 5:
                job["retrycnt"] = int(job["retrycnt"]) + 1
                self.add_job(job)
                return True
        return False

    def save_sch_list(self, job, res):
        if not os.path.exists("prov"):
            os.makedirs("prov")
        with self.locker:
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

    def run_job(self, job):
        i = random.randint(15, 30)
        if job["type"] is "u1":
            print "searching %s, start at %d" % (job["sySsdm"], job["start"])
            url = "http://gaokao.chsi.com.cn/zsjh/searchZsjh--year-%s,searchType-1,sySsdm-%s,start-%d.dhtml" % (job["year"], job["sySsdm"], job["start"])
            #url = "http://gaokao.chsi.com.cn/zsjh/searchZsjh.do?ccdm=&jhxzdm=&kldm=&searchType=1&ssdm=&" \
            #      "sySsdm=%s&year=%s&yxmc=&start=%d" % (job["sySsdm"], job["year"], job["start"])
            header = {"User-Agent":r"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0",
                      #"Referer":r"http://gaokao.chsi.com.cn/zsjh/",
                      #"Origin":r"http://gaokao.chsi.com.cn",
                      "Host": r"gaokao.chsi.com.cn",
                      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                      "Accept - Language": "zh-CN,zh;q=0.5",
                      "Accept - Encoding": "gzip, deflate",
                      "Connection": "keep-alive",
                      "Cache - Control": "max-age=0"
                      #"X-Requested-With":r"XMLHttpRequest",
                      #"Pragma":r"no-cache"
                      }
            con = self.sessionReq.request_url(url, headers=header)
            if con is None or con.text.strip() == "":
                print "result is None!"
                spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " nothing return ! Readd..\n")
                time.sleep(i)
                self.re_add_job(job)
                return
            res = con.text
            if r"302 Found" in res:
                spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " 302 Found ! Readd..\n")
                time.sleep(i)
                self.re_add_job(job)
                firstCraw = True
                setattr(self._curltls, 'firstCraw', firstCraw)
                return
            elif r"403 " in con.text:
                print "403 Forbidden (操作被拒绝) 列表页"
                spider.runtime.Log.error(job["sySsdm"] + ", start at " + str(job["start"]) + "403 Forbidden ! Readd..\n")
                time.sleep(i)
                self.re_add_job(job)
                firstCraw = True
                setattr(self._curltls, 'firstCraw', firstCraw)
                return
            elif re.search(u'无查询结果', res):
                print "无查询结果!"
                spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " no data! Readd..\n")
                time.sleep(i)
                self.re_add_job(job)
                firstCraw = True
                setattr(self._curltls, 'firstCraw', firstCraw)
                return
            elif re.search(ur'<H1>错误</H1>', res):
                print "<H1>错误</H1>!"
                time.sleep(i)
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
                        #else:
                        #    spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " no more page! Readd!\n")
                        #    self.re_add_job(job)

                yxdms = re.findall(r"doDialog\('(\d+)'", res, re.S)
                if len(yxdms) == 0:
                    spider.runtime.Log.error(job["sySsdm"]+", start at "+ str(job["start"]) + " no url! Readd.\n")
                    time.sleep(i)
                    self.re_add_job(job)
                    return
                for yxdm in yxdms:
                    job2 = {"yxdm": yxdm, "sySsdm": job["sySsdm"], "year": "2015", "type":"u2"}
                    self.add_job(job2)
                if self.check_sch_list(url):
                    self.save_sch_list(job, res)
                    self.check_sch_list(url, False)
                else:
                    print "该列表页已抓取过！"

        elif job["type"] is "u2":
            url = r"http://gaokao.chsi.com.cn/zsjh/search.do?" \
                  r"ccdm=&jhxzdm=&kldm=&method=majorList&sySsdm=%s&year=%s&yxdm=%s" % (job["sySsdm"], job["year"], job["yxdm"])
            header = {"User-Agent":r"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:39.0) Gecko/20100101 Firefox/39.0",
                      "Host": "gaokao.chsi.com.cn",
                      "Referer": "http://gaokao.chsi.com.cn/zsjh/",
                      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                      "Accept - Language": "zh-CN,zh;q=0.5",
                      "Accept - Encoding": "gzip, deflate",
                      "Connection": "keep-alive",
                      "Cache - Control": "max-age=0"
                      }
            if self.check_sch_detail(job):
                con = self.sessionReq.request_url(url, headers=header)
                if con is None or con.text.strip() is "":
                    print "Nothing back!readd job" + job.__str__()
                    time.sleep(i)
                    self.re_add_job(job)
                    return
                if r"302 Found" in con.text:
                    print "302 Found!"
                    spider.runtime.Log.error(job.__str__()+" 302 Found ! Readd..\n")
                    time.sleep(i)
                    self.re_add_job(job)
                    return
                if r"403 " in con.text:
                    print "403 Forbidden (操作被拒绝) 详情页"
                    spider.runtime.Log.error(job.__str__() + " 302 Found ! Readd..\n")
                    time.sleep(i)
                    self.re_add_job(job)
                    return
                res = con.text
                self.save_sch_detail(job, res)
            else:
                print job["sySsdm"] + ":" + str(job["yxdm"]) + "-----该学校已抓取过！！！"

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail(['wangwei@ipin.com'], '%s DONE' % sys.argv[0], msg)
            pass
        elif evt == 'STARTED':
            #spider.misc.stacktracer.trace_start('res.trace.html')
            pass

if __name__ == '__main__':
    spider.util.use_utf8()
    r = Yggaokao(50)
    r.load_proxy('proxy')
    r.run()
