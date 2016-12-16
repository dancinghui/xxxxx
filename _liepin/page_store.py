#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import PageStoreBase
from spider.runtime import Log
from spider.util import htmlfind
from spider.util import TimeHandler
import spider
import re



class PageStoreLP(PageStoreBase):

    def __init__(self):
        super(PageStoreLP, self).__init__('jd_liepin')
        self.crawlered_ids = set()

    def extract_content(self):
        content = self.get_cur_doc().cur_content
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        content = re.search(r'"job-main main-message ">.*?职位描述：.*?"content content-word">(.*?)</div>',content, re.S)
        if content:
            content = htmlfind.remove_tag(content.group(1), 1)
            return content

        return None

    def page_time(self):
        m = re.search(r'"icons24 icons24-time"></i>(.*?)</span>', self.get_cur_doc().cur_content, re.S)
        if m:
            ft = m.group(1)
            return TimeHandler.fmt_time(ft)

    def check_should_fetch(self, jobid):
        if not super(PageStoreLP, self).check_should_fetch(jobid):
            return False

        return True



