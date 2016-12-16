#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import time

import datetime

from spider.genquery import GenQueries
from spider.httpreq import BasicRequests
from spider.spider import Spider, SpiderErrors


class HangzhouGenJobs(BasicRequests):
    def __init__(self, sf='jobs'):
        BasicRequests.__init__(self)
        self._main_url = 'http://www.zjsfgkw.cn/Document/JudgmentBook'
        self._court_search_url = 'http://www.zjsfgkw.cn/Judges/GetCountByCountId'
        self._book_search_url = 'http://www.zjsfgkw.cn/document/JudgmentSearch'
        self.start_date = '19700101'
        self.end_date = time.strftime('%Y%m%d', time.localtime())
        self.save_file = sf

    def fetch_court_list(self):
        con = self.request_url(self._main_url)
        if con and con.text:
            return re.findall(r'<li fyid="(\d*)">([^<]*)<\/li>', con.text)
        else:
            return []

    def get_court_paper_count(self, court_id, start_date, end_date):
        data = {
            'pageno': '1',
            'pagesize': '5',
            'ajlb': '',
            'cbfy': court_id,
            'ah': '',
            'jarq1': start_date,
            'jarq2': end_date,
            'key': ''
        }

        con = self.request_url(self._book_search_url, data=data)
        if con and con.text:
            res = re.search(r'"total":(\d+)', con.text)
            if res:
                print court_id, res.group(1)
                return int(res.group(1))
        return 0

    def run(self):
        courts = self.fetch_court_list()
        clist = []
        for court in courts:
            c = {}
            c['id'] = court[0]
            c['name'] = court[1]
            c['count'] = self.get_court_paper_count(court[0], self.start_date, self.end_date)
            clist.append(c)

        with open(self.save_file, 'w') as f:
            for c in clist:
                f.write(str(c) + '\n')
        print 'save ', len(clist)

    def test_get_paper_count(self):
        count = self.get_court_paper_count('1300', self.start_date, self.end_date)
        print 'page count', count


class HangzhouListSpider(Spider):
    start_date = '19700101'
    end_date = time.strftime('%Y%m%d', time.localtime())

    def __init__(self, threadcnt=5, savefile='jobs'):
        Spider.__init__(self, threadcnt)
        self.courts = {}
        self.save_file = savefile
        self.retry_limit = 10

    def dispatch(self):
        self.add_main_job({'type': 'main', 'url': 'http://www.zjsfgkw.cn/Document/JudgmentBook'})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def fetch_court_list(self, url):
        con = self.request_url(url)
        if con and con.text:
            return re.findall(r'<li fyid="(\d*)">([^<]*)<\/li>', con.text)
        else:
            return []

    def search(self, **kwargs):
        pageno = kwargs.get('pageno', 1)
        pagesize = kwargs.get('pagesize', 10)
        ajlb = kwargs.get('ajlb', '')
        cbfy = kwargs.get('cbfy', '')
        ah = kwargs.get('ah', '')
        jarq1 = kwargs.get('jarq1', HangzhouListSpider.start_date)
        jarq2 = kwargs.get('jarq2', HangzhouListSpider.end_date)
        key = kwargs.get('key', '')
        # url = 'http://www.zjsfgkw.cn/document/JudgmentSearch?ajlb=%s&cbfy=%s&ah=%s&key=%s&jarq1=%s&jarq2=%s&pageno=%s&pagesize=%s' % (
        #     ajlb, cbfy, ah, key, jarq1, jarq2, pageno, pagesize)
        # return self.request_url(url)

        return self.request_url('http://www.zjsfgkw.cn/document/JudgmentSearch', data={
            'pageno': pageno,
            'pagesize': pagesize,
            'ajlb': ajlb,
            'cbfy': cbfy,
            'ah': ah,
            'jarq1': jarq1,
            'jarq2': jarq2,
            'key': key
        })

    def get_court_paper_count(self, court_id, start_date, end_date):
        con = self.search(pageno=1, pagesize=5, cbfy=court_id, jarq1=start_date, jarq2=end_date)
        if con and con.text:
            res = re.search(r'"total":(\d+)', con.text)
            if res:
                print court_id, res.group(1)
                return int(res.group(1))
            else:
                return -1
        return -1

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        if 'list' == jobid['type']:
            if jobid['times'] <= 0:
                print 'exceeds retry limit,', jobid['id'], jobid['url']
                return
            count = self.get_court_paper_count(jobid['id'], HangzhouListSpider.start_date,
                                               HangzhouListSpider.end_date)
            if count < 0:
                jobid['times'] -= 1
                self.re_add_job(jobid)
                return
            self.courts[jobid['id']]['count'] = count
        elif 'main' == jobid['type']:
            clist = self.fetch_court_list(jobid['url'])
            for id, name in clist:
                self.courts[id] = {'id': id, 'name': name, 'count': 0}
            for id, name in clist:
                self.add_job({'type': 'list', 'id': id, 'url': 'http://www.zjsfgkw.cn/document/JudgmentSearch',
                              'times': self.retry_limit})
        else:
            print 'Invalid jobid', jobid

    def save(self):
        if len(self.courts) > 0:
            with open(self.save_file, 'w') as f:
                for id, c in self.courts.items():
                    f.write(str(c) + '\n')
                print '', len(self.courts), 'courts saved in', self.save_file

    def event_handler(self, evt, msg, **kwargs):
        if 'DONE' == evt:
            self.save()


if __name__ == '__main__':
    job = HangzhouListSpider()
    job.load_proxy('proxy')
    # job.run()
    con = job.search(jarq1='20160401', jarq2='20160607',pageno=100,pagesize=50)
    res=eval(con.text.replace('null','None'))
    for i in res['list']:
        print i
    print res['total']
    print len(res['list'])
