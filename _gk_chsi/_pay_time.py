#!/usr/bin/env python
# -*- coding:utf8 -*-
# !/usr/bin/env python
# -*- coding:utf8 -*-
from accounts import AccountManager, Accounts, ac_pay
from accounts import CardManager
from accounts import pay_time

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

    jobs = [
        {
            'accounts': [
                # {'username': 'nm2016e0', 'proxy': '106.75.134.190:18888:ipin:ipin1234', 'password': 'shi2026cxs',
                #  'card': {'account': 'IOFMSZBCY', 'password': '447760308'},
                #  'ua': ua[1]},
                # {'username': 'cq2016e2', 'proxy': '106.75.134.191:18888:ipin:ipin1234', 'password': 'shi2026cxs',
                #  'card': {'account': 'DTJWREXDJ', 'password': '639884120'},
                #  'ua': ua[3]},
                # {'username': 'cq2016e3', 'proxy': '106.75.134.192:18888:ipin:ipin1234', 'password': 'shi2026cxs',
                #  'card': {'account': 'FAWWWOAWH', 'password': '515471056'},
                #  'ua': ua[4]},
                # {'username': 'cq2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2026cxs',
                #  'card': {'account': 'YWFHOBEMP', 'password': '953526591'},
                #  'ua': ua[2]},
                # {'username': 'jl2016e2', 'proxy': '101.200.178.46:3128', 'password': 'shi2026cxs', 'ua': ua[5],                 'card': {'account': 'INWAWCRLX', 'password': '128213319'}},
                # {'username': 'bj2016e0', 'proxy': '106.75.134.190:18888:ipin:ipin1234', 'password': 'shi2026cxs',                 'ua': ua[5],
                #  'card': {'account': 'BREKRYRBH', 'password': '730773288'}},
                # {'username': 'jl2016e0', 'proxy': '106.75.134.191:18888:ipin:ipin1234', 'password': 'shi2026cxs',
                #  'ua': ua[5],
                #  'card': {'account': 'QODHQLZKX', 'password': '578996171'}},
                {'username': 'jl2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2026cxs',
                 'ua': ua[5],
                 'card': {'username': 'LERKALTCD', 'password': '843998054'}},

            ], 'prefix': 'cq'}

    ]

    # accounts = [
    #     {'username': 'sichuan102', 'password': 'bobo2016', 'prefix': 'sc', 'sleep': 1.0, 'sch.seeds': 'school.res.sc',
    #      'proxy': None, 'kldms': ['6', '2'], 'school': False, 'sch.parser': False,
    #      'spec.parser': False, 'spec': False, 'detail': True, 'name': u'四川', 'ua': ua[5], 'detail.recover': True,
    #      'detail.parser': False, 'detail.seeds': 'detail.seeds.sc.3', 'job_tag': '.3', 'thcnt': 4,
    #      'bkccs': ['1', '2']}
    # ]

    # for ac in jobs[0]['accounts']:
    #     print BaseGkChsiFsxSpider.pay_time(ac, jobs[0]['prefix'], ac['card'])
    #     print BaseGkChsiFsxSpider.get_remain_time(ac, jobs[0]['prefix'])


    cm = CardManager()
    ac = AccountManager()
    # pay_time('510', '广东', ac, cm, 7)
    # pay_time('510', '河南', ac, cm, 8)
    # pay_time('510', '山东', ac, cm, 6)
    # pay_time('310', '山东', ac, cm, 1)
    # pay_time('510', '安徽', ac, cm, 6)
    # pay_time('150', '安徽', ac, cm, 1)
    # pay_time('150', '江苏', ac, cm, 1)
    # pay_time('310', '江苏', ac, cm, 1)
    # pay_time('510', '江苏', ac, cm, 4)
    # pay_time('510', '湖南', ac, cm, 4)
    # pay_time('310', '湖南', ac, cm, 1)
    # pay_time('150', '湖南', ac, cm, 1)
    # pay_time('510', '河北', ac, cm, 5)
    # pay_time('510', '江西', ac, cm, 4)
    # pay_time('310', '江西', ac, cm, 1)
    # pay_time('510', '陕西', ac, cm, 3)
    # pay_time('310', '陕西', ac, cm, 1)
    #
    # pay_time('510', '山西', ac, cm, 3)
    # pay_time('310', '山西', ac, cm, 1)

    # pay_time('510', '贵州', ac, cm, 3)
    # pay_time('310', '贵州', ac, cm, 1)
    #
    # pay_time('510', '广西', ac, cm, 3)
    # pay_time('310', '广西', ac, cm, 1)

    # pay_time('310', '甘肃', ac, cm, 1)
    # pay_time('510', '甘肃', ac, cm, 3)

    # pay_time('150', '云南', ac, cm, 1)
    # pay_time('510', '云南', ac, cm, 3)


    # pay_time('510', '黑龙江', ac, cm, 3)
    #
    # pay_time('510', '内蒙古', ac, cm, 2)
    #
    # pay_time('510', '新疆', ac, cm, 2)
    # pay_time('310', '新疆', ac, cm, 1)

    # pay_time('510', '青海', ac, cm, 1)
    # pay_time('510', '海南', ac, cm, 1)
    # pay_time('510', '宁夏', ac, cm, 1)

    # ac_pay(ac, cm, '510', 'gs2016e5', '甘肃')


    # pay_time('510', '天津', ac, cm, 1)

    # ac_pay(ac, cm, '510', 'sxty2016e5', '山西')

    # ac_pay(ac, cm, '510', 'yn2016e5', '云南')

    # ac_pay(ac, cm, '310', 'nx2016e2', '宁夏')

    # ac_pay(ac, cm, '510', 'gz2016e4', '贵州')
    # ac_pay(ac, cm, '510', 'gz2016e5', '贵州')
    # ac_pay(ac, cm, '510', 'hainan2016e5', '海南')
    # ac_pay(ac, cm, '150', 'sxty2016e6', '山西')
    # ac_pay(ac, cm, '150', 'sxty2016e7', '山西')
    # ac_pay(ac, cm, '150', 'hunan2016e7', '湖南')
    # ac_pay(ac, cm, '150', 'sxxa2016e7', '陕西')

    # ac_pay(ac, cm, '310', 'gs2016e6', '甘肃')
    # ac_pay(ac, cm, '150', 'gs2016e6', '甘肃')
    # ac_pay(ac, cm, '150', 'qh2016e6', '青海')

    # ac_pay(ac, cm, '510', 'tj2016e6', '天津')
    # ac_pay(ac, cm, '150', 'sxty2016e5', '山西')
    # ac_pay(ac, cm, '150', 'gx2016e5', '广西')
    # ac_pay(ac, cm, '150', 'nm2016e5', '内蒙古')
    # ac_pay(ac, cm, '150', 'hebei2016e6', '河北')
    # ac_pay(ac, cm, '150', 'hebei2016e7', '河北')
    # ac_pay(ac, cm, '150', 'hebei2016e1', '河北')
    # pay_time('510', '福建', ac, cm, 1)
    # pay_time('510', '福建', ac, cm, 1)
    # pay_time('510', '福建', ac, cm, 1)
    # pay_time('310', '福建', ac, cm, 1)
    # pay_time('150', '福建', ac, cm, 1)
    pay_time('150', '福建', ac, cm, 2)
    cm.save()
    ac.save()
    pass
