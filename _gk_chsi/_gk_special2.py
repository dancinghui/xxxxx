#!/usr/bin/env python
# -*- coding:utf8 -*-
import HTMLParser
import copy
import logging
import os
import re
import time

from chsispider import BaseGkChsiFsxSpider, GkChsiSpecialPaperStore, ChsiSpecialSpider
from court.save import LinkSaver
from spider import spider


class GkChsiSpecialSpider2(BaseGkChsiFsxSpider):
    """
    学信网阳光高考省市分数线单用户单线程爬虫,抓取高校录取层次对,高校,高校代码,层次

    seeds title:省市,科类,科类代码,层次,层次代码,年份,院校代码,院校名称
    """

    def __init__(self, threadcnt, account, prefix, proxy=None, sleep=0, captcha_limit=50000000,
                 kldms=None, seeds='spec_seeds', year='15', bkccs=None,
                 recover=False, recover_seeds=None, sleep_max=5, ua='firefox'):
        super(GkChsiSpecialSpider2, self).__init__(threadcnt, account, prefix, proxy, sleep, captcha_limit, sleep_max,
                                                   ua)
        if kldms is None:
            kldms = ['5', '1']
        if bkccs is None:
            bkccs = ['1', '2']
        self.special_saver = GkChsiSpecialPaperStore('yggk_spec_' + prefix)
        self.prefix = prefix
        self.seeds = seeds
        if proxy:
            self.set_proxy(proxy)

        self.recover = recover
        self.kldms = kldms
        self.bkccs = bkccs
        self.parser = HTMLParser.HTMLParser()
        self.year = year
        self.info_saver = LinkSaver(prefix + '_spec_data')
        self.recover_seeds = recover_seeds

    def dispatch(self):

        seed_list = []
        if self.recover_seeds:
            with open(self.recover_seeds, 'r') as seeds:
                for seed in seeds:
                    data = eval(seed.strip())
                    if self.special_saver.find_any(self.special_saver.channel + '://' + '%s/%s/%s/%s/%s/%s' % (
                            data['yxdm'], data['years'], data['kldm'], data['bkcc'], data['wclx'], data['start'])):
                        seed_list.append(data)
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
                            'years': param[5],
                            'yxmc': param[7].decode('utf-8')}

                if self.recover and self.special_saver.find_any(
                                        self.special_saver.channel + '://' + '%s/%s/%s/%s/%s/%s' % (
                                data['yxdm'], data['years'], data['kldm'], data['bkcc'], data['wclx'],
                                data['start'])):
                    continue
                seed_list.append(data)
        print 'remain seeds:', len(seed_list)
        for kldm in self.kldms:
            for bkcc in self.bkccs:
                self.post_kldm_bkcc_for_session(kldm, bkcc)
                print 'loading for ', kldm, bkcc
                for seed in seed_list:
                    if self.year == seed['years'] and seed['kldm'] == kldm and seed['bkcc'] == bkcc:
                        self.add_main_job(seed)
                print 'recover %s seeds' % len(seed_list)
                time.sleep(2)
                self.wait_q()
        self.add_job(None)

    def handle_job(self, jobid):
        url = 'http://gk.chsi.com.cn/recruit/listSpecBySchool.do'
        # con = self.request_url(url, data={'yxdm': jobid['yxdm']})
        # 服务器需要之前的请求传递参数，因为这个页面只接收两个参数
        con = self.request_url(url, data={'yxdm': jobid['yxdm'], 'start': jobid['start']})
        if not con:
            self.on_work_failed(None, jobid, url)
            return
        if self._check_result(con.text, jobid, url):
            '''exceptions is found'''
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
                    data['start'] = page * 32
                    self.add_job(data)
            else:
                logging.warn('failed to parse pages %s', str(jobid))

    def extract_special(self, content):
        return re.findall(r'<input type="radio" name="zydm" value="([\d\w]*)" class="radio">([^<]*)</td>', content)

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.special_saver.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


class GkChsiSpecialSpiderCaptcha(BaseGkChsiFsxSpider):
    """
    学信网阳光高考省市分数线单用户单线程爬虫,抓取高校录取层次对,高校,高校代码,层次

    seeds title:省市,科类,科类代码,层次,层次代码,年份,院校代码,院校名称
    """

    def __init__(self, threadcnt, account, prefix, proxy=None, sleep=0, captcha_limit=50000000,
                 kldms=None, seeds='spec_seeds', year='15', bkccs=None, session_life=600, sleep_internal=1200,
                 recover=False, recover_seeds='recover_seeds', sleep_max=5, ua='firefox'):
        super(GkChsiSpecialSpiderCaptcha, self).__init__(threadcnt, account, prefix, proxy, sleep, captcha_limit,
                                                         sleep_max,
                                                         ua)
        if kldms is None:
            kldms = ['5', '1']
        if bkccs is None:
            bkccs = ['1', '2']
        self.special_saver = GkChsiSpecialPaperStore('yggk_spec_' + prefix)
        self.prefix = prefix
        self.seeds = seeds
        if proxy:
            self.set_proxy(proxy)
        self.session_life = session_life
        self.recover = recover
        self.kldms = kldms
        self.bkccs = bkccs
        self.parser = HTMLParser.HTMLParser()
        self.year = year
        self.info_saver = LinkSaver(prefix + '_spec_data')
        self.detail_url_format = 'http://gk.chsi.com.cn/recruit/listWeiciBySpec.do?year=%s&yxdm=%s&zydm=%s&start=%s'
        self.recover_seeds = recover_seeds
        self.sleep_internal = sleep_internal

    def dispatch(self):
        for kldm in self.kldms:
            for bkcc in self.bkccs:
                self.post_kldm_bkcc_for_session(kldm, bkcc)
                if self.recover and self.recover_seeds:
                    seed_list = []
                    with open(self.recover_seeds, 'r') as seeds:
                        for seed in seeds:
                            data = eval(seed.strip())
                            if self.year == data['years'] and data['kldm'] == kldm and data['bkcc'] == bkcc:
                                seed_list.append(data)
                    for seed in seed_list:
                        self.add_main_job(seed)
                    print 'recover %s seeds' % len(seed_list)
                else:
                    with open(self.seeds, 'r') as f:
                        for l in f:
                            param = l.strip().split(',')
                            if len(param) != 8:
                                logging.warn('invalid seeds %s', l)
                                continue
                            if self.year == param[5] and param[2] == kldm and param[4] == bkcc:
                                self.add_main_job(
                                    {'wclx': 1, 'yxdm': param[6], 'kldm': param[2], 'bkcc': param[4], 'start': 0,
                                     'years': param[5],
                                     'yxmc': param[7].decode('utf-8')})
                time.sleep(2)
                self.wait_q()
        self.add_job(None)

    def check_login(self):
        t = time.time() - self.login_time
        if t >= self.session_life:
            self.logout()
            time.sleep(self.sleep_internal)
            print '我已经睡了', self.sleep_internal / 60.0, '分钟'
            logging.info('我已经睡了%s分钟', self.sleep_internal / 60)
            self.login()

    def handle_job(self, jobid):
        self.check_login()
        url = 'http://gk.chsi.com.cn/recruit/listSpecBySchool.do'
        # con = self.request_url(url, data={'yxdm': jobid['yxdm']})
        # 服务器需要之前的请求传递参数，因为这个页面只接收两个参数
        con = self.request_url(url, data={'yxdm': jobid['yxdm'], 'start': jobid['start']})
        if not con:
            self.on_work_failed(None, jobid, url)
            return
        if not self._check_result(con.text, jobid, url):
            '''exception is found'''
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
                    data['start'] = page * 32
                    self.add_job(data)
            else:
                logging.warn('failed to parse pages %s', str(jobid))

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
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'spider.spec.log'), level=logging.NOTSET,
                        format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                        datefmt='%m/%d %I:%M:%S %p')

    # accounts = {'username': 'hubei101', 'password': 'bobo2016', 'prefix': 'hb', 'proxy': None, 'kldms': [1, 5]}
    # accounts = {'username': 'jsu2015', 'password': 'AHO001009', 'prefix': 'jsu', 'proxy': '183.239.167.122:8080'}
    # accounts = {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'proxy': '58.211.13.26:55336',
    #             'kldms': [2, 6]}
    # accounts = {'username': 'akg999', 'password': 'AHO001009', 'prefix': 'sh', 'proxy': '58.211.13.26:55336',
    accounts = {'username': 'start0945', 'password': 'AHO001009', 'prefix': 'nm',
                'proxy': '192.168.1.39:3428', 'kldms': ['5', '1'], 'score': 750, 'thcnt': 2,
                'sleep': 1.0,
                'bkccs': ['1', '2']}
    #             'kldms': [1, 5]}
    # kldms = BaseGkChsiFsxSpider.get_kldms(accounts, accounts['prefix'])
    # print 'new kldms', kldms
    # if len(kldms) == 2:
    #     accounts['kldms',] = [kldms[0][0], kldms[1][0]]
    # gen_sch_seeds(accounts['score'], 'sch.seeds.' + accounts['prefix'], accounts['kldms'])
    job = ChsiSpecialSpider(accounts['thcnt'], accounts, accounts['prefix'], accounts['proxy'], accounts['sleep'],
                            kldms=accounts['kldms'],
                            recover=False, seeds='spec.seeds.%s' % accounts['prefix'],
                            captcha_limit=5000000)
    # job = GkChsiFsxSpider(1, accounts, accounts['prefix'], accounts['proxy'], 1, kldms=accounts['kldms'],captcha_limit=5000000)
    job.run()
