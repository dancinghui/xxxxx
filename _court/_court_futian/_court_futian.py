#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import re
import time
import urllib2
import uuid
from urllib import quote

from selenium import webdriver

from court.cspider import JobSpliter, CourtSpider
from court.save import CourtStore
from court.swfutils import swf2text
from court.util import remove_file
from spider import spider
from spider.httpreq import BasicRequests


class FutianSpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class FutianCourtStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'ft_court')

    def parse_time(self):
        m = re.search(ur'<h6>发布日期：([^><]+)</h6>', self.get_cur_doc().cur_content)
        if m:
            return m.group(1)
        else:
            return None


class FutianGenQueries(BasicRequests):
    def __init__(self):
        BasicRequests.__init__(self)
        self.url = 'http://www.ftcourt.gov.cn/cpwspt/writopenlist.aspx?cls=0'
        self.params = {}
        self.count = 0

    def run(self):
        self.get_form_values()
        self.show()

    def get_form_values(self):
        con = self.request_url(self.url)
        params = []
        if con:
            m = re.search(ur'<a[^>]*doPostBack\(\'anpWritList\',\'(\d+)\'\)"[^>]*>最后一页<\/a>', con.text)
            if m:
                self.count = int(m.group(1))
            form = re.search(r'<form[^>]*id="ctl00">.*?<\/form>', con.text, re.S)
            if form:
                form = form.group()
                # print form
                inputs = re.findall(r'<input[^>]*>', form, re.S)
                for p in inputs:
                    attrs = re.findall(r'((name|value)="([^"]*))', p)
                    if len(attrs) > 1:
                        param = {}
                        for a, k, v in attrs:
                            param[k] = v
                        params.append(param)
                    elif len(attrs) > 0:
                        for a, k, v in attrs:
                            if k == u'name':
                                params.append({k: v, u'value': ''})
        res = {}
        for p in params:
            res[p[u'name']] = p[u'value']
        res.pop('btnSearch')
        res.pop('btnChongz')
        self.params = copy.deepcopy(res)

    def show(self):
        print self.params
        print self.count
        print self.url


class FutianCourtSpider(CourtSpider):
    "深圳福田区法院爬虫"

    def __init__(self, threadcnt):
        CourtSpider.__init__(self, threadcnt)
        self._name = 'FutianCourt'
        self.pagestore = FutianCourtStore()
        self.job_spliter = FutianSpliter()
        self._test_mode = True

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        jt = jobid['type']
        url = jobid['url']

        if 'paper' == jt:
            print url
            con = self.request_url(url)
            if con is None or con.text is None:
                return
            else:
                u = re.search(r'SwfFile: \'../upload/swf/(.*.swf)\',', con.text)
                if not u:
                    return
                real_url = 'http://www.ftcourt.gov.cn/upload/swf/' + quote(u.group(1).encode('utf-8'))
                con = urllib2.urlopen(real_url)
                if con is None:
                    return
                context = con.read()
                context = self.extract_swf_file(url, context)
            if context is not None:
                jid = self.extract_paper_id(url)
                if jid is not None:
                    self.pagestore.save(int(time.time()), jid, real_url, context)
                else:
                    print 'failed to find paper id, paper not save', url
                print url, '=>', len(context)
            else:
                print 'fail to find content for:', url
            return
        elif 'main' == jt:
            data = jobid['data']
            con = self.request_url(url, data=data)
            if con and con.text:
                urls = self.extract_paper_url(con.text)
                for u in urls:
                    self.add_job({'type': 'paper', 'url': u})
                if self._test_mode:
                    print 'add paper', len(urls), ' jobs', data['__EVENTARGUMENT']
            else:
                print 'no paper found', url

    def extract_swf_file(self, url, con):
        jid = str(uuid.uuid4())
        if jid is not None:
            fn = '/tmp/%s.pdf' % jid
            f = open(fn, 'wb')
            f.write(con)
            f.flush()
            f.close()
            text = swf2text(fn)
            remove_file(fn)
            return text
        return None

    def dispatch(self):
        ft = FutianGenQueries()
        ft.run()
        if ft.count > 0:
            for page in range(1, ft.count + 1):
                data = copy.deepcopy(ft.params)
                data['__EVENTTARGET'] = 'anpWritList'
                data['__EVENTARGUMENT'] = str(page)
                self.add_main_job({'type': 'main', 'url': ft.url, 'data': data})
        else:
            print 'No main job to add'
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def need_split(self, context, url):
        return False

    def extract_paper_id(self, url):
        m = re.findall(r'id=(\d+)', url)
        if m is not None:
            return m[0]
        return None

    def extract_paper_url(self, content):
        m = re.findall(r'<a href=\'(writview.aspx\?id=\d+)\'', content)
        urls = []
        if m is not None:
            m = spider.util.unique_list(m)
            for u in m:
                urls.append('http://www.ftcourt.gov.cn/cpwspt/' + u)
        return urls

    def add_list_job(self, url, con):
        pass


def find_and_print_page(driver):
    content = driver.page_source
    m = re.findall(r'<a href="javascript:toPage\(\d+,\'getlist\'\);">&gt;</a>', content)
    print m


if __name__ == '__main__':
    job = FutianCourtSpider(1)
    job.load_proxy('proxy')
    job.run()
    # test_search_by_xpath()
