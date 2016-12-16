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


class CO_Zhuopin_Store(PageStoreBase):
    def __init__(self):
        PageStoreBase.__init__(self, 'co_zhuopin', 'mongodb://hadoop2/co_crawler')
        # self.testmode = 1
        self.hdoc = None

    def extract_content(self):
        content = ''
        spans = htmlfind.findTag(self.get_cur_doc().cur_content, 'table', 'class="i_table"')
        if spans:
            ps = re.findall(r'<tr[^<>]*>(.*?)</tr>', spans[0], re.S)
            for tr in ps:
                tds = re.findall(r'<td[^<>]*>(.*?)</td>', tr, re.S)
                for td in tds:
                    content += htmlfind.remove_tag(td, True) + "#"

        if isinstance(content, unicode):
            content = content.encode('utf-8')
        print content
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

class CO_ZhuopinSpider(Spider):
    def __init__(self, threadcont):
        super(CO_ZhuopinSpider, self).__init__(threadcont)
        self.page_store = CO_Zhuopin_Store()

    def dispatch(self):
        for i in range(10, 99999):
            self.add_main_job({'id': str(i)})
        self.wait_q()
        self.add_main_job(None)
    def run_job(self, job):
        if isinstance(job, dict):
            url = "http://www.highpin.cn/company/%s.html" % job['id']
            res = self.request_url(url)
            data = res.text
            if isinstance(data, unicode):
                data = data.encode('utf-8')
            if re.search(u'该企业信息不存在',  data ):
                print job, "match nothing"
            else:
                print "saving %s ..." % job['id']
                self.page_store.save(int(time.time()), job['id'], url, data)

if __name__ == "__main__":
    s = CO_ZhuopinSpider(20)
    s.load_proxy('proxy.txt')
    s.run()
