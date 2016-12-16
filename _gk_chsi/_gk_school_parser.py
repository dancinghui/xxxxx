#!/usr/bin/env python
# -*- coding:utf8 -*-
import re

from gkutils.parser import FileAbstractParser
from spider import spider


class GkChsiSchoolParser(FileAbstractParser):
    """高考位次分数线解析器"""
    kldms = {'1': u'文科', '11': u'文科', '2': u'文史', '5': u'理科', '15': u'理科', '6': u'理工'}
    bkccs = {'1': u'本科', '2': u'专科'}
    title = '省市,科类,科类代码,层次,层次代码,年份,院校代码,院校名称'

    def __init__(self, name, channel, dburl='mongodb://root:helloipin@localhost/', save_title=True, save_name=None):
        FileAbstractParser.__init__(self, channel, name, save_name, url=dburl)
        self.save_title = save_title
        self.unfetched_list = []
        self.fetched_list = []

    def save(self, saver, page):
        saver.add(page)

    def pre_save(self, saver):
        if saver is None:
            return

    def parse_content(self, title, content):
        m = re.findall(r'<input type="radio" name="yxdm" value="(\d+)" class="radio">([^<]*)</td>', content[1])
        res = []
        if m and len(m) > 0:
            for code, name in m:
                res.append('%s,%s,%s' % (title, code, name.strip()))
        else:
            print 'can\'t find any  school from paper', title
        return res

    def title_str(self, title):
        try:
            s = '%s,%s,%s,%s,%s,%s' % (
                self.name, GkChsiSchoolParser.kldms[str(title['kldm'])], title['kldm'],
                GkChsiSchoolParser.bkccs[str(title['bkcc'])], title['bkcc'],
                title['years'])
            return s
        except KeyError:
            return '%s,%s,%s,%s,%s,%s' % (self.name, str(title['kldm']), title['kldm'],
                                          str(title['bkcc']), title['bkcc'],
                                          title['years'])

    def parse(self, detail):
        jid = detail['indexUrl'].encode('utf-8').split('//')[1]
        if jid[0] == '{':
            title = eval(jid)
        else:
            params = jid.split('/')
            title = {'highscore': params[3], 'lowscore': params[4], 'bkcc': params[2], 'kldm': params[1],
                     'years': params[0], 'start': params[5]}
        title_str = self.title_str(title).encode('utf-8')
        res = self.parse_content(title_str, detail['content'])
        if len(res) != 0:
            self.fetched_list.append(str(title))
            return res
        else:
            self.unfetched_list.append(str(title))
            return []

    def on_finish(self):
        FileAbstractParser.on_finish(self)
        self.fetched_list = spider.util.unique_list(self.fetched_list)
        self.unfetched_list = spider.util.unique_list(self.unfetched_list)
        ls = []
        for l in self.unfetched_list:
            if l not in self.fetched_list:
                ls.append(l)
        self.unfetched_list = ls
        print '%d unfetched' % len(ls)
        print '%d fetched' % len(self.fetched_list)
        with open('unfetch_' + self.channel, 'w') as f:
            for l in self.unfetched_list:
                f.write(l + '\n')


if __name__ == '__main__':
    # job = GkChsiSchoolParser(u'湖北', 'yggk_sch_hb', save_title=True)
    name = '福建'
    job = GkChsiSchoolParser(name, 'yggk_sch_fj', save_title=False, save_name='spec.seeds.fj')
    job.run()
