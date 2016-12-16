#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
import os
from spider import spider
import time
from spider.ipin.savedb import PageStoreBase
from spider.runtime import Log
from spider.savebin import BinSaver

from spider.spider import Spider
from spider.util import htmlfind, TimeHandler


class CO_Liepin_Store(PageStoreBase):
    def __init__(self):
        PageStoreBase.__init__(self, 'co_liepin', 'mongodb://localhost/co_crawler')
        # self.testmode = 1
        self.hdoc = None

    def extract_content(self):
        content = ''
        spans = htmlfind.findTag(self.get_cur_doc().cur_content, 'div', 'class="company-introduction clearfix"')
        if spans:
            ps = re.findall(r'<p[^<>]*>(.*?)</p>', spans[0], re.S)
            for p in ps:
                content += htmlfind.remove_tag(p, True) + "#"

        if isinstance(content, unicode):
            content = content.encode('utf-8')
        return content

    def check_should_fetch(self, jdid):
        indexUrl = "%s://%s" % (self.channel, jdid)
        return not self.find_any(indexUrl)

    def page_time(self):
        localtime = time.localtime(time.time())
        localtime = time.strftime('%Y-%m-%d', localtime)
        t = TimeHandler.fmt_time(localtime)
        return t

    def getopath(self):
        dirs = ['/data/crawler/_files3_', '/opt/_test_store_']
        for di in dirs:
            if os.path.isdir(di) and os.access(di, os.W_OK):
                return di
        raise RuntimeError("no dir to write files.")

class CO_LiepinSpider(Spider):
    def __init__(self, threadcont):
        super(CO_LiepinSpider, self).__init__(threadcont)
        self.page_store = CO_Liepin_Store()

    def dispatch(self):
        for i in range(100000, 10000000):
           self.add_main_job({'id': str(i), type: 'root'})
        #self.add_main_job({'pre': 'https://company.liepin.com', 'id': '', 'type': 'root'})
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, job):
        url = 'https://company.liepin.com/' + job['id']
        print url
        res = self.request_url(url)
        data = res.text
        if isinstance(data, unicode):
            data = data.encode('utf-8')
        if re.search(u'您访问的页面不存在或已删除!', data):
            print job, "match nothing"
        else:
            print "saving %s ..." % job['id']
            self.page_store.save(int(time.time()), job['id'], url, data)
        '''if job['type'] == 'root':
            m = re.findall('共(\d+)页', data)
            pgnum = m[0]
            for i in range(int(pgnum)):
                self.add_job({'pre': job['pre'] + '/pn' + str(i), 'type': 'list', 'id': ''}, True)
        elif job['type'] == 'list':
            print '---------------------' + job['pre'] + '----------------'
            outlinks = re.findall('https://company.liepin.com/(\d+)/', data)
            dic = {}
            for outlink in outlinks:
                dic[outlink] = '0'
            for key in dic.keys():
                self.add_job({'pre': 'https://company.liepin.com/', 'type': 'page', 'id': str(key)})
        else:
            if re.search(u'您访问的页面不存在或已删除!', data):
                print job, "match nothing"
            else:
                print "saving %s ..." % job['id']
                self.page_store.save(int(time.time()), job['id'], url, data)
        '''

if __name__ == "__main__":
    s = CO_LiepinSpider(20)
    s.load_proxy('proxy.txt')
    s.run()
