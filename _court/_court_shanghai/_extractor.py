#!/usr/bin/env python
# -*- coding:utf8 -*-
import re

import datetime

from court.save import LinkSaver
from gkutils.parser import CWPParser


class ShanghaiExtractor(CWPParser):
    """解析文书案号"""

    def __init__(self):
        CWPParser.__init__(self, 'shanghai_court', 'court')
        self.an_saver = LinkSaver('ah.%s.txt' % self.name)

    def process_child_item(self, item):
        line='%s|%s' % (item[0], item[1])
        print line
        self.an_saver.add(line)

    def init(self):
        print 'job start at', datetime.datetime.now()
        return CWPParser.init(self)

    def parse_item(self, page):
        m = re.search('(（\d{4}）.*\d+号)', page['content'][1])
        if m:
            return [[m.group(1), page['indexUrl'][17:].encode()]]
        return []

    def on_finish(self):
        self.an_saver.flush()


if __name__ == '__main__':
    job = ShanghaiExtractor()
    job.run()
