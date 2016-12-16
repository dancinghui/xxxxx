#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import threading
import unittest

import time
import random

from court.sessionrequests import ETOSSessionRequests
from spider.httpreq import SessionRequests

accounts = [['ln2016e6', 'shi2016cxs'], ['ln2016e1', 'shi2016cxs'], ['ln2016e2', 'shi2016cxs'],
            ['ln2016e3', 'shi2016cxs'], ['ln2016e5', 'shi2016cxs'], ['ln2016e4', 'shi2016cxs'],
            ['sc2016e0', 'shi2016cxs'],
            ['sc2016e1', 'shi2016cxs'], ['sc2016e2', 'shi2016cxs'],
            ['sc2016e3', 'shi2016cxs'], ['sc2016e4', 'shi2016cxs'], ['sc2016e5', 'shi2016cxs'], ]
__lock = threading.RLock()


def __print(account, tid, message, *args):
    with __lock:
        print account, tid, message, args[:]


def _session_test(req, tid):
    print 'thread %d starts' % tid
    cookie = None
    con = req.request_url('http://gk.chsi.com.cn/login.do',
                          data={'j_username': accounts[tid][0], 'j_password': accounts[tid][1]})
    if con:
        cookie = req.get_cookie('JSESSIONID')
        __print(accounts[tid][0], tid, con.cookies)
        __print(accounts[tid][0], tid, cookie)

    con = req.request_url('http://gk.chsi.com.cn/index.do')
    time.sleep(random.randint(1, 5))
    if con:
        c = req.get_cookie('JSESSIONID')
        assert c is None or c == cookie
        __print(accounts[tid][0], tid, con.cookies)
        __print(accounts[tid][0], tid, c)
        m = re.search(ur'<td align="right">.*? 剩余：</td><td align="left">\d+分钟</td></tr>', con.text)
        assert m is not None
        __print(accounts[tid][0], tid, m.group())

    con = req.request_url('http://gk.chsi.com.cn/user/logout.do', data={})
    if con:
        c = req.get_cookie('JSESSIONID')
        assert c is None or c == cookie
        __print(accounts[tid][0], tid, con.cookies)
        __print(accounts[tid][0], tid, c)


class ETOSSessionRequestsTest(unittest.TestCase):
    @staticmethod
    def test_atos_session():
        cnt = 10
        random.seed = int(time.time())
        threads = []
        req = ETOSSessionRequests()
        for i in range(0, cnt):
            t = threading.Thread(target=_session_test, args=(req, i))
            threads.append(t)
        for t in threads:
            t.start()

        time.sleep(5)
        for t in threads:
            t.join()

    @staticmethod
    def test_session():
        cnt = 10
        random.seed = int(time.time())
        threads = []
        req = SessionRequests()
        for i in range(0, cnt):
            t = threading.Thread(target=_session_test, args=(req, i))
            threads.append(t)
        for t in threads:
            t.start()

        time.sleep(5)
        for t in threads:
            t.join()


if __name__ == '__main__':
    unittest.main()
