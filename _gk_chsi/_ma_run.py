#!/usr/bin/env python
# -*- coding:utf8 -*-
import Queue
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

from multiacspider import BaseGkChsiFsxSpider

from multiacspider import ChsiSchoolSpider

from multiacspider import ChsiSpecialSpider

from multiacspider import ChsiDetailSpider

from multiacspider import gen_sch_seeds

from multiacspider import split_seeds

from _gk_school_parser import GkChsiSchoolParser

from _gk_spec_parser import GkChsiSpecParser

from _detail_parser import GkChsiDetailParser
from accounts import AccountManager, ProxyManager, provinces, ProxyQueue

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

    def run(self):
        if len(self.accounts['accounts']) > 0:
            kldms = BaseGkChsiFsxSpider.get_kldms(self.accounts['accounts'][0], self.accounts['prefix'])
            if len(kldms) == 2:
                self.accounts['kldms'][0] = str(kldms[0][0])
                self.accounts['kldms'][1] = str(kldms[1][0])
        prefix = self.accounts['prefix']
        if self.accounts['school'] and len(self.accounts['accounts']) > 0:
            gen_sch_seeds(self.accounts['score'], 'sch.seeds.' + prefix, self.accounts['kldms'])
            job = ChsiSchoolSpider(self.accounts['thcnt'], self.accounts['accounts'], self.accounts['prefix'],
                                   self.accounts['proxy'],
                                   sleep=self.accounts['sleep'],
                                   recover=self.accounts['sch.recover'],
                                   kldms=self.accounts['kldms'], bkccs=self.accounts['bkccs'],
                                   seeds='sch.seeds.' + prefix)
            job.run()

        if self.accounts['sch.parser'] and len(self.accounts['accounts']) > 0:
            # job = GkChsiSchoolParser(u'湖北', 'yggk_sch_hb', save_title=True)
            job = GkChsiSchoolParser(self.accounts['name'], 'yggk_sch_' + prefix, save_title=False,
                                     save_name='spec.seeds.' + prefix)
            job.run()

        if self.accounts['spec']:
            job = ChsiSpecialSpider(self.accounts['thcnt'], self.accounts['accounts'],
                                    self.accounts['prefix'],
                                    self.accounts['proxy'],
                                    sleep=self.accounts['sleep'],
                                    recover=self.accounts['spec.recover'],
                                    kldms=self.accounts['kldms'], bkccs=self.accounts['bkccs'],
                                    seeds='spec.seeds.' + prefix)
            job.run()
        if self.accounts['spec.parser']:
            # parse data
            parser = GkChsiSpecParser(self.accounts['name'], 'yggk_spec_' + prefix, save_title=False,
                                      detail='detail.seeds.' + prefix)
            parser.run()
        if self.accounts['detail'] and len(self.accounts['accounts']) > 0:
            job = ChsiDetailSpider(self.accounts['thcnt'], self.accounts['accounts'], self.accounts['prefix'],
                                   self.accounts['proxy'],
                                   sleep=self.accounts['sleep'],
                                   recover=self.accounts['detail.recover'],
                                   kldms=self.accounts['kldms'], bkccs=self.accounts['bkccs'],
                                   seeds='detail.seeds.' + prefix)

            job.run()

        if self.accounts['detail.parser']:
            parser = GkChsiDetailParser(self.accounts['name'], 'yggk_detail_' + prefix,
                                        save_title=True)
            parser.run()


def gen_jobs_params(jobs, school=True, spec=True, detail=True, sch_parser=True, spec_parser=True,
                    detail_parser=True, sch_r=True,
                    spec_r=True, detail_r=True, threadcnt=2, kldms=None, bkccs=None, sleep=1.0):
    if bkccs is None:
        bkccs = ['1', '2']
    if kldms is None:
        kldms = ['5', '1']
    return {
        'accounts': jobs['accounts'],
        'prefix': jobs['prefix'], 'sleep': sleep, 'school': school, 'sch.parser': sch_parser, 'kldms': kldms,
        'bkccs': bkccs, 'proxy': jobs['proxy'],
        'spec.parser': spec_parser, 'spec': spec, 'detail': detail, 'name': jobs['name'], 'detail.recover': detail_r,
        'spec.recover': spec_r, 'sch.recover': sch_r, 'score': jobs['score'],
        'detail.parser': detail_parser, 'thcnt': threadcnt}


def run_full_jobs(accounts, sleep=1.0):
    runner = FullJobRunner(gen_jobs_params(accounts, sleep=sleep))
    runner.run()


def run_school_jobs(accounts, recover=True, results=False):
    runner = FullJobRunner(
        gen_jobs_params(accounts, spec=False, detail=False, spec_parser=False, detail_parser=False,
                        sch_r=recover, sch_parser=results))
    runner.run()


def run_detail_jobs(accounts, gen_seeds=True, recover=True):
    runner = FullJobRunner(
        gen_jobs_params(accounts, spec=False, school=False,
                        detail=False, spec_parser=gen_seeds, detail_parser=False,
                        detail_r=recover, sch_parser=False))
    runner.run()


def run_spec_jobs(accounts, seeds=True, recover=True, results=False):
    runner = FullJobRunner(
        gen_jobs_params(accounts, spec=True, school=False, detail=False, spec_parser=results,
                        detail_parser=False,
                        spec_r=recover, sch_parser=seeds))
    runner.run()


def gen_spec_unfetched_seeds(accounts):
    runner = FullJobRunner(
        gen_jobs_params(accounts, school=False, spec=False, detail=False, sch_parser=False,
                        spec_parser=True, detail_parser=False))
    runner.run()
    os.system('cp \'unfetched_seeds_yggk_spec_%s\' \'spec.seeds.%s\'' % (accounts['prefix'], accounts['prefix']))


def re_do_spec(accounts):
    runner = FullJobRunner(
        gen_jobs_params(accounts, school=False, spec=True, detail=True, sch_parser=False,
                        spec_parser=True, detail_parser=False, spec_r=False))
    runner.run()


def gen_detail_unfetched_seeds(accounts):
    runner = FullJobRunner(
        gen_jobs_params(accounts, school=False, spec=False, detail=False, sch_parser=False,
                        spec_parser=False, detail_parser=True))
    runner.run()
    os.system('cp \'unfetched_seeds_yggk_detail_%s\' \'detail.seeds.%s\'' % (accounts['prefix'], accounts['prefix']))


def re_do_detail(accounts):
    runner = FullJobRunner(
        gen_jobs_params(accounts, school=False, spec=False, detail=True, sch_parser=False,
                        spec_parser=False, detail_parser=True, detail_r=False))
    runner.run()


def recruit_jobs(accs, sleep=1.0):
    start = datetime.now()
    try:
        runner = FullJobRunner(
            gen_jobs_params(accs, sleep=sleep, detail_parser=False))
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


def recheck(accs, sleep=1.0, level=0):
    if level >= 0:
        start = datetime.now()
        try:
            runner = FullJobRunner(
                gen_jobs_params(accs, sleep=sleep, detail_parser=False))
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
            gen_spec_unfetched_seeds(accs)
            re_do_spec(accs)
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

            gen_detail_unfetched_seeds(accs)
            re_do_detail(accs)

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
    def __init__(self, jobs, proxy='proxy_s'):
        self.ac = AccountManager()
        self.pm = ProxyManager()
        self.pq = ProxyQueue()
        self.pq.load(proxy)
        self.pm.load(proxy)
        self.jobs = jobs
        self.threads = []
        self.running = False
        self.job_queue = Queue.Queue()

    def init(self):
        random.seed(int(time.time()))
        for job in self.jobs:
            job['proxy'] = self.pm.get_good_proxy(1)
            for ac in self.ac.get(job['name'], job['count']):
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
            , 'proxy': None
            , 'score': 750
        }
        if job['name'] == '海南':
            ac['score'] = 900
        elif job['name'] == '上海':
            ac['score'] = 600
        elif job['name'] == '江苏':
            ac['score'] = 500
        acs = self.ac.get(job['name'], job['count'])
        if len(acs) > 0:
            for a in acs:
                ac['accounts'].append(a.gen_run_param())
            proxy = self.pq.get_good_proxy()
            print '%s start ' % ac['name']
            recruit_jobs(ac)
            self.pq.release(proxy)

    def runner(self, tid):
        job = self.jobs[tid]
        ac = {
            'accounts': []
            , 'name': job['name']
            , 'prefix': provinces[job['name']]
            , 'score': 750
            , 'proxy': job['proxy']
        }
        if job['name'] == '海南':
            ac['score'] = 900
        elif job['name'] == '上海':
            ac['score'] = 600
        elif job['name'] == '江苏':
            ac['score'] = 500
        for a in self.ac.get(job['name'], job['count']):
            ac['accounts'].append(a.gen_run_param())
        print '%s start ' % ac['name']
        recruit_jobs(ac)


class QueueJobManager():
    def __init__(self, jobs, thcnt=2, proxy='proxy_s', times=3):
        self.ac = AccountManager()
        self.pq = ProxyManager()
        self.pq.load(proxy)
        self.jobs = jobs
        self.threads = []
        self.running = False
        self.thread_cnt = thcnt
        self.times = times
        self.job_queue = Queue.Queue()
        self.done_job = 0
        self.job_lock = threading.RLock()

    def distpatch(self):
        for job in self.jobs:
            ac = {
                'accounts': []
                , 'name': job['name']
                , 'prefix': provinces[job['name']]
                , 'score': 750
                , 'times': 0
            }
            if job['name'] == '海南':
                ac['score'] = 900
            elif job['name'] == '上海':
                ac['score'] = 600
            elif job['name'] == '江苏':
                ac['score'] = 500
            acs = self.ac.get(job['name'], job['count'])
            if len(acs) > 0:
                for a in acs:
                    ac['accounts'].append(a.gen_run_param())
                self.job_queue.put(ac)

    def run(self):
        if self.running:
            return
        self.running = True
        self.distpatch()
        for tid in range(self.thread_cnt):
            proxy = self.pq.get_good_proxy()
            if proxy is None:
                break
            t = threading.Thread(target=self.runner, args=(proxy,))
            self.threads.append(t)
        for t in self.threads:
            t.start()
        time.sleep(2)
        for t in self.threads:
            t.join()
        self.ac.save()
        self.threads = []

    def runner(self, proxy):
        while True:
            ac = self.job_queue.get()
            ac['proxy'] = proxy
            times = ac.get('times', 0)
            if times < self.times:
                print '%s start %d' % (ac['name'], ac['times'])
                recruit_jobs(ac)
                ac['times'] += 1
                ac['proxy'] = None
                self.job_queue.put(ac)
            else:
                print '%s start check crawling' % ac['name']
                level = 0
                while level < 3:
                    level = recheck(ac, level=level)
                with self.job_lock:
                    self.done_job += 1
                    if self.done_job >= len(self.jobs):
                        break


if __name__ == '__main__':
    jobs = [
        {'name': '内蒙古', 'count': 3},
        # {'name': '新疆', 'count': 3},
        # {'name': '河南', 'count': 8},

    ]
    qm = QueueJobManager(jobs)
    qm.run()
