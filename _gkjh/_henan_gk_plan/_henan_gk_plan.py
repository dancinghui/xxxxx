# !/usr/bin/env python
# -*- coding:utf8 -*-
import os
import re
import time

from gspider.cspider import JobSpliter, GaokaoSpider
from gspider.save import GaokaoStore

from court.cspider import CourtSpider
from court.save import CourtStore
from spider import spider


class HenanSpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class HenanGaokaoStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'gk_henan_plan')


def remove_file(file):
    if os.path.exists(file) and os.path.isfile(file):
        os.remove(file)


class HenanGaokaoSpider(CourtSpider):
    "高校在北京的招生计划爬虫"

    def __init__(self, threadcnt):
        CourtSpider.__init__(self, threadcnt)
        self._name = 'HenanGaokaoSpider'
        self.pagestore = HenanGaokaoStore()
        self.job_spliter = HenanSpliter()
        self._cur_page = 0
        self._test_mode = True

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        code = HenanGaokaoSpider.fix_code(jobid['code'])
        url = 'http://www.heao.gov.cn/JHCX/PZ/enrollplan/PCList.aspx?YXDH=%s' % code

        con = self.request_url(url)
        if con:
            urls = self.extract_detail_url(con.text)
            if urls is None or len(urls) == 0:
                print 'on plan for', url
                return
            for u, title in urls:
                self.get_plan_detail('http://www.heao.gov.cn/JHCX/PZ/enrollplan/' + u, title, code)

    def get_plan_detail(self, url, title, code):
        con = self.request_url(url)
        if not con:
            print 'None request response for', url
            return
        content = self.extract_content(con.text)
        if content is None:
            print 'None content for ', title, url
            return
        self.pagestore.save(int(time.time()), code + '-' + self.extract_encroll_batch(url), url, content)

    @staticmethod
    def fix_code(code):
        if code < 0:
            return '000'
        elif code < 10:
            return '000%d' % code
        elif code < 100:
            return '00%d' % code
        elif code < 1000:
            return '0%d' % code
        return str(code)

    def extract_encroll_batch(self, url):
        m = re.search(r'\&PC=(\w+)', url)
        if m:
            return m.group(1)
        return ''

    def dispatch(self):
        # 院校最大代号是9955
        for code in range(1, 9956):
            self.add_job({'type': 'main', 'code': code})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def need_split(self, context, url):
        return False

    def extract_content(self, context):
        m = re.search(r'<span id="SpanPlanSchoolInfo">.*', context)
        if m:
            return m.group(0)
        return None

    def extract_paper_id(self, url):
        return None

    @staticmethod
    def extract_detail_url(content):
        res = re.findall(r'<a href="([^"]*)">\[([^\]]*)\]</a>', content)
        return res

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
    job = HenanGaokaoSpider(1)
    job.load_proxy('proxy')
    job.run()
