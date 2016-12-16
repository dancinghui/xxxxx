#!/usr/bin/env python
# -*- coding:utf8 -*-

import sys
sys.path.append(sys.path[0]+"/../")
print sys.path

from spider.spider import Spider
from page_store import Jd58PageStore
from spider.httpreq import SpeedControlRequests
from qdata import urls, inds
from spider.runtime import Log
import spider
import time
import re

class Jd58Spider(Spider):
    def __init__(self, thread_cnt):
        super(Jd58Spider, self).__init__(thread_cnt)
        self.page_store = Jd58PageStore()
        self.speed_control_request = SpeedControlRequests()
        self.page_store.testmode = False
        self.get_latest = None


    def real_dispatch(self):
        for url in urls:
            for ind in inds:
                i = 1
                while 1:
                    realUrl = url + ind + '/pn{}/'.format(i)
                    if self.get_latest:
                        l_time = spider.util.TimeHandler.getTimeOfNDayBefore(self.get_latest) / 1000
                        l_time_local = time.localtime(l_time)
                        l_time_str = '%04d%02d%02d' % (l_time_local[0], l_time_local[1], l_time_local[2])

                        h_time_local = time.localtime(time.time())
                        h_time_str = '%04d%02d%02d' % (h_time_local[0], h_time_local[1], h_time_local[2])

                        realUrl += "?postdate={}_{}".format(l_time_str, h_time_str)

                    # self.add_main_job({"urlpart": realUrl,  "type":"loadPage"})
                    has_next = self.parse_html(realUrl)
                    if not has_next:
                        break
                    i += 1

    def parse_html(self, url):
        res = self.speed_control_request.with_sleep_requests(url, sleep=0.05)
        if not res:
            return True
        els = re.findall(r'entityId=(\d+)', res.text)

        if not els:
            return False

        part = url.split("pn")[0]
        for el in els:
            self.add_main_job({"urlpart": part, "jobid":el, "type":"jdPage"})

        if re.search(ur'新信息较少', res.text):
            return False

        return True

    def dispatch(self):
        self.real_dispatch()
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):
        if isinstance(jobid, dict):
            url = "{}{}x.shtml".format(jobid['urlpart'], jobid['jobid'])
            if not self.page_store.check_should_fetch(jobid['jobid']):
                return

            res = self.speed_control_request.with_sleep_requests(url, sleep=0.05)
            if res is not None:
                self.page_store.save(int(time.time()), jobid['jobid'], url, res.text)
            else:
                self.re_add_job(jobid)
                Log.error(("failed get url", url))

    def event_handler(self, evt, msg, **kwargs):
        if "START" == evt:
            spider.util.sendmail(["<jianghao@ipin.com>"], "58 jd爬取", msg)
            return

        if "DONE" == evt:
            spider.util.sendmail(["<jianghao@ipin.com>"], "58 jd爬取", msg)
            return

if __name__ == '__main__':
    _58_spider = Jd58Spider(20)
    _58_spider.speed_control_request.load_proxy('proxy', True)
    _58_spider.run()



