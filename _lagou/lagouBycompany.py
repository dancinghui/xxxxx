# coding=utf-8

import sys

import re

sys.path.append(sys.path[0]+"/../")
print sys.path

from spider.savebin import BinSaver
from spider.spider import Spider
from spider.util import htmlfind, TimeHandler
from page_store import PageStoreLG
from spider.httpreq import SpeedControlRequests
from queries import q
from spider.runtime import Log
import spider
import time
import json


class LagouBycompany(Spider):
    def __init__(self, thread_cnt, company):
        super(LagouBycompany, self).__init__(thread_cnt)
        self.page_store = PageStoreLG()
        self.speed_control_requests = SpeedControlRequests()
        self.page_store.testmode = False
        self.list = []
        with open(company) as file_:
            for line in file_:
                self.list.append(line.strip())

    def dispatch(self):
        for i in self.list:
            self.add_main_job({'u': str(i), 'type': 'co'})
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, job):
        jobtype = self.get_job_type(job)
        if jobtype == 'co':
            url = 'http://www.lagou.com/gongsi/j%s.html' % job['u']
            print url
            con = self.request_url(url)
            if con is not None:
                self.parse_list(con.text, job['u'])
            else:
                self.re_add_job(job)
        elif jobtype == 'list':
            url = job['base'] + job['u']
            print url
            con = self.request_url(url)
            if con is not None:
                self.parse_html(con.text)
            else:
                self.re_add_job(job)
        elif jobtype == 'jd':
            url = 'http://www.lagou.com/jobs/%s.html' %job['u']
            if self.page_store.check_should_fetch(job['u']):
                con = self.request_url(url)
                if con is not None:
                    self.page_store.save(int(time.time()), job['u'], url, con.text)
                else:
                    self.re_add_job(job)
                    Log.error("failed get url", url)
            else:
                pass

    def parse_list(self, text, jobid):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        m = re.search('共有 <span class="list_total">(\d+)</span> 个在招职位', text)
        if m:
            pagecnt = (int(m.group(1)) + 9) / 10
            for i in range(1, pagecnt + 1):
                self.add_job({'type': 'list', 'u': '?positionFirstType=全部&pageSize=10&companyId=%s&pageNo=%d' %(jobid, i), 'base': 'http://www.lagou.com/gongsi/searchPosition.json'})
            if pagecnt == 0:  # no record found.
                Log.error("%s => NO_PAGES!" % jobid)
                return

    def parse_html(self, text):
        if isinstance(text, unicode):
            text = text.encode('utf-8')
        a = re.findall(r'"positionId":(\d+),', text)
        urls = spider.util.unique_list(a)
        for pageurl in urls:
            self.add_job({'type': 'jd', 'u': pageurl})

    def event_handler(self, evt, msg, **kwargs):

        if "DONE" == evt:
            spider.util.sendmail(["<wangwei@ipin.com>"], "lagou jd爬取", msg + '\nsaved: %d  by company' % self.page_store.saved_count)
            return


if __name__ == '__main__':
    company_lagou = LagouBycompany(4, 'company')
    company_lagou.load_proxy('proxy', True)
    company_lagou.speed_control_requests.load_proxy('proxy', True)
    company_lagou.run()