#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import time

from _court._court_foshan._court_foshan import FSCourtStore, FSSpliter
from court.cspider import CourtSpider
from court.save import LinkSaver
from spider import spider


class FsLinkSpider(CourtSpider):
    def __init__(self, threadcnt):
        CourtSpider.__init__(self, threadcnt)
        self._name = 'FoshanLinkSpider'
        self._test_mode = True
        self.page_size = 20
        self.link_saver = LinkSaver("links")

    def run_job(self, jobid):
        if not isinstance(jobid, dict) or not jobid.has_key('type') or not jobid.has_key('url'):
            raise ValueError('invalid jobid')
        jt = jobid['type']
        url = jobid['url']

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
            self.link_saver.add(u)

    def dispatch(self):
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
        m = re.findall(r'id=(\d+)', url)
        if m is not None:
            return m[0]
        return None

    def extract_paper_url(self, content):
        li = re.search(r'<div id="gl3_content_main">.*?<\/div>', content, re.S)
        m = []
        if li:
            rs = li.group().strip()
            li_content = re.sub(r'<.*?>|\r|\n|\&nbsp;|\t', '',
                                re.sub('</li>', '|', re.sub(r'</dt>', ',',
                                                            re.sub(r'<a href="', '',
                                                                   re.sub(r'" target[^>]*>', '', rs)))))

            if li_content:
                if isinstance(li_content, unicode):
                    li_content = li_content.encode('utf-8')
                m = li_content.strip().split('|')
        urls = []
        for u in m:
            urls.append(u.strip())
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
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


if __name__ == "__main__":
    job = FsLinkSpider(10)
    job.run()
