#!/usr/bin/env python
# -*- coding:utf8 -*-
import os
import re
import sys
import time

from court.cspider import JobSpliter, CourtSpider
from court.save import CourtStore, LinkSaver
from court.util import date_cs2num, cs_date_pattern_recent
from spider import spider


class FSSpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class FSCourtStore(CourtStore):
    def __init__(self,channel='fs_court'):
        CourtStore.__init__(self, channel)

    def parse_time(self):
        time_str = re.findall(cs_date_pattern_recent, self.get_cur_doc().cur_content)
        if time_str:
            return date_cs2num(time_str[0])
        return None


class FSCourtSpider(CourtSpider):
    "佛山法院爬虫"

    def __init__(self, threadcnt, list_seeds=None):
        CourtSpider.__init__(self, threadcnt)
        self._name = 'FoshanCourt'
        self.pagestore = FSCourtStore()
        self.job_spliter = FSSpliter()
        self._test_mode = True
        self.page_size = 20
        self.list_seeds = list_seeds

    def run_job(self, jobid):
        if not isinstance(jobid, dict) or not jobid.has_key('type') or not jobid.has_key('url'):
            raise ValueError('invalid jobid')
        jt = jobid['type']
        url = jobid['url']

        if 'paper' == jt:
            print url
            con = self.request_url(url)
            context = None
            if con is None or con.text is None:
                context = None
            else:
                u = re.search(ur'\$\("#xl_content"\)\.load\("(/CourtProject//upload/cpws/[-/\d]+.htm)"\);', con.text)
                if u:
                    con = self.request_url('http://www.fszjfy.gov.cn/' + u.group(1))
                    if con is None or con.text is None:
                        context = None
                    else:
                        context = self.extract_content(con.text)
            if context is not None:
                jid = self.extract_paper_id(url)
                if jid is not None:
                    self.pagestore.save(int(time.time()), jid, url, context)
                else:
                    print 'failed to find paper id, paper not save', url
                print url, '=>', len(context)
            else:
                print 'fail to find content for:', url
            return

        if 'main' != jt or not jobid.has_key('page'):
            raise ValueError('Invalid main job id')

        page = jobid['page']
        urls = self.post_page(page, url)
        if len(urls) == 0:
            print 'no page url found at', page
            return
        elif self._test_mode:
            print 'add job', len(urls)
        urls = spider.util.unique_list(urls)
        for u in urls:
            self.add_job({'type': 'paper', 'url': u})

    def dispatch(self):
        if self.list_seeds:
            with open(self.list_seeds, 'r') as f:
                for l in f:
                    if l[:4] == 'http':
                        self.add_main_job({'type': 'paper', 'url': l.strip()})
                    else:
                        job = l.split(',', 3)
                        if len(job) >= 2:
                            self.add_main_job({'type': 'paper', 'url': 'http://www.fszjfy.gov.cn%s' % job[1]})
            pass
        else:
            count = self.fetch_paper_count()
            for page in range(1, count / self.page_size + 1):
                self.add_main_job({'type': 'main',
                                   'url': 'http://www.fszjfy.gov.cn/CourtProject/index/index-cpws!search.action#',
                                   'page': page})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def fetch_paper_count(self):
        con = self.request_url('http://www.fszjfy.gov.cn/CourtProject/index/index-cpws!search.action#')
        count = 0
        if con:
            size = re.search(r'<input value="(\d+)" id="pageSize"', con.text)
            pages = re.search(r'<input value="(\d+)" id="pageTotal"', con.text)
            if pages:
                pages = int(pages.group(1))
            else:
                pages = 1
            if size:
                count = int(size.group(1)) * pages
        return count

    def need_split(self, context, url):
        return False

    def extract_content(self, context):
        return context

    def extract_paper_id(self, url):
        m = re.findall(r'id=([\w\d]+)', url)
        if m is not None:
            return m[0]
        return None

    def extract_paper_url(self, content):
        m = re.findall(r'<a href="(/CourtProject/index/index-cpws!getCpwsxl.action\?id=\d+)"', content)

        urls = []
        for u in m:
            urls.append('http://www.fszjfy.gov.cn/' + u)
        return urls

    def add_list_job(self, url, con):
        pass

    def post_page(self, page, url):
        data = {'pageNo': page,
                'pageSize': self.page_size,
                'search': '',
                'ah': '',
                'startTime': '',
                'endTime': '',
                'ajyear': '',
                'ahtxt': '',
                'ajfymc': '',
                'ajlb': '',
                'fymc': '0'}
        con = self.request_url(url, data=data)
        time.sleep(1)
        if con is None:
            return None
        return self.extract_paper_url(con.text)

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "Court Spider:%s\n" % self._name
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


def test_post_page():
    job = FSCourtSpider(1)
    job.load_proxy('proxy')
    job.post_page(2, 'http://www.fszjfy.gov.cn/CourtProject/index/index-cpws!search.action#')


if __name__ == '__main__':
    mode = 3
    if mode == 2:
        test_post_page()
    else:
        thcnt = 5
        if 3 == mode:
            job = FSCourtSpider(thcnt, 'seed.txt')
        else:
            job = FSCourtSpider(thcnt)
        # job.load_proxy('proxy')
        job.run()
