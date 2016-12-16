#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import PageStoreBase
from spider.runtime import Log
from spider.util import TimeHandler
import spider


class PageStoreWL(PageStoreBase):

    def __init__(self):
        super(PageStoreWL, self).__init__('jd_wealink')

    def extract_content(self):
        content = spider.util.htmlfind(self.get_cur_doc().cur_content, 'class="job-description"', 0)
        try:
            content = content.get_text()
        except:
            Log.errorbin("invalid jd content %s" % self.get_cur_doc().cur_url, self.get_cur_doc().cur_content)
            return None
        return content

    def page_time(self):

        tag = spider.util.htmlfind(self.get_cur_doc().cur_content, 'class="publish-time"', 0)
        try:
            tag = tag.get_text()
        except:
            Log.errorbin("invalid jd content %s" % self.get_cur_doc().cur_url, self.get_cur_doc().cur_content)
            return None

        return TimeHandler.fmt_time(tag)




