#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import re

from court.save import LinkSaver
from gkutils.parser import FileAbstractParser
from spider import spider


class GkChsiDetailParser(FileAbstractParser):
    """高考位次分数线解析器"""
    kldms = {'1': u'文科', '11': u'文科', '2': u'文史', '5': u'理科', '15': u'理科', '6': u'理工'}
    bkccs = {'1': u'本科', '2': u'专科'}
    struct = {
        'prov': '省市',
        'years': '年份',
        'klmc': '科类',
        'kldm': '科类代码',
        'ccmc': '报考层次',
        'bkcc': '层次代码',
        'yxdm': '院校代码',
        'yxmc': '院校名称',
        'zydm': '专业代码',
        'zymc': '专业名称',
        'lqwc': '录取位次',
        'wcfs': '位次分数',
        'ksrs': '该位次所有考生人数',
        'lqpc': '录取批次',
        'pcrs': '该批次录取人数',
        'start': 0
    }

    title = '省市,年份,科类,科类代码,层次,层次代码,院校代码,院校名称,专业代码,专业名称'

    def __init__(self, name, channel, dburl='mongodb://root:helloipin@localhost/', save_title=True):
        FileAbstractParser.__init__(self, channel, name, 'res_detail_%s.csv' % name, url=dburl)
        self.save_title = save_title
        self.unfetch_list = []
        self.fetched_list = []

    def save(self, saver, page):
        saver.add(page)

    def pre_save(self, saver):
        if self.save_title and saver:
            saver.add(self.title_str(GkChsiDetailParser.struct))

    def parse_content(self, indexUrl, content, data):
        sm = re.search(
            r'>(.*?)<span class="colorRED">(.*?)</span>专业<span class="colorRED">\d+</span>年在<span class="colorRED">(.*?)\((.*?),(.*?)\)<\/span>',
            content[1])
        if not sm:
            print 'cannot find title name for', indexUrl
            self.unfetch_list.append(self.to_detail_job(data, False))
            return []
        data['yxmc'] = sm.group(1)
        data['zymc'] = sm.group(2)
        data['prov'] = sm.group(3)
        data['klmc'] = sm.group(4)
        data['ccmc'] = sm.group(5)
        m = re.findall(r'<tr align="center" class="table_style_small">(.*?)<\/tr>', content[1], re.S)
        result = []
        if m and len(m) > 0:
            self.fetched_list.append(self.to_detail_job(data, False))
            for item in m:
                ds = copy.deepcopy(data)
                res = re.sub('<.*?>|\s', '', re.sub('<\/td>', ',', item)).split(',')
                ds['lqwc'] = res[0]
                ds['wcfs'] = res[1]
                ds['ksrs'] = res[2]
                ds['lqpc'] = res[3]
                ds['pcrs'] = res[4]
                s = self.title_str(ds)
                result.append(s)
        else:
            self.unfetch_list.append(self.to_detail_job(data, False))
            print 'cannot find any specialities', indexUrl
        return result

    def to_detail_job(self, title, mc=True):
        if mc:
            return str({'years': title['years'], 'kldm': title['kldm'], 'bkcc': title['bkcc'], 'yxdm': title['yxdm'],
                        'zydm': title['zydm'], 'wclx': 1, 'start': title['start'], 'zymc': title['zymc']})
        else:
            return str({'years': title['years'], 'kldm': title['kldm'], 'bkcc': title['bkcc'], 'yxdm': title['yxdm'],
                        'zydm': title['zydm'], 'wclx': 1, 'start': title['start'], 'zymc': ''})

    def title_str(self, title):
        return '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s' % (
            title['prov'], title['years'], title['klmc'], title['kldm'],
            title['ccmc'], title['bkcc'], title['yxdm'], title['yxmc'], title['zydm'],
            title['zymc'], title['lqwc'], title['wcfs'], title['ksrs'],
            title['lqpc'], title['pcrs'])

    def parse(self, detail):
        # indexUrl:  yggk_detail_hb://10001/15/5/1/1/0/020100
        # channel://yxdm/year/kldm/bkcc/wclx/start/zydm/
        # start 分页标识，表示该页的起止
        title = detail['indexUrl'].encode('utf-8').split('/')
        data = copy.deepcopy(GkChsiDetailParser.struct)
        data['prov'] = title[0].split('_')[2]
        data['yxdm'] = title[2]
        data['kldm'] = title[4]
        data['bkcc'] = title[5]
        data['years'] = title[3]
        data['zydm'] = title[8]
        data['start'] = title[7]
        return self.parse_content(detail['indexUrl'].encode('utf-8'), detail['content'], data)

    def on_finish(self):
        FileAbstractParser.on_finish(self)
        unfetch_saver = LinkSaver('unfetched_seeds_detail_' + self.channel)
        self.unfetch_list = spider.util.unique_list(self.unfetch_list)
        self.fetched_list = spider.util.unique_list(self.fetched_list)
        unfetched = []
        for link in self.unfetch_list:
            if link not in self.fetched_list:
                unfetched.append(link)
        self.unfetch_list = unfetched
        for link in self.unfetch_list:
            unfetch_saver.add(link)
        unfetch_saver.flush()
        fetchsaver = LinkSaver('fetched_seeds_detail_' + self.channel)
        for l in self.fetched_list:
            fetchsaver.add(str(l))
        fetchsaver.flush()
        print 'fetched jobs', len(self.fetched_list)
        print 'unfetched jobs', len(self.unfetch_list)


if __name__ == '__main__':
    # job = GkChsiDetailParser(u'湖北', 'yggk_detail_hb', save_title=True)
    # job.run()
    #
    job = GkChsiDetailParser(u'福建', 'yggk_detail_fj', save_title=False)
    # job = GkChsiDetailParser(u'四川', 'yggk_detail_sc', save_title=True)
    job.run()
    # job = GkChsiDetailParser('liaoning', 'yggk_detail_ln_',
    #                          save_title=True)  # job = GkChsiDetailParser(u'四川', 'yggk_detail_sc', save_title=True)
    # job.run()
    # job = GkChsiDetailParser('error', 'yggk_detail_sh',
    #                          save_title=True)  # job = GkChsiDetailParser(u'四川', 'yggk_detail_sc', save_title=True)
    # job.run()
