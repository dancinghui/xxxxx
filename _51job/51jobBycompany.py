#!/usr/bin/env python
# -*- coding:utf8 -*-
import urllib2

import chardet
import qdata
import spider.genquery
import copy
import time
import spider.util
import re
import sys
import urllib
from _51job import PageStore51
from spider.ipin.savedb import PageStoreBase
from spider.spider import Spider
from spider.util import htmlfind, TimeHandler
from spider.runtime import Log
from spider.httpreq import BasicRequests
import spider.misc.stacktracer


class JD51ByCompany(Spider):
    def __init__(self, thcnt, company):
        Spider.__init__(self, thcnt)
        self.default_headers = {'Cookie':'guide=1'}
        self.pagestore = PageStore51()
        self._name = "jd51"
        self.list = []
        with open(company) as file_:
            for line in file_:
                self.list.append(line.strip())

    def dispatch(self):
        for i in self.list:
            self.add_main_job({'u': str(i), 'type': 'co'})
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, job):
        jobtype = self.get_job_type(job)
        if jobtype == 'co':
            url = 'http://jobs.51job.com/all/co%s.html' %job['u']
            print url
            con = self.request_url(url)
            if con is not None:
                self.parse_list(con.text, url)
                self.parse_html(con.text)
            else:
                self.re_add_job(job)
        elif jobtype == 'list':
            url = job['base']
            postdata = {'pageno': job['u'], 'hidTotal': job['hid']}
            print url + '  ' + str(postdata)
            postdata = urllib.urlencode(postdata)
            oper = urllib2.urlopen(url, postdata, timeout=20)
            data = oper.read()
            data = data.decode(chardet.detect(data)['encoding'])
            data = data.encode('utf-8')
            if data is not None:
                self.parse_html(data)
            else:
                self.re_add_job(job)
        elif jobtype == 'jd':
            url = job['u']
            m = re.search(r'/(\d+)\.html', url)
            if m:
                if self.pagestore.check_should_fetch(m.group(1)):
                    con = self.request_url(url)
                    if con is not None:
                        self.pagestore.save(int(time.time()), m.group(1), url, con.text)
                    else:
                        self.re_add_job(job)
                        Log.error("failed get url", url)
                        # self.re_add_job(jobid)
                else:
                    #Log.warning("skip fetch url:", url)
                    pass

    def parse_list(self, text, url):
        a = re.findall(r'>(\d+)</a></li>', text)
        urls = spider.util.unique_list(a)
        hid = re.findall(r' name="hidTotal" value="(\d+)">', text)
        if len(hid) != 0:
            for pageurl in urls:
                self.add_job({'type': 'list', 'u': pageurl, 'base': url, 'hid': hid[0]})

    def parse_html(self, text):
        a = re.findall(r'http://jobs\.51job\.com/[a-z0-9A-Z_\-]*/\d+\.html', text)
        urls = spider.util.unique_list(a)
        for pageurl in urls:
            self.add_job({'type': 'jd', 'u': pageurl})

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['wangwei@ipin.com', 'lixungeng@ipin.com'], '%s DONE from company' % sys.argv[0], msg)
        elif evt == 'STARTED':
            #spider.misc.stacktracer.trace_start('res.trace.html')
            pass


def test_ps():
    ps = PageStore51()
    ps.testmode = True
    br = BasicRequests()
    br.select_user_agent('firefox')
    url = "http://jobs.51job.com/beijing-hdq/70320056.html?s=0"
    con = br.request_url(url)
    ps.save(int(time.time()), "jd_51job://", url, con.text)


if __name__ == '__main__':
    j = JD51ByCompany(50, 'company')
    # j.load_proxy('proxy')
    j.run()
