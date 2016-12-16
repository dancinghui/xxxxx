#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import PageStoreBase
from spider.util import TimeHandler, htmlfind


class PageStoreLinkedIn(PageStoreBase):

    def __init__(self):
        super(PageStoreLinkedIn, self).__init__('jd_linkedin')

    def extract_content(self):
        content = htmlfind.findTag(self.get_cur_doc().cur_content, 'div', 'class="rich-text" itemprop="description"')
        if content and len(content) > 0:
            content = htmlfind.remove_tag(content[0], 1)
        return content

    def page_time(self):
        #TODO
        tag = htmlfind.findTag(self.get_cur_doc().cur_content, 'li', 'class="posted" itemprop="datePosted"')

        if tag and len(tag) > 0:
            return TimeHandler.fmt_time(tag[0])

        return None






