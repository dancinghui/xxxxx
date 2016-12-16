#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import logging
import os
import random
import re
import threading
import time
import traceback
from datetime import datetime

import pymongo

from _detail_parser import GkChsiDetailParser
from _gk_school_parser import GkChsiSchoolParser
from _gk_spec_parser import GkChsiSpecParser
from accounts import AccountManager, ProxyManager, provinces, ProxyQueue
from chsispider import BaseGkChsiFsxSpider, ChsiDetailSpider, ChsiSpecialSpider, split_seeds, gen_sch_seeds, \
    ChsiSchoolSpider
from spider.runtime import Log
from spider.savebin import BinReader
from spider.util import sendmail

school_model = {
    'account': [],
    'prefix': '',
    'kldms': '',
    'sleep': 1.0,
    'score': 750,
    'recover': False
}
spec_model = {
    'account': [],
    'prefix': '',
    'kldms': [],
    'bkccs': [],
    'sleep': 1.0,
    'score': 750,
    'seeds': 'seeds',
    'recover': False,
}
detail_model = {
    'account': [],
    'prefix': '',
    'kldms': [],
    'bkccs': [],
    'sleep': 1.0,
    'score': 750,
    'seeds': 'seeds',
    'recover': False,
}

ua = [
    'firefox',
    '=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36',
    '=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:45.0) Gecko/20100101 Firefox/45.0',
    '=Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0)',
    '=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36',
    '=Opera/9.80 (Windows NT 6.2; Win64; x64) Presto/2.12.388 Version/12.17',
    '=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:45.0) Gecko/20100101 Firefox/45.0',
    '=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.110 Safari/537.36'
    '=Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36 OPR/26.0.1656.60'
]


class FullJobRunner():
    def __init__(self, accounts):
        self.accounts = accounts
        logging.basicConfig(
            filename=os.path.join(os.getcwd(), '%s.spider.log' % self.accounts['prefix']),
            level=logging.NOTSET,
            format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
            datefmt='%m/%d %I:%M:%S %p')

    def split_jobs(self, runner, arr):
        threads = []
        for ac in arr:
            t = threading.Thread(target=runner, args=(ac,))
            threads.append(t)
        for t in threads:
            t.start()
        time.sleep(3)
        for t in threads:
            t.join()

    @staticmethod
    def fetch_remain_time(accounts):
        rt = []
        for ac in accounts['accounts']:
            rt.append(BaseGkChsiFsxSpider.get_remain_time(ac, accounts['prefix']))
        return rt

    def fetch_school(self, params):
        #             'kldms': [1, 5]}
        job = ChsiSchoolSpider(params['thcnt'], params['account'], params['prefix'], params['account']['proxy'],
                               sleep=params['sleep'],
                               recover=params['recover'], ua=params['account']['ua'],
                               kldms=params['kldms'], bkccs=params['bkccs'], seeds=params['account']['seeds'],
                               job_tag=params['account']['job_tag'])
        # job = GkChsiFsxSpider(1, accounts, accounts['prefix'], accounts['proxy'], 1, kldms=accounts['kldms'],captcha_limit=5000000)
        job.run()

    def fetch_spec(self, params):
        job = ChsiSpecialSpider(params['thcnt'], params['account'], params['prefix'], params['account']['proxy'],
                                sleep=params['sleep'],
                                recover=params['recover'], ua=params['account']['ua'],
                                kldms=params['kldms'], bkccs=params['bkccs'], seeds=params['account']['seeds'],
                                job_tag=params['account']['job_tag'])
        job.run()

    def fetch_detail(self, params):
        job = ChsiDetailSpider(params['thcnt'], params['account'], params['prefix'], params['account']['proxy'],
                               sleep=params['sleep'],
                               recover=params['recover'], ua=params['account']['ua'],
                               kldms=params['kldms'], bkccs=params['bkccs'], seeds=params['account']['seeds'],
                               job_tag=params['account']['job_tag'])

        job.run()

    def run(self):
        if len(self.accounts['accounts']) > 0:
            kldms = BaseGkChsiFsxSpider.get_kldms(self.accounts['accounts'][0], self.accounts['prefix'])
            if len(kldms) == 2:
                self.accounts['kldms'][0] = str(kldms[0][0])
                self.accounts['kldms'][1] = str(kldms[1][0])
        prefix = self.accounts['prefix']
        if self.accounts['school'] and len(self.accounts['accounts']) > 0:
            gen_sch_seeds(self.accounts['score'], 'sch.seeds.' + prefix, self.accounts['kldms'])
            rates = FullJobRunner.fetch_remain_time(self.accounts)
            split_seeds('sch.seeds.' + prefix, len(self.accounts['accounts']), rates=rates)
            arr = []
            i = 1
            for ac in self.accounts['accounts']:
                params = copy.deepcopy(school_model)
                params['account'] = ac
                params['account']['seeds'] = 'sch.seeds.' + prefix + '.' + str(i)
                params['prefix'] = self.accounts['prefix']
                params['sleep'] = self.accounts['sleep']
                params['kldms'] = self.accounts['kldms']
                params['bkccs'] = self.accounts['bkccs']
                params['recover'] = self.accounts['sch.recover']
                params['account']['job_tag'] = '.' + str(i)
                params['thcnt'] = self.accounts['thcnt']
                arr.append(params)
                i += 1
            self.split_jobs(self.fetch_school, arr)
            pass

        if self.accounts['sch.parser'] and len(self.accounts['accounts']) > 0:
            # job = GkChsiSchoolParser(u'湖北', 'yggk_sch_hb', save_title=True)
            job = GkChsiSchoolParser(self.accounts['name'], 'yggk_sch_' + prefix, save_title=False,
                                     save_name='spec.seeds.' + prefix)
            job.run()

        if self.accounts['spec']:
            rates = FullJobRunner.fetch_remain_time(self.accounts)
            split_seeds('spec.seeds.' + prefix, len(self.accounts['accounts']), rates=rates)
            arr = []
            i = 1
            for ac in self.accounts['accounts']:
                params = copy.deepcopy(detail_model)
                params['account'] = ac
                params['prefix'] = prefix
                params['sleep'] = self.accounts['sleep']
                params['account']['seeds'] = 'spec.seeds.' + prefix + '.' + str(i)
                params['kldms'] = self.accounts['kldms']
                params['bkccs'] = self.accounts['bkccs']
                params['thcnt'] = self.accounts['thcnt']
                params['account']['job_tag'] = '.' + str(i)
                params['recover'] = self.accounts['spec.recover']
                i += 1
                arr.append(params)
            self.split_jobs(self.fetch_spec, arr)
        if self.accounts['spec.parser']:
            # parse data
            parser = GkChsiSpecParser(self.accounts['name'], 'yggk_spec_' + prefix, save_title=False,
                                      detail='detail.seeds.' + prefix)
            parser.run()
        if self.accounts['detail'] and len(self.accounts['accounts']) > 0:
            rates = FullJobRunner.fetch_remain_time(self.accounts)
            split_seeds('detail.seeds.' + prefix, len(self.accounts['accounts']), rates=rates)
            arr = []
            i = 1
            for ac in self.accounts['accounts']:
                params = copy.deepcopy(detail_model)
                params['account'] = ac
                params['prefix'] = prefix
                params['sleep'] = self.accounts['sleep']
                params['account']['seeds'] = 'detail.seeds.' + prefix + '.' + str(i)
                params['kldms'] = self.accounts['kldms']
                params['bkccs'] = self.accounts['bkccs']
                params['thcnt'] = self.accounts['thcnt']
                params['account']['job_tag'] = '.' + str(i)
                params['recover'] = self.accounts['detail.recover']
                i += 1
                arr.append(params)
            self.split_jobs(self.fetch_detail, arr)
        if self.accounts['detail.parser']:
            parser = GkChsiDetailParser(self.accounts['name'], 'yggk_detail_' + prefix,
                                        save_title=True)
            parser.run()


class Counter():
    def __init__(self, channel):
        self.mongo = pymongo.MongoClient('mongodb://root:helloipin@localhost/')
        self.channel = 'page_store_' + channel

    def read_all(self):
        res = []
        c = self.mongo.admin[self.channel]
        bin_reader = None
        for i in c.find():
            (ft, ofn, pos) = i['pageContentPath'].split('::')
            if bin_reader is None or bin_reader.fd.name != ofn:
                bin_reader = BinReader(ofn)
            i['content'] = bin_reader.readone_at(int(pos))
            res.append(i)
        return res

    def run(self, offile='account.log', mode='w'):
        lines = []
        res = self.read_all()
        for page in res:
            m = re.search(r'<td align="right">([\w\d]+)\s*[^\s<]*\s*剩余：</td><td align="left">(\d+)分钟</td>',
                          page['content'][1])
            if m:
                data = {}
                data['account'] = m.group(1)
                data['time'] = m.group(2)
                data['url'] = page['indexUrl']
                lines.append(data)
                print data['account'], data['time']
            else:
                print 'failed to find account', page['indexUrl']
        with open(offile, mode) as f:
            for c in lines:
                f.write(c['account'] + ':' + c['time'] + ':' + c['url'] + '\n')


def gen_jobs_params(accounts, name, prefix, school=True, spec=True, detail=True, sch_parser=True, spec_parser=True,
                    detail_parser=True, sch_r=True,
                    spec_r=True, detail_r=True, threadcnt=2,
                    score=750, kldms=None, bkccs=None, sleep=1.0):
    if bkccs is None:
        bkccs = ['1', '2']
    if kldms is None:
        kldms = ['5', '1']
    return {
        'accounts': accounts,
        'prefix': prefix, 'sleep': sleep, 'school': school, 'sch.parser': sch_parser, 'kldms': kldms,
        'bkccs': bkccs,
        'spec.parser': spec_parser, 'spec': spec, 'detail': detail, 'name': name, 'detail.recover': detail_r,
        'spec.recover': spec_r, 'sch.recover': sch_r, 'score': score,
        'detail.parser': detail_parser, 'thcnt': threadcnt}


def run_full_jobs(accounts, name, prefix, score=750, sleep=1.0):
    runner = FullJobRunner(gen_jobs_params(accounts, name, prefix, score=score, sleep=sleep))
    runner.run()


def run_school_jobs(accounts, name, prefix, score=750, recover=True, results=False):
    runner = FullJobRunner(
        gen_jobs_params(accounts, name, prefix, spec=False, detail=False, spec_parser=False, detail_parser=False,
                        score=score, sch_r=recover, sch_parser=results))
    runner.run()


def run_detail_jobs(accounts, name, prefix, gen_seeds=True, recover=True):
    runner = FullJobRunner(
        gen_jobs_params(accounts, name, prefix, spec=False, school=False,
                        detail=False, spec_parser=gen_seeds, detail_parser=False,
                        detail_r=recover, sch_parser=False))
    runner.run()


def run_spec_jobs(accounts, name, prefix, seeds=True, recover=True, results=False):
    runner = FullJobRunner(
        gen_jobs_params(accounts, name, prefix, spec=True, school=False, detail=False, spec_parser=results,
                        detail_parser=False,
                        spec_r=recover, sch_parser=seeds))
    runner.run()


def gen_spec_unfetched_seeds(accounts, name, prefix):
    runner = FullJobRunner(
        gen_jobs_params(accounts, name, prefix, school=False, spec=False, detail=False, sch_parser=False,
                        spec_parser=True, detail_parser=False))
    runner.run()
    os.system('cp \'unfetched_seeds_yggk_spec_%s\' \'spec.seeds.%s\'' % (prefix, prefix))


def re_do_spec(accounts, name, prefix):
    runner = FullJobRunner(
        gen_jobs_params(accounts, name, prefix, school=False, spec=True, detail=True, sch_parser=False,
                        spec_parser=True, detail_parser=False, spec_r=False))
    runner.run()


def gen_detail_unfetched_seeds(accounts, name, prefix):
    runner = FullJobRunner(
        gen_jobs_params(accounts, name, prefix, school=False, spec=False, detail=False, sch_parser=False,
                        spec_parser=False, detail_parser=True))
    runner.run()
    os.system('cp \'unfetched_seeds_yggk_detail_%s\' \'detail.seeds.%s\'' % (prefix, prefix))


def re_do_detail(accounts, name, prefix):
    runner = FullJobRunner(
        gen_jobs_params(accounts, name, prefix, school=False, spec=False, detail=True, sch_parser=False,
                        spec_parser=False, detail_parser=True, detail_r=False))
    runner.run()


def smart_full_job(accs, name, prefix, score=750, sleep=1.0, level=0):
    if level >= 0:
        start = datetime.now()
        try:
            runner = FullJobRunner(
                gen_jobs_params(accs, name, prefix, score=score, sleep=sleep, detail_parser=False))
            runner.run()
        except Exception as e:
            msg = ''
            Log.error(e)
            traceback.print_exc()
            msg += 'end time:%s\n' % datetime.now()
            msg += 'start time:%s\n' % start
            msg += 'exception:%s\n' % e.__class__
            msg += 'message:%s\n' % e.message
            msg += 'level:0\n'
            sendmail(['shibaofeng@ipin.com'], 'chsi spider exception', msg)
            return 0
    if level >= 1:
        start = datetime.now()
        try:
            gen_spec_unfetched_seeds(accs, name, prefix)
            re_do_spec(accs, name, prefix)
        except Exception as e:
            msg = ''
            Log.error(e)
            traceback.print_exc()
            msg += 'end time:%s\n' % datetime.now()
            msg += 'start time:%s\n' % start
            msg += 'exception:%s\n' % e.__class__
            msg += 'message:%s\n' % e.message
            msg += 'level:1\n'
            sendmail(['shibaofeng@ipin.com'], 'chsi spider exception', msg)
            return 1
    if level >= 2:
        start = datetime.now()
        try:

            gen_detail_unfetched_seeds(accs, name, prefix)
            re_do_detail(accs, name, prefix)

        except Exception as e:
            msg = ''
            Log.error(e)
            traceback.print_exc()
            msg += 'end time:%s\n' % datetime.now()
            msg += 'start time:%s\n' % start
            msg += 'exception:%s\n' % e.__class__
            msg += 'message:%s\n' % e.message
            msg += 'level:2\n'
            sendmail(['shibaofeng@ipin.com'], 'chsi spider exception', msg)
            return 2
    return 3


class JobManager():
    def __init__(self, jobs, proxy='proxy_r'):
        self.ac = AccountManager()
        self.pm = ProxyManager()
        self.pq = ProxyQueue()
        self.pq.load(proxy)
        self.pm.load(proxy)
        self.jobs = jobs
        self.threads = []
        self.running = False

    def init(self):
        random.seed(int(time.time()))
        for job in self.jobs:
            for ac in self.ac.get(job['name'], 2):
                ac.proxy = self.pm.get_good_proxy(7)
                ac.user_agent = ua[random.randint(0, len(ua)) % len(ua)]
        for job in self.jobs:
            for ac in self.ac.get(job['name'], job['count']):
                if ac.proxy is None:
                    ac.proxy = self.pm.get_good_proxy(1)
                    ac.user_agent = ua[random.randint(0, len(ua)) % len(ua)]

    def run(self):
        if self.running:
            return
        self.init()
        for tid in range(len(self.jobs)):
            t = threading.Thread(target=self.runner, args=(tid,))
            self.threads.append(t)
        for t in self.threads:
            t.start()
        time.sleep(2)
        for t in self.threads:
            t.join()
        self.ac.save()

    def random_run(self):
        if self.running:
            return
        for tid in range(len(self.jobs)):
            t = threading.Thread(target=self.rand_runner, args=(tid,))
            t.start()
            t.setDaemon(True)
            time.sleep(1)
            self.threads.append(t)
        time.sleep(2)
        for t in self.threads:
            t.join()
        self.ac.save()

    def rand_runner(self, tid):
        job = self.jobs[tid]
        ac = {
            'accounts': []
            , 'name': job['name']
            , 'prefix': provinces[job['name']]
        }
        acs = self.ac.get(job['name'], job['count'])
        if len(acs) > 0:
            for a in acs:
                a.proxy = self.pq.get_good_proxy()
                ac['accounts'].append(a.gen_run_param())
            level = 0
            print '%s start ' % ac['name']
            while level < 3:
                if ac['name'] != '海南':
                    level = smart_full_job(ac['accounts'], ac['name'], ac['prefix'], level=level)
                else:
                    level = smart_full_job(ac['accounts'], ac['name'], ac['prefix'], 900, level=level)
            for a in acs:
                self.pq.release(a.proxy)
                a.proxy = None

    def runner(self, tid):
        job = self.jobs[tid]
        ac = {
            'accounts': []
            , 'name': job['name']
            , 'prefix': provinces[job['name']]
        }
        for a in self.ac.get(job['name'], job['count']):
            ac['accounts'].append(a.gen_run_param())
        level = 0
        print '%s start ' % ac['name']
        while level < 3:
            if ac['name'] != '海南':
                level = smart_full_job(ac['accounts'], ac['name'], ac['prefix'], level=level)
            else:
                level = smart_full_job(ac['accounts'], ac['name'], ac['prefix'], 900, level=level)
