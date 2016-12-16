#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import threading
import time

from bjspider import CData, FoodMakerExtendLock, BJSpider
from court.save import LinkSaver
from court.util import Captcha
from spider import spider


class BjListSpider(BJSpider):
    def __init__(self, threadcnt, last_page=None, total_page=22305, save_file='seeds.dat', sleep=0.0, proxy_life=180):
        super(BjListSpider, self).__init__(threadcnt, 'BjListSpider', proxy_life=proxy_life)

        self.test_mode = False
        self.sleep = sleep
        self.zero_link_count = 0
        self.lock = threading.Lock()
        self._shutdown = False
        self.result_saver = LinkSaver(save_file, 'a')
        self.captcha = FoodMakerExtendLock(threadcnt - 1)
        self.last_page = last_page
        self.total_page = total_page

    def dispatch(self):
        if self.last_page is not None and self.last_page <= self.total_page:
            for page in range(self.last_page, self.total_page + 1):
                self.add_main_job({'type': 'list', 'url': 'http://www.bjcourt.gov.cn/cpws/index.htm?page=%s' % page})
        else:
            self.add_main_job({'type': 'main', 'url': 'http://www.bjcourt.gov.cn/cpws/index.htm'})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def with_sleep_request_url(self, url, **kwargs):
        time.sleep(self.sleep)
        return self.request_url(url, **kwargs)

    def _dec_worker(self):
        self.captcha.decrease()
        super(BjListSpider, self)._dec_worker()

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        if self._shutdown:
            return
        jt = jobid['type']
        url = jobid['url']
        time.sleep(2)

        con = self.with_sleep_request_url(url, timeout=10)
        if self.check_exception(con, jobid):
            return
        m = re.search('yzmInput', con.text)
        if m:
            print self.get_tid(), url, ' need captcha'
            con = self.resolve_captcha(url)
            if self.check_exception(con, jobid):
                return
            if re.search(r'yzmInput', con.text):
                self._shutdown = True
                self.link_saver.add('%d,%d,%s' % (2, 0, url))
                return

        if 'main' == jt:
            m = re.search(ur'您搜到了\s*<em>([0-9]+)</em>\s*条符合条件的文书', con.text, re.S)
            if not m:
                if re.search(r'yzmInput', con.text):
                    self._shutdown = True
                self.link_saver.add('%d,%d,%s' % (2, 0, url))
                return
            papercnt = int(m.group(1))
            if papercnt <= 0:
                print '哎呀，这里没用文书', url
                with self.lock:
                    self.zero_link_count += 1
                return
            print 'there are %d papers on %s' % (papercnt, url)
            self.link_saver.add('%d,%d,%s' % (1, papercnt, url))
            n_url = url
            if n_url.find('?') < 0:
                n_url += '?'
            elif n_url[-1] != '&':
                n_url += '&'
            for page in range((papercnt + 10) / 20 + 1, 1, -1):
                self.add_job({'type': 'list', 'url': n_url + 'page=%s' % page})

        ids = re.findall(r'\/cpws\/paperView.htm\?id=(\d+)', con.text)
        if not ids or len(ids) == 0:
            print 'cannot find any paper on', url
            return
        print 'add %d papers from %s' % (len(ids), url)
        for id in ids:
            self.result_saver.add(id)

    def split_url(self, url):
        urls = CData.split_param(url)
        for u in urls:
            self.add_job({'type': 'main', 'url': u})

    def event_handler(self, evt, msg, **kwargs):
        super(BjListSpider, self).event_handler(evt, msg, **kwargs)
        if evt == 'DONE':
            self.result_saver.flush()
            msg += 'zero count: %d\n' % self.zero_link_count
            msg += 'captcha times: %d\n' % self.captcha_times
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


if __name__ == '__main__':
    gq = BjListSpider(10, last_page=20379)
    gq.load_proxy('proxy', 9, False)
    gq.run()
