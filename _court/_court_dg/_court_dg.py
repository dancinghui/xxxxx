#!/usr/bin/env python
# -*- coding:utf8 -*-
import abc
import re
import time
from uuid import uuid4

from docx2txt import docx2txt

from court.cspider import JobSpliter, CourtSpider
from court.doc2txt import Doc2Txt
from court.save import CourtStore
from court.util import remove_file, date_cs2num
from spider import spider


class DGSpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class DGCourtStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'dg_court')

    def parse_time(self):
        timestr = re.search(ur'[一二三四五六七八九〇○O0ОＯ零十 ]+年[一二三四五六七八九〇0十O○ОＯ ]+月[一二三四五六七八九〇零○O0ОＯ十 ]+日',
                            self.get_cur_doc().cur_content)
        if timestr:
            return date_cs2num(timestr.group().replace(' ', ''))
        return None


class DGCourtSpider(CourtSpider):
    "东莞市第一法院爬虫"

    def __init__(self, threadcnt):
        CourtSpider.__init__(self, threadcnt)
        self._name = 'dgCourt'
        self.pagestore = DGCourtStore()
        self.job_spliter = DGSpliter()
        Doc2Txt.init()

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        jt = jobid['type']
        url = jobid['url']

        if 'paper' == jt:
            context = Doc2Txt.extract_from_file(url)
            if context is not None:
                jid = self.extract_paper_id(url)
                if jid is not None:
                    self.pagestore.save(int(time.time()), jid, url, context.strip())
                else:
                    print 'failed to find paper id, paper not save', url
                print url, '=>', len(context)
            else:
                print 'fail to find content for:', url
            return

        con = self.request_url(url)
        if con is None:
            print 'None response for', url
            return

        if 'main' == jt:
            if self.need_split(con.text, url):
                self.split_url(url)
                return
            self.add_list_job(url, con.text)
        urls = self.extract_paper_url(con.text)
        urls = spider.util.unique_list(urls)
        for url in urls:
            self.add_job({'type': 'paper', 'url': url})

    def dispatch(self):
        self.add_main_job({'type': 'main', 'url': 'http://dyfy.dg.gov.cn/sfgk/cpws.html?&scbz=0&start=0&s=0'})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def need_split(self, context, url):
        return False

    def extract_content(self, context):
        # TODO shall I extract text from doc
        return context

    def extract_paper_id(self, url):
        m = re.findall(r'http://dyfy.dg.gov.cn/sfgk/cpws-download-(\d+).html', url)
        if len(m) > 0:
            return m[0]
        return None

    def extract_paper_url(self, content):
        m = re.findall(ur'<td><a href="(.*)" target="_blank">下载</a></td>', content)

        urls = []
        for u in m:
            urls.append('http://dyfy.dg.gov.cn' + u)
        return urls

    def add_list_job(self, url, con):
        divs = re.findall(ur'<span>共 (\d+) 页</span>', con)
        if divs:
            pagecnt = int(divs[0])
            for page in range(1, pagecnt):
                self.add_job({'type': 'list',
                              'url': ('http://dyfy.dg.gov.cn/sfgk/cpws.html?&scbz=0&start=0&s=%d' % (page * 15))})
        else:
            print url, 'has no more page'

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


class DGCourtTest():
    def test_extract_paper_id(self, url):
        job = DGCourtSpider(1)
        print  job.extract_paper_id(url)


def test():
    t = DGCourtTest()
    t.test_extract_paper_id('http://dyfy.dg.gov.cn/sfgk/cpws-download-5301.html')


if __name__ == '__main__':
    job = DGCourtSpider(1)
    job.load_proxy('proxy')
    job.run()
