#!/usr/bin/env python
# -*- coding:utf8 -*-
import logging
import os

import time

from _detail_parser import GkChsiDetailParser
from _gk_school import GkChsiSchoolSpiderCaptcha
from _gk_school_parser import GkChsiSchoolParser
from _gk_spec_parser import GkChsiSpecParser
from _gk_special2 import GkChsiSpecialSpiderCaptcha
from chsispider import ChsiSpider


def run_jobs(accounts):
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'crawler.log.' + accounts['prefix'] + accounts['job_tag']),
                        level=logging.NOTSET,
                        format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                        datefmt='%m/%d %I:%M:%S %p')

    if accounts['school']:
        #             'kldms': [1, 5]}
        job = GkChsiSchoolSpiderCaptcha(1, accounts, accounts['prefix'], accounts['proxy'], accounts['sleep'],
                                        kldms=accounts['kldms'],
                                        highscore=accounts['score'],
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
        if accounts['school']:
            time.sleep(60)
        job = GkChsiSpecialSpiderCaptcha(1, accounts, accounts['prefix'], accounts['proxy'], accounts['sleep'],
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
    accounts = [
        {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'sleep': 0.95, 'sch.seeds': 'school.res.sc',
         'proxy': '106.75.134.191:18888:ipin:ipin1234', 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
         'spec.parser': True, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[2], 'detail.recover': True,
         'detail.parser': False, 'job_tag': '.1', 'thcnt': 4, 'detail.seeds': 'detail.seeds.sc', 'score': 750,
         'bkccs': ['1', '2']},
        {'username': 'star0945', 'password': 'AHO001009', 'prefix': 'nm', 'sleep': 1.0, 'sch.seeds': 'school.res.nm',
         'proxy': '106.75.134.191:18888:ipin:ipin1234', 'kldms': ['5', '1'], 'school': True, 'sch.parser': True,
         'spec.parser': False, 'spec': True, 'detail': True, 'name': u'内蒙', 'ua': ua[5], 'detail.recover': False,
         'detail.parser': False, 'job_tag': '.1', 'thcnt': 4, 'detail.seeds': 'detail.seeds.nm', 'score': 750,
         'bkccs': ['1', '2']},
        {'username': 'pinkpink', 'password': 'AHO001009', 'prefix': 'jl', 'sleep': 1.0, 'sch.seeds': 'school.res.jl',
         'proxy': '106.75.134.191:18888:ipin:ipin1234', 'kldms': ['5', '1'], 'school': True, 'sch.parser': True,
         'spec.parser': False, 'spec': True, 'detail': True, 'name': u'吉林', 'ua': ua[5], 'detail.recover': False,
         'detail.parser': False, 'job_tag': '.1', 'thcnt': 4, 'detail.seeds': 'detail.seeds.jl', 'score': 750,
         'bkccs': ['1', '2']},
        {'username': 'akg999', 'password': 'AHO001009', 'prefix': 'sh', 'sleep': 1.0, 'sch.seeds': 'school.res.sh',
         'proxy': '106.75.134.191:18888:ipin:ipin1234', 'kldms': ['5', '1'], 'school': True, 'sch.parser': True,
         'spec.parser': False, 'spec': True, 'detail': True, 'name': u'上海', 'ua': ua[5], 'detail.recover': False,
         'detail.parser': False, 'job_tag': '.1', 'thcnt': 4, 'detail.seeds': 'detail.seeds.sh', 'score': 600,
         'bkccs': ['1', '2']},
        {'username': 'none098', 'password': 'AHO001009', 'prefix': 'sx', 'sleep': 1.0, 'sch.seeds': 'school.res.sx',
         'proxy': None, 'kldms': ['5', '1'], 'school': True, 'sch.parser': True,
         'spec.parser': True, 'spec': True, 'detail': False, 'name': u'山西', 'ua': ua[4], 'detail.recover': False,
         'detail.parser': False, 'job_tag': '.1', 'thcnt': 4, 'detail.seeds': 'detail.seeds.sx', 'score': 750,
         'bkccs': ['1', '2']},
        {'username': 'hubei102', 'password': 'bobo2016', 'prefix': 'hb', 'sleep': 0.95, 'sch.seeds': 'school.res.hb',
         'proxy': None, 'kldms': ['5', '1'], 'school': False, 'spec': False, 'detail': True, 'name': u'湖北', 'ua': ua[3],
         'detail.recover': True, 'job_tag': '.1', 'thcnt': 4, 'detail.seeds': 'detail.seeds.hb', 'score': 750,
         'detail.parser': False, 'bkccs': ['1', '2']}
    ]
    run_jobs(accounts[2])
