#!/usr/bin/env python
# -*- coding:utf8 -*-

from run_sichuan import run_jobs

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
        {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
         'proxy': '106.75.134.191:18888:ipin:ipin1234', 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
         'spec.parser': True, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[2], 'detail.recover': True,
         'detail.parser': True, 'job_tag': '.1', 'thcnt': 4,
         'bkccs': ['1', '2']},
        {'username': 'hubei101', 'password': 'bobo2016', 'prefix': 'hb', 'sleep': 1.0, 'sch.seeds': 'school.res.hb',
         'proxy': None, 'kldms': ['5', '1'], 'school': False, 'spec': False,
         'detail': True, 'name': u'湖北', 'ua': ua[3],
         'detail.recover': False, 'job_tag': '.2', 'thcnt': 4,
         'detail.parser': False, 'bkccs': ['1', '2']}
    ]
    run_jobs(accounts[1], 's.2')
