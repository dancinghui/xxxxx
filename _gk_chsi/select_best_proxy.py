#!/usr/bin/env python
# -*- coding:utf8 -*-
import time

from spider import spider
from spider.httpreq import BasicRequests


def test_proxy(proxy, url, count=10):
    c = count
    rq = BasicRequests()
    rq.set_proxy(proxy['p'])
    total = 0
    success = 0
    while c > 0:
        try:
            s = time.time()
            con = rq.request_url(url)
            t = time.time() - s
        except:
            con = None
            t = 0
            pass
        c -= 1
        if con:
            success += 1
            total += t
    if success > 0:
        proxy['v'] = total / success


if __name__ == "__main__":
    proxies = []
    with open('proxy', 'r') as f:
        for l in f:
            proxy = {'p': l.strip(), 'v': 100000000}
            proxies.append(proxy)

    proxies = spider.util.unique_list(proxies)
    print  'load ', len(proxies), 'proxies'
    for p in proxies:
        test_proxy(p, 'http://gk.chsi.com.cn/user/loginNeeded.jsp', 3)
    for i in range(0, len(proxies)):
        for j in range(i + 1, len(proxies)):
            if proxies[i]['v'] > proxies[j]['v']:
                p = proxies[i]
                proxies[i] = proxies[j]
                proxies[j] = p
    with open('proxy_check', 'w') as f:
        for p in proxies:
            f.write(p['p'] + ',' + str(p['v']) + '\n')
