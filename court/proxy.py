#!/usr/bin/env python
# -*- coding:utf8 -*-
import os
import time

from court.util import FileUtils
from spider.httpreq import BasicRequests


class ProxyUtils():
    """utils for proxy"""

    @staticmethod
    def filter_with_speed(proxies, url='http://www.baidu.com', timeout=10):
        results = []
        req = BasicRequests()
        for proxy in proxies:
            req.set_proxy(proxy, len(req.sp_proxies), False)
            try:
                con = req.request_url(url, timeout=timeout)
            except Exception:
                con = None
            if con:
                results.append(proxy)
        return results

    @staticmethod
    def load_proxy(fname):
        proxies = []
        raw_proxies = FileUtils.read_all(fname)
        for proxy in raw_proxies:
            proxies.append(proxy.strip())
        return proxies

    @staticmethod
    def test_proxy_speed(url, proxy, t=60):
        req = BasicRequests()
        req.set_proxy(proxy, 0, False)
        s = time.time()
        count = 0
        while time.time() - s <= t:
            try:
                req.request_url(url, timeout=5)
                count += 1
            except Exception:
                pass
        return count


class KuaidailiProxyManager():
    @staticmethod
    def load_proxy(count):
        req = BasicRequests()
        con = req.request_url(
            'http://dev.kuaidaili.com/api/getproxy/?orderid=925817981728018&num=%s' % count + \
            '&b_pcchrome=1&b_pcie=1&b_pcff=1&protocol=1&method=2&an_an=1&an_ha=1&sp1=1&quality=1&sort=1&format=json&sep=1')
        return eval(con.text)


def redial_local_proxy():
    os.system("sshpass -p 'helloipin' ssh ipin@192.168.1.39 /home/ipin/bin/redial")
