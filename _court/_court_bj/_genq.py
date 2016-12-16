#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import threading
import time

from _court_bj import BJCourtStore, CData
from bjspider import BJSpider
from spider import spider


class GenQueries(BJSpider):
    """Spider which generate query for http://www.bjcourt.gov.cn"""

    def __init__(self, thcnt, sleep=0):
        super(GenQueries, self).__init__(thcnt, 'BeijingListSpider')
        self.test_mode = False
        self.pagestore = BJCourtStore()
        self.sleep = sleep
        self.zero_link_count = 0
        self.lock = threading.Lock()

    def dispatch(self):
        self.add_main_job({'type': 'main', 'url': 'http://www.bjcourt.gov.cn/cpws/index.htm'})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def with_sleep_request_url(self, url, **kwargs):
        time.sleep(self.sleep)
        return self.request_url(url, **kwargs)

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        jt = jobid['type']
        url = jobid['url']
        time.sleep(2)

        con = self.with_sleep_request_url(url, timeout=10)
        if self.check_exception(con, jobid):
            return

        if 'main' == jt:
            m = re.search('yzmInput', con.text)
            if m:
                print self.get_tid(), url, ' need captcha'
                self.split_url(url)
                return
            m = re.search(ur'您搜到了\s*<em>([0-9]+)</em>\s*条符合条件的文书', con.text, re.S)
            if not m:
                yzm = re.search(ur'验证码', con.text)
                if yzm:
                    self.split_url(url)
                    print u'需要验证码', url
                else:
                    print 'Cannot find paper count from', con.code, url
                self.link_saver.add('%d,%d,%s' % (2, 0, url))
                return
            papercnt = int(m.group(1))
            if papercnt <= 0:
                print '哎呀，这里没用文书', url
                with self.lock:
                    self.zero_link_count += 1
                return
            if papercnt > 200:
                print url, 'page count', papercnt, 'need to split'
                self.split_url(url)
                return
            if not re.search('\?', url):
                url += '?'
            if url[-1] != '?' and url[-1] != '&':
                url += '&'
            print 'there are %d papers on %s' % (papercnt, url)
            self.link_saver.add('%d,%d,%s' % (1, papercnt, url))

    def split_url(self, url):
        urls = CData.split_param(url)
        for u in urls:
            self.add_job({'type': 'main', 'url': u})

    def event_handler(self, evt, msg, **kwargs):
        super(GenQueries, self).event_handler(evt, msg, **kwargs)
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


if __name__ == '__main__':
    gq = GenQueries(5)
    gq.load_proxy('proxy')
    gq.run()
