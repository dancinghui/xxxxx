#!/usr/bin/env python
# -*- coding:utf8 -*-
import logging
import re
import threading
import time

import spider.genquery
from bjspider import BJCourtStore, CData, BJSpider, ProxySwapSpider, StatisticsItem
from court.cspider import CourtSpider
from court.save import LinkSaver, LinkDb
from court.sessionrequests import ATOSSessionRequests
from spider import spider


class BJCourtSpider(BJSpider):
    """Spider which crawl legal instrument from http://www.bjcourt.gov.cn"""

    def __init__(self, thcnt, mode='all', sleep=0.0, seeds=None, recover=False):
        super(BJCourtSpider, self).__init__(thcnt, 'BeijingCourtSpider')
        self.pagestore = BJCourtStore()
        self.sleep = sleep
        self.mode = mode
        self.seeds = seeds
        self.recover = recover
        self.total_content_failed = 0
        self.content_failed_lock = threading.Lock()
        self.failed_link_db = LinkDb('bj_failed')
        self.error_count = StatisticsItem()

        # test parameters
        logging.info('%s,threads=%d,lo=%s,sleep=%d,ls=%s' % (self._name, thcnt, mode, sleep, seeds))

    @staticmethod
    def get_paper_seeds(seed_lines):
        seeds = []
        for seed in seed_lines:
            if re.match('^\d+$', seed):
                seeds.append(seed)
                continue
            m = re.match(r'^http:\/\/www\.bjcourt\.gov\.cn\/cpws\/paperView\.htm\?id=(\d+)$', seed)
            if m:
                seeds.append(m.group(1))
        return seeds

    @staticmethod
    def get_list_seeds(seed_lines):
        seeds = []
        for seed in seed_lines:
            if re.match(r'http:\/\/www\.bjcourt\.gov\.cn\/cpws\/index\.htm.*', seed):
                seeds.append(seed)
        return seeds

    def load_seeds(self):
        lines = []
        with open(self.seeds, 'r') as seedfile:
            for line in seedfile:
                lines.append(line.strip())
        return lines

    def dispatch(self):
        if self.seeds:
            lines = self.load_seeds()
            all_seeds = []
            if self.mode == 'paper' or self.mode == 'all':
                seeds = BJCourtSpider.get_paper_seeds(lines)
                for seed in seeds:
                    url = str('http://www.bjcourt.gov.cn/cpws/paperView.htm?id=%s' % seed)
                    if not self.failed_link_db.has_any(
                                            self.failed_link_db.channel + '://' + seed) \
                            and (not self.recover or not self.pagestore.find_any(
                                        self.pagestore.channel + '://' + seed)):
                        all_seeds.append(
                            {'type': 'paper', 'url': url})
            if self.mode == 'list' or self.mode == 'all':
                seeds = BJCourtSpider.get_list_seeds(lines)
                for seed in seeds:
                    all_seeds.append(
                        {'type': 'list', 'url': seed})
            print 'add', len(all_seeds), 'seeds'
            for seed in all_seeds:
                self.add_main_job(seed)
        else:
            self.add_main_job({'type': 'main', 'url': 'http://www.bjcourt.gov.cn/cpws/index.htm'})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def check_and_solve_blocking(self, content, url):
        if re.search(u'您访问的频率太高，请稍后再试', content):
            if self.test_mode:
                self._shutdown_in_test = True
                print '您访问的频率太高，请稍后再试'
                print 'run time ', (time.time() - self._start_timet)
            self.wait_to_reset()
            logging.error('spider has been block,%s' % url)
            return True
        return False

    def on_exception(self):
        self.error_count.add()
        if self.error_count.count() > 100:
            self.change_proxy()
            self.error_count.reset()

    def run_job(self, jobid):
        if self._shutdown:
            return
        if self.test_mode and self._shutdown_in_test:
            # do nothing in test mode when shutdown is True
            return

        jt = jobid['type']
        url = jobid['url']
        if 'paper' == jt:
            con = self.request_url(url)
            print url
            if self.check_exception(con, jobid):
                self.on_exception()
                return
            con = self.check_captcha(url, con, jobid)
            if con is None:
                self.re_add_job(jobid)
                return
            self.error_count.reset()
            m = re.search(r'<div class="grid_layout_920 m0_auto">(.*)<!-- grid_layout_578 end-->', con.text, re.S)
            if m:
                context = m.group(1).strip()
                jid = re.search('id=(\d+)', url)
                if jid:
                    jid = jid.group(1)
                    self.pagestore.save(int(time.time()), jid, url, context)
                else:
                    logging.warn('paper not save,paper id not found for %s' % url)
                logging.info('%s => %s' % (url, len(context)))
            else:
                print 'fail to find content for:', url
                with self.content_failed_lock:
                    self.total_content_failed += 1
                    self.current_failed.add()
                    if self.current_failed.count() > 20:
                        print con.headers
                        m = re.search(r'<span class="info">.*?</span>', con.text)
                        if m:
                            print m.group()
                        else:
                            print 'invalid page', con.text[:20]
                        self.wait_to_reset()
                    if self.current_failed.count() > 50:
                        self.change_proxy()
                        self.current_failed.reset()
                    if u'页面未找到' in con.text:
                        jid = re.search('id=(\d+)', url)
                        jid = jid.group(1)
                        self.failed_link_db.save(url, jid, str({'msg': 'page not found'}), int(time.time()))
                    else:
                        self.re_add_job(jobid)
            return

        con = self.request_url(url)
        if self.check_exception(con, jobid):
            self.on_exception()
            return
        con = self.check_captcha(url, con, jobid)
        if con is None:
            self.re_add_job(jobid)
            return
        self.error_count.reset()
        if 'main' == jt:
            m = re.search('yzmInput', con.text)
            if m:
                print self.get_tid(), url, ' need captcha'
                self.split_url(url)
                logging.info('need captcha %s' % url)
                return
            m = re.search(ur'您搜到了\s*<em>([0-9]+)</em>\s*条符合条件的文书', con.text, re.S)
            if not m:
                yzm = re.search(ur'验证码', con.text)
                if yzm:
                    self._shutdown = True
                else:
                    if self.check_and_solve_blocking(con.text, url):
                        self.re_add_job(jobid)
                    print 'Cannot find paper count from', url
                return
            papercnt = int(m.group(1))
            if papercnt <= 0:
                return
            if papercnt > 200:
                self.split_url(url)
                return
            if not re.search('\?', url):
                url += '?'
            if url[-1] != '?' and url[-1] != '&':
                url += '&'
            logging.info('paper count=%d,%s' % (papercnt, url))
            for page in range(2, (papercnt + 19) / 20 + 1):
                self.add_job({'type': 'list', 'url': str(url + ('page=%s' % page))})
        urls = re.findall(r'<a href="/cpws/paperView.htm\?id=([0-9]+)"[^>]*>', con.text)
        urls = spider.util.unique_list(urls)
        logging.info('%d paper found on %s' % (len(urls), url))
        if 0 == len(urls):
            print 'there are no papers on ', url
        else:
            print url, '===> ', len(urls), ' paper'
            for id in urls:
                self.link_saver.add(id)
            for id in urls:
                self.add_job(
                    {'type': 'paper', 'url': str('http://www.bjcourt.gov.cn/cpws/paperView.htm?id=%s' % id)})

    def wait_to_reset(self):
        """
        wait to reset session and proxy
        """
        # self.reset_session()
        pass

    def split_url(self, url):
        urls = CData.split_param(url)
        for u in urls:
            self.add_job({'type': 'main', 'url': u})

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            msg += "content failed: %d\n" % self.total_content_failed
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass

    def extract_paper_id(self, l):
        m = re.search(r'id=([\d\w]+)', l)
        if m:
            return m.group(1)
        else:
            return ''


def test_split_date():
    urls = [
        'http://www.bjcourt.gov.cn/cpws/index.htm?jbfyId=29&ajlb=1&sxnflx=2&startCprq=2014-08-18&endCprq=2014-09-17',
        'http://www.bjcourt.gov.cn/cpws/index.htm?jbfyId=29&ajlb=1&sxnflx=2&startCprq=2014-08-18&endCprq=2015-09-17',
        'http://www.bjcourt.gov.cn/cpws/index.htm?jbfyId=29&ajlb=1&sxnflx=2&startCprq=&endCprq=',
        'http://www.bjcourt.gov.cn/cpws/index.htm?jbfyId=30&ajlb=3&sxnflx=2',
        'http://www.bjcourt.gov.cn/cpws/index.htm',
        'http://www.bjcourt.gov.cn/cpws/index.htm?jbfyId=29&ajlb=1&sxnflx=2&startCprq=2014-08-18&endCprq=',
        'http://www.bjcourt.gov.cn/cpws/index.htm?jbfyId=29&ajlb=1&sxnflx=2&startCprq=&endCprq=2014-09-17',
        'http://www.bjcourt.gov.cn/cpws/index.htm?jbfyId=29&ajlb=1&sxnflx=2&startCprq=2014-08-18&endCprq=2014-08-25',
        'http://www.bjcourt.gov.cn/cpws/index.htm?jbfyId=19&ajlb=2&sxnflx=2&startCprq=2014-12-31&endCprq=2015-12-31'
    ]
    for url in urls:
        print url
        print '----'
        res = CData.split_time(url)
        for r in res:
            print r
        print '===='


def request_in_one_second(count):
    sleep_time = 1.0 / count
    rq = ATOSSessionRequests()
    rq.set_proxy('101.200.181.36:3128')
    s = time.time()
    for i in range(count * 10):
        # con = rq.request_url('http://gk.chsi.com.cn')
        con = rq.request_url(
            'http://www.bjcourt.gov.cn/cpws/index.htm?jbfyId=29&ajlb=1&sxnflx=2&&&startCprq=1996-12-30&endCprq=1997-12-30')
        if con:
            print con.text
        else:
            print None
        print '----------------------------'
        time.sleep(sleep_time)
    print '====================='
    print time.time() - s


def test_server_request_limit():
    pass


if '__main__' == __name__:
    # # CurlReq.DEBUGREQ = 0
    # # LOG_FILENAME = 'spider.log'
    # # job = BJCourtSpider(1, True, 2)
    # # job.test_mode = True
    # # job.load_proxy('proxy2')
    # # # job.set_proxy('192.168.1.45:3428')
    # # job.run()
    # # test_split_date()

    count = 1
    while count > 0:
        count -= 1
        try:
            job = BJCourtSpider(8, sleep=0.5, mode='paper', seeds='seeds', recover=True)
            # job = ProxyBJCourtSpider(10, sleep=0, list_seeds='links', recover=True, proxy_life=600)
            # # job.test_mode = True
            job.load_proxy('proxy', 0, auto_change=False)
            # # job.test_mode = True
            # # job.set_proxy('192.168.1.39:3428')
            job.run()
            time.sleep(300)
        except Exception as e:
            msg = str(type(e)) + '\n'
            msg += e.message + '\n'
            spider.util.sendmail(['shibaofeng@ipin.com'], 'Beijing Spider Failed:%d' % count, msg)
