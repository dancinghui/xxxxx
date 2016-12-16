#!/usr/bin/python
# -*- coding:utf8 -*-

import copy
import json
import time

import spider.util
from spider.spider import Spider
from spider.httpreq import CurlReq
from zgcpwsw_genq import ZGcpwswData
from zgcpwsw_genq import ZGcpwswBasic
from spider.savebin import FileSaver


class ZGcpwswSpider(ZGcpwswBasic):

    def __init__(self, thcnt):
        ZGcpwswBasic.__init__(self, thcnt)
        #proxy thread
        self._proxy = None
        self.cerr_fs = FileSaver("court_queries/check_error")

    def dispatch(self):
        with open("court_queries/large_count", "r") as lc_fs:
            for line in lc_fs:
                lc_job = eval(line)
                count = lc_job.get("count")
                if count > ZGcpwswData.total_max_record:
                    for i in ZGcpwswData.data_order:
                        for j in ZGcpwswData.order_direction:
                            for k in range(ZGcpwswData.page_max_index):
                                copy_job = copy.deepcopy(lc_job)
                                copy_job["jobid"]["data"]["Index"] = k + 1
                                copy_job["jobid"]["data"]["Page"] = ZGcpwswData.page_max_count
                                copy_job["jobid"]["data"]["Direction"] = ZGcpwswData.order_direction[j]
                                copy_job["jobid"]["data"]["Order"] = ZGcpwswData.data_order[i]

                                self.add_job(copy_job)
                    time.sleep(2)

        with open("court_queries/medium_count") as mc_fs:
            for line in mc_fs:
                mc_job = eval(line)
                count = mc_job.get("count")
                if ZGcpwswData.total_core_record < count <= ZGcpwswData.total_max_record:
                    for j in ZGcpwswData.order_direction:
                        for k in range(ZGcpwswData.page_max_index):
                            copy_job = copy.deepcopy(mc_job)
                            copy_job["jobid"]["data"]["Index"] = k + 1
                            copy_job["jobid"]["data"]["Page"] = ZGcpwswData.page_max_count
                            copy_job["jobid"]["data"]["Direction"] = ZGcpwswData.order_direction[j]

                            self.add_job(copy_job)
                    time.sleep(2)

        with open("court_queries/small_count") as sc_fs:
            for line in sc_fs:
                sc_job = eval(line)
                count = sc_job.get("count")
                if 0 < count <= ZGcpwswData.total_core_record:
                    for k in range(ZGcpwswData.page_max_index):
                        copy_job = copy.deepcopy(sc_job)
                        copy_job["jobid"]["data"]["Index"] = k + 1
                        copy_job["jobid"]["data"]["Page"] = ZGcpwswData.page_max_count

                        self.add_job(copy_job)
                    time.sleep(2)

        self.wait_q()
        self.add_job(None)

    def run_job(self, jobid):
        if isinstance(jobid, dict):
            url = jobid.get("jobid").get("url")
            data = jobid.get("jobid").get("data")
            headers = jobid.get("jobid").get("headers")
            old_count = jobid.get("count")

            try:
                resp = self.request_url(url, data=data, headers=headers)
                if isinstance(resp, CurlReq.Response) and resp and resp.content:
                    result_list = json.loads(json.loads(resp.content))
                    if result_list:
                        flag = False
                        for result in result_list:
                            if result.get("Count"):
                                new_count = int(result.get("Count"))
                                if new_count == old_count:
                                    flag = True
                                else:
                                    flag = False
                            else:
                                print "content"
                                #handle the content

                        if not flag:
                            self.cerr_fs.append(jobid)
                    else:
                        self.add_job(jobid)
                else:
                    # owing to network, return None, add to job
                    time.sleep(1)
                    self.add_job(jobid)
            except Exception, e:
                print e
                time.sleep(1)
                self.add_job(jobid)


if __name__ == "__main__":
    spider.util.use_utf8()
    spider = ZGcpwswSpider(999)
    spider.run()
