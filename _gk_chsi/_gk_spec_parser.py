#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import os
import re

from accounts import provinces
from court.save import LinkSaver
from court.mail import send_attach
from gkutils.parser import FileAbstractParser
from spider import spider


class GkChsiSpecParser(FileAbstractParser):
    """高考位次分数线解析器"""
    kldms = {'2': u'文史', '11': u'文史', '1': u'文史', '6': u'理工', '15': u'理工', '5': u'理工'}
    bkccs = {'1': u'本科', '2': u'专科'}
    title = '省市,年份,科类,科类代码,层次,层次代码,院校代码,院校名称,专业代码,专业名称,录取分数区间'

    def __init__(self, name, channel, dburl='mongodb://root:helloipin@localhost/', save_title=True,
                 detail='detail_seeds', send_mail=False):
        FileAbstractParser.__init__(self, channel, name, 'res_spec_%s.csv' % name, url=dburl)
        self.save_title = save_title
        self.detail_seeds = []
        self.detail_seeds_file = detail
        self.unfetch_list = []
        self.fetched_list = []
        self.send_mail = send_mail

    def save(self, saver, page):
        saver.add(page)

    def pre_save(self, saver):
        if self.save_title:
            saver.add(GkChsiSpecParser.title)

    def parse_content(self, title, content, data, indexUrl):
        sm = re.search(r'([^>\s]+)<span class="colorRED">', content[1])
        job = copy.deepcopy(data)
        if not sm:
            print 'cannot find school name for', title, indexUrl
            self.unfetch_list.append(self.parse_job(indexUrl))
            return []
        sch_name = sm.group(1)
        m = re.findall(r'<input type="radio" name="zydm" value="([\d\w]*)" class="radio">([^<]*)</td>', content[1])
        res = []
        if m and len(m) > 0:
            self.fetched_list.append(self.parse_job(indexUrl))
            for code, name in m:
                ds = copy.deepcopy(data)
                ns = name.strip().split('（')
                res.append('%s,%s,%s,%s,%s' % (title, sch_name, code, ns[0], ns[1][:-3]))
                ds['yxmc'] = sch_name
                ds['zydm'] = code
                ds['zymc'] = ns[0]
                self.detail_seeds.append(ds)
        else:
            self.unfetch_list.append(self.parse_job(indexUrl))
            print 'cannot find any specialities', data
        return res

    def title_str(self, title):
        try:
            s = '%s,%s,%s,%s,%s,%s,%s' % (
                self.name, title[3], GkChsiSpecParser.kldms[title[4]], title[4],
                GkChsiSpecParser.bkccs[title[5]], title[5], title[2])
            return s
        except KeyError:
            return '%s,%s,%s,%s,%s,%s,%s' % (
                self.name, title[3], title[4], title[4], str(title[5]), title[5], title[2])

    def parse_job(self, indexUrl):
        title = indexUrl.split('/')
        data = {'wclx': 1, 'yxdm': title[2], 'kldm': title[4], 'bkcc': title[5], 'start': 0, 'years': title[3],
                'yxmc': ''}
        return ',,%s,,%s,%s,%s,' % (data['kldm'], data['bkcc'], data['years'], data['yxdm'],)

    def parse(self, detail):
        # indexUrl:yggk_spec_hb://10213/15/5/1/1/20
        # channel://yxdm/year/kldm/bkcc/wclx/start
        # start 分页标识，表示该页的起止
        tag = re.search(r'<span class="colorRED">([^\(<>]*?)\(([^,]*),([^\)]*)\)</span>', detail['content'][1])
        if not tag:
            print 'not the right content', detail['indexUrl']
            self.unfetch_list.append(self.parse_job(detail['indexUrl'].encode('utf-8')))
            return []

        prov = tag.group(1).decode('utf-8')
        klmc = tag.group(2).decode('utf-8')
        ccmc = tag.group(3).decode('utf-8')

        title = detail['indexUrl'].encode('utf-8').split('/')
        data = {'wclx': 1, 'yxdm': title[2], 'kldm': title[4], 'bkcc': title[5], 'start': 0, 'years': title[3],
                'yxmc': ''}
        if GkChsiSpecParser.kldms[data['kldm']] != klmc:
            if data['kldm'] == '1' or data['kldm'] == '2' or data['kldm'] == '11':
                title[4] = data['kldm'] = str(int(data['kldm']) + 4)
            elif data['kldm'] == '5' or data['kldm'] == '6' or data['kldm'] == '15':
                title[4] = data['kldm'] = str(int(data['kldm']) - 4)
        if GkChsiSpecParser.bkccs[data['bkcc']] != ccmc:
            if data['bkcc'] == '1':
                title[5] = data['bkcc'] = '2'
            elif data['bkcc'] == '2':
                title[4] = data['bkcc'] = '1'

        title_str = self.title_str(title).encode('utf-8')
        return self.parse_content(title_str, detail['content'], data, detail['indexUrl'].encode('utf-8'))

    def on_finish(self):
        FileAbstractParser.on_finish(self)
        self.detail_seeds = spider.util.unique_list(self.detail_seeds)
        seed_saver = LinkSaver(self.detail_seeds_file, 'w')
        for seed in self.detail_seeds:
            seed_saver.add(str(seed))
        unfetch_saver = LinkSaver('unfetched_seeds_' + self.channel)
        self.unfetch_list = spider.util.unique_list(self.unfetch_list)
        for link in self.unfetch_list:
            if link not in self.fetched_list:
                unfetch_saver.add(str(link))
        fetch_saver = LinkSaver('fetched_seeds_' + self.channel)
        self.fetched_list = spider.util.unique_list(self.fetched_list)
        for link in self.fetched_list:
            fetch_saver.add(str(link))
        print 'fetched', len(self.fetched_list)
        print 'unfetched', len(self.unfetch_list)
        if self.send_mail:
            fname = self._save_name.encode('utf-8')
            os.system("cp '%s' '/tmp/%s'" % (fname, fname))
            send_attach(['shibaofeng@ipin.com'], '%s专业数据' % self.name.encode('utf-8'),
                        '%s高考专业数据' % self.name.encode('utf-8'), '/tmp/%s' % fname,
                        '%s.csv' % self.name.encode('utf-8'))


if __name__ == '__main__':
    name = '福建'
    job = GkChsiSpecParser(name, 'yggk_spec_%s' % provinces[name], save_title=False,
                           detail='detail.seeds.%s' % provinces[name])
    # job = GkChsiSpecParser(u'新疆', 'yggk_spec_xj', save_title=True, detail='detail.seeds.xj')
    # job = GkChsiSpecParser(u'内蒙古', 'yggk_spec_nm', save_title=True, detail='detail.seeds.nm')
    # job = GkChsiSpecParser(u'天津', 'yggk_spec_tj', save_title=True, detail='detail.seeds.tj')
    # job = GkChsiSpecParser(u'湖北', 'yggk_spec_hb', save_title=False,detail='detail.seeds.hb')
    job.run()

    # job = GkChsiSpecParser(u'四川', 'yggk_spec_sc', save_title=False,detail='detail.seeds.sc')
    # job = GkChsiSpecParser('shanghai', 'yggk_spec_sh_', save_title=True, detail='detail.seeds.sh')
    # job.run()
