#!/usr/bin/env python
# -*- coding:utf8 -*-
# !/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import re

from gkutils.parser import Parser


class BeijingParser(Parser):
    def __init__(self):
        Parser.__init__(self, 'gk_bj_plan', 'Beijing')

    def parse(self, detail):
        title = {}
        try:
            (school, year, lp) = detail['indexUrl'].encode('utf-8').split('//')[1].split('-')
        except ValueError as e:
            (school1, school2, year, lp) = detail['indexUrl'].encode('utf-8').split('//')[1].split('-')
            school = school1 + '-' + school2
            print detail['indexUrl']
        title['year'] = year
        title['school'] = school
        title['kelei'] = lp
        title['yxdm'] = re.search('\/115\/(\d+);', detail['realUrl']).group(1)
        return self.parse_content(title, detail['content'])

    def parse_content(self, title, content):
        plan = []
        items = re.findall(r'<tr bgcolor="">.*?<\/tr>', content[1], re.S)
        for i in items:
            c = re.sub(r'<[^>]*>|\s', '', re.sub('<\/td>', '|', i)).split('|')
            item = copy.deepcopy(title)
            item['pici'] = c[3]
            item['zydh'] = c[0]
            item['zymc'] = c[1]
            item['jhxz'] = ''
            item['xz'] = c[5]
            item['num'] = c[4]
            item['xf'] = c[6]
            item['yz'] = c[7]
            item['beizhu'] = ''
            item['leipie'] = ''
            plan.append(item)
        return plan


def test_parse_content():
    f = open('a.html', 'r')
    content = ''
    for l in f:
        content += l
    items = re.findall(r'<tr bgcolor="">.*?<\/tr>', content, re.S)
    for i in items:
        c = re.sub(r'<[^>]*>|\s', '', re.sub('<\/td>', '|', i)).split('|')
        print c
        print '====================================='
    print len(items)


if __name__ == '__main__':
    # test_parse_content()
    job = BeijingParser()
    job.run()
