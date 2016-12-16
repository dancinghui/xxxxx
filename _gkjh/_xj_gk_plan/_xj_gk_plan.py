# !/usr/bin/env python
# -*- coding:utf8 -*-
import re
import time

from court.cspider import CourtSpider, JobSpliter
from court.save import CourtStore
from spider import spider


class XJSpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class XjGaokaoStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'gk_xj_plan')

    def parse_title(self):
        return self.get_cur_doc().cur_content

    def parse_time(self):
        return None


class XjGaokaoSpider(CourtSpider):
    "高校在北京的招生计划爬虫"

    def __init__(self, threadcnt):
        CourtSpider.__init__(self, threadcnt)
        self._name = 'XJGaokaoSpider'
        self.pagestore = XjGaokaoStore()
        self.job_spliter = XJSpliter()
        self._cur_page = 0
        self._test_mode = True

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        jt = jobid['type']
        url = jobid['url']
        con = self.request_url(url)
        if con:
            if 'main' == jt:
                urls = re.findall(r'<a href=([^>]*) target=\'g_mainframe\'>', con.text)
                print 'url count', len(urls), url
                for u in urls:
                    if isinstance(u, unicode):
                        u = u.encode('utf-8')
                    self.add_job({'type': 'paper', 'url': 'http://124.117.250.18/ptjh/y_jhqr/' + u.strip()})
            else:
                content = self.extract_content(con.text)
                jid = self.extract_paper_id(url)
                if jid is None:
                    print 'None jid for:', url
                    return
                print url, '==>', len(content)
                self.pagestore.save(int(time.time()), jid, url, content)
                if not re.search(r'page=', url):
                    page = re.search(r'<span>(\d+)\/(\d+)<\/span>', con.text)
                    if page:
                        cur_page = int(page.group(1))
                        total_page = int(page.group(2))
                        if cur_page < total_page:
                            for page in range(cur_page + 1, total_page + 1):
                                self.add_job({'type': 'paper', 'url': (url + ('&page=%d' % page))})

        else:
            print 'None response for', url

    def dispatch(self):
        yzdm = ['01', '02', '05', '04', '95']
        pcdm = ['z', '1', 'D', 'E', 'F', 'M', 'K', '2', 'T', '3', '4', '5', 'S', '6']
        for y in yzdm:
            for p in pcdm:
                self.add_main_job({'type': 'main',
                                   'url': 'http://124.117.250.18/ptjh/y_jhqr/g_leftframe.php?yzdm=%s&pcdm=%s' % (y, p)})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def need_split(self, context, url):
        return False

    def extract_content(self, context):
        m = re.search(r'<TABLE.*<\/TABLE>', context, re.S)
        if m:
            return m.group(0)
        return None

    def extract_paper_id(self, url):
        m = re.findall(r'yzdm=([\w\d])+\&pcdm=([\w\d]+)\&yxdh=(\d+)\&', url)
        if m:
            page = re.search(r'page=(\d+)', url)
            if page:
                m[0] += tuple(page.group(1))
            return '-'.join(m[0])
        return None

    @staticmethod
    def extract_detail_url(content):
        return re.findall(r'<a href="([^"]*)">\[([^\]]*)\]</a>', content)

    def extract_paper_url(self, content):
        pass

    def add_list_job(self, url, con):
        pass

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "Gaokao Spider:%s\n" % self._name
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


if __name__ == '__main__':
    job = XjGaokaoSpider(1)
    job.load_proxy('proxy')
    job.run()
