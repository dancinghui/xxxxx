#!/usr/bin/env python
# -*- coding:utf8 -*-

from qcclogin import QccLogin, QccData
from spider.ipin.savedb import PageStoreBase
from spider.spider import Spider, MRLManager, AccountErrors
import re
import time
from spider.httpreq import ProxyError
import sys
import spider.util
from spider.runtime import Log
from test import MTRunBase, MTRunner


class QccPageStore(PageStoreBase):
    def __init__(self):
        PageStoreBase.__init__(self, "qichacha")

    def page_time(self):
        return 1450346105*1000

    def check_should_fetch(self, cpid):
        indexUrl = "%s://%s" % (self.channel, cpid)
        if self.find_any(indexUrl):
            return False
        return True

    def extract_content(self):
        m = re.search(r'<div class="detail-info">(.*?)<div class="wrap_style mb15  pd5"  id="comment" name="comment">', self.get_cur_doc().cur_content, re.S)
        if m:
            a = re.sub(ur'<[a-zA-Z/!][^<>]*>', '', m.group(1))
            return a.strip()
        Log.error(self.get_cur_doc().cur_url, "no content")
        return None


class QccSpider(Spider):
    def __init__(self, threadcnt, acc_file):
        # self.qcclogin = QccLogin(acc)
        self.pagestore = QccPageStore()
        self.qcc_acc_manager = MRLManager(QccData(acc_file).get_accounts(), QccLogin)
        super(QccSpider, self).__init__(threadcnt)

    def _do_requests(self, url, **kwargs):
        r = Spider._do_requests(self, url, **kwargs)
        if r is None:
            return r
        if r.text.strip() == u"":
            raise ProxyError('ip blocked.')
        return r

    def dispatch(self):
        # self.qcclogin.do_login()
        f = open("r1.txt", "rb")

        currline = 0
        # if len(sys.argv) is 4:
        #     skipto = int(sys.argv[1].strip())
        #     endline = int(sys.argv[2].strip())
        #     Log.warning("skipto %d, endline %d. account file is %s."% (skipto, endline, sys.argv[3]))
        # else:
        #     raise RuntimeError("please use command-line arguments. arg[1]=skipto, arg[2]=endline, arg[3]=account_file_path")
        skipto = 0
        endline = 20000
        for line in f:
            currline += 1
            if currline >= skipto:
                key = line.split(" ")[-1].strip()
                job = {"kw": key, "page": "1", "type": "u1"}
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

    def run_job(self, job):
        if job["type"] is "u1":
            key = job["kw"]
            page = str(job["page"])
            url = "http://qichacha.com/search?key=" + key + "&index=name&" + "p=" + page
            # con = self.qcclogin.request_url(url)
            con = self.qcc_acc_manager.el_request(url)
            res = con.text
            if res.strip() == "":
                time.sleep(10)
                self.add_job(job)
                return
            elif re.search(u'小查还没找到数据', res):
                Log.error("key="+key+", page="+page+", no data!\n")
            else:
                Log.error("searching %s" % key)
                urls = self._match(res, r'<h3 class="site-list-title"><a href="(.*?)"')
                if len(urls) == 0:
                    Log.errorbin("%s %s" % (key,url), con.text)
                    raise AccountErrors.NoAccountError(key)
                for u in urls:
                    job2 = {"url": u, "type": "u2", "retrycnt": "0"}
                    self.add_job(job2)
                # catch page 1 only
                # if page is '1':
                #     corp_count = int(self._match(res, r'<span class="search-key">(.*?)</span>')[0])
                #     pg_count = (corp_count + 9)/10
                #     #not vip limit in 10 pages
                #     if pg_count >= 10:
                #         pg_count = 10
                #     for i in range(2, pg_count+1):
                #         job3 = {"kw": key, "page": str(i), "type": "u1"}
                #         self.add_job(job3)

        elif job["type"] is "u2":
            url = "http://qichacha.com"+job["url"]
            cpid = job["url"][1:]

            if self.pagestore.check_should_fetch(cpid):
                con = self.request_url(url)
                if con is None or self.retry(con, job):
                    return
                self.pagestore.save(int(time.time()), cpid, url, con.text)
            else:
                Log.warning("skip ", cpid)

    def _match(self, content, pattern1, pattern2=''):
        list = re.findall(pattern1, content, re.S)
        result_list = []
        if pattern2 is not '':
            for i in range(len(list)):
                tlist = re.findall(pattern2, list[i], re.S)
                for j in range(len(tlist)):
                    result_list.append(tlist[j].strip())
            return result_list
        else:
            for i in range(len(list)):
                list[i] = list[i].strip()
            return list
    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            # spider.util.sendmail(['lixungeng@ipin.com', 'hanpeiyuan@ipin.com'], '%s DONE' % sys.argv[0], msg)
            pass
        elif evt == 'STARTED':
            #spider.misc.stacktracer.trace_start('res.trace.html')
            pass

class QccMTRun(MTRunBase):
    def __init__(self):
        MTRunBase.__init__(self)

    def run(self):
        if not hasattr(self, "spider"):
            self.spider = QccSpider(1, "acc_checked%d.txt" % self._tid)
            self.spider.load_proxy("../_zhilian/curproxy")
            self.search_time = 0
        while True:
            self._index, job = self._mgr.jobpager.get_job(self._tid, self._index)
            if job is None:
                Log.error(self._tid, "breaking............")
                break
            #run main job
            currtime = time.time()
            if (currtime - self.search_time) < 3 :
                Log.warning("thread%d sleep 3 s......" % self._tid)
                time.sleep(3)
            self.run_job(job)
            self.search_time = time.time()
            while not self.spider.job_queue.empty() or not self.spider.job_queue2.empty() or not self.spider.job_queue3.empty():
                job, ismainjob = self.spider._get_a_job()
                if job is not None:
                    self.spider.run_job(job)

    def run_job(self, jobline):
         with self._mgr._lock:
            key = re.split("\s+", jobline)[2].encode("utf8")
            print key
            job =  {"kw": key, "page": "1", "type": "u1"}
            self.spider.run_job(job)

if __name__ == '__main__':
    spider.util.use_utf8()
    r = MTRunner(QccMTRun, 5, 'r2w.txt')
    r.run()
