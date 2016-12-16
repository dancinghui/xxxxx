#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import time
from datetime import datetime

from court.save import LinkSaver
from gkutils.parser import CWPParser
from zlspider import PatentStore, Patent


class PatentAbstractExtractor(CWPParser):
    def __init__(self):
        CWPParser.__init__(self, 'abs_list', 'abs_list', 'zhuanli')
        self.store = PatentStore('abstract')
        self.failed_link = LinkSaver('abstract.parser.failed.txt')
        self.url_format = 'http://epub.sipo.gov.cn/dxbdl.action?strSources=fmmost&strWhere=%s&recordCursor=0&strLicenseCode=&action=dxbdln'
        self.save_count = 0

    def init(self):
        print 'job start at', datetime.now()

    def on_finish(self):
        print '%d patents saved' % self.save_count

    def process_child_item(self, item):
        self.save_count += 1
        if self.test_mode:
            print item['apply_code']
            print item['pub_code']
            print item['type']
            print item['code']
            # print item['content']
        else:
            jid = item['apply_code'] + '/' + item['pub_code']
            if not self.store.find_any(self.store.channel + '://' + jid):
                self.store.save(int(time.time()), jid,
                                Patent.form_download_url(item['pub_code'], item['type'], item['code']), item['content'])

    def parse_item(self, page):
        patent_contents = re.findall(
            r'<div class="cp_box">.*?<img src="qrcode/\w{2}\d+\w?.png" width="74" height="74" /></a>',
            page['content'][1], re.S)
        patents = []
        for pc in patent_contents:
            m = re.search(r'申请号：(\d+\w?)</li>', pc)
            if m:
                apply_code = m.group(1)
            else:
                self.failed_link.add('1,%s' % page['indexUrl'])
                continue
            u = re.search(r"javascript:dxb3\('(\w+)','([\w\d]+)','(\d)'\);", pc)
            if not u or len(u.groups()) < 3:
                self.failed_link.add('2,%s' % page['indexUrl'])
                continue
            patents.append(
                {'apply_code': apply_code, 'pub_code': u.group(2), 'content': pc, 'type': u.group(1),
                 'code': u.group(3)})
        return patents

    @staticmethod
    def parse_content(pc):
        con = re.sub('&nbsp;|&ensp;', '', re.sub('<[^>]*>', '', pc.replace('</li>', '\n').replace('<ul>', '\n')))
        con = re.sub(r'\n+', '\n', con.replace(' ', '').replace('\t', ''))
        res = []
        for c in con.split('\n'):
            cr = c.strip()
            if cr != '':
                res.append(cr)
        c9 = res[9]
        res[8] = res[8].replace('全部', '') + c9
        res.remove(c9)
        return '\n'.join(res).lstrip()

    def save(self, saver, page):
        pass


if __name__ == '__main__':
    job = PatentAbstractExtractor()
    job.test_mode = False
    job.run()
