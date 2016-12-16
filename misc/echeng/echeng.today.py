#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
import time

from savebin import BinSaver

from spider import Spider


class EchengTodaySpider(Spider):
    def dispatch(self):
        self.bs = BinSaver("echeng.today.bin")
        self.max_no = 0
        self.add_main_job(1)
        idx = 1
        while self.max_no == 0:
            time.sleep(1)
        while idx <= self.max_no:
            idx += 1
            self.add_main_job(idx)
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):
        print "job is ", jobid
        if isinstance(jobid, int):
            url = "http://www.cheng95.com/positions/search?published_id=1&page=%d" % jobid
            print url
            res = self.request_url(url, [])
            if jobid == 1:
                rm = re.search(ur'pageConfig.*?totalpage\s*:\s*(\d+)', res.text)
                self.max_no = int(rm.group(1))
            rr = re.findall(ur"""position-item data-id="(\d+)""", res.text)
            for no in rr:
                a = {'type':'detail', 'id':int(no)}
                self.add_job(a)
        if isinstance(jobid, dict) and jobid.get('type', None) == 'detail':
            jdid = jobid.get('id', 0)
            if jdid != 0:
                url = "http://www.cheng95.com/positions/detail?id=%d" % jdid
                res = self.request_url(url, [])
                print "saveing echeng.%d" % jdid
                self.bs.append("echeng.%d" % jdid, res.text)

if __name__ == "__main__":
    s = EchengTodaySpider(20)
    s.run()
