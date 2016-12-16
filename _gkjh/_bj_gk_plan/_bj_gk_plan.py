# !/usr/bin/env python
# -*- coding:utf8 -*-
import os
import re
import time

from selenium import webdriver
from selenium.webdriver.support.select import Select

from gspider.cspider import JobSpliter, GaokaoSpider
from gspider.save import GaokaoStore

from court.cspider import CourtSpider
from court.save import CourtStore
from spider import spider
import qdata


class BJSpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class BJGaokaoStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'gk_bj_plan')


def remove_file(file):
    if os.path.exists(file) and os.path.isfile(file):
        os.remove(file)


class BJGaokaoSpider(CourtSpider):
    "高校在北京的招生计划爬虫"

    def __init__(self, threadcnt):
        CourtSpider.__init__(self, threadcnt)
        self._name = 'BJGaokaoSpider'
        self.pagestore = BJGaokaoStore()
        self.job_spliter = BJSpliter()
        self._cur_page = 0
        self._test_mode = True

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        con = self.post_for_plan(jobid['code'], jobid['subject'], jobid['yc'])
        if con:
            content = self.extract_content(con.text)
            jid = jobid['school'].encode('utf-8') + '-' + jobid['year'] + '-' + jobid['subject'].encode(
                'utf-8')

            if content is None:
                print 'None content for ', jid
            if not re.search(r'<tr bgcolor="">', content):
                print jid, '===>', 'has not plan'
                return
            if self._test_mode:
                print jid, '==>', len(content)
            self.pagestore.save(int(time.time()), jid,
                                'http://query.bjeea.cn/queryService/rest/plan/115/' + jobid['code'].encode(
                                    'utf-8') + ';jid=' + jid,
                                content)

    def dispatch(self):
        schools = qdata.schools
        subjects = [u'文科', u'理科', u'单考']
        years = {'2015年': '3488'}
        # years = {'2015年': '3488', '2014年': '2765', '2013年': '2285', '2012年': '1723', '2011年': '1340', '2010年': '1020'}
        for sch, code in schools.items():
            for subject in subjects:
                for yn, yc in years.items():
                    self.add_job(
                        {'type': 'main', 'school': sch, 'code': str(code), 'subject': subject, 'year': yn,
                         'yc': str(yc)})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def need_split(self, context, url):
        return False

    def extract_content(self, context):
        m = re.search(
            r'(<table width="570" border="0" cellspacing="0" cellpadding="0">.*)<input type="hidden" id="schoolcode"',
            context, re.S)
        if m:
            return m.group(1)
        return None

    def extract_paper_id(self, url):
        return None

    def extract_paper_url(self, content):
        m = re.findall(r"return goschool\('(\d+)',.*\)", content)
        if m is not None:
            urls = []
            for u in m:
                urls.append('http://query.bjeea.cn/queryService/rest/plan/115/' + u)
            return urls
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

    def post_for_plan(self, school, subject, year):
        url = "http://query.bjeea.cn/queryService/rest/plan/115/" + school
        data = {'examId': year, 'schoolcode': school, 'subjectName': subject}
        return self.request_url(url, data=data)

    def test_post_for_plan(self):
        con = self.post_for_plan('1020', u'理科', '3488')
        if con:
            print self.extract_content(con.text)
        else:
            print 'None post response'


if __name__ == '__main__':
    job = BJGaokaoSpider(1)
    job.load_proxy('proxy')

    job.run()
