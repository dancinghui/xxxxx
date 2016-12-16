#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import PageStoreBase
from spider.runtime import Log
from spider.util import htmlfind
from spider.util import TimeHandler


class CV58Config(object):
    mongdb_url = "mongodb://localhost/cv_crawler"


class CV58PageStore(PageStoreBase):
    def __init__(self):
        super(CV58PageStore, self).__init__('cv_58job', dburl=CV58Config.mongdb_url)

    def extract_content(self):

        cur_content = self.get_cur_doc().cur_content
        if isinstance(cur_content, unicode):
            cur_content = cur_content.encode('utf-8')

        content_part1 = htmlfind.findTag(cur_content, 'ul', 'contact-list')
        if not content_part1:
            return
        content_part1 = htmlfind.remove_tag(content_part1[0], True)
        content_part2 = htmlfind.findTag(cur_content, 'div', 'field')
        for c in content_part2:
            if r'求职意向' in c:
                content_part2 = c
                break

        content_part2 = htmlfind.remove_tag(content_part2, True)

        return content_part1 + content_part2

    def page_time(self):

        cur_content = self.get_cur_doc().cur_content
        if isinstance(cur_content, unicode):
            cur_content = cur_content.encode('utf-8')

        tag = htmlfind.findTag(cur_content, 'span', 'class="last-modified"')
        try:
            tag = htmlfind.remove_tag(tag[0], 1)
        except:
            Log.errorbin("invalid jd pubtime %s" % self.get_cur_doc().cur_url, self.get_cur_doc().cur_content)
            raise
        if isinstance(tag, unicode):
            tag = tag.encode('utf-8')

        return TimeHandler.fmt_time(tag)

    def check_should_fetch(self, jobid):
        if not super(CV58PageStore, self).check_should_fetch(jobid):
            return False
        return True