#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import os
import re
import time
from urllib import urlencode

from court.cspider import JobSpliter, CourtSpider
from court.doc2txt import Doc2Txt
from court.save import CourtStore
from court.util import date_cs2num
from genq import WLMQGenQuery
from spider.httpreq import BasicRequests, SessionRequests


class WLMQSpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class WLMQCourtStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'wlmq_court')

    def parse_time(self):
        m = re.search(ur'[一二三四五六七八九〇零○Ｏ十]{4}年[一二三四五六七八九〇Ｏ十○]{1,2}月[一二三四五六七八九〇Ｏ零○十]{1,3}日',
                      self.get_cur_doc().cur_content)
        if m:
            return date_cs2num(m.group())
        else:
            return None


def remove_file(file):
    if os.path.exists(file) and os.path.isfile(file):
        os.remove(file)


class WLMQCourtSpider(CourtSpider):
    "乌鲁木齐市若干相同模板法院法律文书爬虫"

    def __init__(self, threadcnt):
        CourtSpider.__init__(self, threadcnt)
        self._name = 'WulumuqiCourt'
        self.pagestore = WLMQCourtStore()
        self.job_spliter = WLMQSpliter()
        self._test_mode = False
        Doc2Txt.init()

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        jt = jobid['type']
        url = jobid['url']

        if 'paper' == jt:
            print url
            context = Doc2Txt.extract_from_file(url)
            if isinstance(context, unicode):
                context = context.encode('utf-8')
            if context is not None:
                jid = self.extract_paper_id(url)
                if jid is not None:
                    self.pagestore.save(int(time.time()), jid[0], url, context.strip())
                print url, '=>', len(context)
            else:
                print 'fail to find content for:', url
            return

        if 'main' != jt:
            return
        host = self.extract_host(url)
        param = jobid['param']
        param['hdPageIndex'] = jobid['page']
        param['__EVENTTARGET'] = 'btnNext'
        con = self.request_url(url, data=param)
        urls = self.extract_paper_url_with_host(con.text, host)
        for u in urls:
            self.add_job({'type': 'paper', 'url': host + u})

    def dispatch(self):
        fn = 'jobs'
        if not os.path.exists(fn):
            gen = WLMQGenQuery(fn)
            gen.run()
        with open(fn, 'r') as f:
            for l in f:
                p = eval(l.strip())
                for page in range(0, int(p['page_count'])):
                    self.add_main_job(
                        {'type': 'main', 'url': p['url'], 'page': page, 'param': p['param']})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def need_split(self, context, url):
        return False

    def extract_content(self, context):
        return context

    def extract_paper_id(self, url):
        m = re.findall(r'/([\w\d_]+)\.(pdf|doc)', url)
        if len(m) > 0:
            return m[0]
        return None

    def extract_paper_url_with_host(self, content, host):
        m = re.findall(r'href=\' (cpwsplay.aspx?[^\']+)\'', content)
        urls = []
        for u in m:
            url = host + u.strip()
            con = self.request_url(url)
            if con is not None:
                link = re.search(r'<iframe src="([^"]+)"', con.text)
                if link:
                    link = link.group(1).strip()
                    if link != 'about:blank':
                        urls.append(link)
        return urls

    def add_list_job(self, url, con):
        if re.search(r'btnNext', con):
            self.add_job({'type': 'main', 'url': url})
        else:
            print 'This is the last page'

    def post_for_list(self, url, data):
        con = self.request_url(url, data=data)
        urls = []
        if con and con.text:
            urls = self.extract_paper_url(con.text)
        return urls

    def extract_host(self, url):
        return re.search(r'^\w+:\/\/[^\/]*/', url).group()


def test_read_jobs():
    ps = []
    keys = []
    with open('jobs', 'r') as f:
        for l in f:
            p = eval(l)
            ps.append(p)
            print len(p['param'].keys())
            if len(keys) < len(p['param'].keys()):
                keys = p['param'].keys()
    for k in keys:
        print k, '\t',
        for p in ps:
            if p['param'].has_key(k):
                print p['param'][k], '|',
            else:
                print '|',
        print ''


def test_post_list():
    ll = []
    with open('jobs', 'r') as f:
        for s in f:
            ll.append(s)
    l = ll[3]
    print l
    v = eval(l.encode('utf-8'))
    if not isinstance(v, dict):
        return
    p = copy.deepcopy(v['param'])
    if not isinstance(p, dict):
        return
    print p.keys()
    # p['__EVENTARGUMENT'] = ''
    p['hdPageIndex'] = '10'
    # p.pop('hdPageIndex')
    # p.pop('__VIEWSTATE')
    if p.has_key('__LASTFOCUS'):
        p.pop('__LASTFOCUS')
    # p.pop('__EVENTVALIDATION')
    p['__EVENTTARGET'] = 'btnNext'

    print len(p)
    rq = SessionRequests()
    # con = rq.request_url(v['url'])
    # if con and con.text:
    #     m = re.search(r'<title.*', con.text)
    #     if m:
    #         print m.group()
    #     else:
    #         print len(con.text)
    data = urlencode(p)
    con = rq.request_url(v['url'], data=p)
    print p
    if con and con.text:
        m = re.search(r'<title.*', con.text)

        print con.text


if __name__ == '__main__':
    job = WLMQCourtSpider(5)
    job.load_proxy('proxy')
    job.run()
    # test_read_jobs()
    # test_post_list()
