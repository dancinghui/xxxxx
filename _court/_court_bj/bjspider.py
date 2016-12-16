#!/usr/bin/env python
# -*- coding:utf8 -*-
import datetime
import logging
import re
import threading
import time

from court.cspider import ProxySwapSpider
from court.save import LinkSaver, CourtStore, SpiderLinkStore
from court.util import Captcha


class FoodMakerLock():
    '''
    家里要做饭，规定先回来的一个人下厨，做什么由全体其他全体成员（不包括下厨的）决定
     首先先回来的进入厨房等待，当最后一个人回来时通知下厨的做什么菜，当做完菜的时候下厨的通知大家吃饭

     多个线程共用一个session抓取一个网页，网站限制用户过度抓取当访问量达到某一程度到时候要求用户输入一次验证码
     当遇到验证码的时候所有线程停下来，由第一个线程去验证验证码，当验证码改好后通知其他线程验证成功了
    '''

    def __init__(self, waiter_count):
        self.__lock = threading.RLock()
        self.__waiter_count = waiter_count
        if self.__waiter_count < 0:
            self.__waiter_count = 0
        self.__current_waiters = 0
        self.__current_waiters_lock = threading.RLock()
        self.__doing = False
        self.__waiters_ready = threading.Condition()

    def decrease(self):
        with self.__lock:
            if self.__waiter_count > 0:
                self.__waiter_count -= 1

    def success(self):
        with self.__lock:
            print 'reset condition', threading.currentThread().getName()
            self.__doing = False
        print 'captcha done', threading.currentThread().getName()
        self.__waiters_ready.notifyAll()
        print 'release waiter ready', threading.currentThread().getName()
        self.__waiters_ready.release()

    def reset(self):
        with self.__lock:
            self.__success = False
            self.__doing = False

    def wait(self):
        if self.__doing:
            self.__waiters_ready.acquire()
            with self.__current_waiters_lock:
                self.__current_waiters += 1
                print 'waiter is coming', threading.currentThread().getName()
                if self.__current_waiters >= self.__waiter_count:
                    print 'waiters are all here', threading.currentThread().getName()
                    self.__waiters_ready.notify()
            self.__waiters_ready.wait()
            print 'waiter wait for captcha resolving', threading.currentThread().getName()
            with self.__current_waiters_lock:
                print 'waiter is leaving', threading.currentThread().getName()
                self.__current_waiters -= 1
            self.__waiters_ready.release()
            return False
        else:
            self.__waiters_ready.acquire()
            print 'im lock down the done state', threading.currentThread().getName()
            print 'i am trying to resolve captcha', threading.currentThread().getName()
            self.__doing = True
            print 'im waiting for waiters ready', threading.currentThread().getName()
            self.__waiters_ready.wait()
            print 'im resolving captcha', threading.currentThread().getName()
            return True


class FoodMakerExtendLock():
    '''
     多个线程共用一个session抓取一个网页，网站限制用户过度抓取当访问量达到某一程度到时候要求用户输入一次验证码
     当遇到验证码的时候所有线程进入等待区停下来，由第一个线程去验证验证码，当验证码改好后通知其他线程验证成功了,
     这时其他线程离开等待区开始工作，最后一个离开的线程通知验证线程做好离开工作，最后验证线程才离开
    '''

    def __init__(self, waiter_count):
        self.__lock = threading.RLock()
        self.__waiter_count = waiter_count
        if self.__waiter_count < 0:
            self.__waiter_count = 0
        self.__current_waiters = 0
        self.__current_waiters_lock = threading.RLock()
        self.__doing = False
        self.__waiters_ready = threading.Condition()
        self._next_try_lock = threading.Lock()

    def decrease(self):
        with self.__lock:
            if self.__waiter_count > 0:
                self.__waiter_count -= 1

    def success(self):
        with self.__lock:
            print 'reset condition', threading.currentThread().getName()
            self.__doing = False
        self._next_try_lock.acquire()
        print 'captcha done', threading.currentThread().getName()
        self.__waiters_ready.notifyAll()
        print 'i am waiter leaving', threading.currentThread().getName()
        self.__waiters_ready.wait()
        print 'i am close the door', threading.currentThread().getName()
        self.__waiters_ready.release()
        self._next_try_lock.release()

    def reset(self):
        with self.__lock:
            self.__success = False
            self.__doing = False

    def wait(self):
        print 'waiting for next try lock', threading.currentThread().getName()
        self._next_try_lock.acquire()
        if self.__doing:
            print 'im am a waiter', threading.currentThread().getName()
            self._next_try_lock.release()
            print 'waiter %s release next try lock' % threading.currentThread().getName()
            print 'acquire waiters ready condition', threading.currentThread().getName()
            self.__waiters_ready.acquire()
            with self.__current_waiters_lock:
                self.__current_waiters += 1
                print 'waiter is coming', threading.currentThread().getName()
                if self.__current_waiters >= self.__waiter_count:
                    print 'waiters are all here', threading.currentThread().getName()
                    self.__waiters_ready.notify()
            self.__waiters_ready.wait()
            print 'waiter wait for captcha resolving', threading.currentThread().getName()
            with self.__current_waiters_lock:
                print 'waiter is leaving', threading.currentThread().getName()
                self.__current_waiters -= 1
                if self.__current_waiters == 0:
                    print 'all waiters leaved', threading.currentThread().getName()
                    self.__waiters_ready.notify()
            self.__waiters_ready.release()
            return False
        else:
            print 'im am the cook', threading.currentThread().getName()
            with self.__lock:
                print 'im setting doing true', threading.currentThread().getName()
                self.__doing = True
            # 给waiter 放行
            self.__waiters_ready.acquire()
            print 'im lock down the done state', threading.currentThread().getName()
            print 'i am trying to resolve captcha', threading.currentThread().getName()
            print 'im waiting for waiters ready', threading.currentThread().getName()
            self._next_try_lock.release()
            print 'i released next try_lock', threading.currentThread().getName()
            self.__waiters_ready.wait()
            print 'im resolving captcha', threading.currentThread().getName()
            return True

    def failed(self):
        self.success()


class StatisticsItem():
    def __init__(self):
        self.__mutex = threading.RLock()
        self.__count = 0

    def add(self):
        with self.__mutex:
            self.__count += 1

    def reset(self):
        with self.__mutex:
            self.__count = 0

    def count(self):
        return self.__count


class BJSpider(ProxySwapSpider):
    def __init__(self, thcnt, name='BeijingCourtSpider', link_saver='links', saver_mode='a', sleep=0.0,
                 proxy_life=180, captcha_limit=100):
        super(BJSpider, self).__init__(thcnt, proxy_life)
        self._name = name
        self.link_saver = LinkSaver(link_saver, saver_mode)
        self.total_content_failed = 0
        self.current_failed = StatisticsItem()
        self.linkstore = SpiderLinkStore('bj_court')
        # test parameters
        self.test_mode = False
        self._shutdown_in_test = False
        self.sleep = sleep
        self.captcha = FoodMakerExtendLock(thcnt - 1)
        self._shutdown = False
        self.captcha_times = 0
        self.captcha_limit = captcha_limit
        self.captcha_lock = threading.Lock()

    def check_if_blocked(self, content, url):
        '''check if proxy if blocked'''
        if re.search(ur'您访问的频率太高，请稍后再试|403', content):
            if self.test_mode:
                self._shutdown_in_test = True
                print '您访问的频率太高，请稍后再试'
                print 'run time ', (time.time() - self._start_timet)
            logging.error('spider has been block,%s' % url)
            return True
        return False

    def report(self):
        if self.link_saver:
            self.link_saver.flush()
        super(BJSpider, self).report()

    def check_exception(self, con, jobid):
        '''check if there are exception in response,true if exception are found and cannot be continue,
            false if no exception is found or exception is handled and is ok to continue'''
        if con is None:
            print 'null response'
            self.re_add_job(jobid)
            return True
        if con.text is None:
            print 'None content type'
            print con.headers
            self.re_add_job(jobid)
            return True
        if con.code >= 400:
            print con.headers
            if 502 == con.code:
                logging.error('proxy error 502 %s', jobid['url'])
                self.change_proxy()
                return True
            if 404 == con.code:
                print '啊呵,404,服务器上居然找不到这个页面', jobid['url']
                if re.search('Connection: close', con.headers):
                    self.re_add_job(jobid)
                    self.current_failed.add()
                    if self.current_failed.count() > 50:
                        self.change_proxy()
                logging.info('page not found on the server %s', jobid['url'])
                return True
            if 500 > con.code >= 400:
                print 'request error', jobid['url']
                self.re_add_job(jobid)
                return True
            if 600 > con.code >= 500:
                print 'server error', con.code, jobid['url']
                cnt = jobid.get('_failcnt_', 0)
                if cnt < 47:
                    jobid['_failcnt'] = 47
                self.re_add_job(jobid)
                return True
            print '600 以上的code,涨见识了！哈哈哈！', jobid['url']
            logging.info('failed with response code %d,%s', con.code, jobid['url'])
            self.re_add_job(jobid)
            return True
        if re.search(u'您访问的频率太高，请稍后再试', con.text):
            print u'我被封了', con.code
            self.on_server_blocked(jobid)
            return True
        return False

    def on_server_blocked(self, jobid):
        self.change_proxy()
        self.re_add_job(jobid)

    def with_sleep_request_url(self, url, **kwargs):
        time.sleep(self.sleep)
        return self.request_url(url, **kwargs)

    def resolve_captcha(self, url):
        if self.captcha.wait():
            count = 3
            con = None
            while count > 0 and con is None:
                con = self.request_url('http://www.bjcourt.gov.cn/yzm.jpg')
                count -= 1
            if con:
                with self.captcha_lock:
                    self.captcha_times += 1
                    if self.captcha_limit < self.captcha_times:
                        self.captcha.failed()
                        self._shutdown = True
                        print 'captcha exceeds limit,is going to shutdown'
                        return
                code = Captcha.resolve_with_lianzhong(con.content)
                print 'captcha code:', code
                # params = url.split('?')
                con = self.request_url('http://www.bjcourt.gov.cn/cpws/checkkaptcha.htm?yzm=' + code, data={})
                if con:
                    if "'success':true" in con.text:
                        self.captcha.success()
                        return self.request_url(url)
            self.captcha.failed()

    def check_captcha(self, url, con, jobid):
        m = re.search('yzmInput', con.text)
        if m:
            print 'thread', self.get_tid(), url, ' need captcha'
            con = self.resolve_captcha(url)
            if self.check_exception(con, jobid):
                return
            if re.search(r'yzmInput', con.text):
                self._shutdown = True
                self.link_saver.add('%d,%d,%s' % (2, 0, url))
                return
        return con


class CData():
    @staticmethod
    def split_param(url):
        if not re.search(r'\?', url):
            url += '?'
        url = re.sub(r'page=[0-9]+', 'page=1', url)
        urls = []
        if not re.search(r'jbfyId=[0-9]+', url):
            for fy in [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 29, 30]:
                urls.append('&'.join([url, 'jbfyId=%d' % fy]))
        elif not re.search(r'ajlb=[0-9]+', url):
            for ajlb in range(1, 6):
                urls.append('&'.join([url, 'ajlb=%d' % ajlb]))
        elif not re.search(r'sxnflx=[0-9]+', url):
            urls.append('&'.join([url, 'sxnflx=1']))
            urls.append('&'.join([url, 'sxnflx=2']))
        else:
            return CData.split_time(url)

        return urls

    time1990 = datetime.datetime(*time.strptime('1990-01-01', '%Y-%m-%d')[:3])
    time2000 = datetime.datetime(*time.strptime('2000-01-01', '%Y-%m-%d')[:3])
    time2010 = datetime.datetime(*time.strptime('2010-01-01', '%Y-%m-%d')[:3])

    @staticmethod
    def split_time(url):
        """
        时间不要早于1990-01-01，开始时间要晚于结束时间
        """
        urls = []

        if url.find('?') >= 0:
            if url[-1] != '&':
                url += '&'
        else:
            url += '?'
        if not re.search(r'startCprq|endCprq', url):
            ly = datetime.datetime.today() - datetime.timedelta(days=365)
            lystr = ly.strftime('%Y-%m-%d')
            urls.append(url + 'startCprq=%s&endCprq=' % lystr)
            urls.append(url + 'startCprq=&endCprq=%s' % lystr)
            return urls
        ft = re.search(r'startCprq=([0-9-]+)', url)
        tt = re.search(r'endCprq=([0-9-]+)', url)
        url = re.sub(r'startCprq=[0-9-]*', '', url)
        url = re.sub(r'endCprq=[0-9-]*', '', url)
        url = re.sub(r'&{2,}', '&', url)

        if not ft:
            oldtime = time.strptime('1990-01-01', '%Y-%m-%d')
        else:
            oldtime = time.strptime(ft.group(1), '%Y-%m-%d')
        if not tt:
            newtime = time.strptime(datetime.datetime.today().strftime('%Y-%m-%d'), '%Y-%m-%d')
        else:
            newtime = time.strptime(tt.group(1), '%Y-%m-%d')
        oldtime = datetime.datetime(*oldtime[:3])
        newtime = datetime.datetime(*newtime[:3])
        timearr = CData.split_to_time_arr(oldtime, newtime)
        l = len(timearr) - 1
        i = 0
        while i < l:
            urls.append(url + ('startCprq=%s&endCprq=%s' % (timearr[i].strftime('%Y-%m-%d'),
                                                            timearr[i + 1].strftime('%Y-%m-%d'))))
            i += 1
        return urls

    @staticmethod
    def split_to_time_arr(oldtime, newtime):
        if newtime > CData.time2010 > oldtime:
            return [oldtime, CData.time2010, newtime]
        elif newtime > CData.time2000 > oldtime:
            return [oldtime, CData.time2000, newtime]
        delta = newtime - oldtime
        if delta.days > 365:
            delta = datetime.timedelta(days=365)
        elif delta.days > 30:
            delta = datetime.timedelta(days=30)
        elif delta.days > 1:
            delta = datetime.timedelta(days=delta.days / 2)
        return CData.gen_date_arr(oldtime, newtime, delta)

    @staticmethod
    def gen_date_arr(f, t, delta):
        if not isinstance(f, datetime.datetime) or not isinstance(t, datetime.datetime):
            return []
        else:
            tt = f
            arr = []
            while tt < t:
                arr.append(tt)
                tt += delta
            arr.append(t)
        return arr


class BJCourtStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'bj_court')
