#!/usr/bin/env python
# encoding:utf-8

from lxml import html
from spider.spider2 import MRLManager, Spider2, GenQueries2
from spider.spider import ShareMRLManager
import spider.util
import re
import sys
import time
import HTMLParser
from spider.ipin.savedb import PageStoreBase
from job51login import Job51Login, CV51Data
from spider.runtime import Log
import os
import json
import spider.misc.stacktracer

mongo_cvdb_url = os.getenv('PAGESTORE_DB', "mongodb://localhost/cv_crawler")
mongo_channel = 'cv_51job'

def new51JbLogin(ac):
    a = Job51Login(ac)
    #a.load_proxy('checked_proxy')
    return a

class CV51PageStore(PageStoreBase):
    def __init__(self):
        PageStoreBase.__init__(self, mongo_channel, mongo_cvdb_url)

    def extract_content(self):
        #<td style="padding-top:10px;" id="divInfo">
        dom = html.fromstring(self.get_cur_doc().cur_content)
        xx = dom.xpath("//td[@id='divInfo']")
        if xx is not None and len(xx)>0:
            return xx[0].text_content()
        Log.errorbin(self.get_cur_doc().cur_url, self.get_cur_doc().cur_content)
        Log.error("get cv failed", self.get_cur_doc().cur_url)
        time.sleep(5)
        return None

    def page_time(self):
        m = re.search(ur'lblResumeUpdateTime.*?(\d+-\d+-\d+)', self.get_cur_doc().cur_content)
        if m:
            t = time.mktime(time.strptime(m.group(1), '%Y-%m-%d'))
            return int(t) * 1000
        return None

    def check_should_fetch(self, jdid):
        indexUrl = "%s://%s" % (self.channel, jdid)
        return not self.find_new(indexUrl)


class CV51GetCV(Spider2):
    def __init__(self, thcnt, cvaccs, cfgname):
        Spider2.__init__(self, thcnt)
        self._name = 'cv51getcv_' + cfgname
        self.cv51nm = ShareMRLManager(cvaccs, new51JbLogin)
        self.pagestore = CV51PageStore()
        self.hasher = spider.util.LocalHashChecker()

    def push_job(self, j):
        if j is None:
            self._no_more_wait_job = True
            return
        if isinstance(j, dict):
            self.add_job(j)
        elif isinstance(j, list):
            for d in j:
                self.add_job(d)
        else:
            raise RuntimeError('invalid job')
        while self._jobq.get_mqsz() > 3000:
            # 队列任务太多, 要等等了
            time.sleep(1)

    def wait_job(self):
        return self.wait_job_by_condition()

    def run_job(self, jobid):
        if self.get_job_type(jobid) != 'cvurl':
            return
        #http://ehire.51job.com/Candidate/ResumeView.aspx?hidUserID=2801&hidEvents=23&hidKey=b4c9f030c69853ed26b3b5a92a20fb45
        url = jobid['url']
        m = re.search(r'hidUserID=(\d+)', url)
        if m is None:
            return
        jdid = m.group(1)
        with self.locker:
            spider.util.FS.dbg_append_file('ooo.txt', jdid)
        if self.hasher.query(jdid) > 0:
            print "%s duplicated" % jdid
            return

        if self.pagestore.check_should_fetch(jdid):
            con = self.cv51nm.el_request(url)
            if con is None:
                self.re_add_job(jobid)
                return
            else:
                getime = int(time.time())
                if u'此人简历保密' in con.text:
                    Log.warning(jdid, "此人简历保密")
                    self.hasher.add(jdid)
                else:
                    self.pagestore.save(getime, jdid, url, con.text)
        else:
            print "skip %s" % jdid

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['lixungeng@ipin.com', 'jianghao@ipin.com'], '%s DONE' % sys.argv[0], msg)


class CV51GenQueries(GenQueries2):
    def __init__(self, thdcnt, mainacs):
        GenQueries2.__init__(self, thdcnt)
        self._name = mongo_channel
        self.cv51nm = ShareMRLManager(mainacs, new51JbLogin)
        self.jobpusher = None
        self.modtime = None

    def init_conditions(self):
        CV51Data.add(self, 'AREA', CV51Data.AREA)
        CV51Data.add(self, 'AGE', CV51Data.AGE)
        CV51Data.add(self, 'SEX', CV51Data.SEX)
        CV51Data.add(self, 'WORKYEAR', CV51Data.WORKYEAR)
        CV51Data.add(self, 'TOPDEGREE', CV51Data.TOPDEGREE)
        CV51Data.add(self, 'JOBSTATUS', CV51Data.JOBSTATUS)
        CV51Data.add(self, 'TOPMAJOR', CV51Data.TOPMAJOR)
        print "max count:", self.get_max_count()

    def req_search_page(self, kvs):
        headers = {'Referer': Job51Login.search_page}
        con = self.cv51nm.el_request(Job51Login.search_page, data=kvs, headers=headers)
        return con

    def run_job(self, jobid):
        GenQueries2.run_job(self, jobid)
        tp = self.get_job_type(jobid)
        if tp == 'psearch':
            con = self.req_search_page(jobid['kvs'])
            if con is None:
                self.re_add_job(jobid)
            else:
                jobinfo={'hv':jobid['kvs']['hidValue'], 'page':jobid['kvs']['pagerBottom$txtGO']}
                self._queue_cvs(con.text, jobinfo)

    def _queue_cvs(self, text, jobinfo):
        xxs = re.findall(ur'''/Candidate/ResumeView\.aspx[^'"]*''', text)
        xxs = spider.util.unique_list(xxs)
        h = HTMLParser.HTMLParser()
        joblst = []
        for i in xxs:
            url = "http://ehire.51job.com" + h.unescape(i)
            joblst.append({'type':'cvurl', 'url':url})
        # Log.error(jobinfo, joblst)
        self.jobpusher(joblst)

    def need_split(self, url, level, isLast):

        # LASTMODIFYSEL:
        # 3: 最近一个月更新
        # 2015: 2015年更新
        # 2014: 2014年更新
        if self.modtime:
            url["LASTMODIFYSEL"] = self.modtime
        caller = lambda n: n.get_search_data(url)
        kvs, con = self.cv51nm.ensure_login_do(None, caller, None)

        if con is None:
            time.sleep(1)
            return self.need_split(url, level, isLast)

        #TODO: replace with better method...
        m = re.search(ur'每页显示：(.*?)</div>', con.text, re.S)
        if m is None:
            Log.warning("empty!!")
            time.sleep(600)
            self.cv51nm.set_nologin()
        text = re.sub(r"<[^<>]*>", "", m.group(1))
        text = re.sub(r"&nbsp;|\s", '', text)
        m1 = re.search(ur"(\d+)条", text)
        xcount = int(m1.group(1))
        self._queue_cvs(con.text, url)

        m1 = re.search(ur"(\d+)/(\d+)页", text)
        pages = int(m1.group(2))
        print url, "%d条 %d页" % (xcount,pages)
        time.sleep(2)
        if xcount>=3000:
            return True
        for pg in range(2, pages+1):
            kvs1 = Job51Login.update_search_data(kvs, pg)
            self.add_job({'type':'psearch', 'kvs':kvs1, 'dontreport':1})
        return False

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            self.jobpusher(None)
        elif evt == 'STARTED':
            #spider.misc.stacktracer.trace_start('res.trace.html')
            pass


def main():

    print """
            -c  账户文件
            -t  3|2015|2014 最近一个月|2015年更新|2014年更新
    """

    opts = spider.util.GetOptions('c:t:')
    cfg = opts.get('-c')
    if not cfg:
        print "没有帐号不能运行"
        return
    modtime = opts.get('-t')
    # if modtime:
    #     global mongo_channel
    #     mongo_channel += modtime

    #load accounts.
    jcfg = json.loads(open(cfg).read())
    cfgname = re.sub(".*/", "", cfg)
    gcv = CV51GetCV(1, jcfg['gcv'], cfgname)
    gcv.run(True)
    r = CV51GenQueries(1, jcfg['gcv'])
    r.jobpusher = lambda v : gcv.push_job(v)
    r.modtime = modtime
    r.bindopts(opts)
    r.run()
    gcv.wait_run(True)


if __name__ == '__main__':
    spider.util.use_utf8()
    main()
