#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import json
import logging
import re
import sys
import time

from court.cspider import JobSpliter, ATOSSessionCourtSpider, ETOSSessionCourtSpider
from court.save import CourtStore, LinkSaver
from court.util import date_cs2num
from spider import spider
from spider.captcha.lianzhong import LianzhongCaptcha


class ShenzhenSpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class ShenzhenCourtStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'sz_court')

    def parse_time(self):
        time_str = re.search(r'<meta name="meta:save-date" content="([^"]*)">',
                             self.get_cur_doc().cur_content)
        if time_str:
            return date_cs2num(time_str.group(1)[:10])
        return None


class ShenzhenCourtSpider(ETOSSessionCourtSpider):
    "深圳法院诉讼服务平台爬虫"

    def __init__(self, thread_count=1, list_only=False, save_link=False, from_link=False, recover=False, seeds='seeds'):
        super(ShenzhenCourtSpider, self).__init__(thread_count)
        self._name = 'ShenzhenCourt'
        self.pagestore = ShenzhenCourtStore()
        self.job_spliter = ShenzhenSpliter()
        self._captcha_times = range(0, thread_count)
        self.test_mode = False
        self.pagesize = 50
        self.list_only = list_only
        self.save_link = save_link
        self.link_saver = None
        self.seeds = seeds
        if self.save_link:
            self.link_saver = LinkSaver('saved.links', 'a+b')
        self.from_link = from_link
        self.recover = recover

    def dispatch(self):
        if self.from_link:
            links = []
            with open(self.seeds, 'r') as f:
                for l in f:
                    if len(l) > 0:
                        if l[:4] == 'http':
                            links.append(l.strip())
                        else:
                            links.append(l.strip().split(',')[-1])
            if self.recover:
                tmp = links
                links = []
                for l in tmp:
                    if not self.pagestore.find_any(self.pagestore.channel + '://' + self.extract_paper_id(l)):
                        links.append(l)
            for l in links:
                self.add_job({'type': 'paper', 'url': l})
            print 'add %d paper links' % len(links)
            logging.info('add %d paper links', len(links))
        else:
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
        con = super(ShenzhenCourtSpider, self).request_url(url, **kwargs)
        if con and con.text:
            return self.check_captcha(con, url)
        return con

    def run_job(self, jobid):
        jt = jobid['type']
        url = jobid['url']
        if 'paper' == jt:
            if self.list_only:
                return
            con = self.request_url(url)
            '''check exception'''
            if self.check_exceptions(con, jobid):
                return
                # con = self.check_captcha(con.text, url)
            u = re.search(r'src=\'(\/temp\/ws\-[\d\w]+\-[\d\w]+.html)\'', con.text)
            if u is None:
                logging.warn('cannot find source page url in %s', url)
                return
            con = self.request_url('http://ssfw.szcourt.gov.cn/' + u.group(1))
            if con is None or con.text is None:
                logging.warn('source page is None %s', u.group(1))
                return
            context = self.extract_content(con.text)
            if context is not None:
                jid = self.extract_paper_id(url)
                if jid is not None:
                    self.pagestore.save(int(time.time()), jid, url, context)
                else:
                    logging.warn('failed to find paper id,page nodt save,%s', url)
                    print 'failed to find paper id, paper not save', url
                print url, '=>', len(context)
                logging.info('%s==>%d', url, len(context))
            else:
                print 'fail to find content for:', url
                logging.info('cannot find content %s', url)
            return

        con = self.request_url(url)
        if con is None:
            logging.error('failed to fetch list page %s', url)
            return

        if 'main' == jt:
            if self.need_split(con.text, url):
                self.split_url(url)
                logging.info('job is split %s', url)
                return
            self.add_list_job(url, con.text)
        urls = self.extract_paper_url(con.text)
        urls = spider.util.unique_list(urls)
        logging.info('%s add %d papers', url, len(urls))
        print 'add ', len(urls), 'paper urls', url
        if not self.list_only:
            for u in urls:
                self.add_job({'type': 'paper', 'url': u})
        if self.save_link:
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

    def check_exceptions(self, con, jobid):
        if con is None or con.text is None:
            logging.error('failed to fetch paper page %s', jobid['url'])
            print 'failed to fetch page %s' % jobid['url']
            self.re_add_job(jobid)
            return True
        m404 = re.search('\/temp\/judgedocument404\.jsp', con.text)
        if m404:
            logging.info('page %s is missing from the server', jobid['url'])
            print 'page %s is missing from the server' % jobid['url']
            return True
        return False

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
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


def test_extract_paper_url(sr):
    con = sr.request_url('http://ssfw.szcourt.gov.cn/frontend/anjiangongkai/JudgeDocument/21/?ajlb=2&fydm=440300')
    urls = sr.extract_paper_url(con.text)
    print urls


if __name__ == '__main__':
    # job = ShenzhenCourtSpider(4, True, True)
    job = ShenzhenCourtSpider(4, False, False, True, recover=True)
    # job.load_proxy('proxy', auto_change=False)
    job.test_mode = False
    resolve = 5
    if resolve == 2:
        with open('yzm.jpeg', 'rb') as f:
            con = f.read()
            code = job.resolve_captcha(con)
            print code
    elif resolve == 3:
        test_extract_paper_url(job)
    else:
        # job.load_proxy('proxy.txt')
        job.run()
