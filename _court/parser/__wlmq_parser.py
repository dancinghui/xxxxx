#!/usr/bin/env python
# -*- coding:utf8 -*-
import re

from court.util import cs_date_pattern_recent_utf8
from parser import AbstractCourtParser


class WLMQParser(AbstractCourtParser):
    def __init__(self):
        AbstractCourtParser.__init__(self, 'page_store_wlmq_court', '乌鲁木齐', 'wlmq.dat')

    def parse_title(self, content):
        res = content.split('\n', 3)
        if len(res) >= 3:
            return res[0] + res[1]
        elif len(res) >= 1:
            return res[0]
        return ''

    def parse_code(self, content):
        m = re.search(r'((（)|\()[\d\s]{4,}((）)|\)).*?((民)|(刑)|(执)|(行)).*?[\w\s]+号', content)
        if m:
            return m.group()
        return ''

    def parse_content(self, content):
        return content

    def parse_date(self, content):
        m = re.search(r'[一二三四五六七八九0〇○Ｏ零十OО\s]{4,}年[一二三四五六七八九〇十0○ＯOО\s]+月[一二三四五六七八九〇零○Ｏ0十OО\s]+日', content)
        if m:
            return m.group()
        return ''

    def pre_save(self, saver):
        pass


if __name__ == '__main__':
    p = WLMQParser()
    p.run()
