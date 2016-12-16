#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import Bin2DB
from page_store import PageStoreLP
import re
import sys


class LPBin2DB(Bin2DB):
    def __init__(self):
        Bin2DB.__init__(self)
        self.pagestore = PageStoreLP()

    def parse_name(self, n):
        # jd_liepin.1571236.1453208396
        # returns (get_time, jd_id)
        m = re.match(r'jd_liepin\.(\d+)\.(\d+)', n)
        if m:
            return m.group(2), m.group(1)
        return None, None

    def get_pagestore(self):
        return self.pagestore

    def get_url(self, jdid):
        jdid = int(jdid)
        url = "http://job.liepin.com/%03d_%07d/" % (jdid/10000, jdid)
        return url


if __name__ == "__main__":
    sb = LPBin2DB()
    for fn in sys.argv[1:]:
        sb.save(fn)
