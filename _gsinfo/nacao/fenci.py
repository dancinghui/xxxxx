#!/usr/bin/env python
# encoding:utf-8
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from spider.httpreq import BasicRequests, SessionRequests
from spider.spider import Spider
import random
import time
import imghdr
import spider.util
from spider.savebin import FileSaver
from urllib import quote
import json

filter_result = set()
filter_line = set()

class Fenci(Spider):
    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        self.saver = FileSaver("r1_fenci_local.txt")
        self.init_result()


    def init_result(self):
        with open("r1_fenci_local.txt", "r") as f:
            cnt = 0
            for line in f:
                cnt += 1
                line = line.strip()
                filter_result.add(line.decode("utf-8"))
        print "init result finish...", cnt

    def wait_q_breakable(self):
        lt = 0
        while True:
            if not self.job_queue.empty() or not self.job_queue2.empty() or not self.job_queue3.empty():
                time.sleep(5)
            if time.time() < lt + 1 and self._running_count == 0:
                return True
            time.sleep(2)
            lt = time.time()
            if self._worker_count == 0:
                return False

    def dispatch(self):
        with open("/home/windy/r1.txt", "r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                if line in filter_line:
                    print cnt, "code [ %s ] already split !" % line
                    continue
                ary = line.split(" ")
                x = -1
                for ay in ary:
                    x += 1
                    if x == 0 or x == 1:
                        continue
                    job = {"cnt": cnt, "key": ay}
                    self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)


    def run_job(self, job):
        key = job.get("key")
        url = "http://192.168.1.92:8911/firm_name/" + quote(key)
        res = None
        while True:
            res = self.request_url(url)
            if res is None or res.code != 200:
                print key, "res is None " if res is None else "res.code = %d " % res.code
                continue
            break
        text = res.text
        ary = text.split(" ")
        if len(ary) != 0:
            result = ary[0]
            if result != "" and result not in filter_result:
                self.saver.append(result)
                filter_result.add(result)
                print key, " ---> ", result
            else:
                print "result=", result, " or filter...."

    def try_try(self):
        url = "http://192.168.1.97:8911/firm_name"
        names = ["中霸集团有限公司", "深圳市靓字号通信连锁有限公司中国电信古城合作厅", "广东科龙电器股份有限公司深圳售后服务中心"]
        data = {"inc_names": spider.util.utf8str(names)}
        res = self.request_url(url, data=data)
        result = json.loads(res.text)
        for r in result:
            print r

if __name__ == '__main__':
    n = Fenci(1)
    #n.run()
    n.try_try()
