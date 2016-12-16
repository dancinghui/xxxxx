#!/usr/bin/env python
# -*- coding:utf8 -*-


import qdata
import random
import re
from requests import sessions

class Config(object):
    COUNT = 300


class CV58TestCaseGet(object):
    def __init__(self):
        self.count = 0
        self.sess = sessions.Session()


    def get_cases(self):
        with open('idx', 'wb') as f:
            while self.count < Config.COUNT:
                i = self.get_one()
                if i:
                    f.write('%s\n' % i)
                    self.count += 1
                    print "SUCESS %s, Count %d" % (i, self.count)
                else:
                    print "FAIL: %s" % i


    def get_one(self):
        i = random.randint(0, len(qdata.urls)-1)
        url = qdata.urls[i]
        ind = qdata.inds[random.randint(0, len(qdata.inds) - 1)]
        page = random.randint(0,200)

        realUrl = "{}qz{}/pn{}".format(url, ind, page)

        return self.parse_html(realUrl)


    def parse_html(self, url):
        res = self.sess.get(url)
        els = re.findall(r'resume/(\d+)', res.text)
        els = set(els)

        if not els:
            return False

        els = list(els)
        return els[random.randint(0, len(els)-1)]


if __name__ == '__main__':
    ts = CV58TestCaseGet()
    ts.get_cases()