#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import threading
import unittest

import time

from court.cspider import ATOSSessionSpider


class MySessionSpider(ATOSSessionSpider):
    def __init__(self):
        super(MySessionSpider, self).__init__(3)
        self.jobs = [
            'http://www.fszjfy.gov.cn/pub/court_7/homepage/',
            'http://www.bjcourt.gov.cn/cpws/index.htm',
            'http://www.hshfy.sh.cn/shfy/gweb/index.html',
            'http://www.bjcourt.gov.cn/fyyw/index.htm',
            'http://www.hshfy.sh.cn/shfy/gweb/channel_spyj.jsp?zd=spyj',
            'http://www.bjcourt.gov.cn/cpws/index.htm',
            'http://www.hshfy.sh.cn/shfy/gweb/index.html']
        self.host = threading.local()

    def gethost(self, url):
        m = re.search(r':\/\/([^\/]+)\/', url)
        if m:
            return m.group(1)

    def dispatch(self):
        for u in self.jobs:
            self.add_main_job({'type': self.gethost(u), 'url': u})
        time.sleep(2)
        self.wait_q()
        self.add_main_job(None)

    def thread_init(self, tid):
        r = tid % 3
        if r == 0:
            setattr(self.host, 'host', 'www.bjcourt.gov.cn')
        elif r == 1:
            setattr(self.host, 'host', 'www.fszjfy.gov.cn')
        else:
            setattr(self.host, 'host', 'www.hshfy.sh.cn')

    def run_job(self, jobid):
        host = getattr(self.host, 'host', None)
        if host is None:
            host = jobid['type']
            setattr(self.host, 'host', host)
        jt = jobid['type']
        if jt != host:
            print 'not the right host', host, jobid['url']
            self.re_add_job(jobid)
            time.sleep(1)
            return
        con = self.request_url(jobid['url'])
        if con:
            print  jobid['type'], con.cookies
        curlckjar = getattr(self._curltls, 'cookies', None)
        if curlckjar:
            print jobid['type'], '2,', curlckjar


class SessionSpiderTestCase(unittest.TestCase):
    def __init__(self):
        super(SessionSpiderTestCase, self).__init__()
        self.spider = MySessionSpider()

    def run(self, result=None):
        self.spider.run()

    def runTest(self):
        self.spider.run()


if __name__ == '__main__':
    test = SessionSpiderTestCase()
    test.run()
