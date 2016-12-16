#!/usr/bin/env python
# -*- coding:utf8 -*-
from court.save import LinkSaver
from gkutils.parser import CWPParser
from shspider import ShanghaiCourtStore


class ShanghaiStoreFilter(CWPParser):
    def __init__(self):
        CWPParser.__init__(self, 'shanghai_court', 'shanghai_court')
        self.pagestore = ShanghaiCourtStore('sh_court_2')
        self.link_saver = LinkSaver('wrong.id.txt')

    def process_child_item(self, item):
        self.pagestore.save(int(item['crawlerUpdateTime'] / 1000), item['indexUrl'][17:], item['realUrl'],
                            item['content'][1])

    def parse_item(self, page):
        if page['indexUrl'][17] != '/':
            return [page]
        self.link_saver.add(page['indexUrl'][17:])
        return []

    def on_finish(self):
        self.link_saver.flush()

    def on_save(self, items):
        for item in items:
            self.pagestore.save(int(item['crawlerUpdateTime'] / 1000), item['indexUrl'][17:], item['realUrl'],
                                item['content'][1])


if __name__ == '__main__':
    job = ShanghaiStoreFilter()
    job.run()
