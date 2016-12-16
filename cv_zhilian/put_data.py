#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import Bin2DB
import cv_zhilian
import re
import sys


class DisPageStore(cv_zhilian.CVZLPageStore):
    def save_time_log(self, indexUrl, cur_tm):
        return

    def do_save(self, odoc, content, fnpath=None, offset=None):
        odoc.update({'pageContentPath': "binf::%s::%d" % (fnpath, offset)})
        return self.upsert_doc(odoc['indexUrl'], odoc)


class CVBin2DB(Bin2DB):
    def __init__(self):
        Bin2DB.__init__(self)
        self.pagestore = DisPageStore()

    def parse_name(self, n):
        m = re.match(r'cv_zhilian\.([a-zA-Z0-9]+)\.(\d+)', n)
        if m:
            return m.group(2), m.group(1)
        return None, None

    def get_pagestore(self):
        return self.pagestore

    def get_url(self, jdid):
        return "http://rd.zhaopin.com/resumepreview/resume/viewone/1/%s_1_1" % jdid


if __name__ == "__main__":
    sb = CVBin2DB()
    for fn in sys.argv[1:]:
        sb.save(fn)
