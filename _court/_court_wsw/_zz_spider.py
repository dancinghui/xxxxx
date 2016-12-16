#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import threading
import time

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from wswsave import WenshuCourtStore
from court.cspider import ATOSSessionCourtSpider
from spider import spider
from spider.httpreq import SessionRequests


class WenshuCourtSpider(ATOSSessionCourtSpider):
    "文书网裁判文书爬虫"

    def __init__(self, thread_count, seeds=None, name='ZhengzhouCourtSpider'):
        super(WenshuCourtSpider, self).__init__(thread_count)
        self._name = name
        self.seeds = seeds
        self.pagestore = WenshuCourtStore()
        self._cookie_lock = threading.RLock()
        self._is_cookie_loaded = False
        self._mutex_time_out = 10
        self._cookies = None

    def dispatch(self):
        for seed in self.seeds:
            self.add_main_job({'type': 'main', 'url': seed})

        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    @staticmethod
    def load_cookies(url):
        driver = webdriver.Firefox()
        driver.get(url)
        cookies = driver.get_cookies()
        driver.close()
        return cookies

    def set_cookies(self, url):
        self._cookie_lock.acquire()
        if not self._is_cookie_loaded:
            cookies = WenshuCourtSpider.load_cookies(url)
            if len(cookies) > 0:
                for c in cookies:
                    self.add_cookie(c['domain'], c['name'], c['value'], path=c['path'], secure=c['secure'])
                self._cookies = cookies
                self._is_cookie_loaded = True
        self._cookie_lock.release()

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            print 'Job must be dict,but got', type(jobid)
            return
        jt = jobid['type']
        url = jobid['url']

        if 'main' == jt:
            driver = webdriver.Firefox()
            driver.get(url)
            if not self._is_cookie_loaded:
                self._cookie_lock.acquire()
                cookies = driver.get_cookies()
                if len(cookies) > 0:
                    for c in cookies:
                        self.add_cookie(c['domain'], c['name'], c['value'], path=c['path'], secure=c['secure'])
                    self._cookies = cookies
                    self._is_cookie_loaded = True
                self._cookie_lock.release()
            count = 0
            total_count = re.search(r'<span id="span_datacount" style="color:red;">(\d+)<\/span>', driver.page_source)
            if total_count:
                total_count = total_count.group(1)
            else:
                total_count = 1
            pcnt = (total_count + 2) / 5
            while count < pcnt:  # 一页五篇
                urls = self.extract_paper_url(driver.page_source)
                for u in urls:
                    self.add_job({'type': 'paper', 'url': u})
                count += 1
                try:
                    next_button = driver.find_element_by_xpath('//*[@id="pageNumber"]/a[6]')
                except NoSuchElementException:
                    break
                if next_button is None or next_button.text != u'下一页':
                    break
                next_button.click()
            driver.close()

        else:
            if not self._is_cookie_loaded:
                self.re_add_job(jobid)
                return
            con = self.request_url(url)
            if con is None:
                print 'fail to request', url
                return
            content = self.extract_content(con.text)
            jid = self.extract_paper_id(con.text)
            self.pagestore.save(int(time.time()), jid, url, content)

    def extract_paper_id(self, url):
        m = re.search(r'DocID=([\w\d-]+)', url)
        if m:
            return m.group(1)
        return None

    def extract_paper_url(self, content):
        m = re.findall(r'<a href="(\/content\/content\?[^"]*)', content)
        urls = []
        for u in m:
            urls.append('http://wenshu.court.gov.cn/' + u)
        return urls

    def extract_content(self, content):
        return content

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "Court Spider:%s\n" % self._name
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass

    def post_search(self, url, data):
        con = self.request_url(url, data=data)
        if con:
            print con.text


def test_fetch_paper(url):
    rq = SessionRequests()
    con = rq.request_url(url)
    print con.headers
    print con.cookies
    print con.text
    con = rq.request_url(url)
    print con.text
    print con.headers
    print con.cookies


def load_url_with_cookies(url, cookies):
    rq = SessionRequests()
    for c in cookies:
        rq.add_cookie(c['domain'], c['name'], c['value'], path=c['path'], secure=c['secure'])
    con = rq.request_url(url)
    if con:
        print con.text
        print con.cookies


def load_cookie_with_sele(url):
    driver = webdriver.Firefox()
    driver.get(url)
    cookies = driver.get_cookies()
    driver.close()
    return cookies


if '__main__' == __name__:
    seeds = [
        'http://wenshu.court.gov.cn/List/List?sorttype=1&conditions=searchWord+%E6%B2%B3%E5%8D%97%E7%9C%81%E9%83%91%E5%B7%9E%E5%B8%82%E4%B8%AD%E7%BA%A7%E4%BA%BA%E6%B0%91%E6%B3%95%E9%99%A2+++%E4%B8%AD%E7%BA%A7%E6%B3%95%E9%99%A2:%E6%B2%B3%E5%8D%97%E7%9C%81%E9%83%91%E5%B7%9E%E5%B8%82%E4%B8%AD%E7%BA%A7%E4%BA%BA%E6%B0%91%E6%B3%95%E9%99%A2']
    mode = 2
    if mode == 1:
        print 'Hello'
    elif mode == 2:
        test_fetch_paper('http://wenshu.court.gov.cn/content/content?DocID=43241722-9e3e-45e3-af0d-64c8e4c7f0b8')
    elif mode == 3:
        cookies = load_cookie_with_sele(
            'http://wenshu.court.gov.cn/content/content?DocID=43241722-9e3e-45e3-af0d-64c8e4c7f0b8')
        print cookies
    elif mode == 4:
        url = 'http://wenshu.court.gov.cn/content/content?DocID=43241722-9e3e-45e3-af0d-64c8e4c7f0b8'
        cookies = load_cookie_with_sele(url)
        print cookies
        load_url_with_cookies(url, cookies)

    else:
        job = WenshuCourtSpider(1, seeds)
        job.load_proxy('proxy')
        job.run()
