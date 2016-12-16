#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
from HTMLParser import HTMLParser

from parser import AbstractCourtParser


class CQNAParser(AbstractCourtParser):
    def __init__(self):
        AbstractCourtParser.__init__(self, 'page_store_cqna_court', '重庆南岸区', 'cqna.dat')
        self.parser = HTMLParser()

    def parse_title(self, content):
        m = re.search(r'<h2 class="title".*?>(.*?)</h2>', content, re.S)
        if m:
            return m.group(1)
        return ''

    def parse_code(self, content):
        # （<SPAN style="FONT-FAMILY: 仿宋_GB2312; FONT-SIZE: 16pt">20XX</SPAN>）<SPAN style="FONT-FAMILY: 仿宋_GB2312; FONT-SIZE: 16pt">X</SPAN>法民初字第<SPAN style="FONT-FAMILY: 仿宋_GB2312; FONT-SIZE: 16pt">号</SPAN></FONT></P>
        m = re.search(
            r'((（)|\().*?[\dXx]+.*?(\)|(）)).*?(法)*((民)|(行)|(刑))((初)|(终)|(一)|(二)|(特)).*?字(第)*.*?[\dXx]+.*?号',
            content)
        if m:
            return re.sub(r'<[^>]*>', '', m.group().strip())
        return ''

    def parse_content(self, content):
        m = re.search(r' <div class="conTxt">(.*?)</div>', content, re.S)
        if m:
            c = m.group(1)
            return re.sub(r'<[^>]*>', '', re.sub(r'<STYLE>.*?</STYLE>', '', re.sub('&nbsp;', ' ', c), 1, re.S)).strip()
        return content

    def parse_date(self, content):
        m = re.search(r'发布时间：([^<]*)', content)
        if m:
            return m.group(1).strip()
        return ''

    def pre_save(self, saver):
        pass


if __name__ == '__main__':
    p = CQNAParser()
    p.test_mode = True
    p.run()
