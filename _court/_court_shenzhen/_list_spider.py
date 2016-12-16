#!/usr/bin/env python
# -*- coding:utf8 -*-

import copy
import json
import logging
import re
import sys
import time

from _court_shenzhen import ShenzhenSpliter
from court.cspider import ETOSSessionCourtSpider
from court.save import LinkSaver, CourtStore
from spider import spider
from spider.captcha.lianzhong import LianzhongCaptcha


class ShenzhenCourtListSpider(ETOSSessionCourtSpider):
    "深圳法院诉讼服务平台爬虫"

    def __init__(self, thread_count=1, full_mode=False, seeds='seeds'):
        super(ShenzhenCourtListSpider, self).__init__(thread_count, 'list.spider.log')
        self._name = 'ShenzhenListSpider'
        self.job_spliter = ShenzhenSpliter()
        self._captcha_times = range(0, thread_count)
        self.test_mode = False
        self.pagesize = 50
        self.full_mode = full_mode
        self.link_saver = LinkSaver(seeds, 'a')

    def dispatch(self):

        self.add_main_job({'type': 'main',
                           'url': 'http://ssfw.szcourt.gov.cn/frontend/anjiangongkai/JudgeDocument/25?ajlb=2&fydm=440300&page=1&pageLimit=%d&caseNo=' % self.pagesize})
        self.add_main_job({'type': 'main',
                           'url': 'http://ssfw.szcourt.gov.cn/frontend/anjiangongkai/JudgeDocument/25?ajlb=2&fydm=440301&page=1&pageLimit=%d&caseNo=' % self.pagesize})
        self.add_main_job({'type': 'main',
                           'url': 'http://ssfw.szcourt.gov.cn/frontend/anjiangongkai/JudgeDocument/25?ajlb=2&fydm=440302&page=1&pageLimit=%d&caseNo=' % self.pagesize})
        self.add_main_job({'type': 'main',
                           'url': 'http://ssfw.szcourt.gov.cn/frontend/anjiangongkai/JudgeDocument/25?ajlb=2&fydm=440303&page=1&pageLimit=%d&caseNo=' % self.pagesize})
        self.add_main_job({'type': 'main',
                           'url': 'http://ssfw.szcourt.gov.cn/frontend/anjiangongkai/JudgeDocument/25?ajlb=2&fydm=440304&page=1&pageLimit=%d&caseNo=' % self.pagesize})
        self.add_main_job({'type': 'main',
                           'url': 'http://ssfw.szcourt.gov.cn/frontend/anjiangongkai/JudgeDocument/25?ajlb=2&fydm=440305&page=1&pageLimit=%d&caseNo=' % self.pagesize})
        self.add_main_job({'type': 'main',
                           'url': 'http://ssfw.szcourt.gov.cn/frontend/anjiangongkai/JudgeDocument/25?ajlb=2&fydm=440306&page=1&pageLimit=%d&caseNo=' % self.pagesize})
        self.add_main_job({'type': 'main',
                           'url': 'http://ssfw.szcourt.gov.cn/frontend/anjiangongkai/JudgeDocument/25?ajlb=2&fydm=440307&page=1&pageLimit=%d&caseNo=' % self.pagesize})

        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def thread_init(self, tid):
        self._captcha_times[tid] = 0

    def check_captcha(self, con, url):
        m = re.search(u'.*需要验证，请输入验证码.*', con.text)
        if m:
            print m.group()
            tid = getattr(self._tls, 'tid', -1)
            if tid < 0:
                sys.stderr.write('invalid thread id in run_job')
                raise RuntimeError('Invalid tid')
            c = 0
            while c < 10:
                img = self.get_captcha(tid)
                self._captcha_times[tid] += 1
                c += 1
                if not img:
                    continue
                code = self.resolve_captcha(img)
                if not code:
                    continue
                success = self.post_captcha(code, None)
                logging.info('captcha times:%d', self._captcha_times[tid])
                if self.test_mode:
                    print "captcha times: ", self._captcha_times[tid]
                if success == 'true':
                    if re.split(r'\/anjiangongkai\/JudgeDocument', url):
                        u = url + '?code=' + code
                    else:
                        u = url + '&code=' + code
                    con = self.request_url(u)
                    return con
        else:
            if self.test_mode:
                print 'do not need resolve captcha', url
                logging.warn('do not need resolve captcha %s', url)
        return con

    def request_url(self, url, **kwargs):
        con = super(ShenzhenCourtListSpider, self).request_url(url, **kwargs)
        if con and con.text:
            return self.check_captcha(con, url)
        return con

    def check_exception(self, con, jobid):
        if con is None:
            print '回应是None,你说怎么办吧', jobid['url']
            self.re_add_job(jobid)
            return True
        if con.text is None:
            print 'response text是None', jobid['url']
            self.re_add_job(jobid)
            return True
        m = re.search(
            r'<!DOCTYPE html><html><head><meta charset=utf-8><\/head><\/head><body><script>window.location=\'([^\']*)\'<\/script><\/body><\/html>',
            con.text)
        if m:
            url = 'http://ssfw.szcourt.gov.cn' + m.group(1)
            self.add_job({'type': jobid['type'], 'url': url})
            print 'js 页面跳转,目的地是', url
            return True

    def run_job(self, jobid):
        jt = jobid['type']
        url = jobid['url']

        con = self.request_url(url)
        if self.check_exception(con, jobid):
            return

        if self.need_split(con.text, url):
            self.split_url(url)
            logging.info('job is split %s', url)
            return
        if jt == 'main':
            self.add_list_job(url, con.text)
        urls = self.extract_paper_url(con.text)
        urls = spider.util.unique_list(urls)
        logging.info('%s add %d papers', url, len(urls))
        print 'add', len(urls), 'paper urls', url
        if len(urls) == 0:
            pass
        if self.full_mode:
            m = re.search(
                r'http:\/\/ssfw.szcourt.gov.cn\/frontend\/anjiangongkai\/JudgeDocument\/(\d+)\?ajlb=(\d+)&fydm=(\d+)&page=(\d+)&pageLimit=(\d+)&caseNo='
                , url)
            if m:
                tp = m.group(1)
                ajlb = m.group(2)
                fydm = m.group(3)
                page = m.group(4)
                size = m.group(5)
                for u in urls:
                    self.link_saver.add('%s,%s,%s,%s,%s,%s' % (tp, ajlb, fydm, page, size, u))
        else:
            for u in urls:
                self.link_saver.add(u)

    def need_split(self, context, url):
        return False

    def extract_content(self, context):
        return context

    def extract_paper_id(self, url):
        m = re.findall(r'anjiangongkai\/JudgeDocument\/(\d+)\/information\/([\d\w]+)\/([\d\w]+)\/', url)
        if len(m) > 0:
            return '-'.join(m[0])
        return None

    def extract_paper_url(self, content):
        m = re.findall(r'<a href="(\/frontend\/anjiangongkai\/JudgeDocument\/\d+\/information\/[^"]*)">',
                       content)
        if m is not None:
            urls = []
            for u in m:
                urls.append('http://ssfw.szcourt.gov.cn' + u)
            return urls
        return None

    def add_list_job(self, url, con):
        divs = re.findall(ur'\(\d+条记录，每页\d+条记录，共(\d+)页\)', con)
        if divs:
            pagecnt = int(divs[0])
            print 'add ', pagecnt, 'list url,', url
            logging.info('add %d list url from %s', pagecnt, url)
            for page in range(2, pagecnt + 1):
                self.add_job({'type': 'list', 'url': re.sub(r'page=\d+?', 'page=%d' % page, url)})
        else:
            print url, 'has no more page'
            logging.info('no list page for %s', url)

    def post_captcha(self, code, session):
        # url = 'http://ssfw.szcourt.gov.cn/frontend/validateRandCode?code=%s' % (code)
        if session is None:
            url = 'http://ssfw.szcourt.gov.cn/frontend/validateRandCode?code=%s' % code
        else:
            url = 'http://ssfw.szcourt.gov.cn/frontend/validateRandCode;jsessionid=%s?code=%s' % (session, code)
        con = self.request_url(url, data={})
        if con:
            if self.test_mode:
                print "post captcha cookies:", con.cookies
                # print "post captcha headers:", con.headers
                print 'captcha resolve result', con.text
            res = json.loads(con.text)
            return res['success']
        else:
            print 'None response'
        return None

    def resolve_captcha(self, img):
        server = LianzhongCaptcha()
        points = server.point_check()
        if points <= 0:
            print 'there are no more points'
            return
        print 'There are %d points remaining' % points

        captcha = server.resolve(img)
        if self.test_mode:
            print 'resolved captcha', captcha
        return captcha

    def get_captcha(self, tid):
        con = self.request_url('http://ssfw.szcourt.gov.cn/yzm.jsp')
        if con is None:
            print "get none captcha response"
            return
        context = copy.deepcopy(con.content)
        print '====get_captcha===='
        # print 'headers:', con.headers
        print 'cookies:', con.cookies
        return context

    @staticmethod
    def get_session_id(con):
        if isinstance(con, str) or isinstance(con, unicode):
            m = re.search(r'JSESSIONID=([\w\d]+)', con)
            if m is None:
                m = re.search(r'jsessionid=([\w\d]+)', con)
        else:
            m = re.search(r'jsessionid=([\w\d]+)', con.text)
        if m:
            return m.group(1)
        else:
            return None

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "Court Spider:%s\n" % self._name
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


def test_extract_paper_url(sr):
    con = sr.request_url('http://ssfw.szcourt.gov.cn/frontend/anjiangongkai/JudgeDocument/21/?ajlb=2&fydm=440300')
    urls = sr.extract_paper_url(con.text)
    print urls


if __name__ == '__main__':
    job = ShenzhenCourtListSpider(4, full_mode=True)
    # job.load_proxy('proxy', auto_change=False)
    job.test_mode = False

    job.run()
