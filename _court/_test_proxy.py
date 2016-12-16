#!/usr/bin/env python
# -*- coding:utf8 -*-
from court.util import ProxyUtils, FileUtils
from spider.httpreq import BasicRequests

if __name__ == '__main__':
    proxies = ProxyUtils.load_proxy('/home/skiloop/PycharmProjects/getjd/spider/proxy/proxy.txt')
    filters = ProxyUtils.filter_with_speed(proxies)
    FileUtils.save_all('nproxy', filters)
