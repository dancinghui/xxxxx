#!/usr/bin/env python
# -*- coding:utf8 -*-
import re

from court.save import LinkSaver
from gkutils.parser import FileAbstractParser


class GkChsiParser(FileAbstractParser):
    """高考位次分数线解析器"""
    kldms = {'1': u'文科', '2': u'文史', '5': u'理科', '6': u'理工'}
    bkccs = {'1': u'本科', '2': u'专科'}
    title = '省市,科类,层次,年份,院校名称,专业名称,位次,本位次录取数,该专业总录取数,最低分,最低分位次,最高分,最高分位次,平均分'

    def __init__(self, name, channel, dburl='mongodb://root:helloipin@localhost/'):
        FileAbstractParser.__init__(self, channel, name, 'res_%s.csv' % name, dburl)
        self.score_rank = []

    def save(self, saver, page):
        saver.add(page)

    def pre_save(self, saver):
        saver.add(GkChsiParser.title)
        s2 = LinkSaver('res_score_%s' % self.name, 'w')
        s2.add('省市,科类,层次,位次,分数')
        for r in self.score_rank:
            s2.add(r)
        s2.flush()

    def parse_content(self, title, content):
        m = re.findall(r'<tr align="center" class="table_style_small">.*?<\/tr>', content[1], re.S)
        rlist = []
        for item in m:
            res = re.sub(',查看,', '', re.sub(r'<[^>]*>|\s', '', re.sub(r'<\/td>', ',', item)))
            rlist.append('%s,%s' % (title, res))
        return rlist

    def title_str(self, title):
        return '%s,%s,%s' % (self.name, GkChsiParser.kldms[title['kldm']], GkChsiParser.bkccs[title['bkcc']])

    def parse(self, detail):
        title = {}
        (name, year, wclx, kldm, bkcc, score, wcpp, page) = detail['indexUrl'].encode('utf-8').split('//')[1].split('/')
        title['name'] = name
        title['year'] = year
        title['wclx'] = wclx
        title['kldm'] = kldm
        title['bkcc'] = bkcc
        title['score'] = score
        title['wcpp'] = wcpp
        title['page'] = page
        title_str = self.title_str(title).encode('utf-8')
        self.score_rank.append('%s,%s,%s' % (title_str, title['wclx'], title['score']))
        return self.parse_content(title_str, detail['content'])


if __name__ == '__main__':
    job = GkChsiParser(u'湖北', 'gkchsi_hb')
    job.run()
