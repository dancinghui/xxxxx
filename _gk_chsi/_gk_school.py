#!/usr/bin/env python
# -*- coding:utf8 -*-
import HTMLParser
import copy
import logging
import os
import re
import time

from court.save import LinkSaver
from chsispider import BaseGkChsiFsxSpider, gen_sch_seeds, ChsiSchoolSpider
from spider import spider
from spider.ipin.savedb import PageStoreBase


class GkChsiFsxStore(PageStoreBase):
    def __init__(self, channel, dburl="mongodb://root:helloipin@localhost/admin"):
        PageStoreBase.__init__(self, channel, dburl)

    def extract_content(self):
        return self.get_cur_doc().cur_content

    def page_time(self):
        return int(time.mktime(list(time.localtime())) * 1000)


class GkChsiFsxScoreStore(GkChsiFsxStore):
    def __init__(self, channel):
        GkChsiFsxStore.__init__(self, channel)

    def extract_content(self):
        return self.get_cur_doc().cur_content

    def page_time(self):
        return int(time.mktime(list(time.localtime())) * 1000)


class GkChsiSchoolPaperStore(GkChsiFsxStore):
    def __int__(self, channel):
        GkChsiFsxStore.__init__(self, channel)

    def extract_content(self):
        m = re.search(r'<form name="queryByYxdmForm".*?<\/form>', self.get_cur_doc().cur_content, re.S)
        if m:
            return m.group()
        return self.get_cur_doc().cur_content

    def page_time(self):
        return int(time.mktime(list(time.localtime())) * 1000)


class GkChsiSchoolSpider(BaseGkChsiFsxSpider):
    """
    学信网阳光高考省市分数线单用户单线程爬虫,抓取高校录取层次对,高校,高校代码,层次
    """

    def __init__(self, threadcnt, account, prefix, proxy=None, sleep=0.0, highscore=750,
                 captcha_limit=50000,
                 kldms=None, seeds=None,
                 recover=False, sleep_max=5, ua='firefox'):
        super(GkChsiSchoolSpider, self).__init__(threadcnt, account, prefix, proxy, sleep, captcha_limit, sleep_max, ua)
        if kldms is None:
            kldms = [1, 5]
        self.pagestore = GkChsiSchoolPaperStore('yggk_sch_' + prefix)
        self.prefix = prefix
        if proxy:
            self.set_proxy(proxy)
        self.highscore = highscore
        self.minscore = {}
        self.recover = recover
        self.kldms = kldms
        self.parser = HTMLParser.HTMLParser()
        self.curl_share = None
        self.login()
        self.info_saver = LinkSaver(prefix + '_data')
        self.seeds = seeds

    def __del__(self):
        self.logout()

    def dispatch(self):
        kldms = self.fetch_kldms()
        self.info_saver.append('kldm:' + str(kldms) + '\n')
        if len(kldms) == 2:
            self.kldms[0] = str(kldms[0][0])
            self.kldms[1] = str(kldms[1][0])
        if self.seeds:
            seeds = []
            with open(self.seeds, 'r') as job_saver:
                lines = job_saver.readlines()
                job_saver.close()
                for l in lines:
                    if not self.recover or not self.pagestore.find_any(self.pagestore.channel + '://' + str(l.strip())):
                        seeds.append(eval(l))
            for seed in seeds:
                self.add_main_job(seed)
            print 'recover %d jobs' % len(seeds)
        else:
            s = self.highscore
            while s >= 50:
                for kldm in self.kldms:
                    for bkcc in [1, 2]:
                        self.add_main_job(
                            {'highscore': s, 'lowscore': s - 50, 'bkcc': bkcc, 'kldm': kldm,
                             'years': 15, 'start': 0})
                s -= 50
            if s > 0:
                for kldm in self.kldms:
                    for bkcc in [1, 2]:
                        self.add_main_job(
                            {'highscore': s, 'lowscore': 0, 'bkcc': bkcc, 'kldm': kldm,
                             'years': 15, 'start': 0})
        time.sleep(2)
        self.wait_q()
        self.add_job(None)

    def handle_job(self, jobid):
        url = 'http://gk.chsi.com.cn/recruit/listRecruitSchool.do'
        con = self.request_url(url, data=jobid)
        if not con or not con.text:
            self.on_work_failed(None, jobid, url)
            return
        if re.search(u'您输入的数据不符合要求,请按照下面的提示信息进行修改', con.text):
            logging.info('re add job,%s', str(jobid))
            self.re_add_job(jobid)
            print '查询错误', str(jobid)
            return
        self.pagestore.save(int(time.time()), str(jobid), url, con.text)
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

    def fetch_kldms(self):
        if self.login_time < -1:
            raise Exception('failed to login')
        con = self.request_url('http://gk.chsi.com.cn/recruit/queryByScore.do')
        if con and con.text:
            m = re.search(r'<select name="kldm">.*?</select>', con.text, re.S)
            if m:
                return re.findall(r'<option value=["\'](\d+)["\'][^>]*>(.*?)<\/option>', m.group())
        return []

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


class GkChsiSchoolSpiderCaptcha(BaseGkChsiFsxSpider):
    """
    学信网阳光高考省市分数线单用户单线程爬虫,抓取高校录取层次对,高校,高校代码,层次
    """

    def __init__(self, threadcnt, account, prefix, proxy=None, sleep=0.0, highscore=750, captcha_limit=50000,
                 kldms=None, session_life=600, sleep_internal=1200,
                 recover=False, sleep_max=5, ua='firefox'):
        super(GkChsiSchoolSpiderCaptcha, self).__init__(threadcnt, account, prefix, proxy, sleep, captcha_limit,
                                                        sleep_max, ua)
        if kldms is None:
            kldms = [1, 5]
        self.pagestore = GkChsiSchoolPaperStore('yggk_sch_' + prefix)
        self.prefix = prefix
        if proxy:
            self.set_proxy(proxy)
        self.highscore = highscore
        self.minscore = {}
        self.recover = recover
        self.kldms = kldms
        self.parser = HTMLParser.HTMLParser()
        self.curl_share = None
        self.session_life = session_life
        self.login()
        self.info_saver = LinkSaver(prefix + '_data')
        self.sleep_internal = sleep_internal

    def __del__(self):
        self.logout()

    def dispatch(self):
        kldms = self.fetch_kldms()
        self.info_saver.append('kldm:' + str(kldms) + '\n')
        if len(kldms) == 2:
            self.kldms[0] = str(kldms[0][0])
            self.kldms[1] = str(kldms[1][0])
        if self.recover:
            with open('sch_' + self.prefix + '_undo_jobs_old', 'r') as job_saver:
                lines = job_saver.readlines()
                job_saver.close()
                for l in lines:
                    self.add_main_job(eval(l))
                print 'recover %d jobs' % len(lines)
        else:

            s = self.highscore
            while s >= 50:
                for kldm in self.kldms:
                    for bkcc in [1, 2]:
                        self.add_main_job(
                            {'highscore': s, 'lowscore': s - 50, 'bkcc': bkcc, 'kldm': kldm,
                             'years': 15, 'start': 0})
                s -= 50
            if s > 0:
                for kldm in self.kldms:
                    for bkcc in [1, 2]:
                        self.add_main_job(
                            {'highscore': s, 'lowscore': 0, 'bkcc': bkcc, 'kldm': kldm,
                             'years': 15, 'start': 0})
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
        url = 'http://gk.chsi.com.cn/recruit/listRecruitSchool.do'
        con = self.request_url(url, data=jobid)
        if not con or not con.text:
            self.on_work_failed(None, jobid, url)
            return
        self.pagestore.save(int(time.time()), str(jobid), url, con.text)
        if 0 == jobid['start']:
            m = re.search(ur'共 (\d+) 页', con.text)
            if m:
                pages = int(m.group(1))
                logging.info('found %d pages for %s', pages, str(jobid))
                for page in range(1, pages + 1):
                    data = copy.deepcopy(jobid)
                    data['start'] = page * 20
                    self.add_job(data)
            else:
                logging.warn('failed to parse pages %s', str(jobid))

    def fetch_kldms(self):
        if self.login_time < -1:
            raise Exception('failed to login')
        con = self.request_url('http://gk.chsi.com.cn/recruit/queryByScore.do')
        if con and con.text:
            m = re.search(r'<select name="kldm">.*?</select>', con.text, re.S)
            if m:
                return re.findall(r'<option value=["\'](\d+)["\'][^>]*>(.*?)<\/option>', m.group())
        return []

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


if __name__ == '__main__':
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'spider.sch.log'), level=logging.NOTSET,
                        format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                        datefmt='%m/%d %I:%M:%S %p')

    # accounts = {'username': 'hubei101', 'password': 'bobo2016', 'prefix': 'hb', 'proxy': None, 'kldms': [1, 5]}
    # accounts = {'username': 'jsu2015', 'password': 'AHO001009', 'prefix': 'jsu', 'proxy': '183.239.167.122:8080'}
    # accounts = {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'proxy': '58.211.13.26:55336',
    #             'kldms': [2, 6]}
    # accounts = {'username': 'akg999', 'password': 'AHO001009', 'prefix': 'sh', 'proxy': '58.211.13.26:55336',
    accounts = {'username': 'ln2016e0', 'password': 'shi2016cxs', 'prefix': 'ln',
                'proxy': '106.75.136.205:80', 'kldms': ['5', '1'], 'score': 750, 'thcnt': 2,
                'sleep':1.0,
                'bkccs': ['1', '2']}
    #             'kldms': [1, 5]}
    # kldms = BaseGkChsiFsxSpider.get_kldms(accounts, accounts['prefix'])
    # print 'new kldms', kldms
    # if len(kldms) == 2:
    #     accounts['kldms',] = [kldms[0][0], kldms[1][0]]
    # gen_sch_seeds(accounts['score'], 'sch.seeds.' + accounts['prefix'], accounts['kldms'])
    job = ChsiSchoolSpider(accounts['thcnt'], accounts, accounts['prefix'], accounts['proxy'], accounts['sleep'],
                           kldms=accounts['kldms'],
                           recover=False, seeds='sch.seeds.%s' % accounts['prefix'],
                           captcha_limit=5000000)
    # job = GkChsiFsxSpider(1, accounts, accounts['prefix'], accounts['proxy'], 1, kldms=accounts['kldms'],captcha_limit=5000000)
    job.run()
