#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import PageStoreBase
from spider.util import htmlfind
import time
import os


class COZLPageStore(PageStoreBase):
    def __init__(self, channel, dburl = "mongodb://hadoop2/co_crawler"):
        PageStoreBase.__init__(self, channel, dburl)

    def extract_content(self):
        content = self.get_cur_doc().cur_content
        if isinstance(content, unicode):
            content = content.encode('utf-8')

        find = htmlfind(content, '<table class="comTinyDes">', 0)
        try:
            rs = find.get_text()
            rs = htmlfind.remove_tag(rs, 1)
            return rs
        except Exception as e:
            print "co_id: %s, exception: %r" % (self.get_cur_doc().cur_jdid, e)
            return None

    def page_time(self):
        # 公司没有更新时间， 直接返回现在的时间
        return int(time.time() * 1000)

    def check_should_fetch(self, jdid):
        indexUrl = "%s://%s" % (self.channel, jdid)
        return not self.find_any(indexUrl)

    def getopath(self):
        dirs = ['/v01/data/crawler/_files3_', '/opt/_test_store_']
        for di in dirs:
            if os.path.isdir(di) and os.access(di, os.W_OK):
                return di
        raise RuntimeError("no dir to write files.")
