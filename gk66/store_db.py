#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider, AccountErrors
import re
from spider.savebin import BinSaver
import random
import threading
import spider.util
import mongoengine
import sys
from score_gk66 import Score_gk66

filename = None
mongoengine.connect(None, alias="gk66", host="mongodb://crawler:crawler@192.168.1.81,192.168.1.82,192.168.1.83/gaokao_crawler", socketKeepAlive=True, wtimeout=100000)

class StoreDB(Spider):
    """这是针对爬到的数据在./all文件夹下所有的＊_data.txt文件导入到数据库gaokao_crawler.gk66_score中"""
    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        self.num_count = 0
        self.file_count = 0

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
        path = './all/'
        for parent,dirnames,filenames in os.walk(path):
            for fn in filenames:
                print 'filename is :'+fn
                global filename
                filename = fn
                datapath=os.path.join(os.path.dirname(__file__), "./all/"+fn)
                cnt = 0
                with open(datapath) as f:
                    while True:
                        cnt += 1
                        line = f.readline()
                        if not line: break
                        job = {"value": line, "cnt": cnt}
                        self.add_job(job, True)
                self.file_count += 1
        self.wait_q_breakable()
        self.add_job(None, True)


    def get_fail_cnt(self, addv):
        fc = getattr(self._curltls,'failcount',0)
        if (addv):
            fc += addv
            setattr(self._curltls, 'failcount', fc)
        return fc


    def run_job(self, jobid):
        cnt = jobid["cnt"]
        try:
            value = eval(jobid.get("value"))
            self.store_score(value)
        except Exception as e:
            print cnt, "发生错误：", e
        if self.num_count % 1000 == 0:
            print '------------------- num_count = %d ------------------------ file_count = %d--------------------'%(self.num_count,self.file_count)

    def store_score(self, value):
        print filename+' being write-->', value
        obj=Score_gk66.objects(location=value["location"],year=value["year"],bz=value["bz"],wl=value["wl"],school=value['school'],spec=value['spec'],rank=value['rank'],score=value['score'],batch=value["batch"],score_number=value['score_number'],spec_number=value['spec_number'],high_score=value['high_score'],high_score_rank=value['high_score_rank'],low_score=value['low_score'],low_score_rank=value['low_score_rank'],average_score=value['average_score'],average_score_rank=value['average_score_rank']).no_cache().timeout(False).first()
        if not obj:
            obj=Score_gk66(location=value["location"],year=value["year"],bz=value["bz"],wl=value["wl"],school=value['school'],spec=value['spec'],rank=value['rank'],score=value['score'],batch=value["batch"],score_number=value['score_number'],spec_number=value['spec_number'],high_score=value['high_score'],high_score_rank=value['high_score_rank'],low_score=value['low_score'],low_score_rank=value['low_score_rank'],average_score=value['average_score'],average_score_rank=value['average_score_rank'])
            obj.save()
            self.num_count+=1
            print "保存成功：", value
        else:
            print "数据已存在"


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

if __name__ == "__main__":
    start = time.time()
    s = StoreDB(1)
    s.run()
    end = time.time()
    print "time : {} , count : {} ,speed : {}t/s".format((end-start), s.num_count, s.num_count/(end-start))
