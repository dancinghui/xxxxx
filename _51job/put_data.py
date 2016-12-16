#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import Bin2DB
from spider.util import htmlfind, TimeHandler
import _51job
import re
import sys


class DisJD51PageStore(_51job.PageStore51):
    def save_time_log(self, indexUrl, cur_tm):
        return

    def do_save(self, odoc, content, fnpath=None, offset=None):
        odoc.update({'pageContentPath': "binf::%s::%d" % (fnpath, offset)})
        return self.upsert_doc(odoc['indexUrl'], odoc)

    def extract_content(self):
        content=''
        cur_doc = self.get_cur_doc().cur_content
        if isinstance(cur_doc, unicode):
            cur_doc = cur_doc.encode('utf-8')
        find = re.search(r'tCompany_text">(.*?)</div>', cur_doc, re.S)
        if find:
            content = htmlfind.remove_tag(find.group(1), True)
            return content

        divs = htmlfind.findTag(cur_doc, 'div', 'class="jtag inbox">')
        if divs:
            spans = re.findall(r'<span[^<>]*>(.*?)</span>', divs[0], re.S)
            if spans:
                spans = spans[:-1] # 忽略更新时间
                for span in spans:
                    content += htmlfind.remove_tag(span, True) + "#"

        if isinstance(content, unicode):
            content = content.encode('utf-8')

        hf = htmlfind(self.get_cur_doc().cur_content, '<div class="bmsg job_msg inbox">', 0)
        t2 = htmlfind.remove_tag(hf.get_node(), 1)

        if isinstance(t2, unicode):
            t2 = t2.encode('utf-8')

        content = content + t2
        return content

    def page_time(self):
        cur_doc = self.get_cur_doc().cur_content
        if isinstance(cur_doc, unicode):
            cur_doc = cur_doc.encode('utf-8')

        s = re.search(r'发布日期：</dt>.*?<dd class="text_dd">(.*?)</dd>', cur_doc, re.S)
        if s:
            return TimeHandler.fmt_time(s.group(1))

        tag = htmlfind.findTag(cur_doc, 'div', 'class="jtag inbox"')
        if tag:
            m = re.search(r'(\d*-?\d+-\d+发布)', tag[0])
            if m:
                t = TimeHandler.fmt_time(m.group(1))
                return t



class JD51Bin2DB(Bin2DB):
    def __init__(self):
        Bin2DB.__init__(self)
        self.pagestore = DisJD51PageStore()

    def parse_name(self, n):
        m = re.match(r'jd_51job\.(\d+)\.(\d+)', n)
        if m:
            return m.group(2), m.group(1)
        return None, None

    def get_pagestore(self):
        return self.pagestore

    def get_url(self, jdid):
        return "http://jobs.51job.com/all/%s.html" % jdid


if __name__ == "__main__":
    sb = JD51Bin2DB()
    for fn in sys.argv[1:]:
        sb.save(fn)
