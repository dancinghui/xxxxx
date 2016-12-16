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


class CO_51job_Store(PageStoreBase):
    def __init__(self):
        PageStoreBase.__init__(self, 'co_51job', 'mongodb://hadoop2/co_crawler')
        # self.testmode = 1
        self.hdoc = None

    def extract_content(self):
        content = ''
        divs = htmlfind.findTag(self.get_cur_doc().cur_content, 'div', 'class="in"')
        if divs:
            ps = re.findall(r'<p[^<>]*>(.*?)</p>', divs[0], re.S)
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
        dirs = ['/v01/data/crawler/_files3_', '/opt/_test_store_']
        for di in dirs:
            if os.path.isdir(di) and os.access(di, os.W_OK):
                return di
        raise RuntimeError("no dir to write files.")

class CO_51Spider(Spider):
    def __init__(self, threadcont):
        super(CO_51Spider, self).__init__(threadcont)
        self.page_store = CO_51job_Store()

    def dispatch(self):
        for i in range(100000, 10000000):
            self.add_main_job({'id': str(i)})
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, job):
        url = 'http://jobs.51job.com/all/co%d.html' %job['id']
        res = self.request_url(url)
        data = res.text
        if isinstance(data, unicode):
            data = data.encode('utf-8')

        if re.search(u'您选择的公司不存在或者已经过期!',  data ):
            print job, "match nothing"
        else:
            print "saving %s ..." % job['id']
            self.page_store.save(int(time.time()), job['id'], url, data)

if __name__ == "__main__":
    s = CO_51Spider(50)
    s.load_proxy('proxy.txt')
    s.run()
