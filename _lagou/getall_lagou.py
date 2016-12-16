#coding=utf-8


import sys
sys.path.append(sys.path[0]+"/../")
print sys.path

from spider.savebin import BinSaver
from spider.spider import Spider
from spider.util import htmlfind
from page_store import PageStoreLG
from spider.httpreq import SpeedControlRequests
from spider.runtime import Log
import time



class JobLagouSpider(Spider):
    def __init__(self, thread_cnt):
        super(JobLagouSpider, self).__init__(thread_cnt)
        self.page_store = PageStoreLG()
        self.speed_control_request = SpeedControlRequests()
        self.page_store.testmode = False

    def dispatch(self):
        self.bs = BinSaver('joblagou.bin')
        for i in xrange(0, 1500000):
            self.add_main_job(str(i))
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):

        if not self.page_store.check_should_fetch(jobid):
            return
        url = "http://www.lagou.com/jobs/{}.html".format(jobid)
        res = self.speed_control_request.with_sleep_requests(url, sleep=0.1)
        if htmlfind.findTag(res.text, 'div', 'position_del'):
            print "jobid: {} match nothing".format(jobid)
            return
        if res is not None:
            self.page_store.save(int(time.time()), jobid, url, res.text)
        else:
            self.re_add_job(jobid)
            Log.error("failed get url", url)


if __name__ == '__main__':
    lagou_spider = JobLagouSpider(1)
    lagou_spider.speed_control_request.load_proxy('proxy', True)
    lagou_spider.run()





