#!/usr/bin/env python
# -*- coding:utf8 -*-
# !/usr/bin/env python
# -*- coding:utf8 -*-
from accounts import AccountManager
from runner import run_full_jobs, gen_jobs_params, FullJobRunner, JobManager

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
    # proxy1 = ['117.185.122.205:8080', '61.174.13.12:443', '219.65.88.139:80', '31.168.236.236:8080',
    #           '106.75.134.190:18888:ipin:ipin1234', '108.59.10.141:55555', '138.36.27.5:80', '185.7.3.244:8080']
    # proxy2 = ['106.75.134.189:18888:ipin:ipin1234', '42.118.216.220:8080','190.122.184.85:8080','']
    # proxy3 = ['183.111.169.204:8080', '54.153.72.59:8083']
    # proxy4 = ['222.176.112.10:80', '183.111.169.202:8080']
    # proxy5 = ['101.226.249.237:80', '42.118.216.219:8080']
    # proxy6 = ['183.111.169.203:8080', '210.245.25.228:8080']
    # proxy7 = ['106.75.134.191:18888:ipin:ipin1234', '183.111.169.205:8080']
    # proxy8 = ['112.23.1.167:8080', '120.25.214.90:80']
    #
    # am = AccountManager()
    # acs = am.get('广东', 8)

    # accounts = [
    #     {'username': 'sichuan102', 'password': 'bobo2016', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
    #      'proxy': None, 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
    #      'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[5], 'detail.recover': True,
    #      'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.3', 'job_tag': '.3', 'thcnt': 4,
    #      'bkccs': ['1', '2']}
    # ]
    # print FullJobRunner.fetch_remain_time(jobs[0])
    # run_full_jobs(accounts, u'北京', 'bj')
    jobs = [
        {'name': '广东', 'count': 8},
        {'name': '陕西', 'count': 4},
        {'name': '河南', 'count': 8},
        {'name': '山东', 'count': 7},
        {'name': '山西', 'count': 4},
        {'name': '江西', 'count': 5},
        {'name': '安徽', 'count': 7},
        {'name': '河北', 'count': 5},
        {'name': '江苏', 'count': 6},
        {'name': '湖南', 'count': 6},
    ]
    jm = JobManager(jobs)
    jm.random_run()
