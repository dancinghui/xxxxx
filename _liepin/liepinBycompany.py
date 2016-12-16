#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
import sys
import time
from page_store import PageStoreLP
from spider.spider import Spider, SpiderErrors
import spider.util
from spider.runtime import Log
import spider.misc.stacktracer
from spider.util import htmlfind
from spider.racer import TimedLock
from spider.captcha.lianzhong import LianzhongCaptcha


class LiepinBycompay(Spider):
    def __init__(self, thcnt, company):
        Spider.__init__(self, thcnt)
        self.pagestore = PageStoreLP()
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
            url = 'https://company.liepin.com/%s' %job['u']
            print url
            con = self.request_url(url)
            if con is not None:
                self.parse_list(con.text, url)
                self.parse_html(con.text)
            else:
                self.re_add_job(job)
        elif jobtype == 'list':
            url = job['base'] + '/pn' + job['u']
            print url
            con = self.request_url(url)
            if con is not None:
                self.parse_html(con.text)
            else:
                self.re_add_job(job)
        elif jobtype == 'jd':
            url = job['u']
            m = re.search(r'.*?_(\d+)/', url)
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
        spans = htmlfind.findTag(text, 'span', 'class="addition"')
        if spans:
            if isinstance(spans[0],unicode):
                spans[0] = spans[0].encode('utf-8')
            m = re.search(r'共(\d+)页', spans[0], re.S)
            if m:
                for i in range(2, int(m.group(1))):
                    self.add_job({'type': 'list', 'u': str(i), 'base': url})

    def parse_html(self, text):
        a = re.findall(r'https://job.liepin.com/.*?_\d+/', text)
        urls = spider.util.unique_list(a)
        for pageurl in urls:
            self.add_job({'type': 'jd', 'u': pageurl})

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'STARTED':
            pass
            # spider.misc.stacktracer.trace_start('res.liepin_qiye.html')
        if evt == 'DONE':
            msg += "saved : %d\n" % self.pagestore.saved_count
            print msg
            spider.util.sendmail(['lixungeng@ipin.com', 'wangwei@ipin.com'], '%s DONE by company' % sys.argv[0], msg)

if __name__ == "__main__":
    s = LiepinBycompay(10, 'company')
    s.load_proxy('proxy')
    # s.set_proxy(['106.75.134.189:18889:ipin:helloipin'], index=0, auto_change=False)
    s.run()
