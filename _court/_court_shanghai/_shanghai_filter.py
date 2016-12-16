#!/usr/bin/env python
# -*- coding:utf8 -*-
from court.save import LinkSaver
from gkutils.parser import CWPParser
from shspider import ShanghaiCourtStore


class ShanghaiStoreFilter(CWPParser):
    def __init__(self):
        CWPParser.__init__(self, 'sh_court', 'sh_court')
        self.pagestore = ShanghaiCourtStore('shanghai_court')
        self.link_saver = LinkSaver('invalid.seeds.txt')

    def init(self):
        pass

    def process_child_item(self, item):
        self.pagestore.save(int(item['crawlerUpdateTime'] / 1000), item['indexUrl'][10:], item['realUrl'],
                            item['content'][1])

    def parse_item(self, page):
        if 'JavaScript</p></h3></center></body></html>' not in page['content'][1]:
            return [page]
        self.link_saver.add(page['indexUrl'][10:])
        return []

    def on_finish(self):
        self.link_saver.flush()

    def on_save(self, items):
        for item in items:
            self.pagestore.save(int(item['crawlerUpdateTime'] / 1000), item['indexUrl'][10:], item['realUrl'],
                                item['content'][1])


if __name__ == '__main__':
    job = ShanghaiStoreFilter()
    job.run()
