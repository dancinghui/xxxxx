#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import datetime
import random
import re
import time

import pycurl

from court.save import LinkSaver
from court.util import KuaidailiProxyManager
from spider import spider
from spider.httpreq import CurlReq
from spider.savebin import FileSaver
from zlspider import ZhuanliBaseSpider


def date_split(start, end):
    if start == end:
        return [[start, end]]
    st = datetime.datetime.strptime(start, '%Y.%m.%d')
    et = datetime.datetime.strptime(end, '%Y.%m.%d')
    delta = et - st
    if 2 < delta.days:
        days = delta.days / 2
        mt1 = st + datetime.timedelta(days=days)
        mt2 = st + datetime.timedelta(days=(days + 1))
        mid1 = mt1.strftime('%Y.%m.%d')
        mid2 = mt2.strftime('%Y.%m.%d')
        return [[start, mid1], [mid2, end]]
    elif 2 == delta.days:
        mt1 = st + datetime.timedelta(days=1)
        mid1 = mt1.strftime('%Y.%m.%d')
        return [[start, mid1], [end, end]]
    elif 1 == delta.days:
        return [[start, start], [end, end]]
    return [[start, end]]


ua = [
    'firefox',
    '=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36 Vivaldi/1.1.453.59',
    '=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:46.0) Gecko/20100101 Firefox/46.0',
    '=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36',
    '=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0',
    '=Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)',
    '=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36',
    '=Opera/9.80 (Windows NT 6.2; Win64; x64) Presto/2.12.388 Version/12.17',
    '=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:45.0) Gecko/20100101 Firefox/45.0',
    '=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36'
    '=Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60'
]


class ListSeedGenQueries(ZhuanliBaseSpider):
    def __init__(self, thcnt=4, limit=5000, recover=False):
        super(ListSeedGenQueries, self).__init__(thcnt)
        self.bs2 = FileSaver("failed_urls.txt")
        self.limit = limit
        self.test_mode = False
        self.sf = LinkSaver('seed.dat', 'a')
        self.failed_jobs = LinkSaver('seed.failed.dat', 'w')
        self.count = 0
        self.failed = 0
        self.sleep = 0
        self.recover = recover
        self.timeout = 60
        self.today = datetime.datetime.now().strftime('%Y.%m.%d')
        random.seed = int(time.time())
        self.select_user_agent(ua[2])

    def dispatch(self):
        if self.recover:
            with open('old.failed.dat', 'r') as f:
                for l in f:
                    d = l.strip().split(',', 1)
                    data = eval(d[1])
                    data['_failcnt_'] = 0
                    self.add_main_job(data)
        else:
            self.add_main_job(
                {'type': 'pub', 'pub': ['1985.01.01', self.today], 'app': ['-', '-'], 'level': -1})
        time.sleep(2)
        self.wait_q()
        self.add_job(None)

    @staticmethod
    def get_query_word(jobid):
        word = '公开（公告）日=BETWEEN[\'' + jobid['pub'][0] + '\',\'' + jobid['pub'][1] + '\']'
        if 'pub' != jobid['type']:
            word += ' AND 申请日=BETWEEN[\'' + jobid['app'][0] + '\',\'' + jobid['app'][1] + '\']'
        return word

    def run_job(self, jobid):
        url = self.form_query_url(self.get_query_word(jobid), size=1)
        datestr = self.get_date_str(jobid)
        try:
            res = self.need_split(datestr, jobid['level'], url)
        except RuntimeError as e:
            if 'no proxy' in e.message:
                count = 3
                self.re_add_job(jobid)
                proxies = {}
                while count > 0:
                    proxies = KuaidailiProxyManager.load_proxy(30)
                    if proxies['data']['count'] > 0:
                        break
                    count -= 1
                if count <= 0 or not proxies.has_key('data') or not proxies['data'].has_key('count') or proxies['data'][
                    'count'] <= 0:
                    self._shutdown()
                    return
                print 'load %d proxies from kuaidaili' % proxies['data']['count']
                self.set_proxy(proxies['data']['proxy_list'], 15 if (proxies['data']['count'] > 15) else 0)
                return
            else:
                raise
        if res[0] == 0:
            self.re_add_job(jobid)
            return
        elif res[0] == 1:
            with self.locker:
                self.failed += 1
                self.failed_jobs.add('1,' + str(jobid))
            return
        elif res[0] == 3:
            with self.locker:
                self.count += 1
                self.sf.add('1,%s,%d,%d' % (datestr, jobid['level'], res[1]))
            return
        dates = date_split(jobid[jobid['type']][0], jobid[jobid['type']][1])
        if len(dates) <= 0:
            with self.locker:
                self.failed += 1
                self.failed_jobs.add('0,' + str(jobid))
            return
        if len(dates) == 1:
            if 'pub' == jobid['type']:
                self.add_job({'type': 'app', 'pub': jobid['pub'], 'level': jobid['level'] + 1,
                              'app': ['1985.01.01', '2009.12.31']})
                self.add_job({'type': 'app', 'pub': jobid['pub'], 'level': jobid['level'] + 1,
                              'app': ['2010.01.01', self.today]})
            else:
                with self.locker:
                    self.count += 1
                    self.sf.add('2,%s,%d,%d' % (datestr, jobid['level'], res[1]))
                    print '(%d)%s ==> %s cannot split any more' % (jobid['level'], datestr, res[1])
            return
        level = jobid['level'] + 1
        for d in dates:
            job = copy.deepcopy(jobid)
            job['_failcnt_'] = 0
            job['level'] = level
            job[job['type']] = d
            self.add_job(job)

    @staticmethod
    def get_date_str(jobid):
        return '[%s,%s],[%s,%s]' % (
            jobid['pub'][0], jobid['pub'][1], jobid['app'][0], jobid['app'][1])

    def need_split(self, datestr, level, url):
        # self.select_user_agent(ua[random.randint(0, len(ua) - 1)])
        con = self.request_url(url)
        time.sleep(self.sleep)
        if con is None:
            print 'none response %s' % datestr
            return [0, 0]
        if re.search(u'<title>错误页面</title>', con.text):
            print 'no results %s' % datestr
            return [1, 0]
        counts = re.findall('num\w{4}\.value = "(\d+)";', con.text)
        if len(counts) <= 0:
            print 'invalid pages', datestr
            return [1, 0]
        if self.test_mode:
            print 'counts:', counts
        self.check_state()
        paper_count = 0
        for c in counts:
            paper_count += int(c)
        with self.locker:
            print "[%d][%d]-%s ==> %s %s" % (
                level, paper_count, datestr, len(counts), 'failed' if (paper_count > self.limit) else 'ok')
        if paper_count > self.limit:
            return [2, paper_count]
        return [3, paper_count]

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += 'saved: %d\n' % self.count
            msg += 'failed: %d\n' % self.failed
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s finished' % self._name, msg)


if __name__ == '__main__':
    CurlReq.DEBUGREQ = 0
    job = ListSeedGenQueries(2)
    job.select_user_agent(
        '=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36 Vivaldi/1.1.453.59')
    # job.set_proxy('192.168.1.39:3428', 0)
    job.set_proxy('192.168.1.39:3428:ipin:helloipin', 0)
    # job.set_proxy('106.75.134.190:18888:ipin:ipin1234', 0)
    # job.set_proxy('106.75.134.190:18888:ipin:ipin1234')
    # job.load_proxy('proxy')
    job.recover = True
    job.run()
