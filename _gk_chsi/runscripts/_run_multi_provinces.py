#!/usr/bin/env python
# -*- coding:utf8 -*-

import logging
import os
import threading
import time

from _detail_parser import GkChsiDetailParser
from _gk_school import GkChsiSchoolSpider
from _gk_school_parser import GkChsiSchoolParser
from _gk_spec_parser import GkChsiSpecParser
from _gk_special2 import GkChsiSpecialSpider2
from chsispider import ChsiSpider


def run_jobs(accounts):
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'crawler.log.' + accounts['prefix'] + accounts['job_tag']),
                        level=logging.NOTSET,
                        format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                        datefmt='%m/%d %I:%M:%S %p')

    if accounts['school']:
        #             'kldms': [1, 5]}
        job = GkChsiSchoolSpider(1, accounts, accounts['prefix'], accounts['proxy'], accounts['sleep'],
                                 kldms=accounts['kldms'],
                                 highscore=750,
                                 captcha_limit=5000000, recover=False)
        # job = GkChsiFsxSpider(1, accounts, accounts['prefix'], accounts['proxy'], 1, kldms=accounts['kldms'],captcha_limit=5000000)
        job.run()
    if accounts['sch.parser']:
        # job = GkChsiSchoolParser(u'湖北', 'yggk_sch_hb', save_title=True)
        job = GkChsiSchoolParser(accounts['name'], 'yggk_sch_' + accounts['prefix'], save_title=True,
                                 save_name='spec.seeds.' + accounts['prefix'])
        job.run()

    if accounts['spec']:
        # fetch spec

        job = GkChsiSpecialSpider2(1, accounts, accounts['prefix'], accounts['proxy'], accounts['sleep'],
                                   bkccs=accounts['bkccs'], kldms=accounts['kldms'],
                                   seeds='spec.seeds.' + accounts['prefix'],
                                   recover_seeds='spec.recover.seeds.' + accounts['prefix'])
        job.run()
    if accounts['spec.parser']:
        # parse data
        parser = GkChsiSpecParser(accounts['name'], 'yggk_spec_' + accounts['prefix'], save_title=True,
                                  detail='detail.seeds.' + accounts['prefix'])
        parser.run()
    if accounts['detail']:
        job = ChsiSpider(accounts['thcnt'], accounts, accounts['prefix'], accounts['proxy'], sleep=accounts['sleep'],
                         recover=accounts['detail.recover'],
                         kldms=accounts['kldms'], bkccs=accounts['bkccs'], seeds=accounts['detail.seeds'],
                         job_tag=accounts['job_tag'])
        job.run()
    if accounts['detail.parser']:
        parser = GkChsiDetailParser(accounts['name'], 'yggk_detail_' + accounts['prefix'], save_title=True)
        parser.run()


def split_seeds(sf, prefix, size):
    links = []
    with open(sf, 'r') as f:
        for l in f:
            links.append(l.strip())
        count = 0
        fs = []
        for i in range(1, size + 1):
            s1 = open(prefix + str(i), 'w')
            fs.append(s1)
        for l in links:
            r = count % 3
            fs[r].write(l + '\n')
            count += 1
        for f in fs:
            f.flush()
            f.close()
    return len(links)


class JobRunner():
    def __init__(self, accounts):
        self.accounts = accounts

    def run(self):
        threads = []
        for ac in self.accounts:
            t = threading.Thread(target=run_jobs, args=(ac,))
            threads.append(t)
        for t in threads:
            t.start()
        time.sleep(3)
        for t in threads:
            t.join()


if __name__ == '__main__':
    ua = [
        None,
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
    # {'username': 'hubei102', 'password': 'bobo2016', 'prefix': 'hb', 'sleep': 0.95, 'sch.seeds': 'school.res.hb',
    #  'proxy': None, 'kldms': ['5', '1'], 'school': False, 'spec': False, 'detail': True, 'name': '', 'ua': ua[3],
    #  'detail.recover': True,
    #  'detail.parser': True, 'bkccs': ['1', '2']}
    # accounts = [
    #     {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
    #      'proxy': '106.75.134.189:18888:ipin:ipin1234', 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
    #      'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[4], 'detail.recover': True,
    #      'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.1', 'job_tag': '.3', 'thcnt': 4,
    #      'bkccs': ['1', '2']},
    #     {'username': 'sichuan101', 'password': 'bobo2016', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
    #      'proxy': None, 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
    #      'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[3], 'detail.recover': True,
    #      'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.2', 'job_tag': '.3', 'thcnt': 4,
    #      'bkccs': ['1', '2']},
    #     {'username': 'sichuan102', 'password': 'bobo2016', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
    #      'proxy': None, 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
    #      'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[5], 'detail.recover': True,
    #      'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.3', 'job_tag': '.3', 'thcnt': 4,
    #      'bkccs': ['1', '2']}
    # ]
    accounts = [
        {'username': 'sichuan102', 'password': 'bobo2016', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
         'proxy': None, 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
         'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[5], 'detail.recover': True,
         'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.3c.3', 'job_tag': '.3', 'thcnt': 4,
         'bkccs': ['1', '2']},
        {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
         'proxy': '106.75.134.190:18888:ipin:ipin1234', 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
         'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[4], 'detail.recover': True,
         'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.3c.1', 'job_tag': '.1', 'thcnt': 4,
         'bkccs': ['1', '2']},
        {'username': 'sichuan101', 'password': 'bobo2016', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
         'proxy': '106.75.134.189:18888:ipin:ipin1234', 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
         'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[3], 'detail.recover': True,
         'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.3c.2', 'job_tag': '.2', 'thcnt': 4,
         'bkccs': ['1', '2']}

    ]
    # accounts = [
    #     {'username': 'sichuan102', 'password': 'bobo2016', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
    #      'proxy': None, 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
    #      'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[5], 'detail.recover': True,
    #      'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.3', 'job_tag': '.3', 'thcnt': 4,
    #      'bkccs': ['1', '2']}
    # ]
    job = JobRunner(accounts)

    job.run()

    # parse results
    accounts2 = [
        {'username': 'sichuan102', 'password': 'bobo2016', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
         'proxy': None, 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
         'spec.parser': True, 'spec': False, 'detail': False, 'name': u'四川', 'ua': ua[5], 'detail.recover': True,
         'detail.parser': True, 'detail.seeds': 'detail.seeds.sc.3', 'job_tag': '.3', 'thcnt': 4,
         'bkccs': ['1', '2']}
    ]

    job = JobRunner(accounts2)
    job.run()

    # split job seeds
    length = split_seeds('unfetched_seeds_detail_yggk_detail_sc', 'detail.seeds.sc.l.', 3)
    print 'remain len', length
    accounts3 = [
        {'username': 'sichuan102', 'password': 'bobo2016', 'prefix': 'sc', 'sleep': 1.0,
         'sch.seeds': 'school.res.sc',
         'proxy': None, 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
         'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[5], 'detail.recover': False,
         'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.l.3', 'job_tag': '.3', 'thcnt': 4,
         'bkccs': ['1', '2']},
        {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
         'proxy': '106.75.134.190:18888:ipin:ipin1234', 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
         'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[4], 'detail.recover': False,
         'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.l.1', 'job_tag': '.3', 'thcnt': 4,
         'bkccs': ['1', '2']},
        {'username': 'sichuan101', 'password': 'bobo2016', 'prefix': 'sc', 'sleep': 1.0,
         'sch.seeds': 'school.res.sc',
         'proxy': '106.75.134.189:18888:ipin:ipin1234', 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
         'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[3], 'detail.recover': False,
         'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.l.2', 'job_tag': '.3', 'thcnt': 4,
         'bkccs': ['1', '2']}
    ]
    if length > 0:
        # fetch remain
        job = JobRunner(accounts3)
        job.run()

        # parse results again
        job = JobRunner(accounts2)
        job.run()
