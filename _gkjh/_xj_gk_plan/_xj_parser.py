#!/usr/bin/env python
# -*- coding:utf8 -*-
# !/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import re

from gkutils.parser import Parser


class XinjiangParser(Parser):
    pcdm = {'z': '本科零批次',
            '1': '本科一批次',
            'D': '（汉语系）贫困专项南疆单列对口援疆计划本科一批次',
            'E': '（汉语系）贫困专项南疆单列对口援疆计划本科二批次',
            'F': '南疆单列对口援疆计划本科三批次',
            'M': '（民语系）贫困专项南疆单列对口援疆计划（本一院校）',
            'K': '（民语系）贫困专项南疆单列对口援疆计划（本二院校',
            '2': '本科二批次',
            'T': '本科三批提前批次',
            '3': '本科三批次',
            '4': '专科零批次',
            '5': '高职(专科)一批次',
            'S': '高职(专科)二批次',
            '6': '三校高职批次'
            }
    yzdm = {'01': '汉语言',
            '02': '民语言',
            '04': '蒙语言',
            '05': '民考汉',
            '95': '双语班'
            }

    def __init__(self):
        Parser.__init__(self, 'gk_xj_plan', 'Xinjiang')

    def parse(self, detail):
        title = {}
        try:
            rs = re.findall(r'yzdm=(\d+)\&pcdm=([\w\d])\&yxdh=(\d+)\&yxmc=\d+([^\d]+)',
                            detail['realUrl'].encode('utf-8'))
        except ValueError as e:
            print e.message
            print detail['indexUrl']
            return
        title['year'] = '2015'
        title['school'] = rs[0][3]
        title['yz'] = XinjiangParser.yzdm[rs[0][0]]
        title['pici'] = XinjiangParser.pcdm[rs[0][1]]
        title['yxdm'] = rs[0][2]
        return self.parse_content(title, detail['content'])

    def parse_content(self, title, content):
        plan = []
        items = re.findall(r'<TR>.*?<\/TR>', content[1], re.S)
        for i in items[2:-1]:
            c = re.sub(r'<[^>]*>|\s', '', re.sub('<\/TD>', '|', i)).split('|')
            item = copy.deepcopy(title)
            item['kelei'] = c[0]
            item['zydh'] = c[1]
            item['zymc'] = c[2]
            item['jhxz'] = ''
            item['xz'] = c[3]
            item['num'] = c[5]
            item['xf'] = c[4]
            item['beizhu'] = c[6]
            item['leipie'] = c[7]
            plan.append(item)
        return plan


def test_parse_content():
    f = open('a.html', 'r')
    content = ''
    for l in f:
        content += l
    items = re.findall(r'<TR>.*?<\/TR>', content, re.S)
    for i in items:
        c = re.sub(r'<[^>]*>|\s', '', re.sub('<\/TD>', '|', i)).split('|')
        print c
        print '====================================='
    print len(items)


if __name__ == '__main__':
    # test_parse_content()
    job = XinjiangParser()
    job.run()
