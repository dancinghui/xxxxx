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
    读取bin文件，只针对过滤阿里巴巴和爱拼信息
    """
    def __init__(self,thcnt):
        Spider.__init__(self,thcnt)
        # self.uc_count = 0
        # self.tc_count = 0
        # self.yy_count = 0
        self.all_count = 0
        self.bin_list = ['jobui_job_data1.bin','jobui_job_bu.bin','jobui_job_data2.bin']
        #self.bin_list = ['jobui_job.bin','jobui_job2.bin','jobui_job4.bin']
        self.domains = []
        self.file_s = FileSaver('domains.txt')

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
        # ali = '<a href="/company/281097/" class="fs18 sbox f000 fwb block" target="_blank">阿里巴巴集团</a>'
        # ipin_sz = '<a href="/company/12684631/" class="fs18 sbox f000 fwb block" target="_blank">深圳爱拼信息科技有限公司</a>'
        # ipin_gz = '<a href="/company/11361520/" class="fs18 sbox f000 fwb block" target="_blank">广州爱拼信息科技有限公司</a>'
        # uc = '<a href="/company/11987385/" class="fs18 sbox f000 fwb block" target="_blank">UC优视(UC浏览器)</a>'
        # tc = '<a href="/company/1236/" class="fs18 sbox f000 fwb block" target="_blank">深圳市腾讯计算机系统有限公司</a>'
        # yy = '<a href="/company/399611/" class="fs18 sbox f000 fwb block" target="_blank">广州华多网络科技有限公司</a>'
        #
        # if uc in content:
        #     print '#######################################find uc...',self.all_count
        #     id = re.findall(r'jobui_job.(\d+).',job.get("id"))[0]
        #     filename = './html/'+id +".html"
        #     self.new_file(filename,content)
        #     self.uc_count += 1
        # elif tc in content :
        #     print '#######################################find tc...',self.tc_count
        #     id = re.findall(r'jobui_job.(\d+).',job.get("id"))[0]
        #     filename = './html/' + id +".html"
        #     self.new_file(filename,content)
        #     self.tc_count += 1
        # elif yy in content:
        #     print '#######################################find ipin...',self.yy_count
        #     id = re.findall(r'jobui_job.(\d+).',job.get("id"))[0]
        #     filename = './html/' + id +".html"
        #     self.new_file(filename,content)
        #     self.yy_count += 1
        # else:
        #     print job.get("id")

        m = re.search(ur'<em class="sourceWeb common-icon"></em>(.*)</dd>',content)
        if m:
            domain = m.group(1)
            m1 = re.search(ur'<a class="no-style fwb " rel="nofllow" target="_blank" href="(.*)" onclick="_hmt.push\(\[\'_trackEvent\', \'jobInfo\', \'jobInfo_info\',\'jobInfo_info_jobSourceWeb\'\]\);">(.*)</a>',domain)
            if m1:
                domain = m1.group(2)

            if domain in self.domains:
                print '[%s] already in domains...'
            else:
                self.domains.append(domain)
                self.file_s.append('"'+domain+'"')
                print '[%s] add to domains...'
        else:
            print 'no match...'


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            dms = ''
            for i in s.domains:
                dms = dms+i+','
            print 'domains==',dms
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], dms)

    # def new_file(self,filename,content):
    #     a = open(filename,'w')
    #     a.write(content)
    #     a.close()
    #     print 'write file %s success ' % filename

if __name__ == "__main__":
    start = time.time()
    s = JobuiIpinAli(100)
    s.run()
    dms = ''
    for i in s.domains:
        dms = dms+i+','
    print 'domains==',dms
    end = time.time()
    print 'time = ',(end-start)
    print 'all_count:[%d],uc_count:[%d],tc_count:[%d],yy_count:[%d]'%(s.all_count,s.uc_count,s.tc_count,s.yy_count)
