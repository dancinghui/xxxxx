# !/usr/bin/env python
# -*- coding:utf8 -*-
import re
import time

from court.cspider import CourtSpider, JobSpliter
from court.save import CourtStore
from spider import spider
import school


class HUNANSpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class HunanGaokaoStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'gk_hunan_plan')


class HunanGaokaoSpider(CourtSpider):
    "高校在北京的招生计划爬虫"

    def __init__(self, threadcnt):
        CourtSpider.__init__(self, threadcnt)
        self._name = 'HunanGaokaoSpider'
        self.pagestore = HunanGaokaoStore()
        self.job_spliter = HUNANSpliter()
        self._cur_page = 0
        self._test_mode = True

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        self.post_for_plan_detail(jobid['name'])

    def post_for_plan_detail(self, name):
        url = 'http://www.hneeb.cn/website/search_jh.asp'
        data = {'select': '2', 'getstring': name.encode('gb2312')}
        con = self.request_url(url, data=data)
        jid = name.encode('utf-8')
        if con:
            context = con.content.decode('gbk', 'replace')
            if re.search(ur'没有查询到任何内容|操作时间', context):
                print jid, 'no result found'
                return
            if not self.pagestore.save(int(time.time()), jid, url + ';' + jid, context):
                print jid, 'content not save'
        else:
            print jid, 'None response'

    def dispatch(self):
        for sch in school.schools:
            self.add_main_job({'type': 'main', 'name': sch})
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
        return None

    def extract_paper_url(self, content):
        return None

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
    job = HunanGaokaoSpider(4)
    job.load_proxy('proxy')
    job.run()
