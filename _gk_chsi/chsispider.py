#!/usr/bin/env python
# -*- coding:utf8 -*-
import HTMLParser
import copy
import logging
import random
import re
import threading
import time
import uuid

from court.captcha import Captcha
from court.cspider import ATOSSessionCourtSpider
from court.save import LinkSaver
from court.util import save_file, remove_file
from spider import spider
from spider.ipin.savedb import PageStoreBase


class GkChsiFsxStore(PageStoreBase):
    def __init__(self, channel, dburl="mongodb://root:helloipin@localhost/admin"):
        PageStoreBase.__init__(self, channel, dburl)

    def extract_content(self):
        return self.get_cur_doc().cur_content

    def page_time(self):
        return int(time.mktime(list(time.localtime())) * 1000)


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
        m = re.search(r'<table width="775" border="0" align="center" cellpadding="0" cellspacing="0">.*<\/table><\/td>',
                      self.get_cur_doc().cur_content, re.S)
        if m:
            return m.group()
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


class SleepSpider(ATOSSessionCourtSpider):
    def __init__(self, threadcnt, sleep=1.0, failed_limit=50):
        super(SleepSpider, self).__init__(threadcnt, failed_limit)
        self.sleep = sleep
        self.last_request_time = time.time()

    def request_url(self, url, **kwargs):
        t = time.time() - self.last_request_time
        if t < self.sleep:
            time.sleep(self.sleep - t)
        try:
            con = super(SleepSpider, self).request_url(url, **kwargs)
            self.last_request_time = time.time()
            return con
        except Exception as e:
            self.last_request_time = time.time()
            raise e


class InvalidQueryError(Exception):
    pass


class StatisticsItem():
    def __init__(self, name):
        self.__name = name
        self.__count = 0
        self.__lock = threading.Lock()

    def increase(self):
        with self.__lock:
            self.__count += 1

    def count(self):
        return self.__count

    def name(self):
        return self.__name


class BaseGkChsiFsxSpider(SleepSpider):
    """
    学信网阳光高考省市分数线单用户单线程爬虫
    """

    def __init__(self, threadcnt, account, prefix, proxy=None, sleep=0.0, captcha_limit=5000000, sleep_max=5,
                 ua='firefox'):
        super(BaseGkChsiFsxSpider, self).__init__(threadcnt, sleep, failed_limit=2)
        self.select_user_agent(ua)
        self.account = account
        self.full_tag = prefix
        self.proxy = proxy
        self.max_sleep = sleep_max
        if proxy:
            self.set_proxy(proxy)
        self.success_count = 0
        self.lock = threading.Lock()
        self.remain_time = 0
        self.login_time = -1
        self._shutdown = False
        self.job_saver = LinkSaver('undo.jobs.%s' % self.full_tag)
        self.failed_saver = LinkSaver('failed.jobs.%s' % self.full_tag)
        self._captcha_times = 0
        self._captcha_resolved_limits = captcha_limit
        self.success_sleep_count = 0
        self.login()
        self.parser = HTMLParser.HTMLParser()
        self.c = self.full_tag + str(random.randint(1, 100))
        self.except_state = [StatisticsItem('request error'), StatisticsItem('speed error'),
                             StatisticsItem('captcha error'),
                             StatisticsItem('login error'), StatisticsItem('server error'),
                             StatisticsItem('remain time error'), StatisticsItem('query error')]

    def __del__(self):
        self.logout()

    def request_url(self, url, **kwargs):
        try:
            con = super(BaseGkChsiFsxSpider, self).request_url(url, **kwargs)
        except(KeyboardInterrupt, SystemExit):
            self._shutdown = True
            return

        if con is None:
            return None
        if re.search('<form name="CheckAccessForm" method="post" action="/checkcode/CheckAccess.do">',
                     con.text):
            if self.on_captcha():
                return
            self._captcha_times += 1
            if self._captcha_resolved_limits >= self._captcha_times:
                m = re.search(r'<input name="url"  type="hidden" value="([^"]*)"\/>', con.text)
                if not m:
                    return con
                con = self.resolve_captcha(self.parser.unescape(m.group(1)))
                if not con:
                    logging.error('encounter captcha resolve problem %d,%d', self._captcha_times,
                                  self._captcha_resolved_limits)
                    raise Exception('fail to resolve captcha %s' % url)
                logging.info('captcha resolve success,captcha times:%d', self._captcha_times)
            else:
                self._shutdown = True
                raise Exception('captcha exceeds limit')
        return con

    def on_captcha(self):
        return False

    def login(self):
        data = {'j_username': self.account['username'], 'j_password': self.account['password']}
        con = super(BaseGkChsiFsxSpider, self).request_url('http://gk.chsi.com.cn/login.do', data=data)
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
            else:
                logging.error('failed to find remain time')
        return False

    def logout(self):
        return super(BaseGkChsiFsxSpider, self).request_url('http://gk.chsi.com.cn/user/logout.do', data={})

    def resolve_captcha(self, url):
        count = 0
        while count < 5:
            count += 1
            rd = random.random() * 10000
            con = super(BaseGkChsiFsxSpider, self).request_url('http://gk.chsi.com.cn/ValidatorIMG.JPG?ID=%s' % str(rd))
            if not con or not con.content:
                logging.info('failed to fetch captcha')
                return False
            fname = '/tmp/' + str(uuid.uuid4()) + '.jpg'
            save_file(con.content, fname)
            res = Captcha.resolve(fname, self.c)
            remove_file(fname)
            if not res:
                logging.error('fail to resolve captcha')
                continue
            data = {'CHKNUM': res, 'url': url}
            if data['url'] is None:
                logging.error('Invalid host found %s', url)
                return None
            con = super(BaseGkChsiFsxSpider, self).request_url('http://gk.chsi.com.cn/checkcode/CheckAccess.do',
                                                               data=data)
            if con and con.text:
                m = re.search('<form name="CheckAccessForm" method="post" action="/checkcode/CheckAccess.do">',
                              con.text)
                if not m:
                    return con
            time.sleep(0.2)
        logging.warn('try to resolve captcha 100 times for %s' % url)
        print 'try to resolve captcha 100 times for %s' % url
        return None

    def _other_exception_checking(self, content, jobid, url):
        ''':return False if no exceptions are found'''
        return False

    def __on_failed(self):
        '''
        work on failed
        '''
        with self.lock:
            self.success_count = 0

    def _check_result(self, content, jobid, url):
        '''
        check if there are any exception in results if result exception is found
               job will be re add to failed list or exception is raise
        :return return True if there are exception,otherwise False
        '''
        try:
            ret = self._check_failed_type(content, jobid, url)
            if ret:
                self.__on_failed()
            return ret
        except Exception as e:
            self.__on_failed()
            raise e

    def re_add_failed_job(self, jobid):
        self.re_add_job(jobid)

    def _check_failed_type(self, content, jobid, url):
        '''
        check if there any exception,if  exceptions are found then return true,other wise false
        exceptions may be None request response,captcha failed,acount time exceeds etc.
        if failed exception is handle then job may be add again to queue
        '''
        if content is None:
            logging.error('fail to fetch content from %s with %s' % (url, str(jobid)))
            self.re_add_failed_job(jobid)
            self.except_state[0].increase()
            return True
            # raise Exception('fail to fetch content from %s with %s' % (url, str(jobid)))
        if re.search(ur'1秒内|访问错误', content):
            # raise Exception('too many connections in one second,%s' % url)
            logging.error('too many connections in one second,%s' % url)
            self.re_add_failed_job(jobid)
            self.except_state[1].increase()
            time.sleep(self.sleep / 2.0)
            return True

        if re.search('<form name="CheckAccessForm" method="post" action="/checkcode/CheckAccess.do">', content):
            self._captcha_times += 1
            self.except_state[2].increase()
            if self._captcha_resolved_limits >= self._captcha_times:
                con = self.resolve_captcha(url)
                if con:
                    logging.info('captcha resolve success,captcha times:%d', self._captcha_times)
                else:
                    logging.warn('failed to resolve captcha')
                self.re_add_failed_job(jobid)
                return False
            logging.error('encounter captcha %d,%d', self._captcha_times, self._captcha_resolved_limits)
            self._shutdown = True
            raise Exception('captcha failed')

        # need login
        if re.search(u'查看此栏目需要先登录', content):
            logging.info('need login')
            self.except_state[3].increase()
            self.login()
            self.re_add_failed_job(jobid)
            return True
            # server error
        if re.search(u'对不起，系统出现异常，请把此页面信息发给管理员', content):
            logging.info('server error')
            self.except_state[4].increase()
            time.sleep(0.5)
            self.re_add_failed_job(jobid)
            return True
        # no more time
        if re.search(r'<p class="pay"><a href="\/user\/prechongzhi.do">.*?<\/a><\/p>', content):
            self._shutdown = True
            logging.error('No more time,need to pay')
            self.except_state[5].increase()
            raise Exception('Time exceeds,need to pay more')

        # invalid query parameters
        if re.search(u'您输入的数据不符合要求,请按照下面的提示信息进行修改:', content):
            logging.error('invalid query parameters: %s', str(jobid))
            self.except_state[6].increase()
            raise InvalidQueryError('invalid query parameters: %s', str(jobid))

        # check time:
        m = re.search(ur'<td align="left">(\d+)分钟</td></tr>', content)
        if m:
            self.remain_time = int(m.group(1))
            if self.remain_time <= 0:
                self._shutdown = True
                raise Exception('remain time failed %d', self.remain_time)
        return self._other_exception_checking(content, jobid, url)

    def on_work_failed(self, content, jobid, url):
        '''work on work failed'''
        self.__on_failed()
        if not self._other_exception_checking(content, jobid, url):
            raise Exception('unknown network exception %s' % str(jobid))

    def __on_shutdown(self, jobid):
        self.job_saver.add(str(jobid) + '\n')

    def handle_job(self, jobid):
        pass

    def pay_more_time(self, account, password):
        data = {'username': account, 'password': password}
        con = self.request_url('http://gk.chsi.com.cn/user/chongzhi.do', data=data)
        pay_time = 0
        if con and con.text:
            m = re.search(ur'<strong>(\d+)<\/strong>[^<]*<strong>(\d+)<\/strong>.*?<\/div>', con.text, re.S)
            if m:
                self.login_time = time.time()
                self.remain_time = int(m.group(2))
                pay_time = int(m.group(1))
                if self.remain_time > 0:
                    logging.info('remaining time %d min,pay time %d ', self.remain_time, pay_time)
                else:
                    print '哎呀，居然没充值成功', m.group()
                    logging.error('pay failed')
            else:
                logging.error('failed to pay time')
        return [pay_time, self.remain_time]

    def pre_job(self, jobid):
        if self._shutdown:
            self.__on_shutdown(jobid)
            return True
        return False

    @staticmethod
    def get_kldms(accounts, prefix):
        chsispider = BaseGkChsiFsxSpider(1, accounts, prefix, accounts['proxy'])
        time.sleep(2)
        con = chsispider.request_url('http://gk.chsi.com.cn/recruit/queryByScore.do')
        if con and con.text:
            m = re.search(r'<select name="kldm">.*?</select>', con.text, re.S)
            if m:
                chsispider.logout()
                return re.findall(r'<option value=["\'](\d+)["\'][^>]*>(.*?)<\/option>', m.group())
        chsispider.logout()
        return []

    @staticmethod
    def get_remain_time(accounts, prefix):
        chsispider = BaseGkChsiFsxSpider(1, accounts, prefix, accounts['proxy'])
        return chsispider.remain_time

    @staticmethod
    def pay_time(accounts, prefix, card):
        chsispider = BaseGkChsiFsxSpider(1, accounts, prefix, accounts['proxy'])
        res = chsispider.pay_more_time(card['username'], card['password'])
        return res

    def run_job(self, jobid):
        if self.pre_job(jobid):
            return
        with self.lock:
            if self.success_count > 50:
                self.success_count = 0
                self.success_sleep_count += 1
                if self.success_sleep_count > 100:
                    self.logout()
                    logging.info('sleep for 30 seconds')
                    time.sleep(30)
                    self.success_sleep_count = 0
                    if not self.login():
                        logging.error('fail to log in')
                        self._shutdown = True
                        raise Exception('log in failed')
        self.handle_job(jobid)
        with self.lock:
            self.success_count += 1

    def extract_content(self, content):
        """extract rank paper content"""
        m = re.search(r'<table[^>]*class="query"[^>]*>.*?<\/table>', content, re.S)
        if m:
            return m.group()

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.special_saver.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass

    def report(self):
        super(BaseGkChsiFsxSpider, self).report()
        self.job_saver.flush()
        self.failed_saver.flush()

    def post_kldm_bkcc_for_session(self, kldm, bkcc):
        count = 5
        while count > 0:
            # 发送请求不接受数据
            url1 = 'http://gk.chsi.com.cn/recruit/listSchByYxmc.do'
            data = {'wclx': 1, 'yxmc': '北京大学', 'kldm': kldm, 'bkcc': bkcc, 'start': 0, 'years': '15'}
            con = self.request_url(url1, data=data)
            if con and con.text:
                break
            count -= 1


class ChsiSpider(BaseGkChsiFsxSpider):
    def __init__(self, threadcnt, account, tag, proxy=None, sleep=0.0, captcha_limit=50000000, sleep_max=5,
                 ua='firefox', seeds='detail_seeds', recover=False, year='15', bkccs=None, kldms=None,
                 job_tag='', spider_type='detail', post_kldms=True):
        super(ChsiSpider, self).__init__(threadcnt, account, '%s%s' % (tag, job_tag), proxy, sleep, captcha_limit,
                                         sleep_max,
                                         ua)
        if kldms is None:
            kldms = ['5', '1']
        if bkccs is None:
            bkccs = ['1', '2']
        self.pagestore = self.new_page_store(spider_type, tag)
        self.full_tag = tag
        self.seeds = seeds
        if proxy:
            self.set_proxy(proxy)
        self.kldms = kldms
        self.bkccs = bkccs
        self.recover = recover
        self.info_saver = LinkSaver('info_data_%s_%s%s' % (spider_type, tag, job_tag))
        self.failed_saver = LinkSaver('%s.failed.seeds.%s%s' % (spider_type, tag, job_tag))
        self.invalid_saver = LinkSaver('%s.invalid.seeds.%s%s' % (spider_type, tag, job_tag))
        self.year = year
        self.failed_list = []
        self.invalid_list = []
        self.spider_type = spider_type
        self.post_kldms = post_kldms

    def dispatch(self):
        # read all seeds
        seeds = []
        with open(self.seeds, 'r') as f:
            for l in f:
                data = self.parse_seed(l.strip())
                if not data:
                    continue
                if self.year == str(data['years']):
                    if not self.recover or not self.pagestore.find_any(
                                            self.pagestore.channel + '://' + self.get_job_id(data)):
                        seeds.append(data)
        print 'load ', len(seeds), 'jobs'
        count = 10
        while len(seeds) > 0 and count > 0:
            count -= 1
            logging.info('remain tries %d', count)
            for kldm in self.kldms:
                for bkcc in self.bkccs:
                    seeds = self.request_list(seeds, kldm, bkcc)
                    logging.info('seeds %d,failed %d,kldm=%s,bkcc=%s,tries=%d', len(seeds), len(self.failed_list), kldm,
                                 bkcc, count)
                    time.sleep(2)
                    self.wait_q()
            seeds += self.failed_list
            self.failed_list = []
        self.wait_q()
        self.add_job(None)
        self.failed_list = seeds

    def handle_job(self, jobid):
        pass

    def re_add_failed_job(self, jobid):
        if jobid.has_key('content'):
            jobid.pop('content')
        if jobid.has_key('url'):
            jobid.pop('url')
        cnt = jobid.get('_failed_cnt_', 0) + 1
        jobid['_failed_cnt_'] = cnt
        self.failed_list.append(jobid)

    def save_invalid_job(self, jobid):
        cnt = jobid.get('_invalid_cnt_', 0) + 1
        jobid['_invalid_cnt_'] = cnt
        if cnt < 2:
            self.re_add_failed_job(jobid)
        else:
            if jobid.has_key('content'):
                jobid.pop('content')
            if jobid.has_key('url'):
                jobid.pop('url')
            self.invalid_list.append(jobid)

    def request_list(self, seeds, kldm, bkcc):
        remains = []
        if self.post_kldms:
            self.post_kldm_bkcc_for_session(kldm, bkcc)
            for seed in seeds:
                if seed['kldm'] == kldm and bkcc == seed['bkcc']:
                    self.add_main_job(seed)
                else:
                    remains.append(seed)
        else:
            for seed in seeds:
                self.add_main_job(seed)
        return remains

    def run_job(self, jobid):
        if self.pre_job(jobid):
            return
        if not jobid.has_key('content'):
            self.re_add_failed_job(jobid)
            return
        detail_content = jobid['content']
        if detail_content is None:
            self.re_add_failed_job(jobid)
            return
        try:
            if self._check_result(detail_content.text, jobid, jobid['url']):
                '''exception is found and handled'''
                return
        except InvalidQueryError as e:
            logging.info(e.message)
            self.save_invalid_job(jobid)
            return
        except Exception as e:
            logging.info(e.message)
            self.re_add_failed_job(jobid)
            return
        if not jobid.has_key('url'):
            print jobid
            self.re_add_failed_job(jobid)
            return
        jid = self.get_job_id(jobid)
        print 'saving %s==>%s' % (jid, len(detail_content.text))
        self.pagestore.save(int(time.time()), jid, jobid['url'], detail_content.text)

    def get_job_title(self, jobid):
        raise NotImplementedError('Virtual method called')

    def new_page_store(self, spider, tag):
        raise NotImplementedError('Virtual method called')

    def get_job_id(self, jobid):
        raise NotImplementedError('Virtual method called')

    def parse_page(self, jobid, content):
        raise NotImplementedError('Virtual method called')

    def get_url(self, jobid):
        raise NotImplementedError('Virtual method called')

    def report_job(self, jobid):
        raise NotImplementedError('Virtual method called')

    def add_job(self, jobid, mainjob=False):
        if jobid is None:
            super(ChsiSpider, self).add_job(jobid, mainjob)
            return
        url = self.get_url(jobid)
        count = 3
        content = None
        while count > 0 and not content:
            content = self.request_content(jobid, url)
            count -= 1
        if content is None:
            self.re_add_failed_job(jobid)
            return
        jobid['content'] = content
        jobid['url'] = url
        self.report_job(jobid)
        super(ChsiSpider, self).add_job(jobid, mainjob)
        self.parse_page(jobid, content)

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += 'seeds: %s\n' % self.seeds
            msg += "saved: %d\n" % self.pagestore.saved_count
            msg += 'captcha times: %s\n' % self._captcha_times
            msg += 'remain seeds: %d\n' % len(self.failed_list)
            msg += 'invalid seeds: %d\n' % len(self.invalid_list)
            for item in self.except_state:
                msg += '%s: %d\n' % (item.name(), item.count())
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
            print 'remain seeds', len(self.failed_list)
            print 'invalid seeds', len(self.invalid_list)
            for seed in self.invalid_list:
                self.invalid_saver.add(str(seed))
            self.invalid_saver.flush()
            for seed in self.failed_list:
                self.failed_saver.add(str(seed))
            self.failed_saver.flush()
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass

    def parse_seed(self, param):
        raise NotImplementedError('Virtual method called')

    def request_content(self, jobid, url):
        raise NotImplementedError('Virtual method called')


class ChsiDetailSpider(ChsiSpider):
    def __init__(self, threadcnt, account, tag, proxy=None, sleep=0.0, captcha_limit=50000000, seeds='detail_seeds',
                 recover=False, sleep_max=5, ua='firefox', year='15', bkccs=None, kldms=None, job_tag=''):
        super(ChsiDetailSpider, self).__init__(threadcnt, account, tag, proxy, sleep, captcha_limit, sleep_max,
                                               ua, seeds=seeds, recover=recover, year=year, bkccs=bkccs, kldms=kldms,
                                               job_tag=job_tag, spider_type='detail')

        self.detail_url_format = 'http://gk.chsi.com.cn/recruit/listWeiciBySpec.do?year=%s&yxdm=%s&zydm=%s&start=%s'

    def get_job_title(self, jobid):
        return '%s/%s/%s/%s/%s/%s' % (
            jobid['yxdm'], jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['wclx'],
            jobid['start'])

    def new_page_store(self, spider, tag):
        return GkChsiDetailPaperStore('yggk_%s_%s' % (spider, tag))

    def get_job_id(self, jobid):
        return '%s/%s/%s' % (self.get_job_title(jobid), jobid['zydm'], int(jobid['start']) / 10)

    def report_job(self, jobid):
        logging.info('fetched spec %s,%s,%s,%s', jobid['zymc'], jobid['zydm'], jobid['start'], jobid['url'])

    def parse_page(self, jobid, content):
        if 0 == jobid['start']:
            m = re.search(ur'共 (\d+) 页', content.text)
            if not m:
                logging.warn('failed to find page count %s,%s,%s', jobid['kldm'], jobid['bkcc'], jobid['url'])
                return
            page_cnt = int(m.group(1))
            if page_cnt <= 1:
                return
            d = copy.deepcopy(jobid)
            d.pop('content')
            d.pop('url')
            for p in range(1, page_cnt):
                job = copy.deepcopy(d)
                job['start'] = p * 10
                self.add_main_job(job)

    def parse_seed(self, l):
        if l[0] == '{':
            data = eval(l)
        else:
            param = l.strip().split(',')
            if len(param) != 8:
                logging.warn('invalid seeds %s', l)
                return None
            data = {'wclx': 1, 'yxdm': param[6], 'kldm': param[2], 'bkcc': param[4], 'start': 0,
                    'years': param[5], 'zydm': param[7], 'zymc': param[8].encode('utf-8')}
        return data

    def get_url(self, jobid):
        return self.detail_url_format % (jobid['years'], jobid['yxdm'], jobid['zydm'], jobid['start'])

    def request_content(self, jobid, url):
        return self.request_url(url)


class ChsiSpecialSpider(ChsiSpider):
    def __init__(self, threadcnt, account, tag, proxy=None, sleep=0.0, captcha_limit=50000000, seeds='spec.seeds',
                 recover=False, sleep_max=5, ua='firefox', year='15', bkccs=None, kldms=None, job_tag=''):
        super(ChsiSpecialSpider, self).__init__(threadcnt, account, tag, proxy, sleep, captcha_limit, sleep_max,
                                                ua, seeds=seeds, recover=recover, year=year, bkccs=bkccs, kldms=kldms,
                                                job_tag=job_tag, spider_type='spec')

    def get_job_title(self, jobid):
        return '%s/%s/%s/%s/%s/%s' % (
            jobid['yxdm'], jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['wclx'],
            jobid['start'])

    def request_content(self, jobid, url):
        return self.request_url(url)

    def report_job(self, jobid):
        logging.info('fetched school %s,%s,%s', jobid['yxdm'], jobid['start'], jobid['url'])

    def new_page_store(self, spider, tag):
        return GkChsiSpecialPaperStore('yggk_%s_%s' % (spider, tag))

    def get_job_id(self, jobid):
        return self.get_job_title(jobid)

    def parse_page(self, jobid, content):
        if 0 == jobid['start']:
            m = re.search(ur'共 (\d+) 页', content.text)
            if m:
                pages = int(m.group(1))
                job = copy.deepcopy(jobid)
                job.pop('content')
                job.pop('url')
                logging.info('found %d pages for %s', pages, str(jobid))
                for page in range(1, pages):
                    data = copy.deepcopy(job)
                    data['start'] = page * 32
                    self.add_main_job(data)
            else:
                logging.warn('failed to parse pages %s', str(jobid))

    def get_url(self, jobid):
        return 'http://gk.chsi.com.cn/recruit/listSpecBySchool.do?yxdm=%s&start=%s' % (jobid['yxdm'], jobid['start'])

    def parse_seed(self, l):
        if l[0] == '{':
            data = eval(l.strip())
        else:
            param = l.strip().split(',')
            if len(param) != 8:
                logging.warn('invalid seeds %s', l)
                return
            data = {'wclx': 1, 'yxdm': param[6], 'kldm': param[2], 'bkcc': param[4], 'start': 0,
                    'years': param[5],
                    'yxmc': param[7].decode('utf-8')}
        return data


class ChsiSchoolSpider(ChsiSpider):
    def __init__(self, threadcnt, account, tag, proxy=None, sleep=0.0, captcha_limit=50000000, seeds='school.seeds',
                 recover=False, sleep_max=5, ua='firefox', year='15', bkccs=None, kldms=None, job_tag=''):
        super(ChsiSchoolSpider, self).__init__(threadcnt, account, tag, proxy, sleep, captcha_limit, sleep_max,
                                               ua, seeds=seeds, recover=recover, year=year, bkccs=bkccs, kldms=kldms,
                                               job_tag=job_tag, spider_type='sch', post_kldms=False)

    def get_job_title(self, jobid):
        return ''

    def request_content(self, jobid, url):
        return self.request_url(url, data={'highscore': jobid['highscore'], 'lowscore': jobid['lowscore'],
                                           'bkcc': jobid['bkcc'], 'kldm': jobid['kldm'],
                                           'years': jobid['years'], 'start': jobid['start']})

    def report_job(self, jobid):
        logging.info('fetched range %s,%s,%s', jobid['highscore'], jobid['kldm'], jobid['bkcc'])

    def new_page_store(self, spider, tag):
        return GkChsiSchoolPaperStore('yggk_%s_%s' % (spider, tag))

    def get_job_id(self, jobid):
        return '%s/%s/%s/%s/%s/%s' % (
            jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['highscore'], jobid['lowscore'], jobid['start'])

    def parse_page(self, jobid, content):
        if 0 == jobid['start']:
            m = re.search(ur'共 (\d+) 页', content.text)
            if m:
                pages = int(m.group(1))
                logging.info('found %d pages for %s', pages, str(jobid))
                job = copy.deepcopy(jobid)
                job.pop('content')
                job.pop('url')
                for page in range(1, pages):
                    data = copy.deepcopy(job)
                    data['start'] = page * 20
                    self.add_main_job(data)
            else:
                logging.warn('failed to parse pages %s', str(jobid))

    def get_url(self, jobid):
        return 'http://gk.chsi.com.cn/recruit/listRecruitSchool.do'

    def parse_seed(self, l):
        if l[0] == '{':
            return eval(l.strip())
        else:
            p = l.split('/')
            return {'years': p[2], 'bkcc': p[4], 'kldm': p[3], 'wclx': 1, 'highscore': p[5], 'lowscore': p[6],
                    'start': p[7]}


def gen_sch_seeds(highscore, seeds, kldms=None):
    if kldms is None:
        kldms = ['5', '1']
    s = highscore
    jobs = []
    while s >= 50:
        for kldm in kldms:
            for bkcc in ['1', '2']:
                jobs.append(
                    {'highscore': s, 'lowscore': s - 50, 'bkcc': bkcc, 'kldm': kldm,
                     'years': 15, 'start': 0})
        s -= 50
    if s > 0:
        for kldm in kldms:
            for bkcc in ['1', '2']:
                jobs.append(
                    {'highscore': s, 'lowscore': 0, 'bkcc': bkcc, 'kldm': kldm,
                     'years': 15, 'start': 0})

    with open(seeds, 'w') as f:
        for j in jobs:
            f.write(str(j) + '\n')
        f.flush()


def split_seeds(sf, size, new_name=None, rates=None):
    if new_name == None:
        new_name = sf
    if not isinstance(size, int):
        raise ValueError('size is required as int')
    if size == 0:
        raise ValueError('size must larger than 0')
    if rates is None:
        rates = [1.0 / size] * size
    else:
        if not isinstance(rates, list):
            raise ValueError('rates is require as list or None')
        for r in rates:
            if not isinstance(r, float) and not isinstance(r, int):
                raise ValueError('all elements in rates are required to be numeric')
            if r < 0:
                raise ValueError('all elements in rates are required to be not negative')
        if len(rates) > size:
            rates = rates[:size]
        ss = sum(rates)
        if ss > 0:
            ce = []
            for r in rates:
                ce.append(r * 1.0 / ss)
            rates = ce

    links = []
    with open(sf, 'r') as f:
        for l in f:
            links.append(l)
    s = len(links)
    cs = []
    for r in rates:
        cs.append(int(r * s))
    count = 0
    fidx = 0
    fs = []
    cc = 0
    for i in range(1, size + 1):
        s1 = open(new_name + '.' + str(i), 'w')
        fs.append(s1)
    while count < s and len(links) > 0 and fidx < size:
        if cs[fidx] > cc:
            seed = random.choice(links)
            fs[fidx].write(seed)
            links.remove(seed)
            cc += 1
            count += 1
        else:
            cc = 0
            fidx += 1
    if len(links) > 0:
        fidx = 0
        while fidx < size and cs[fidx] == 0:
            fidx += 1
        if 0 <= fidx < size:
            for l in links:
                fs[fidx].write(l)
    for f in fs:
        f.flush()
        f.close()
    return s
