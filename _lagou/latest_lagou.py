# coding=utf-8

import sys
sys.path.append(sys.path[0]+"/../")
print sys.path

from spider.savebin import BinSaver
from spider.spider import Spider
from spider.util import htmlfind, TimeHandler
from page_store import PageStoreLG
from spider.httpreq import SpeedControlRequests
from queries import q
from spider.runtime import Log
import spider
import time
import json


class LatestLagouSpider(Spider):
    def __init__(self, thread_cnt):
        super(LatestLagouSpider, self).__init__(thread_cnt)
        self.page_store = PageStoreLG()
        self.speed_control_requests = SpeedControlRequests()

        self.page_store.testmode = False

    def getIds(self, q):
        url = "http://www.lagou.com/jobs/positionAjax.json"
        hasNext = True
        pageIndex = 0
        total_num = 100
        while hasNext and pageIndex <= total_num:
            pageIndex += 1
            q["pn"] = pageIndex
            res = self.request_url(url, data=q)
            json_resp = json.loads(res.text)
            if "content" in json_resp and "positionResult" in json_resp["content"] \
                and "result" in json_resp["content"]["positionResult"]:

                # if pageIndex == 1:
                #     total_num = json_resp["content"]["totalPageCount"]

                if not json_resp["content"]["positionResult"]["result"]:
                    hasNext=False
                elif json_resp["content"]["positionResult"]["result"]:
                    hasNext = True
                    for item in json_resp["content"]["positionResult"]["result"]:
                        create_time = item['createTimeSort']
                        # 昨天的不管
                        if TimeHandler.isBeforeNDay(create_time, 2):
                            yield item["positionId"]
                            break
                        yield item["positionId"]

    def dispatch(self):
        self.bs = BinSaver('joblagou.bin')
        for query in q:
            try:
                for jobid in self.getIds(query):
                    if isinstance(jobid, int):
                        jobid = str(jobid)
                    self.add_main_job(jobid)
            except Exception as e:
                continue
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):
        if not self.page_store.check_should_fetch(jobid):
            return
        url = "http://www.lagou.com/jobs/{}.html".format(jobid)
        res = self.speed_control_requests.with_sleep_requests(url, sleep=0.1)
        if htmlfind.findTag(res.text, 'div', 'position_del'):
            print "jobid: {} match nothing".format(jobid)
        if res is not None:
            self.page_store.save(int(time.time()), jobid, url, res.text)
        else:
            self.re_add_job(jobid)
            Log.error("failed get url", url)

    def event_handler(self, evt, msg, **kwargs):

        if "DONE" == evt:
            spider.util.sendmail(["<wangwei@ipin.com>"], "lagou jd爬取", msg + '\nsaved: %d' % self.page_store.saved_count)
            return


if __name__ == '__main__':
    latest_lagou = LatestLagouSpider(4)
    latest_lagou.load_proxy('proxy', True)
    latest_lagou.speed_control_requests.load_proxy('proxy', True)
    latest_lagou.run()
