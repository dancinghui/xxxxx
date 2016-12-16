#!/usr/bin/env python
# -*- coding:utf8 -*-
# !/usr/bin/env python
# -*- coding:utf8 -*-
from _run_2 import run_fun, run_fun2
from accounts import AccountManager, provinces
from runner import run_full_jobs, gen_jobs_params, FullJobRunner, JobManager, smart_full_job

if __name__ == '__main__':
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
    #
    # jobs = [
    #     {
    #         'accounts': [
    #             {'username': 'ln2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2026cxs',
    #              'ua': ua[2]},
    #             {'username': 'ln2016e1', 'proxy': '106.75.134.190:18888:ipin:ipin1234', 'password': 'shi2026cxs',
    #              'ua': ua[3]},
    #             {'username': 'ln2016e2', 'proxy': '106.75.134.191:18888:ipin:ipin1234', 'password': 'shi2026cxs',
    #              'ua': ua[4]},
    #             {'username': 'ln2016e3', 'proxy': '106.75.134.192:18888:ipin:ipin1234', 'password': 'shi2026cxs',
    #              'ua': ua[5]},
    #             {'username': 'ln2016e4', 'proxy': '101.200.179.38:3128', 'password': 'shi2026cxs',
    #              'ua': ua[6]},
    #         ],
    #         'prefix': 'ln', 'sleep': 1.0,
    #         'sch.seeds': 'school.res.ln',
    #         'kldms': ['5', '1'], 'school': True, 'sch.parser': True, 'spec.seeds': 'spec.seeds.ln',
    #         'spec.parser': True, 'spec': True, 'detail': True, 'name': u'辽宁', 'detail.recover': True,
    #         'spec.recover': True, 'sch.recover': True, 'score': 750,
    #         'detail.parser': True, 'detail.seeds': 'detail.seeds.ln', 'thcnt': 4,
    #         'bkccs': ['1', '2']},
    #     {
    #         'accounts': [
    #             {'username': 'sh2016e0', 'proxy': '101.226.249.237:80', 'password': 'shi2026cxs',
    #              'ua': ua[0]},
    #             {'username': 'sh2016e1', 'proxy': None, 'password': 'shi2026cxs',
    #              'ua': ua[1]},
    #             {'username': 'sh2016e2', 'proxy': '101.200.178.46:3128', 'password': 'shi2026cxs',
    #              'ua': ua[7]},
    #         ],
    #         'prefix': 'sh', 'sleep': 1.0,
    #         'sch.seeds': 'school.res.ln',
    #         'kldms': ['5', '1'], 'school': True, 'sch.parser': True, 'spec.seeds': 'spec.seeds.ln',
    #         'spec.parser': True, 'spec': True, 'detail': True, 'name': u'上海', 'detail.recover': True,
    #         'spec.recover': True, 'sch.recover': True, 'score': 750,
    #         'detail.parser': True, 'detail.seeds': 'detail.seeds.ln', 'thcnt': 4,
    #         'bkccs': ['1', '2']},
    # ]
    # jobs = [
    #     {
    #         'accounts': [
    #             {'username': 'ln2016e0', 'proxy': None, 'password': 'shi2026cxs', 'ua': ua[2]},
    #         ],
    #         'prefix': 'ln', 'sleep': 1.0, 'school': False, 'sch.parser': False,
    #         'spec.parser': True, 'spec': True, 'detail': True, 'name': u'辽宁', 'detail.recover': True,
    #         'spec.recover': True, 'sch.recover': True, 'score': 750,
    #         'detail.parser': True, 'thcnt': 4}
    #
    # ]
    # jobs = [
    #     {
    #         'accounts': [
    #             {'username': 'doing222', 'proxy': '101.200.178.46:3128', 'password': 'AHO001009', 'ua': ua[2]},
    #         ],
    #         'prefix': 'tj', 'sleep': 1.0, 'school': False, 'sch.parser': True, 'kldms': ['5', '1'], 'bkccs': ['2', '1'],
    #         'spec.parser': True, 'spec': True, 'detail': False, 'name': 'tianjin', 'detail.recover': True,
    #         'spec.recover': True, 'sch.recover': False, 'score': 750,
    #         'detail.parser': False, 'thcnt': 4}
    #
    # ]
    # proxies = []
    # am = AccountManager()
    # with open('proxy_r') as f:
    #     for l in f:
    #         proxies.append(l.strip())
    # proxies.append(None)
    # idx = [5, 6, 7]
    # count = len(idx)
    # name = '宁夏'
    # ac = {
    #     'accounts': []
    #     , 'name': name
    #     , 'prefix': provinces[name]
    # }
    # acs = am.get(name, count)
    # i = 0
    # for a in acs:
    #     a.proxy = proxies[idx[i]]
    #     ac['accounts'].append(a.gen_run_param())
    #     i += 1
    # run_fun2(ac)

    am = AccountManager()
    # with open('proxy_r') as f:
    #     for l in f:
    #         proxies.append(l.strip())
    # idx = [28]
    # count = len(idx)
    name = '宁夏'

    acsa = am.get(name, 8)
    acs = []
    for a in acsa:
        acs.insert(0, a)
    for a in acs:
        a.proxy = '192.168.1.39:3428'
        runner = FullJobRunner(
            gen_jobs_params([a.gen_run_param()], name, provinces[name], spec=False, detail=True, school=False,
                            spec_parser=False, detail_parser=False,
                            sch_parser=False))
        runner.run()
