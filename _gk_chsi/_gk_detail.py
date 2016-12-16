#!/usr/bin/env python
# -*- coding:utf8 -*-
import HTMLParser
import copy
import logging
import os
import re
import time

from _gk_chsi import GkChsiFsxStore
from court.save import LinkSaver
from chsispider import BaseGkChsiFsxSpider, ChsiSpider, ChsiDetailSpider
from spider import spider
from spider.ipin.savedb import PageStoreBase


class GkChsiDetailPaperStore(GkChsiFsxStore):
    def __int__(self, channel):
        GkChsiFsxStore.__init__(self, channel)

    def extract_content(self):
        m = re.search(r'<table width="100%" border="0" align="center" cellpadding="0" cellspacing="0">.*?<\/table>',
                      self.get_cur_doc().cur_content, re.S)
        if m:
            return m.group()
        return self.get_cur_doc().cur_content

    def page_time(self):
        return int(time.mktime(list(time.localtime())) * 1000)


class GkChsiDetailSpider(BaseGkChsiFsxSpider):
    """
        学信网阳光高考省市分数线单用户单线程爬虫,抓取高校录取层次对,高校,高校代码,层次

        seeds title:省市,科类,科类代码,层次,层次代码,年份,院校代码,院校名称
        """

    def __init__(self, threadcnt, account, prefix, proxy=None, sleep=0.0, captcha_limit=50000000, seeds='detail_seeds',
                 recover=False, sleep_max=5, ua='firefox', year='15', bkccs=None, kldms=None):
        super(GkChsiDetailSpider, self).__init__(threadcnt, account, prefix, proxy, sleep, captcha_limit, sleep_max,
                                                 ua)
        if kldms is None:
            kldms = ['5', '1']
        if bkccs is None:
            bkccs = ['1', '2']
        self.pagestore = GkChsiDetailPaperStore('yggk_detail_' + prefix)
        self.prefix = prefix
        self.seeds = seeds
        if proxy:
            self.set_proxy(proxy)
        self.kldms = kldms
        self.bkccs = bkccs
        self.recover = recover
        self.parser = HTMLParser.HTMLParser()
        self.info_saver = LinkSaver(prefix + '_detail_data')
        self.year = year
        self.detail_url_format = 'http://gk.chsi.com.cn/recruit/listWeiciBySpec.do?year=%s&yxdm=%s&zydm=%s&start=%s'

    def dispatch(self):
        for kldm in self.kldms:
            for bkcc in self.bkccs:
                self.post_kldm_bkcc_for_session(kldm, bkcc)
                seeds = []
                with open(self.seeds, 'r') as f:
                    for l in f:
                        if l[0] == '{':
                            data = eval(l.strip())
                        else:
                            param = l.strip().split(',')
                            if len(param) != 8:
                                logging.warn('invalid seeds %s', l)
                                continue
                            data = {'wclx': 1, 'yxdm': param[6], 'kldm': param[2], 'bkcc': param[4], 'start': 0,
                                    'years': param[5], 'zydm': param[7], 'zymc': param[8].encode('utf-8')}
                        if data['kldm'] == kldm and bkcc == data['bkcc'] and self.year == data[
                            'years']:
                            if self.recover and self.pagestore.find_any(
                                                    self.pagestore.channel + '://' + self.get_jobid(data)):
                                continue
                            seeds.append(data)
                for seed in seeds:
                    self.add_main_job(seed)
                print 'add', len(seeds), 'jobs'
                time.sleep(2)
                self.wait_q()
        self.add_job(None)

    def handle_job(self, jobid):
        content = self.extract_detail(jobid)
        if 0 == jobid['start']:
            if content is None:
                return
            m = re.search(ur'共 (\d+) 页', content)
            if not m:
                return
            page_cnt = int(m.group(1))
            if page_cnt <= 1:
                return
            for p in range(1, page_cnt):
                job = copy.deepcopy(jobid)
                job['start'] = p * 10
                self.add_job(job)

    def get_jobid(self, jobid):
        return '%s/%s/%s/%s/%s/%s/%s/%s' % (
            jobid['yxdm'], jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['wclx'],
            jobid['start'], jobid['zydm'], int(jobid['start']) / 10)

    def extract_detail(self, jobid):
        logging.info('parsing special %s,%s', jobid['zymc'], jobid['zydm'])
        detail_url = self.detail_url_format % (jobid['years'], jobid['yxdm'], jobid['zydm'], jobid['start'])
        detail_content = self.request_url(detail_url)
        if not detail_content or not detail_content.text:
            logging.error('fail to fetch %s', detail_url)
            self.info_saver.append('detail failed:%s,%s' % (str(jobid), detail_url))
            return
        jtitle = '%s/%s/%s/%s/%s/%s' % (
            jobid['yxdm'], jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['wclx'],
            jobid['start'])
        self.pagestore.save(int(time.time()), '%s/%s/%s' % (jtitle, jobid['zydm'], int(jobid['start']) / 10),
                            detail_url, detail_content.text)
        return detail_content.text

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


class GkChsiDetailSpider2(BaseGkChsiFsxSpider):
    """
    学信网阳光高考省市分数线单用户单线程爬虫,抓取高校录取层次对,高校,高校代码,层次

    seeds title:省市,科类,科类代码,层次,层次代码,年份,院校代码,院校名称
    """

    def __init__(self, threadcnt, account, prefix, proxy=None, sleep=0.0, captcha_limit=50000000, seeds='detail_seeds',
                 recover=False, sleep_max=5, ua='firefox', year='15', bkccs=None, kldms=None):
        super(GkChsiDetailSpider2, self).__init__(threadcnt, account, prefix, proxy, sleep, captcha_limit, sleep_max,
                                                  ua)
        if kldms is None:
            kldms = ['5', '1']
        if bkccs is None:
            bkccs = ['1', '2']
        self.pagestore = GkChsiDetailPaperStore('yggk_detail_' + prefix)
        self.prefix = prefix
        self.seeds = seeds
        if proxy:
            self.set_proxy(proxy)
        self.kldms = kldms
        self.bkccs = bkccs
        self.recover = recover
        self.parser = HTMLParser.HTMLParser()
        self.info_saver = LinkSaver(prefix + '_detail_data')
        self.year = year
        self.detail_url_format = 'http://gk.chsi.com.cn/recruit/listWeiciBySpec.do?year=%s&yxdm=%s&zydm=%s&start=%s'

    def dispatch(self):
        for kldm in self.kldms:
            for bkcc in self.bkccs:
                self.post_kldm_bkcc_for_session(kldm, bkcc)
                seeds = []
                with open(self.seeds, 'r') as f:
                    for l in f:
                        if l[0] == '{':
                            data = eval(l.strip())
                        else:
                            param = l.strip().split(',')
                            if len(param) != 8:
                                logging.warn('invalid seeds %s', l)
                                continue
                            data = {'wclx': 1, 'yxdm': param[6], 'kldm': param[2], 'bkcc': param[4], 'start': 0,
                                    'years': param[5], 'zydm': param[7], 'zymc': param[8].encode('utf-8')}
                        if data['kldm'] == kldm and bkcc == data['bkcc'] and self.year == data[
                            'years'] and not self.pagestore.find_any(
                                            self.pagestore.channel + '://' + self.get_jobid(data)):
                            seeds.append(data)
                for seed in seeds:
                    self.add_main_job(seed)
                print 'add', len(seeds), 'jobs'
                time.sleep(2)
                self.wait_q()
        self.add_job(None)

    def handle_job(self, jobid):
        content = self.extract_detail(jobid)
        if 0 == jobid['start']:
            if content is None:
                return
            m = re.search(ur'共 (\d+) 页', content)
            if not m:
                return
            page_cnt = int(m.group(1))
            if page_cnt <= 1:
                return
            for p in range(1, page_cnt):
                job = copy.deepcopy(jobid)
                job['start'] = p * 10
                self.add_job(job)

    def get_jobid(self, jobid):
        return '%s/%s/%s/%s/%s/%s/%s/%s' % (
            jobid['yxdm'], jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['wclx'],
            jobid['start'], jobid['zydm'], int(jobid['start']) / 10)

    def extract_detail(self, jobid):
        logging.info('parsing special %s,%s', jobid['zymc'], jobid['zydm'])
        detail_url = self.detail_url_format % (jobid['years'], jobid['yxdm'], jobid['zydm'], jobid['start'])
        detail_content = self.request_url(detail_url)
        if not detail_content or not detail_content.text:
            logging.error('fail to fetch %s', detail_url)
            self.info_saver.append('detail failed:%s,%s' % (str(jobid), detail_url))
            return
        jtitle = '%s/%s/%s/%s/%s/%s' % (
            jobid['yxdm'], jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['wclx'],
            jobid['start'])
        self.pagestore.save(int(time.time()), '%s/%s/%s' % (jtitle, jobid['zydm'], int(jobid['start']) / 10),
                            detail_url, detail_content.text)
        return detail_content.text

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


if __name__ == '__main__':
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'detail.spider.log.hb.1'), level=logging.NOTSET,
                        format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                        datefmt='%m/%d %I:%M:%S %p')

    accounts = {'username': 'start0945', 'password': 'AHO001009', 'prefix': 'nm',
                'proxy': 'https://ipin:ipin1234@106.75.134.189:18888', 'kldms': ['5', '1'],
                'bkccs': ['1', '2'], 'seeds': 'detail.seeds.nm'}
    # accounts = {'username': 'jsu2015', 'password': 'AHO001009', 'prefix': 'jsu', 'proxy': '183.239.167.122:8080'}
    # accounts = {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'proxy': '58.211.13.26:55336',
    #             'kldms': [2, 6]}
    # accounts = {'username': 'akg999', 'password': 'AHO001009', 'prefix': 'sh', 'proxy': '58.211.13.26:55336',
    #             'kldms': [1, 5]}
    # seeds = 'detail.seeds.hb.2.1'
    # seeds = 's.1'
    job = ChsiDetailSpider(2, accounts, accounts['prefix'], accounts['proxy'], sleep=1.0, recover=True,
                           kldms=accounts['kldms'], bkccs=accounts['bkccs'], seeds=accounts['seeds'])
    job.run()
