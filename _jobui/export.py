#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
#os.environ['PAGESTORE_DB'] = "mongodb://crawler:crawler@192.168.1.81,192.168.1.82,192.168.1.83/gaokao_crawler"
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider
import spider.util
from spider.savebin import CsvSaver, FileSaver
from page_store import PageStoreJobUI
import pymongo
import threading
conn = pymongo.MongoClient("mongodb://raw:raw@192.168.1.81,192.168.1.82,192.168.1.83/jd_jobui_raw")
class JobuiExport(Spider):
    """
    jobui增量--爬取直接入库
    """
    def __init__(self):
        Spider.__init__(self, 50)
        self.success_count = 0
        head = ["_id", "pubTime", "jdFrom", "incName", "incScale", "incIndustry", "incIntro", "incType", "incUrl", "incLocation",
                "jobPosition", "jobNum", "jobType", "jobCate", "sex", "age", "jobMajorList", "jobDiploma", "jobWorkAge", "skillList",
                "jobWorkLoc", "jobSalary", "certList", "workDemand", "workDuty", "jobWelfare", "jobDesc", "jdId",  "jdUrl"]  #"id_src",
        #self.result = CsvSaver("result.csv", head)
        self.result = FileSaver("result.txt")
        line = ""
        i = 0
        for h in head:
            if i+1 == len(head):
                line += h
            else:
                line += h + "#"
            i += 1
        self.result.append(line)
        time.sleep(1)
        #self.exes = {}

    def wait_q_breakable(self):
        lt = 0
        while True:
            if not self.job_queue.empty() or not self.job_queue2.empty() or not self.job_queue3.empty():
                time.sleep(5)
            if time.time() < lt + 1 and self._running_count==0:
                return True
            time.sleep(2)
            lt = time.time()
            if self._worker_count == 0:
                return False

    # def init_obj(self):
    #     threadident = str(threading.currentThread().ident)
    #     tid = self.get_tid()
    #     exe = ""
    #     if tid < 10:
    #         exe = "db.jd_raw_0"+str(tid)+".find()"
    #     else:
    #         exe = "db.jd_raw_"+str(tid)+".find()"
    #     self.exes[threadident] = exe
    #     setattr(self._curltls, "exe", exe)
    #     return exe

    def dispatch(self):
        db = conn.jd_jobui_raw
        i = 63
        cnt = 0
        while i < 64:
            exe = ""
            if i < 10:
                exe = "db.jd_raw_0"+str(i)+".find()"
            else:
                exe = "db.jd_raw_"+str(i)+".find()"
            for line in eval(exe):
                cnt += 1
                job = {"line": line, "cnt": cnt, "exe": exe}
                self.add_job(job, True)
            i += 1
        self.wait_q_breakable()
        self.add_job(None, True)

    def filter(self, line):
        #names = [u"北大纵横", u"温氏集团", u"金诚信矿业管理股份有限公司"]
        incName = line["jdInc"]["incName"]
        if u"北大纵横" in incName or u"温氏集团" in incName or u"金诚信矿业管理股份有限公司" in incName:
            return True
        else:
            return False
        # for name in names:
        #     if name in incName:
        #         return True
        #     else:
        #         return False

    def run_job(self, job):
        ctt = job["line"]
        cnt = job["cnt"]
        exe = job["exe"]
        line = []
        if not self.filter(ctt):
            #print "break ---> ", exe, cnt, ctt["jdInc"]["incName"]
            return
        print "found: ", exe, cnt, ctt["jdInc"]["incName"]
        # db = conn.jd_jobui_raw
        # ctt = db.jd_raw_00.find_one()
        #print "查到:",ctt

        line.append(ctt["_id"].replace("\n", " "))
        line.append(ctt["pubTime"].replace("\n", " "))
        line.append(ctt["jdFrom"].replace("\n", " "))
        #公司信息
        company = ctt["jdInc"]
        line.append(company["incName"].replace("\n", " "))
        line.append(company["incScale"].replace("\n", " "))
        line.append(company["incIndustry"].replace("\n", " "))
        line.append(company["incIntro"].replace("\n", " "))
        line.append(company["incType"].replace("\n", " "))
        line.append(company["incUrl"].replace("\n", " "))
        try:
            line.append(company["incLocation"].replace("\n", " "))
        except Exception as e:
            line.append(" ")
            print "***************************************错误:", e,  company
        #职位信息
        jobinfo = ctt["jdJob"]
        line.append(jobinfo["jobPosition"].replace("\n", " "))
        line.append(jobinfo["jobNum"].replace("\n", " "))
        line.append(jobinfo["jobType"].replace("\n", " "))
        line.append(jobinfo["jobCate"].replace("\n", " "))
        line.append(jobinfo["sex"].replace("\n", " "))
        line.append(jobinfo["age"].replace("\n", " "))

        jobMajorList = jobinfo["jobMajorList"]
        jmr = self.getList(jobMajorList)
        line.append(jmr)

        line.append(jobinfo["jobDiploma"].replace("\n", " "))
        line.append(jobinfo["jobWorkAge"].replace("\n", " "))

        skillList = jobinfo["skillList"]
        ski = self.getList(skillList)
        line.append(ski)

        line.append(jobinfo["jobWorkLoc"].replace("\n", " "))
        line.append(jobinfo["jobSalary"].replace("\n", " "))

        certList = jobinfo["certList"]
        cer = self.getList(certList)
        line.append(cer)

        line.append(jobinfo["workDemand"].replace("\n", " "))
        line.append(jobinfo["workDuty"].replace("\n", " "))
        line.append(jobinfo["jobWelfare"].replace("\n", " "))
        line.append(jobinfo["jobDesc"].replace("\n", " "))

        line.append(ctt["jdId"].replace("\n", " "))
        #line.append(ctt["id_src"].replace("\n", " "))
        line.append(ctt["jdUrl"].replace("\n", " "))

        i = 0
        w = ""
        for wri in line:
            if i+1 == len(line):
                w += wri
            else:
                w += wri + "#"
            i += 1
        self.result.append(w)
        print "write success:", i, cnt, ctt


    def getList(self, lst):
        line = ""
        i = 0
        for l in lst:
            if i+1 == len(lst):
                line += l.replace("\n", " ")
            else:
                line += l.replace("\n", " ") + ","
            i += 1
        return line

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "export execute finish !"
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)


if __name__ == "__main__":
    spider.util.use_utf8()
    start = time.time()
    s = JobuiExport()
    #s.run_job(None)
    s.run()
