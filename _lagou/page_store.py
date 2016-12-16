#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import PageStoreBase
from spider.runtime import Log
from spider.util import TimeHandler
from spider.util import htmlfind
import spider
import re
import time


class PageStoreLG(PageStoreBase):

    def __init__(self):
        super(PageStoreLG, self).__init__('jd_lagou')
        self.crawlered_ids = set()

    def extract_content(self):

        content = ''
        jobbt = spider.util.htmlfind(self.get_cur_doc().cur_content, 'class="job_bt"', 0)
        job_request = htmlfind.findTag(self.get_cur_doc().cur_content, 'dd', 'class="job_request"')
        for e in job_request:
            tags = re.findall(r'<span[^<>]*>(.*?)</span>', e)
            content += '#'.join(tags)
            if isinstance(content, unicode):
                content = content.encode('utf-8')
        try:
            content += jobbt.get_text()
        except:
            Log.errorbin("invalid jd content %s" % self.get_cur_doc().cur_url, self.get_cur_doc().cur_content)
            return None
        return content

    def page_time(self):
        #TODO
        tag = spider.util.htmlfind(self.get_cur_doc().cur_content, 'class="publish_time"', 0)

        try:
            tag = tag.get_text()
        except:
            Log.errorbin("invalid jd content %s" % self.get_cur_doc().cur_url, self.get_cur_doc().cur_content)
            raise

        return TimeHandler.fmt_time(tag)

    def check_should_fetch(self, jobid):
        if not super(PageStoreLG, self).check_should_fetch(jobid):
            return False
        if jobid in self.crawlered_ids:
            return False
        self.crawlered_ids.add(jobid)
        return True




