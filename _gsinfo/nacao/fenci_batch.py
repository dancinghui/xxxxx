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
        self.already = FileSaver("r1_fenci_local_already.txt")
        self.init_result()

    def init_result(self):
        with open("r1_fenci_local.txt", "r") as f:
            cnt = 0
            for line in f:
                cnt += 1
                line = line.strip()
                filter_result.add(line.decode("utf-8"))
        print "init r1_fenci_local finish...", cnt

        with open("r1_fenci_local_already.txt", "r") as f:
            cnt = 0
            for line in f:
                cnt += 1
                line = line.strip()
                filter_line.add(line)
        print "init r1_fenci_local_already finish...", cnt

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
            inc_names = []
            lines = []
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
                    if len(inc_names) == 50:
                        job = {"cnt": cnt, "inc_names": inc_names, "lines": lines}
                        self.add_job(job, True)
                        del inc_names[:]
                        del lines[:]
                    inc_names.append(ay)
                    lines.append(line)
        self.wait_q_breakable()
        self.add_job(None, True)


    def run_job(self, job):
        inc_names = job.get("inc_names")
        cnt = job.get("cnt")
        url = "http://192.168.1.97:8911/firm_name"
        data = {"inc_names": spider.util.utf8str(inc_names)}
        res = None
        while True:
            res = self.request_url(url, data=data)
            if res is None or res.code != 200:
                print cnt, "res is None " if res is None else "res.code = %d " % res.code
                continue
            break
        text = res.text
        try:
            result = json.loads(text)
            print "分词结果:", spider.util.utf8str(result)
            for r in result:
                w = r[0]
                if w in filter_result:
                    continue
                self.saver.append(spider.util.utf8str(r[0]))

            lines = job.get("lines")
            for line in lines:
                self.already.append(line)
                filter_line.add(line)

        except Exception as e:
            print "读取数据异常...", "text=", text , "ERROR:", e


    def try_try(self):
        url = "http://192.168.1.97:8911/firm_name"
        names = ["中霸集团有限公司", "深圳市靓字号通信连锁有限公司中国电信古城合作厅", "广东科龙电器股份有限公司深圳售后服务中心"]
        data = {"inc_names": spider.util.utf8str(names)}
        res = self.request_url(url, data=data)
        result = json.loads(res.text)
        for r in result:
            print r[0], spider.util.utf8str(r[0])

if __name__ == '__main__':
    n = Fenci(10)
    n.run()
    #n.try_try()
