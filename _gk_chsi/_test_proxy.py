#!/usr/bin/env python
# -*- coding:utf8 -*-
import re

from accounts import ProxyManager
from court.util import ProxyUtils
from spider.httpreq import BasicRequests


def test_proxy(proxies, url='http://gk.chsi.com.cn', t=5):
    res = {}
    for proxy in proxies:
        res[proxy] = ProxyUtils.test_proxy_speed(url, proxy, t)
    return res


def try_proxy(proxy, url='http://gaokao.chsi.com.cn', tag=u'阳光高考'):
    req = BasicRequests()
    req.set_proxy(proxy, 0, False)
    # con = req.request_url('http://gk.chsi.com.cn/recruit/listSpecBySchool.do?yxdm=11055&start=0 ')
    con = req.request_url(url, timeout=5)
    if con:
        m = re.search(r'<title>[^<]*<\/title>', con.text)
        if m:
            print m.group()
        return re.search(tag, con.text)


def post_for_proxy():
    req = BasicRequests()
    con = req.request_url(
        'http://dev.kuaidaili.com/api/getproxy/?orderid=925817981728018&num=50&b_pcchrome=1&b_pcie=1&b_pcff=1&protocol=1&method=2&an_an=1&an_ha=1&sp1=1&quality=1&sort=1&format=json&sep=1')
    if con:
        return eval(con.text)


def find_proxy():
    res = {}
    rws = []
    c = 5
    while c > 0:
        proxies = post_for_proxy()
        if proxies is None:
            continue
        c -= 1
        ps = []
        for p in proxies['data']['proxy_list']:
            if p not in rws:
                ps.append(p)
        r = test_proxy(ps)
        for p, v in r.items():
            if v > 5:
                res[p] = v
    with open('res.proxy.dat', 'w') as f:
        for p, v in res.items():
            f.write('%s,%s\n' % (p, v))


def test_valid():
    plist = []
    with open('p.dat', 'r') as f:
        for l in f:
            plist.append(l.strip())
    vlist = []
    for p in plist:
        if try_proxy(p):
            vlist.append(p)
    with open('v.dat', 'w') as f:
        for p in vlist:
            f.write('%s\n' % p)


if __name__ == '__main__':
    # pm=ProxyManager()
    # find_proxy()
    # test()
    pass
    test_valid()
    # try_proxy('43.245.192.50:8080')
    # try_proxy('117.184.117.229:3128')
    # try_proxy('120.52.73.32:8081')
    # try_proxy('106.75.134.193:18888:ipin:ipin1234')
