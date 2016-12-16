# coding=utf-8

import sys
sys.path.append(sys.path[0]+"/../")
print sys.path

from spider.savebin import BinSaver
from spider.spider import Spider
from spider.util import htmlfind
from page_store import PageStoreWL
from spider.httpreq import SpeedControlRequests
from spider.runtime import Log
import spider
import time
import re


class LatestWLSpider(Spider):
    def __init__(self, thread_cnt):
        super(LatestWLSpider, self).__init__(thread_cnt)
        self.page_store = PageStoreWL()
        self.speed_control_request = SpeedControlRequests()

        self.page_store.testmode = False


    def parse_html(self, url):
        res = self.speed_control_request.with_sleep_requests(url, 0.05)

        find = re.findall(r'/zhiwei/view/(\d+)/', res.text)
        if find:
            find = set(find)
            for jobid in find:
                self.add_main_job(jobid)
            if u'下一页' not in res.text:
                return False
            return True
        # has_next = htmlfind.findTag(res.text, 'a', 'p_next')
        # if has_next:
        #     return True

        return False

    def dispatch(self):

        url_template = "http://www.wealink.com/zhaopin/发布-三天内/p{}.html"

        page_num = 1
        has_next = True

        while has_next:
            url = url_template.format(page_num)
            has_next = self.parse_html(url)
            page_num += 1

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

    def event_handler(self, evt, msg, **kwargs):

        if "DONE" == evt:
            spider.util.sendmail(["<jianghao@ipin.com>"], "wealink jd爬取", msg + '\n saved: %d' % self.page_store.saved_count)
            return

if __name__ == '__main__':
    latest_wl = LatestWLSpider(10)
    # latest_wl.load_proxy('proxy', True)
    latest_wl.speed_control_request.load_proxy('proxy', True)
    latest_wl.run()
