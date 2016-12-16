#!/usr/bin/env python
# -*- coding:utf8 -*-
import os
print os.getcwd()

def load_proxy(proxy_file):

    proxies = []
    with open(proxy_file, 'rb') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            proxies.append(line)

    return proxies


PROXIES = load_proxy(os.path.join(os.path.dirname(__file__), 'proxy'))