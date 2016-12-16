#!/usr/bin/env python
# -*- coding:utf8 -*-

import requests

if __name__ == '__main__':
    res = requests.get('http://127.0.0.1:9527/cvDownload?channel=cv_51job&cvId=339585093')
    print res