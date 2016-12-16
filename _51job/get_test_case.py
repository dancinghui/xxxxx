#!/usr/bin/env python
# -*- coding:utf8 -*-

import random
import requests
import re
import time
from lxml import html

class Config(object):
    ID_MIN = 71000000
    ID_MAX = 80000000
    TOTAL_IDS = 200
    MS_3_MONTHS = 7948800

    TEMPLATE_URL = "http://jobs.51job.com/all/{}.html?s=0"


class JD51JobTCase(object):
    def __init__(self):

        self.count = 0

    def get_one(self):
        i = random.randint(Config.ID_MIN, Config.ID_MAX)
        # i = 74630129
        url = Config.TEMPLATE_URL.format(i)
        return self.real_get_one(url, i)

    def real_get_one(self, url, i):
        res = requests.get(url)
        res.encoding = 'gb2312'
        hdoc = html.fromstring(res.text)
        pubT = hdoc.xpath("//div[@class='jtag inbox']/div[@class='t1']/span[last()]")

        now = time.time()
        if pubT:
            find = re.search(r'(\d+)-(\d+)', pubT[0].text_content())
            if find:
                s = list(time.gmtime(now))
                s[1] = int(find.group(1))
                s[2] = int(find.group(2))

                tstamp = time.mktime(s)
                if now - tstamp <= Config.MS_3_MONTHS:
                    return i

            find = re.search(r'(\d+)-(\d+)-(\d+)', pubT[0].text_content())
            if find:
                s = list(time.gmtime(now))

                s[0] = int(find.group(1))
                s[1] = int(find.group(2))
                s[2] = int(find.group(3))

                tstamp = time.mktime(s)
                if now - tstamp <= Config.MS_3_MONTHS:
                    return i

        return None


    def get_cases(self):
        with open("idx", 'wb') as f:
            while self.count < Config.TOTAL_IDS:
                i = self.get_one()
                if i:
                    f.write('%d\n' % i)
                    self.count += 1

                    print "total count:", self.count
                else:
                    print "fail id: ", i


if __name__ == '__main__':
    t = JD51JobTCase()
    t.get_cases()




import os
import sys
os.path.isdir





