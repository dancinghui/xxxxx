#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import PageStoreBase
from spider.runtime import Log
from spider.util import htmlfind
from spider.util import TimeHandler
import spider
import time
import re


class Jd58PageStore(PageStoreBase):
    def __init__(self):
        super(Jd58PageStore, self).__init__('jd_58job')

    def extract_content(self):

        content = htmlfind.findTag(self.get_cur_doc().cur_content, 'div', 'posMsg borb')
        try:
            content = htmlfind.remove_tag(content[0], 1)
        except:
            Log.errorbin("invalid jd content %s" % self.get_cur_doc().cur_url, self.get_cur_doc().cur_content)
            return None
        return content

    def page_time(self):

        tag = htmlfind.findTag(self.get_cur_doc().cur_content, 'ul', 'class="headTag"')
        try:
            tag = htmlfind.remove_tag(tag[0], 1)
        except:
            Log.errorbin("invalid jd pubtime %s" % self.get_cur_doc().cur_url, self.get_cur_doc().cur_content)
            raise
        if isinstance(tag, unicode):
            tag = tag.encode('utf-8')

        if "天前" not in tag:
            return int(time.time() * 1000)
        else:
            find = re.search('(\d+).*?(\d+).*?(\d+)', tag, re.S)
            if find:
                day = find.group(1)
                return TimeHandler.getTimeOfNDayBefore(day)

        raise Exception("not copy time pattern: {}".format(tag))

    def check_should_fetch(self, jobid):
        if not super(Jd58PageStore, self).check_should_fetch(jobid):
            return False
        return True