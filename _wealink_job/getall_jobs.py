#coding=utf-8


import sys
sys.path.append(sys.path[0]+"/../")
print sys.path

from spider.spider import Spider
from page_store import PageStoreWL
from spider.httpreq import SpeedControlRequests
from spider.runtime import Log
import time


class JobWealinkSpider(Spider):
    def __init__(self, thread_cnt):
        super(JobWealinkSpider, self).__init__(thread_cnt)
        self.page_store = PageStoreWL()
        self.speed_control_request = SpeedControlRequests()
        self.page_store.testmode = False

    def dispatch(self):

        for i in xrange(28261133, 31000000):
            self.add_main_job(str(i))
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):

        if not self.page_store.check_should_fetch(jobid):
            return
        url = "http://www.wealink.com/zhiwei/view/{}/".format(jobid)
        res = self.speed_control_request.with_sleep_requests(url, sleep=0.1)
        if res.code == 404:
            print "jobid: {} match nothing".format(jobid)
            return
        if res is not None:
            self.page_store.save(int(time.time()), jobid, url, res.text)
        else:
            self.re_add_job(jobid)
            Log.error("failed get url", url)


if __name__ == '__main__':
    wl_spider = JobWealinkSpider(15)
    wl_spider.speed_control_request.load_proxy('proxy', True)
    wl_spider.run()





