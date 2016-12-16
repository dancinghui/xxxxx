#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
import sys
import time

import spider.util
from spider.runtime import Log
import spider.misc.stacktracer
from zhilian import MProxySpider, ZhilianPageStore
class ZLbycompany(MProxySpider):
    def __init__(self, thcnt, company):
        MProxySpider.__init__(self, thcnt)
        self.pagestore = ZhilianPageStore()
        self.enable_mainjob_timedlock = False
        self.prlist = []
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
            url = 'http://sou.zhaopin.com/jobs/companysearch.ashx?CompID=%s' % job['u']
            print url
            con = self.request_url(url)
            if con is not None:
                self.parse_list(con.text, url)
                self.parse_html(con.text)
            else:
                self.re_add_job(job)
        elif jobtype == 'list':
            url = job['base'] + job['u']
            print url
            con = self.request_url(url)
            if con is not None:
                self.parse_html(con.text)
            else:
                self.re_add_job(job)
        elif jobtype == 'jd':
            url = job['u']
            m = re.search(r'.*?(\d+).htm', url)
            print url
            if m:
                if self.pagestore.check_should_fetch(m.group(1)):
                    con = self.request_url(url)
                    if con is not None:
                        self.pagestore.save(int(time.time()), m.group(1), url, con.text)
                    else:
                        self.re_add_job(job)
                        Log.error("failed get url", url)
                else:
                    pass

    def parse_list(self, text, url):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        m = re.search('共<em>(\d+)</em>个职位满足条件',text)
        if m:
            pagecnt = (int(m.group(1)) + 59) / 60
            for i in range(2, pagecnt + 1):
                self.add_job({'type': 'list', 'u': '&p=%s' %i, 'base': url})
            if pagecnt == 0:  # no record found.
                Log.error("%s => NO_PAGES!" % url)
                return

    def parse_html(self, text):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        a = re.findall(r'http://jobs.zhaopin.com/\d+.htm', text)
        urls = spider.util.unique_list(a)
        for pageurl in urls:
            self.add_job({'type': 'jd', 'u': pageurl})

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['lixungeng@ipin.com', 'wangwei@ipin.com'], '%s DONE by company' % sys.argv[0], msg)
        elif evt == 'STARTED':
            #spider.misc.stacktracer.trace_start('res.trace.html')
            pass


if __name__ == "__main__":
    s = ZLbycompany(30, 'company')
    s.useproxy('proxy')
    #s.load_proxy('curproxy')
    s.run()