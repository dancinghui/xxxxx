#!/usr/bin/env python
# -*- coding:utf8 -*-
import HTMLParser
import copy
import logging
import os
import re
import time

from _gk_chsi import GkChsiFsxStore
from chsispider import BaseGkChsiFsxSpider
from court.save import LinkSaver
from spider import spider


class GkChsiSpecialPaperStore(GkChsiFsxStore):
    def __int__(self, channel):
        GkChsiFsxStore.__init__(self, channel)

    def extract_content(self):
        m = re.search(r'<form name="recruitOfSpecialtyForm".*?<\/form>', self.get_cur_doc().cur_content, re.S)
        if m:
            return m.group()
        return self.get_cur_doc().cur_content

    def page_time(self):
        return int(time.mktime(list(time.localtime())) * 1000)


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


class GkChsiSpecialSpider(BaseGkChsiFsxSpider):
    """
    学信网阳光高考省市分数线单用户单线程爬虫,抓取高校录取层次对,高校,高校代码,层次

    seeds title:省市,科类,科类代码,层次,层次代码,年份,院校代码,院校名称
    """

    def __init__(self, threadcnt, account, prefix, proxy=None, sleep=0, captcha_limit=50000000,
                 kldms=None, seeds='spec_seeds',
                 recover=False, sleep_max=5, ua='firefox'):
        super(GkChsiSpecialSpider, self).__init__(threadcnt, account, prefix, proxy, sleep, captcha_limit, sleep_max,
                                                  ua)
        self.special_saver = GkChsiSpecialPaperStore('yggk_spec_' + prefix)
        self.detail_saver = GkChsiDetailPaperStore('yggk_detail_' + prefix)
        self.prefix = prefix
        self.seeds = seeds
        if proxy:
            self.set_proxy(proxy)

        self.recover = recover
        self.kldms = kldms
        self.parser = HTMLParser.HTMLParser()
        self.curl_share = None
        self.login()
        self.info_saver = LinkSaver(prefix + '_spec_data')
        self.detail_url_format = 'http://gk.chsi.com.cn/recruit/listWeiciBySpec.do?year=%s&yxdm=%s&zydm=%s&start=%s'

    def dispatch(self):
        with open(self.seeds, 'r') as f:
            for l in f:
                param = l.strip().split(',')
                if len(param) != 8:
                    logging.warn('invalid seeds %s', l)
                    continue
                self.add_main_job(
                    {'wclx': 1, 'yxdm': param[6], 'kldm': param[2], 'bkcc': param[4], 'start': 0, 'years': param[5],
                     'yxmc': param[7].decode('utf-8')})
        time.sleep(2)
        self.wait_q()
        self.add_job(None)

    def handle_job(self, jobid):
        url = 'http://gk.chsi.com.cn/recruit/listSpecBySchool.do'
        # con = self.request_url(url, data={'yxdm': jobid['yxdm']})
        # 发送请求不接受数据
        url1 = 'http://gk.chsi.com.cn/recruit/listSchByYxmc.do'
        con = self.request_url(url1, data=
        {'wclx': 1, 'yxmc': jobid['yxmc'], 'kldm': jobid['kldm'], 'bkcc': jobid['bkcc'], 'start': jobid['start'],
         'years': jobid['years']})
        if not con or not con.text:
            self.on_work_failed(None, jobid, url1)
            return
            # con = self.request_url(url, data=jobid)
        # 服务器需要之前的请求传递参数，因为这个页面只接收两个参数
        con = self.request_url(url, data={'yxdm': jobid['yxdm'], 'start': jobid['start']})
        if not con or not con.text:
            self.on_work_failed(None, jobid, url)
            return
        jtitle = '%s/%s/%s/%s/%s/%s' % (
            jobid['yxdm'], jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['wclx'],
            jobid['start'])

        self.special_saver.save(int(time.time()), jtitle, url, con.text)
        if 0 == jobid['start']:
            m = re.search(ur'共 (\d+) 页', con.text)
            if m:
                pages = int(m.group(1))
                logging.info('found %d pages for %s', pages, str(jobid))
                for page in range(1, pages):
                    data = copy.deepcopy(jobid)
                    data['start'] = page * 20
                    self.add_job(data)
            else:
                logging.warn('failed to parse pages %s', str(jobid))
        specials = self.extract_special(con.text)
        logging.info('found %d specials from', len(specials))
        for zydm, zymc in specials:
            content = self.extract_detail(zydm, zymc, jobid, jtitle, 0)
            if content is None:
                continue
            m = re.search(ur'共 (\d+) 页', content)
            if not m:
                continue
            page_cnt = int(m.group(1))
            if page_cnt <= 1:
                continue
            for p in range(1, page_cnt):
                self.extract_detail(zydm, zymc, jobid, jtitle, p)

    def extract_detail(self, zydm, zymc, jobid, jtitle, page):
        logging.info('parsing special %s,%s', zymc, zydm)
        detail_url = self.detail_url_format % (jobid['years'], jobid['yxdm'], zydm, page * 10)
        detail_content = self.request_url(detail_url)
        if not detail_content or not detail_content.text:
            logging.error('fail to fetch %s', detail_url)
            self.info_saver.append('detail failed:%s,%s' % (str(jobid), detail_url))
            return
        self.detail_saver.save(int(time.time()), '%s/%s/%s' % (jtitle, zydm, page), detail_url, detail_content.text)
        return detail_content.text

    def extract_special(self, content):
        return re.findall(r'<input type="radio" name="zydm" value="([\d\w]*)" class="radio">([^<]*)</td>', content)

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.special_saver.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


if __name__ == '__main__':
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'spec_spider.log'), level=logging.NOTSET,
                        format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                        datefmt='%m/%d %I:%M:%S %p')

    accounts = {'username': 'hubei101', 'password': 'bobo2016', 'prefix': 'hb', 'proxy': None, 'kldms': [1, 5]}
    # accounts = {'username': 'jsu2015', 'password': 'AHO001009', 'prefix': 'jsu', 'proxy': '183.239.167.122:8080'}
    # accounts = {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'proxy': '58.211.13.26:55336',
    #             'kldms': [2, 6]}
    # accounts = {'username': 'akg999', 'password': 'AHO001009', 'prefix': 'sh', 'proxy': '58.211.13.26:55336',
    #             'kldms': [1, 5]}
    job = GkChsiSpecialSpider(1, accounts, accounts['prefix'], accounts['proxy'], 1,
                              kldms=accounts['kldms'], recover=False)
    # job = GkChsiFsxSpider(1, accounts, accounts['prefix'], accounts['proxy'], 1, kldms=accounts['kldms'],captcha_limit=5000000)
    job.run()
