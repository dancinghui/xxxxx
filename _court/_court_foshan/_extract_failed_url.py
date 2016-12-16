#!/usr/bin/env python
# -*- coding:utf8 -*-
from court.save import LinkSaver
from gkutils.parser import CWPParser


class Extractor(CWPParser):
    def __init__(self):
        CWPParser.__init__(self, 'fs_court', 'fs')
        self.saver = LinkSaver('seed.txt')

    def process_child_item(self, item):
        self.saver.add(item)
        print '%s saved' % item

    def parse_item(self, page):
        if '页面不存在' in page['content'][1]:
            return [page['realUrl']]
        return []


if __name__ == '__main__':
    e = Extractor()
    e.run()
