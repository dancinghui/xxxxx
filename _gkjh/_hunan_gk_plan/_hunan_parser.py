#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import re

from gkutils.parser import Parser


class HunanParser(Parser):
    def __init__(self):
        Parser.__init__(self, 'gk_hunan_plan', 'Hunan')

    def parse(self, detail):
        title = {}
        title['year'] = '2015'
        title['school'] = detail['indexUrl'].split('//')[1].encode('utf-8')
        title['beizhu'] = ''
        title['leipie'] = ''
        title['yxdm'] = ''
        return self.parse_content(title, detail['content'])

    def parse_content(self, title, content):
        plan = []
        items = re.findall(r'<tr bgcolor="FFFBEF">.*?<\/tr>', content[1], re.S)
        for i in items:
            c = re.sub(r'<[^>]*>|\s', '', re.sub('<\/td>', '|', i)).split('|')
            item = copy.deepcopy(title)
            item['pici'] = c[0]
            item['kelei'] = c[1]
            item['zydh'] = c[2]
            item['zymc'] = c[3]
            item['jhxz'] = c[4]
            item['xz'] = c[5]
            item['num'] = c[6]
            item['xf'] = c[7]
            item['yz'] = ''
            plan.append(item)
        return plan


def test_parse_content():
    f = open('a.html', 'r')
    content = ''
    for l in f:
        content += l
    items = re.findall(r'<tr bgcolor="FFFBEF">.*?<\/tr>', content, re.S)
    for i in items:
        c = re.sub(r'<[^>]*>|\s', '', re.sub('<\/td>', '|', i)).split('|')

        print '====================================='
    print len(items)


if __name__ == '__main__':
    job = HunanParser()
    job.run()
