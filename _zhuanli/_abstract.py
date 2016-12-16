#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import time

import pycurl

from court.save import LinkDb, FailedJobSaver
from court.util import KuaidailiProxyManager
from spider.httpreq import CurlReq
from spider.ipin.savedb import PageStoreBase
from zlspider import ZhuanliBaseSpider, ZhuanliBaseStore


class PatentAbstractStore(ZhuanliBaseStore):
    def __init__(self, channel='abs_list'):
        ZhuanliBaseStore.__init__(self, channel)

    def extract_content(self):
        m = re.search(r'<div class="w790 right">.*<div class="next">', self.get_cur_doc().cur_content, re.S)
        if m:
            return m.group()
        return self.get_cur_doc().cur_content

    def page_time(self):
        return int(time.time() * 1000)


class PatentAbstractSpider(ZhuanliBaseSpider):
    """专利摘要爬虫"""

    def __init__(self, thcnt, recover=False, seeds='seed.dat'):
        ZhuanliBaseSpider.__init__(self, thcnt, recover)
        self.seeds = seeds
        self.page_size = 10  # 3或者10
        self.pagestore = PatentAbstractStore('abs_list')
        self.failed_saver = FailedJobSaver('failed_job.txt')

    def dispatch(self):
        self.failed_saver.tag()
        seeds = []
        with open(self.seeds, 'r') as f:
            for s in f:
                v = self.parse_seed(s)
                if len(v) == 0:
                    continue
                id = self.extract_seed_id(v[0], v[1], v[2])
                pcnt = (int(v[2]) + self.page_size / 2) / self.page_size
                page = 1
                if self.recover:
                    while page <= pcnt:
                        if not self.pagestore.find_any(self.pagestore.channel + '://%s/%d' % (id, page)):
                            break
                        page += 1
                if page <= pcnt:
                    seeds.append(
                        {'type': 'pub', 'pub': v[0], 'app': v[1], 'index': page, 'count': v[2], 'pages': pcnt})
        print 'load %s seeds' % len(seeds)
        for seed in seeds:
            self.add_main_job(seed)
        time.sleep(2)
        self.wait_q()
        self.add_job(None)

    @staticmethod
    def extract_seed_id(pub, app, count):
        return '%s-%s/%s-%s/%s' % (
            pub[0], pub[1], app[0] if (app[0] != '-') else '', app[1] if (app[1] != '-') else '', count)

    @staticmethod
    def parse_seed(seed):
        v = seed.split(',')
        if len(v) != 7:
            print 'invalid seed', seed
            return []
        return [[v[1][1:], v[2][:-1]], [v[3][1:], v[4][:-1]], int(v[6])]

    @staticmethod
    def get_query_word(jobid):
        word = '公开（公告）日=BETWEEN[\'' + jobid['pub'][0] + '\',\'' + jobid['pub'][1] + '\']'
        if jobid['app'][0] != '-' and jobid['app'][1] != '-':
            word += ' AND 申请日=BETWEEN[\'' + jobid['app'][0] + '\',\'' + jobid['app'][1] + '\']'
        return word

    def _on_shutdown(self, jobid):
        self.failed_saver.save(str(jobid))
        return

    def run_job(self, jobid):
        while jobid['index'] <= jobid['pages']:
            if self.check_shutdown(jobid):
                return
            strword = self.get_query_word(jobid)
            url = self.form_query_url(strword, page=jobid['index'], size=self.page_size)
            time.sleep(self.sleep)
            try:
                con = self.request_url(url, timeout=self.timeout)
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
                    if count <= 0 or not proxies.has_key('data') or not proxies['data'].has_key('count') or \
                                    proxies['data'][
                                        'count'] <= 0:
                        self._shutdown()
                        return
                    print 'load %d proxies from kuaidaili' % proxies['data']['count']
                    self.set_proxy(proxies['data']['proxy_list'], 15 if (proxies['data']['count'] > 15) else 0)
                    return
                else:
                    raise
            if self.check_exception(con, jobid):
                print 'exception encounter', jobid
                return
            if re.search(u'<title>错误页面</title>', con.text):
                print '错误页面', jobid
                if not self.re_add_job(jobid):
                    self.failed_saver.save(str(jobid))
                return
            self.check_state()
            self.pagestore.save(int(time.time()),
                                self.extract_seed_id(jobid['pub'], jobid['app'], jobid['count']) + '/' + str(
                                    jobid['index']), url, con.text)
            jobid['index'] += 1
            jobid['_failcnt_'] = 0


if __name__ == '__main__':
    CurlReq.DEBUGREQ = 1
    job = PatentAbstractSpider(10, recover=True)
    # proxies = KuaidailiProxyManager.load_proxy(30)
    # print 'load %d proxies from kuaidaili' % proxies['data']['count']
    # if proxies['data']['count'] > 0:
    #     job.set_proxy(proxies['data']['proxy_list'], 15 if (proxies['data']['count'] > 15) else 0)
    job.set_proxy('192.168.1.39:3428:ipin:helloipin', 0)
    job.timeout = 60
    # job.set_proxy('106.75.134.189:18888:ipin:ipin1234', 0)
    # job.load_proxy('proxy')
    job.run()
