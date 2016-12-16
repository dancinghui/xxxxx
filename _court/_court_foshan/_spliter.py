#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import time

from _court_foshan import FSCourtStore
from court.save import LinkSaver
from gkutils.parser import CWPParser


class Extractor(CWPParser):
    def __init__(self):
        CWPParser.__init__(self, 'fs_court2', 'fs')
        self.store = FSCourtStore('fs_court')

    def process_child_item(self, item):
        m = re.search(r'://([^/:]+)$', item['indexUrl'])
        jid = m.group(1)
        self.store.save(int(time.time()), jid, item['realUrl'], item['content'][1])

    def parse_item(self, page):
        if '页面不存在' not in page['content'][1]:
            return [page]
        return []


if __name__ == '__main__':
    e = Extractor()
    e.run()
