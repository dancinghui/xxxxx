# coding=utf-8

import sys
sys.path.append(sys.path[0]+"/../")
print sys.path

from spider.spider import Spider
from page_store import PageStoreLinkedIn
from spider.httpreq import SpeedControlRequests
import re
import time
import spider


class LinkedInConfig(object):
    URL_TMPLATE = "https://www.linkedin.com/jobs/search?countryCode=cn&locationId=cn:{}&f_I={}"
    PAGE_TMPLATE = "https://www.linkedin.com/jobs2/view/{}"


class LinkedInSpider(Spider):
    def __init__(self, thread_cnt, latest_type=None):
        super(LinkedInSpider, self).__init__(thread_cnt)
        self.page_store = PageStoreLinkedIn()
        self.speed_control_requests = SpeedControlRequests()
        self.latest_type = latest_type
        self.page_store.testmode = False

    def dispatch(self):

        if self.latest_type:
            LinkedInConfig.URL_TMPLATE += "&f_TP={}".format(self.latest_type)
        for locId in range(8876, 9046):
            for indId in range(0, 149):
                if indId == 2:
                    continue

                url = LinkedInConfig.URL_TMPLATE.format(locId, indId)
                self.add_main_job({"type":"search", "url": url})

        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return

        if jobid.get("type", None) == "search":
            self.parse_page(jobid.get("url"))

        elif jobid.get("type", None) == "jdurl":
            url = jobid.get("url")
            jobid = jobid.get("jobid", None)
            if not jobid:
                return
            res = self.speed_control_requests.with_sleep_requests(url, 0.5)
            self.page_store.save(int(time.time()), jobid, url, res.text)

    def parse_page(self, url):

        for page_num in range(1, 41):
            real_url = url + "&start={}&count=25".format(25 * (page_num-1))
            page = self.speed_control_requests.with_sleep_requests(real_url, 0.5)
            jobids = re.findall(r'linkedin.com/jobs2/view/(\d+)', page.text, re.S)
            jobids = set(jobids)

            if not jobids:
                return

            for jobid in jobids:
                url_page = LinkedInConfig.PAGE_TMPLATE.format(jobid)
                self.add_job({"type":"jdurl", "url":url_page, "jobid": jobid}, False)

    def event_handler(self, evt, msg, **kwargs):

        if "DONE" == evt:
            spider.util.sendmail(["<jianghao@ipin.com>"], "linkedin jd爬取", msg + '\nsaved: %d' % self.page_store.saved_count)
            return

if __name__ == '__main__':
    if len(sys.argv) >= 2:
        print "====TO get Latest Jd===="
        if sys.argv[1] not in '1,2,3,4':
            print "USAGE: {} {}".format(sys.argv[0], '1[,2][,3][,4]')

        lkspider = LinkedInSpider(1, sys.argv[1])
        lkspider.speed_control_requests.load_proxy('proxy2', True)
        lkspider.run()

    if len(sys.argv) < 2:
        lkspider = LinkedInSpider(20)
        lkspider.speed_control_requests.load_proxy('proxy2', True)
        lkspider.run()


