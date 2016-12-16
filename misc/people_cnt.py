#!/usr/bin/env python
# -*- coding:utf8 -*-

import re

from spider.savebin import FileSaver
from spider.spider import Spider, SessionRequests


class FindPCnt(Spider):
    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        self.counter = 0
        self.skipcnt = 0
        self.skip_j = 1
        self.ofile = FileSaver('people_result')
        self.headers = {'X-Requested-With':'XMLHttpRequest',
                #'Referer':'https://www.baidu.com/',
                'DNT':1,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language':'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3' }

    def thread_init(self, tid):
        sr = SessionRequests()
        sr._user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:42.0) Gecko/20100101 Firefox/42.0'
        setattr(self._tls, 'ssobj', {'tid':tid, 'session':sr, 'counter':0})

    def newjob(self,jobid):
        self.skip_j = 0
        if jobid == '上海尚秦艺术品销售有限公司 孔雀石':
            self.skip_j = 0
        if self.skip_j:
            return
        self.counter += 1
        if self.counter > self.skipcnt:
            return self.add_job(jobid, True)

    def dispatch2(self):
        self.newjob('上海尚秦艺术品销售有限公司 史学会')
        self.wait_q()
        self.add_job(None, True)

    def dispatch(self):
        with open('inc_people.txt') as f:
            for lines in f:
                l = re.split(r'\s+', lines.strip(), 1)
                if len(l) >= 2:
                    cn = l[0].strip()
                    pn = l[1].strip()
                    jobid = cn + " " + pn
                    self.newjob(jobid)
        with open('baike_people.txt') as f:
            for lines in f:
                l = re.split(r'\s+', lines.strip())
                for pn in l[1:]:
                    pn = re.sub(r'[\d:]', '', pn.strip())
                    jobid = l[0] + " " + pn
                    self.newjob(jobid)
        self.wait_q()
        self.add_job(None, True)

    def xdump(self, ssobj):
        c = ssobj['session'].session.cookies
        if 'BAIDUID' in c.keys():
            print c['BAIDUID']
        else:
            print 'NO_BAIDUID'

    def run_job(self, jobid):
        ssobj = getattr(self._tls, 'ssobj', None)
        ssobj['counter'] += 1
        if ssobj['counter'] % 100 == 1:
            self.xdump(ssobj)
            ssobj['session'].reset_session()
            self.xdump(ssobj)
            ssobj['session'].request_url('https://www.baidu.com/', headers = self.headers)

        url = 'https://www.baidu.com/s?ie=utf-8&wd=' + jobid
        #url = 'http://127.0.0.1:9999/s?ie=utf-8&wd=' + jobid
        print "thisc:%d allc:%d url:%s" % (ssobj['counter'], self.counter, url)

        con = ssobj['session'].request_url(url, headers=self.headers)
        if con is None:
            return self.add_job(jobid)
        m = re.search(ur'百度为您找到相关结果约([\d,]+)个', con.text)
        if m:
            cnt = re.sub(u',', u'', m.group(1))
            print jobid, cnt
            self.ofile.append(jobid + "==>" + cnt.encode('utf-8'))
        else:
            print con.headers
            print con.text
            raise RuntimeError('dddd')

if __name__ == '__main__':
    f = FindPCnt(20)
    f.run()
