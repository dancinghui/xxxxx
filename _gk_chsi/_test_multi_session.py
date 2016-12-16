#!/usr/bin/env python
# -*- coding:utf8 -*-
import logging
import re
import threading

import time

from accounts import AccountManager, provinces, ChsiSession, print_con
from court.cspider import ATOSSessionRequests

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





def test_login(session):
    session.login()


def test_muti_session():
    accounts = {'u': 'huoguo', 'p': 'AHO001009'}
    session = ChsiSession(accounts['u'], accounts['p'])
    session2 = ChsiSession(accounts['u'], accounts['p'])
    session.set_proxy('106.75.134.191:18888:ipin:ipin1234')
    session2.set_proxy('101.200.179.38:3128')
    session.select_user_agent(ua[3])
    session2.select_user_agent(ua[5])
    session.login()
    con = session.request_url('http://gk.chsi.com.cn/recruit/')
    print_con(con)
    print con.cookies
    session2.login()
    time.sleep(1)
    con = session.request_url('http://gk.chsi.com.cn/recruit/')
    con2 = session2.request_url('http://gk.chsi.com.cn/recruit/')
    print  'content 1'
    print_con(con)
    print con.cookies
    print  'content 2'
    print_con(con2)
    print con2.cookies
    print 'session 2 change ip to same as session 1'
    session2.set_proxy('106.75.134.191:18888:ipin:ipin1234')
    print 'do not login after change ip'
    time.sleep(1)
    con2 = session2.request_url('http://gk.chsi.com.cn/recruit/')
    print_con(con2)
    print con2.cookies
    session.logout()
    session2.logout()

def check_multi_accounts():
    accounts = {'u': 'mint123', 'p': 'AHO001009'}
    accounts2 = {'u': 'pinkpink', 'p': 'AHO001009'}
    session = ChsiSession(accounts['u'], accounts['p'])
    session2 = ChsiSession(accounts2['u'], accounts2['p'])

    session.set_proxy('106.75.134.189:18888:ipin:ipin1234')
    session2.set_proxy('106.75.134.189:18888:ipin:ipin1234')

    session.login()
    con = session.request_url('http://gk.chsi.com.cn/recruit/')
    print_con(con)
    print con.cookies
    session2.login()
    con = session.request_url('http://gk.chsi.com.cn/recruit/')
    con2 = session2.request_url('http://gk.chsi.com.cn/recruit/')
    print  'content 1'
    print_con(con)
    print con.cookies
    print  'content 2'
    print_con(con2)
    print con2.cookies
    session.logout()
    session2.logout()


allac = [
    # {'username': 'jsu2015', 'password': 'AHO001009', 'prefix': 'jsu', 'proxy': '183.239.167.122:8080', 'maxscore': 480},
    # {'username': 'akg999', 'password': 'AHO001009', 'prefix': 'shh', 'proxy': '203.195.160.14:8080', 'maxscore': 750},
    # {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'doing222', 'password': 'AHO001009', 'prefix': 'tj', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'none098', 'password': 'AHO001009', 'prefix': 'sx.ty', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'tsingtao2015', 'password': 'AHO001009', 'prefix': 'sd', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'star0945', 'password': 'AHO001009', 'prefix': 'nm', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'mint123', 'password': 'AHO001009', 'prefix': 'ln', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'pinkpink', 'password': 'AHO001009', 'prefix': 'jl', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'hero001', 'password': 'AHO001009', 'prefix': 'henan', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'canton2015', 'password': 'AHO001009', 'prefix': 'gd', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'homo123', 'password': 'AHO001009', 'prefix': 'bj', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'hefei111', 'password': 'AHO001009', 'prefix': 'ah', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'aho120709', 'password': 'ipin2015', 'prefix': 'nx', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 750},
    # {'username': 'coconut007', 'password': 'AHO001009', 'prefix': 'hain', 'proxy': '106.75.134.189:18888:ipin:ipin1234',
    #  'maxscore': 900},
    # {'username': 'ln2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2026cxs'},
    # {'username': 'ln2016e1', 'proxy': '106.75.134.190:18888:ipin:ipin1234', 'password': 'shi2026cxs'},
    # {'username': 'ln2016e2', 'proxy': '106.75.134.191:18888:ipin:ipin1234', 'password': 'shi2026cxs'},
    # {'username': 'ln2016e3', 'proxy': '106.75.134.192:18888:ipin:ipin1234', 'password': 'shi2026cxs'},
    # {'username': 'gs2016e0', 'proxy': '101.226.249.237:80', 'password': 'shi2016cxs'},
    # {'username': 'gs2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gs2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gs2016e4', 'proxy': '101.226.249.237:80', 'password': 'shi2016cxs'},
    # {'username': 'gs2016e5', 'proxy': '101.226.249.237:80', 'password': 'shi2016cxs'},
    # {'username': 'gs2016e6', 'proxy': '101.226.249.237:80', 'password': 'shi2016cxs'},
    # {'username': 'gs2016e7', 'proxy': '101.226.249.237:80', 'password': 'shi2016cxs'},

    # {'username': 'xj2016e0', 'proxy': '101.226.249.237:80', 'password': 'shi2016cxs'},
    # {'username': 'xj2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'xj2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'xj2016e4', 'proxy': '101.226.249.237:80', 'password': 'shi2016cxs'},
    # {'username': 'xj2016e5', 'proxy': '101.226.249.237:80', 'password': 'shi2016cxs'},
    # {'username': 'xj2016e6', 'proxy': '101.226.249.237:80', 'password': 'shi2016cxs'},
    # {'username': 'xj2016e7', 'proxy': '101.226.249.237:80', 'password': 'shi2016cxs'},
    # {'username': 'yn2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'yn2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'yn2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'yn2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gd2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gd2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gd2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gd2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gd2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gd2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gd2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gd2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxty2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxty2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxty2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxty2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxty2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxty2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxty2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxty2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},

    # {'username': 'tj2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'tj2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'tj2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'tj2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'tj2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'tj2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'tj2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'tj2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},

    # {'username': 'yn2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'yn2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'yn2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'yn2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'yn2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'yn2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'yn2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'yn2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},

    # {'username': 'qh2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gx2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gx2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gx2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gx2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gx2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gx2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gx2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gx2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},

    # {'username': 'jl2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'jl2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'jl2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'jl2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'jl2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'jl2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'jl2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'jl2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},

    # {'username': 'hainan2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hainan2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hainan2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hainan2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hainan2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hainan2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hainan2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hainan2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},

    # {'username': 'nx2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nx2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nx2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nx2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nx2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nx2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nx2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nx2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    #
    # {'username': 'sd2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sd2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sd2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sd2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sd2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sd2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sd2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sd2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},

    # {'username': 'ah2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ah2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ah2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ah2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ah2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ah2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ah2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ah2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    #
    # {'username': 'gz2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gz2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gz2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gz2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gz2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gz2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gz2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'gz2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},

    # {'username': 'sxxa2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxxa2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxxa2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxxa2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxxa2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxxa2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxxa2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'sxxa2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    #
    # {'username': 'js2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # #
    # {'username': 'nm2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nm2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nm2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nm2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nm2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nm2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nm2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'nm2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    #
    # {'username': 'hlj2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hlj2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hlj2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hlj2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hlj2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hlj2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hlj2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'hlj2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    #
    # {'username': 'henan2016e0', 'proxy': '108.59.10.138:55555', 'password': 'shi2016cxs'},
    # {'username': 'henan2016e1', 'proxy': '108.59.10.138:55555', 'password': 'shi2016cxs'},
    # {'username': 'henan2016e2', 'proxy': '108.59.10.138:55555', 'password': 'shi2016cxs'},
    # {'username': 'henan2016e3', 'proxy': '108.59.10.138:55555', 'password': 'shi2016cxs'},
    # {'username': 'henan2016e4', 'proxy': '108.59.10.138:55555', 'password': 'shi2016cxs'},
    # {'username': 'henan2016e5', 'proxy': '108.59.10.138:55555', 'password': 'shi2016cxs'},
    # {'username': 'henan2016e6', 'proxy': '108.59.10.138:55555', 'password': 'shi2016cxs'},
    # {'username': 'henan2016e7', 'proxy': '108.59.10.138:55555', 'password': 'shi2016cxs'},
    # {'username': 'hunan2016e0', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hunan2016e1', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hunan2016e2', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hunan2016e3', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hunan2016e4', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hunan2016e5', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hunan2016e6', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hunan2016e7', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hebei2016e0', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hebei2016e1', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hebei2016e2', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hebei2016e3', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hebei2016e4', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hebei2016e5', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hebei2016e6', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'hebei2016e7', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'cq2016e1', 'proxy': '106.75.134.190:18888:ipin:ipin1234', 'password': 'shi2026cxs'},
    # {'username': 'cq2016e2', 'proxy': '106.75.134.191:18888:ipin:ipin1234', 'password': 'shi2026cxs'},
    # {'username': 'cq2016e3', 'proxy': '106.75.134.192:18888:ipin:ipin1234', 'password': 'shi2026cxs'},
    # {'username': 'ln2016e4', 'proxy': '106.75.134.192:18888:ipin:ipin1234', 'password': 'shi2026cxs'},
    # {'username': 'cq2016e4', 'proxy': '106.75.134.193:18888:ipin:ipin1234', 'password': 'shi2026cxs'},
    # {'username': 'ln2016e4', 'proxy': '101.200.179.38:3128', 'password': 'shi2026cxs'},
    # {'username': 'sh2016e0', 'proxy': '101.226.249.237:80', 'password': 'shi2026cxs'},
    # {'username': 'sh2016e1', 'proxy': None, 'password': 'shi2026cxs'},
    # {'username': 'sh2016e2', 'proxy': '101.200.178.46:3128', 'password': 'shi2026cxs'}
    # {'username': 'nm2016e0', 'proxy': None, 'password': 'shi2016cxs'}
    # {'username': 'js2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'js2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    #
    # {'username': 'qh2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'qh2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    #
    # {'username': 'ln2016e0', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ln2016e1', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ln2016e2', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ln2016e3', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ln2016e4', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ln2016e5', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ln2016e6', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},
    # {'username': 'ln2016e7', 'proxy': '106.75.134.189:18888:ipin:ipin1234', 'password': 'shi2016cxs'},

    # {'username': 'tj2016e0', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'tj2016e1', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'tj2016e2', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'tj2016e3', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'tj2016e4', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'tj2016e5', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'tj2016e6', 'proxy': None, 'password': 'shi2016cxs'},
    # {'username': 'tj2016e7', 'proxy': None, 'password': 'shi2016cxs'},
]


def check_and_save(out):
    am = AccountManager()
    for name in provinces.keys():
        for a in am.get_all(name):
            a.remain_time = check_time(a.username, a.password)


if __name__ == '__main__':
    # check_time('sichuan101', 'bobo2016')
    # check_time('sichuan102', 'bobo2016')
    # check_time('huoguo', 'AHO001009')
    am = AccountManager()
    proxy = '106.75.134.192:18888:ipin:ipin1234'
    acs = am.get_all('新疆')
    for a in acs:
        check_time(a.username, a.password, proxy)
    for a in allac:
        check_time(a['username'], a['password'], proxy)
        # check_multi_accounts()
        # check_time('sh2016e0', 'shi2026cxs')
