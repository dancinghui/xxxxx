#!/usr/bin/env python
# -*- coding:utf8 -*-

import time
import cutil
import requests
import re
from lxml import html
import hashlib

class htmlfind:
    def __init__(self, html, reg, which):
        self.s = ''
        self.start = 0
        self.which = 0
        self._begin(html, reg, which)

    def _begin(self, s, reg, which):
        if isinstance(s, unicode):
            s = s.encode('utf-8')
        regtype = type(re.compile(''))
        if isinstance(reg, unicode) or isinstance(reg, str) or isinstance(reg, regtype):
            reg = [reg]
        if not isinstance(reg, list):
            raise RuntimeError("unknown type")
        start=0
        for r in reg:
            if isinstance(r, unicode):
                r = r.encode('utf-8')
            if isinstance(r, str):
                m = re.search(r, s, start)
            elif isinstance(r, regtype):
                m = r.search(s, start)
            else:
                raise RuntimeError("unknown type")
            start = m.end(0)
        self.s = s
        self.start = start
        self.which = which

    def process_form(self):
        return cutil.process_form(self.s, self.start, self.which)

    def get_node(self):
        return cutil.get_html_node(self.s, self.start, self.which)

    def get_text(self):
        return cutil.get_html_text(self.s, self.start, self.which)

    def get_text_hash(self):
        return cutil.get_html_text_hash(self.s, self.start, self.which)


def test1():
    print cutil.gettid()
    print cutil.md5hex('abc')
    print cutil.get_html_text('<a href="dd">a  &nbsp;&#Xa0;&#97;b</a>', 0, 0)
    con = requests.get('http://51job.com/', headers={"User-Agent": "Mozilla/5.0 (compatiable; MSIE/11.0)"})
    print con.apparent_encoding
    if con.apparent_encoding.lower() in ['gb2312', 'gbk', 'gb18030']:
        con.encoding = "gb18030"
    else:
        con.encoding = con.apparent_encoding
    print "get code"
    fl = html.fromstring(con.text)
    tt = fl.xpath("//form[@name='loginform']")
    hehe = tt[0].text_content().strip()
    print hashlib.md5(hehe.encode('utf-8')).hexdigest()

    a, b = htmlfind(con.text, 'name="loginform"', 0).process_form()
    print a,b
    print htmlfind(con.text, 'name="loginform"', 0).get_node()
    print htmlfind(con.text, 'name="loginform"', 0).get_text()
    print htmlfind(con.text, 'name="loginform"', 0).get_text_hash()

if __name__ == '__main__':
    test1()
