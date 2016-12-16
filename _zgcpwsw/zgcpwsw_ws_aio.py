#!/bin/usr/python
# -*- coding:utf-8 -*-

import copy
import time

from spider.spider2 import AioSpider
from spider.spider2 import AioRunner
import spider.util
from zgcpwsw_genq import ZGcpwswData


class ZGcpwswAioSpider(AioSpider):
    def __init__(self):
        AioSpider.__init__(self, ZGcpwswAioRunner)

    def init_jobs(self):
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


class ZGcpwswAioRunner(AioRunner):
    def __init__(self, curl, selproxy, idx):
        AioRunner.__init__(self, curl, selproxy, idx)

    def prepare_req(self, job, curl, proxies):
        pr = AioRunner.prepare_req(self, job, curl, proxies)
        if pr is not None:
            return pr

        url, headers = {}
        curl.prepare_req(url, headers=headers, proxies=proxies)
        return True

    def on_result(self, curl, resp):
        pass

if __name__ == "__main__":
    spider.util.use_utf8()
    spider = ZGcpwswAioSpider()
    spider.load_proxy("proxy")
    spider.run()