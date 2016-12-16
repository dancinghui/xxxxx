#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
import time
import re
import liepin_cv
import json
import spider.util


def main():
    text = os.popen("tail -n 16 screenlog.xg.cron.liepin.cv.py.log").read()
    m = re.search(r'enable <(key\.[0-9a-f\-]+)>', text)
    if m:
        key = m.group(1)
        print key
    else:
        return
    m = re.search(r'(http://www.liepin.com/validation/captcha.*)', text)
    if m:
        url = m.group(1).strip()
        print key, url
        a = liepin_cv.LPRequest(liepin_cv.Cdata.accounts[0])
        a.do_login()
        if a.validate_user(url):
            spider.util.HashChecker().add(key)


if __name__ == '__main__':
    while True:
        main()
        print 'sleeping 60 secs'
        time.sleep(60)
