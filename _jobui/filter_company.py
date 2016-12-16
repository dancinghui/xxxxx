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
import traceback
import spider.util
from spider.savebin import FileSaver,BinReader

class JobuiIpinAli(Spider):
    """
    读取bin文件，只针对过滤指定名称的公司 生成html文件
    """
    def __init__(self,thcnt):
        Spider.__init__(self,thcnt)
        self.all_count = 0
        self.yy_count = 0
        self.bin_list = ['jobui_job_data1.bin','jobui_job_bu.bin','jobui_job_data2.bin']

    def wait_q_breakable(self):
        lt = 0
        while True:
            if not self.job_queue.empty() or not self.job_queue2.empty() or not self.job_queue3.empty():
                time.sleep(5)
            if time.time() < lt + 1 and self._running_count==0:
                return True
            time.sleep(2)
            lt = time.time()
            if self._worker_count == 0:
                return False

    def dispatch(self):
        for binname in self.bin_list:
            bs = BinReader("./jobdata/"+binname)
            #bs = BinReader("./data/"+binname)
            while True:
                (a,b) = bs.readone()
                if a is None:
                    break
                job = {"id":a,"content":b}
                self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)

    def get_fail_cnt(self, addv):
        fc = getattr(self._curltls,'failcount',0)
        if (addv):
            fc += addv
            setattr(self._curltls, 'failcount', fc)
        return fc


    def run_job(self, job):
        self.all_count += 1
        content = job.get("content")
        #print content
        yy1 = '<a href="/company/12428597/" class="fs18 sbox f000 fwb block" target="_blank">YY Inc</a>'
        yy2 = '<a href="/company/12823028/" class="fs18 sbox f000 fwb block" target="_blank">欢聚时代(YY语音)</a>'
        yy3 = '<a href="/company/12534260/" class="fs18 sbox f000 fwb block" target="_blank">欢聚时代北京分公司</a>'
        yy4 = '<a href="/company/12821247/" class="fs18 sbox f000 fwb block" target="_blank">欢聚时代(多玩YY)珠海分公司</a>'
        yy5 = '<a href="/company/399611/" class="fs18 sbox f000 fwb block" target="_blank">广州华多网络科技有限公司</a>'
        yy6 = '<a href="/company/12717677/" class="fs18 sbox f000 fwb block" target="_blank">广州华多网络科技有限公司南京分公司</a>'

        # yy = ['<a href="/company/12428597/" class="fs18 sbox f000 fwb block" target="_blank">YY Inc</a>',
        #       '<a href="/company/12823028/" class="fs18 sbox f000 fwb block" target="_blank">欢聚时代(YY语音)</a>',
        #       '<a href="/company/12534260/" class="fs18 sbox f000 fwb block" target="_blank">欢聚时代北京分公司</a>',
        #       '<a href="/company/12821247/" class="fs18 sbox f000 fwb block" target="_blank">欢聚时代(多玩YY)珠海分公司</a>',
        #       '<a href="/company/399611/" class="fs18 sbox f000 fwb block" target="_blank">广州华多网络科技有限公司</a>',
        #       '<a href="/company/12717677/" class="fs18 sbox f000 fwb block" target="_blank">广州华多网络科技有限公司南京分公司</a>']

        # for y in yy:
        #     if y in content:
        #         id = re.findall(r'jobui_job.(\d+).',job.get("id"))[0]
        #         filename = './html/'+id +".html"
        #         self.new_file(filename,content)
        #         print '#######################################find yy...',filename,self.yy_count
        #         self.yy_count += 1
        #
        # print job.get("id")

        if (yy1 in content) or (yy2 in content) or (yy3 in content) or (yy4 in content) or (yy5 in content) or (yy6 in content):
            id = re.findall(r'jobui_job.(\d+).',job.get("id"))[0]
            filename = './html/'+id +".html"
            print '#######################################find yy...',filename,self.yy_count
            self.new_file(filename,content)
            self.yy_count += 1
        else:
            print job.get("id")


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += '\n read html number:'+str(self.all_count)+",get yy count:"+str(self.yy_count)
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

    def new_file(self,filename,content):
        a = open(filename,'w')
        a.write(content)
        a.close()
        print 'write file %s success ' % filename

if __name__ == "__main__":
    start = time.time()
    s = JobuiIpinAli(100)
    s.run()
