#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import Bin2DB
import page_store
import re
import sys


class DisJDLPPageStore(page_store.PageStoreLP):
    def save_time_log(self, indexUrl, cur_tm):
        return

    def do_save(self, odoc, content, fnpath=None, offset=None):
        odoc.update({'pageContentPath': "binf::%s::%d" % (fnpath, offset)})
        return self.upsert_doc(odoc['indexUrl'], odoc)


class JDLPBin2DB(Bin2DB):
    def __init__(self):
        Bin2DB.__init__(self)
        self.pagestore = DisJDLPPageStore()

    def parse_name(self, n):
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
    sb = JDLPBin2DB()
    for fn in sys.argv[1:]:
        sb.save(fn)
