#!/usr/bin/env python
# -*- coding:utf8 -*-
import abc
import re
import time

from court.cspider import JobSpliter, CourtSpider
from court.save import CourtStore
from spider import spider


class CQNASpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class CQNACourtStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'cqna_court')


class CQNACourtSpider(CourtSpider):
    "重庆市南岸人民法院爬虫,http://www.cqnafy.gov.cn/Category_48/Index.aspx,http://www.cqnafy.gov.cn/Category_49/Index.aspx"

    def __init__(self, threadcnt):
        CourtSpider.__init__(self, threadcnt)
        self._name = 'cqnaCourt'
        self.pagestore = CQNACourtStore()
        self.job_spliter = CQNASpliter()

    def dispatch(self):
        self.add_main_job({'type': 'main', 'url': 'http://www.cqnafy.gov.cn/Category_49/Index.aspx'})
        self.add_main_job({'type': 'main', 'url': 'http://www.cqnafy.gov.cn/Category_48/Index.aspx'})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def need_split(self, context, url):
        return False

    def extract_content(self, context):
        m = re.findall(r'(<div class="main">.*)<div class="page">', context, re.S)
        if m:
            return m[0]
        return None

    def extract_paper_id(self, url):
        m = re.findall(r'http://www.cqnafy.gov.cn/Item/(\d+).aspx', url)
        if m is not None:
            return m[0]
        return None

    def extract_paper_url(self, content):
        m = re.findall(r'<ul class="newsList">.*<div class="page">', content, re.S)
        if not m:
            return None
        m = re.findall(ur'<a href="(/Item/\d+.aspx)" target="_blank" [^>]+>', m[0])
        if m is not None:
            urls = []
            for u in m:
                urls.append('http://www.cqnafy.gov.cn' + u)
            return urls
        return None

    def add_list_job(self, url, con):
        divs = re.findall(ur'<a href="Index_(\d+).aspx">尾页</a>', con)
        if divs:
            pagecnt = int(divs[0])
            for page in range(2, pagecnt + 1):
                self.add_job({'type': 'list',
                              'url': url[0:37] + ('Index_%d.aspx' % page)})
        else:
            print url, 'has no more page'

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


class CQNACourtTest():
    def test_extract_paper_id(self, url):
        job = CQNACourtSpider(1)
        print  job.extract_paper_id(url)


if __name__ == '__main__':
    job = CQNACourtSpider(5)
    job.load_proxy('proxy')
    job.run()
