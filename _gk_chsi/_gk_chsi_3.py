#!/usr/bin/env python
# -*- coding:utf8 -*-
import HTMLParser
import copy
import logging
import os
import random
import re
import threading
import time
import uuid

from court.cspider import ATOSSessionCourtSpider
from court.save import LinkSaver
from court.util import Captcha, save_file, remove_file
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


class GkChsiFsxPaperStore(GkChsiFsxStore):
    def __int__(self, channel):
        GkChsiFsxStore.__init__(self, channel)

    def extract_content(self):
        return self.get_cur_doc().cur_content

    def page_time(self):
        return int(time.mktime(list(time.localtime())) * 1000)


class GkChsiFsxSpider(ATOSSessionCourtSpider):
    """
    学信网阳光高考省市分数线单用户单线程爬虫
    """

    def __init__(self, threadcnt, account, prefix, proxy=None, sleep=0, highscore=750, captcha_limit=50000, kldms=None,
                 recover=False, sleep_max=5, min_score=0, ua='firefox'):
        super(GkChsiFsxSpider, self).__init__(threadcnt)
        if kldms is None:
            kldms = [1, 5]
        self.select_user_agent(ua)
        self.pagestore = GkChsiFsxPaperStore('gkchsi_' + prefix)
        self.score_saver = GkChsiFsxScoreStore('gkchsi_score_' + prefix)
        self.account = account
        self.prefix = prefix
        self.proxy = proxy
        self.sleep = sleep
        self.cur_sleep = sleep
        self.max_sleep = sleep_max
        if proxy:
            self.set_proxy(proxy)
        self.highscore = highscore
        self.min_score_arr = {}
        self.success_count = 0
        self.lock = threading.Lock()
        self.remain_time = 0
        self.login_time = -1
        self.__shutdown = False
        self.job_saver = LinkSaver(self.prefix + '_undo_jobs')
        self.__captcha_times = 0
        self.__captcha_resolved_limits = captcha_limit
        self.recover = recover
        self.success_sleep_count = 0
        self.kldms = kldms
        self.parser = HTMLParser.HTMLParser()
        self.curl_share = None
        self.login()
        self.min_score = min_score

    def __del__(self):
        self.logout()

    def dispatch(self):
        kldms = self.fetch_kldms()
        if len(kldms) == 2:
            self.kldms[0] = str(kldms[0])
            self.kldms[1] = str(kldms[1])
        # data_tmp = {'wclx': 1, 'score': 0, 'bkcc': 1, 'kldm': 1, 'years': 15, 'type': 'score'}
        for kldm in self.kldms:
            self.min_score_arr[str(kldm)] = -1
        if self.recover:
            job_saver = LinkSaver(self.prefix + '_undo_jobs_old', 'r')
            lines = job_saver.readlines()
            job_saver.close()
            for l in lines:
                self.add_main_job(eval(l.strip()))
            print 'recover %d jobs' % len(lines)
        else:
            bkccs = [1, 2]  # 本科,专科
            mid_score = self.min_score + (self.highscore - self.min_score) * 3 / 4
            for score in range(0, max(self.highscore - mid_score, mid_score - self.min_score)):
                up_score = mid_score + score
                down_score = mid_score - score - 1
                for kldm in self.kldms:
                    for bkcc in bkccs:
                        if up_score <= self.highscore:
                            data = {'wclx': 1, 'score': up_score, 'bkcc': bkcc, 'kldm': kldm, 'years': 15}
                            self.add_main_job({'data': data, 'type': 'score'})
                        if down_score >= self.min_score and down_score > 0:
                            data = {'wclx': 1, 'score': down_score, 'bkcc': bkcc, 'kldm': kldm, 'years': 15}
                            self.add_main_job({'data': data, 'type': 'score'})

        time.sleep(2)
        self.wait_q()
        self.add_job(None)

    def fetch_kldms(self):
        if self.login_time < -1:
            raise Exception('failed to login')
        con = self.request_url('http://gk.chsi.com.cn/recruit/queryWeici.do')
        if con and con.text:
            m = re.search(r'<select name="kldm" id="kldm">.*?</select>', con.text, re.S)
            if m:
                res = re.findall(r'<option value=["\'](\d+)["\'][^>]*>', m.group())
                if res and len(res) >= 2:
                    return res[:2]
        return []

    def request_url(self, url, **kwargs):
        time.sleep(self.cur_sleep)
        con = super(GkChsiFsxSpider, self).request_url(url, **kwargs)

        if re.search('<form name="CheckAccessForm" method="post" action="/checkcode/CheckAccess.do">',
                     con.text):
            self.__captcha_times += 1
            if self.__captcha_resolved_limits >= self.__captcha_times:
                m = re.search(r'<input name="url"  type="hidden" value="([^"]*)"\/>', con.text)
                if not m:
                    return None
                con = self.resolve_captcha(self.parser.unescape(m.group(1)))
                if not con:
                    logging.error('encounter captcha resolve problem %d,%d', self.__captcha_times,
                                  self.__captcha_resolved_limits)
                    raise Exception('fail to resolve captcha %s' % url)
                logging.info('captcha resolve success,captcha times:%d', self.__captcha_times)
            else:
                self.__shutdown = True
                raise Exception('captcha exceeds limit')
        return con

    def login(self):
        data = {'j_username': self.account['username'], 'j_password': self.account['password']}
        con = super(GkChsiFsxSpider, self).request_url('http://gk.chsi.com.cn/login.do', data=data)
        # todo: check return results
        logging.info('logging on')
        if con and con.text:
            m = re.search(ur'<td align="left">(\d+)分钟</td></tr>', con.text)
            if m:
                self.login_time = time.time()
                self.remain_time = int(m.group(1))
                if self.remain_time > 0:
                    logging.info('remaining time %d min ', self.remain_time)
                    return True
                else:
                    print '已经没有剩余时间了:', m.group()
                    logging.error('there are no more time left')
                    return False

        return False

    def logout(self):
        return super(GkChsiFsxSpider, self).request_url('http://gk.chsi.com.cn/user/logout.do', data={})

    def resolve_captcha(self, url):
        count = 0
        while count < 100:
            count += 1
            rd = random.random() * 10000
            time.sleep(1)
            con = super(GkChsiFsxSpider, self).request_url('http://gk.chsi.com.cn/ValidatorIMG.JPG?ID=%s' % str(rd))
            if not con or not con.content:
                logging.info('failed to fetch captcha')
                return False
            fname = '/tmp/' + str(uuid.uuid4()) + '.jpg'
            save_file(con.content, fname)
            res = Captcha.resolve(fname)
            remove_file(fname)
            if not res:
                logging.error('fail to resolve captcha')
                continue
            data = {'CHKNUM': res, 'url': url}
            if data['url'] is None:
                logging.error('Invalid host found %s', url)
                return None
            time.sleep(1)
            con = super(GkChsiFsxSpider, self).request_url('http://gk.chsi.com.cn/checkcode/CheckAccess.do', data=data)
            if con and con.text:
                m = re.search('<form name="CheckAccessForm" method="post" action="/checkcode/CheckAccess.do">',
                              con.text)
                if not m:
                    return con
        print 'try captcha times 100 %s' % url
        return None

    def on_net_work_failed(self, content, jobid, url):
        with self.lock:
            if self.cur_sleep <= self.max_sleep:
                self.cur_sleep += 1
            self.success_count = 0
        if content is None:
            logging.error('fail to fetch content from %s with %s' % (url, str(jobid)))
            self.re_add_job(jobid)
            return
            # raise Exception('fail to fetch content from %s with %s' % (url, str(jobid)))
        if re.search(ur'1秒内|访问错误', content):
            # raise Exception('too many connections in one second,%s' % url)
            logging.error('too many connections in one second,%s' % url)
            self.re_add_job(jobid)
            return
        captcha = re.search('<form name="CheckAccessForm" method="post" action="/checkcode/CheckAccess.do">', content)
        if captcha:
            self.__captcha_times += 1
            if self.__captcha_resolved_limits >= self.__captcha_times:
                con = self.resolve_captcha(url)
                if con:
                    logging.info('captcha resolve success,captcha times:%d', self.__captcha_times)
                    self.re_add_job(jobid)
                    return con
            logging.error('encounter captcha %d,%d', self.__captcha_times, self.__captcha_resolved_limits)
            self.__shutdown = True
            raise Exception('captcha failed')

            # check time:
        m = re.search(ur'<td align="left">(\d+)分钟</td></tr>', content)
        if m:
            self.remain_time = int(m.group(1))
            if self.remain_time <= 0:
                self.__shutdown = True
                raise Exception('remain time failed %d', self.remain_time)

        # need login
        if re.search(u'查看此栏目需要先登录', content):
            logging.info('need login')
            self.login()
            self.re_add_job(jobid)
            return
        # no more time
        if re.search(r'<p class="pay"><a href="\/user\/prechongzhi.do">.*?<\/a><\/p>', content):
            self.__shutdown = True
            logging.error('No more time,need to pay')
            raise Exception('Need to pay for more time')
        # invalid query parameters
        if re.search(u'您输入的数据不符合要求,请按照下面的提示信息进行修改:', content):
            logging.error('invalid query parameters: %s', str(jobid))
            return
        raise Exception('unknown network exception %s' % str(jobid))

    def __on_shutdown(self, jobid):
        self.job_saver.add(str(jobid) + '\n')

    def run_job(self, jobid):
        if self.__shutdown:
            self.__on_shutdown(jobid)
            return
        with self.lock:
            if self.success_count > 50:
                self.cur_sleep -= 1
                if self.cur_sleep < self.sleep:
                    self.cur_sleep = self.sleep
                self.success_count = 0
                self.success_sleep_count += 1
                if self.success_sleep_count > 100:
                    self.logout()
                    time.sleep(30)
                    self.success_sleep_count = 0
                    if not self.login():
                        logging.error('fail to log in')
                        self.__shutdown = True
                        raise Exception('log in failed')

        if 'score' == jobid['type']:
            if self.min_score_arr[str(jobid['data']['kldm'])] > jobid['data']['score']:
                # TODO:should I do something?
                pass
            url = 'http://gk.chsi.com.cn/recruit/listWcByScore.do'
            con = self.request_url(url, data=jobid['data'])
            if not con or not con.text:
                logging.info('fail to request job,%d,%d,%d,%d')
                self.on_net_work_failed(None, jobid, url)
                return
            content = re.search(r'<div id="direction1">.*?<\/table>', con.text, re.S)
            if not content:
                logging.error('fail to  extract content %s', str(jobid))
                self.on_net_work_failed(con.text, jobid, url)
                return

            content = content.group()
            id = '%s,%s,%s,%s,%s,%s' % (
                self.prefix, jobid['data']['years'], jobid['data']['wclx'], jobid['data']['kldm'],
                jobid['data']['bkcc'], jobid['data']['score'])

            logging.info('%s==>%d', id, len(content))
            m = re.findall(r'<td align="center" bgcolor="#FFFFFF">([\s\d]+?)<\/td>', content, re.S)
            if not m:
                logging.error('fail to parse rank from %s', id)
                return
            rank = m[0]
            self.score_saver.save(int(time.time()), id, url, "%s,%s,%s,%s" % (id, m[0], m[1].strip(), m[2].strip()))
            if jobid['data']['score'] < 400 and '0' == rank:
                self.min_score_arr[str(jobid['data']['kldm'])] = jobid['data']['score']
            if '0' == rank:
                logging.info('zero rank %s', id)
            else:
                data = copy.deepcopy(jobid['data'])
                data['wc'] = rank
                data['wcpp'] = 1
                data['start'] = 0
                self.add_job({'type': 'rank', 'data': data})
                print 'add rank job', str(data)
        elif 'rank' == jobid['type']:
            url = 'http://gk.chsi.com.cn/recruit/listRecruitWeicis.do'
            con = self.request_url(url, data=jobid['data'])
            if not con or not con.text:
                logging.error('fail to request rank paper %s', str(jobid))
                self.on_net_work_failed(None, jobid, url)
                return
            if re.search(u'1秒内', con.text):
                logging.error('wrong paper content %s', str(jobid))
                self.on_net_work_failed(con.text, jobid, url)
                return
            self.save_rank_paper(jobid['data'], url, con.text, jobid['data']['start'] / 10 + 1, jobid)
            if 0 == jobid['data']['start']:
                m = re.search(ur'共 (\d+) 页', con.text)
                if not m:
                    logging.warn('fail to parse page count %s', str(jobid))
                    return
                pagecnt = int(m.group(1))
                for page in range(2, pagecnt + 1):
                    cdata = copy.deepcopy(jobid['data'])
                    cdata['start'] = 10 * (page - 1)
                    self.add_job({'type': 'rank', 'data': cdata})
        with self.lock:
            self.success_count += 1

    def extract_content(self, content):
        """extract rank paper content"""
        m = re.search(r'<table[^>]*class="query"[^>]*>.*?<\/table>', content, re.S)
        if m:
            return m.group()

    def save_rank_paper(self, data, url, content, page, jobid):
        con = self.extract_content(content)
        if not con:
            logging.error('rank paper content is None')
            self.on_net_work_failed(content, jobid, url)
            return
        id = '%s/%s/%s/%s/%s/%s/%s/%s' % (
            self.prefix, data['years'], data['wclx'], data['kldm'],
            data['bkcc'], data['score'], data['wcpp'], page)
        self.pagestore.save(int(time.time()), id, url, con)
        logging.info('rank job %s==>%d', id, len(con))

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass

    def report(self):
        super(GkChsiFsxSpider, self).report()
        self.job_saver.flush()


if __name__ == '__main__':
    logging.basicConfig(filename=os.path.join(os.getcwd(), '3.spider.log'), level=logging.NOTSET,
                        format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                        datefmt='%m/%d %I:%M:%S %p')
    # accounts = {'username': 'hubei101', 'password': 'bobo2016', 'prefix': 'hb', 'proxy': None, 'kldms': [1, 5]}
    # accounts = {'username': 'jsu2015', 'password': 'AHO001009', 'prefix': 'jsu', 'proxy': '183.239.167.122:8080'}
    # accounts = {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'proxy': '58.211.13.26:55336',
    #             'kldms': [2, 6]}
    # accounts = {'username': 'akg999', 'password': 'AHO001009', 'prefix': 'sh', 'proxy': '58.211.13.26:55336',                'kldms': [1, 5]}
    accounts = {'username': 'homo123', 'password': 'AHO001009', 'prefix': 'bj', 'proxy': '122.96.59.107:82',
                'kldms': [1, 5]}
    ua = [
        '=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36',
        '=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0',
        '=Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)',
        '=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36',
        '=Opera/9.80 (Windows NT 6.2; Win64; x64) Presto/2.12.388 Version/12.17',
        '=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:45.0) Gecko/20100101 Firefox/45.0',
        '=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36'
        '=Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60'
    ]
    job = GkChsiFsxSpider(1, accounts, accounts['prefix'], accounts['proxy'], 1, kldms=accounts['kldms'], highscore=750,
                          captcha_limit=5000000, recover=False, min_score=150, ua=ua[0])
    # job = GkChsiFsxSpider(1, accounts, accounts['prefix'], accounts['proxy'], 1, kldms=accounts['kldms'],captcha_limit=5000000)
    job.run()
