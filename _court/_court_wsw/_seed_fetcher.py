#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import time

import datetime

import spider
from court.save import LinkSaver
from court.util import date_split, Intervals
from wswsave import WenshuLinkDb
from wswspider import WenshuSpider


class SeedGenerator(WenshuSpider):
    """
    Wen shu seed generator
    generator seed format:
    {
     file : court.txt,
     start: 2015-01-01,
     end: 2015-06-20
     }
    因为最大页数是25，超过25的服务器不返回数据，所以需要拆分查询，每次查询文数量不能超过20*25=500
    """
    date_format = '%Y%m%d'

    def __init__(self, seed, thcnt=4, recover=False):
        WenshuSpider.__init__(self, thcnt, recover=recover)
        self.store = WenshuLinkDb('ws_seed')
        self.seed = seed
        self.failed_log = LinkSaver('failed_job.txt')

    def need_split(self, context, url):
        pass

    def get_page_store(self):
        pass

    def add_list_job(self, url, con):
        pass

    def dispatch(self):
        if self.recover:
            seeds = []
            raw_seeds = self.gen_seeds()
            fetched = self.export_fetch()
            for seed in raw_seeds:
                fetched_arr = fetched.get(seed['key'])
                if fetched_arr is None:
                    seeds.append(seed)
                    continue
                unfetched = self.check_unfetched([self.date2i(seed['start']), self.date2i(seed['end'])], fetched_arr.origin)
                for u in unfetched:
                    copy_seed = copy.deepcopy(seed)
                    copy_seed['start'] = u[0]
                    copy_seed['end'] = u[1]
                    seeds.append(copy_seed)
        else:
            seeds = self.gen_seeds()
        print 'load %d seeds' % len(seeds)
        for seed in seeds:
            self.add_main_job(seed)
        time.sleep(2)
        print 'wait for queue'
        self.wait_q()
        self.add_job(None)

    @staticmethod
    def to_list_seed_id(seed):
        return '%s/%s/%s' % (seed['key'], seed['start'], seed['end'])

    def run_job(self, jobid):
        param = self.seed2param(jobid)
        url = 'http://wenshu.court.gov.cn/list/list/?sorttype=0&conditions=searchWord+%s+SLFY++法院名称:%s&conditions=searchWord++CPRQ++裁判日期:%s TO %s' % (
            jobid['court'], jobid['court'], jobid['start'], jobid['end'],)
        con = self.request_results(param, page=1)
        if self.check_exception(con, jobid):
            return
        try:
            res = eval(eval(con.text))
        except NameError as e:
            print 'NameError', e.message
            if not self.re_add_job(jobid):
                self.failed_log.add('0,' + str(jobid))
            return
        if res and len(res) > 0:
            count = int(res[0]['Count'])
            if count > 500:
                print '[%d] %s [%s,%s]==>%d need split' % (
                    jobid['level'], jobid['court'], jobid['start'], jobid['end'], count)
                res = date_split(jobid['start'], jobid['end'])
                if len(res) == 1:
                    print '[%d] %s [%s,%s]==>%d split failed' % (
                        jobid['level'], jobid['court'], jobid['start'], jobid['end'], count)
                    self.failed_log.add('1,' + str(jobid))
                else:
                    self.add_job(
                        {'level': jobid['level'] + 1, 'court': jobid['court'], 'start': res[0][0], 'end': res[0][1],
                         'key': jobid['key']})
                    self.add_job(
                        {'level': jobid['level'] + 1, 'court': jobid['court'], 'start': res[1][0], 'end': res[1][1],
                         'key': jobid['key']})
            else:
                print '[%d] %s [%s,%s]==>%d ok' % (
                    jobid['level'], jobid['court'], jobid['start'], jobid['end'], count)
                self.store.save(url, self.to_list_seed_id(jobid), '%s,%s' % (jobid['court'], count), int(time.time()))
        else:
            print 'fail to get content', jobid
            self.failed_log.add('2,' + str(jobid))

    @staticmethod
    def to_seed(start, end):
        return start.strftime(SeedGenerator.date_format) + end.strftime(SeedGenerator.date_format)

    def gen_seeds(self):
        seeds = []
        with open(self.seed['file'], 'r') as f:
            for l in f:
                d = eval(l.strip())
                seeds.append(
                    {'court': d['court'], 'key': d['key'], 'start': self.seed['start'], 'end': self.seed['end'],
                     'level': 0})
        return seeds

    @staticmethod
    def get_date_str(year, month=None, day=None):
        if day is None:
            day = 1
        if month is None:
            month = 1
        if day < 10:
            ds = '0' + str(day)
        else:
            ds = str(day)
        if month < 10:
            ms = '0' + str(month)
        else:
            ms = str(month)
        return '%s%s%s' % (year, ms, ds)

    @staticmethod
    def get_end_day(year, month):
        if month > 31 or month < 1:
            return 0
        if 2 == month:
            if year % 4 == 0 and year % 400 != 0 or year % 400 == 0:
                return 29
            else:
                return 28
        elif month in [4, 6, 9, 11]:
            return 30
        else:
            return 31

    def export(self, mode='json'):
        seeds = self.store.export_seeds()
        sf = open('seed.dat', 'w')
        sd = {}
        for s in seeds:
            sd[s['id'][(len(self.store.channel) + 3):]] = s['content'].split(',')

        res = []
        for k, v in sd.items():
            ks = k.split('/')
            if mode == 'json':
                res.append(str({'court': v[0], 'count': v[1], 'key': ks[0], 'start': ks[1], 'end': ks[2]}))
            else:
                l = '%s,%s,%s,%s,%s' % (v[0], ks[0], ks[1], ks[2], v[1])
                res.append(l)

        res = spider.util.unique_list(res)
        for r in res:
            print r
            sf.write(r + '\n')
        print '%d seeds saved' % len(res)

    @staticmethod
    def date_convert(date_str):
        return datetime.datetime.strptime(date_str, '%Y-%m-%d')

    RELATIVE_DATE = datetime.datetime.strptime('1970-01-01', '%Y-%m-%d')

    @staticmethod
    def date2i(date_str):
        return (SeedGenerator.date_convert(date_str) - SeedGenerator.RELATIVE_DATE).days

    def export_fetch(self):
        fetched = self.store.export_seeds(lambda item: item['indexUrl'][(len(self.store.channel) + 3):].split('/'))
        res = {}
        for num, start, end in fetched:
            arr = res.get(num)
            s = self.date2i(start)
            e = self.date2i(end)
            if arr:
                arr.add([s, e])
            else:
                itv = Intervals()
                itv.add([s, e])
                res[num] = itv
        for r in res.keys():
            res[r].check()
        return res

    @staticmethod
    def i2date(num):
        return (SeedGenerator.RELATIVE_DATE + datetime.timedelta(days=num)).strftime('%Y-%m-%d')

    @staticmethod
    def check_unfetched(main, intervals):
        interval = Intervals()
        interval.add(main)
        for itv in intervals:
            interval.remove(itv)
        itvs = []
        for itv in interval.origin:
            itvs.append([SeedGenerator.i2date(itv[0]), SeedGenerator.i2date(itv[1])])
        return itvs


def _test_recover():
    seed = {'file': 'court.txt', 'start': '1985-01-01', 'end': '2016-05-31'}
    gen = SeedGenerator(seed, 5, recover=True)
    res = gen.export_fetch()
    origin = [gen.date2i(seed['start']), gen.date2i(seed['end'])]
    for r in res.keys():
        print r, '==>', gen.check_unfetched(origin, res[r].origin)


if __name__ == '__main__':
    seed = {'file': 'court.txt', 'start': '1985-01-01', 'end': '2016-05-31'}
    gen = SeedGenerator(seed, 5, recover=True)
    gen.test_mode = True
    # gen.load_proxy('proxy', index=0, auto_change=True)
    # gen.set_proxy('106.75.134.189:18888:ipin:ipin1234', 0)
    gen.load_proxy('proxy', 1)
    gen.run()
    # res = gen.export_fetch()

    # _test_recover()
