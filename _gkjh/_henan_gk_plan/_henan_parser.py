#!/usr/bin/env python
# -*- coding:utf8 -*-
# !/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import re

from gkutils.parser import Parser
import pici
import yxdh


class HenanParser(Parser):
    def __init__(self):
        Parser.__init__(self, 'gk_henan_plan', 'Henan')

    def parse(self, detail):
        title = {}
        try:
            (school, pc) = detail['indexUrl'].encode('utf-8').split('//')[1].split('-')
        except ValueError as e:
            print e.message
            print detail['indexUrl']
            return
        title['year'] = '2015'
        title['school'] = yxdh.scho_map[school].encode('utf-8')
        title['pici'] = pici.pici[pc]
        title['yxdm'] = re.search(r'\?YXDH=(\d+)', detail['realUrl']).group(1)
        if self.test_mode:
            print detail['content'][1]
            self._print_count += 1
            return []
        else:
            return self.parse_content(title, detail['content'])

    def parse_content(self, title, content):
        plan = []
        items = re.findall(r'<TR>.*?<\/TR>', re.search(r'<table id="pccontent">.*', content[1]).group(),
                           re.S)
        for i in items:
            c = re.sub(r'<[^>]*>|\s|\&nbsp;', '', re.sub('<\/TD>|<\/td>', '|', i)).split('|')
            item = copy.deepcopy(title)
            try:
                zy = re.search(r'\[([\w\d]+)\](.*)', c[0])
                if zy is None:
                    print c[0]
                    continue
                item['zydh'] = zy.group(1)
                item['zymc'] = zy.group(2)
                item['kelei'] = c[1]
                item['xz'] = ''
                item['num'] = c[2]
                item['xf'] = ''
                item['yz'] = ''
                item['jhxz'] = ''
                item['beizhu'] = c[3]
                item['leipie'] = ''
            except IndexError as e:
                print e.message
                print c
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
    job = HenanParser()
    job.test_mode = False
    job.print_limit = 1
    job.run()
