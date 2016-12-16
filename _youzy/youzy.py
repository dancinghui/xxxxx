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
#from spider.util import Log
from lxml import html
import spider.util
from spider.util import htmlfind
from spider.savebin import FileSaver
import json
from youzylogin import YouzyLogin

#http://www.jobui.com/job/132925988/
#thread count mapping to proxy number
class YouzySpider(Spider):

    def __init__(self,thcnt):
        Spider.__init__(self, thcnt)
        self.sessionReq = YouzyLogin()
        self.sessionReq.do_login()
        self.num_count = 0
        self.savefile=FileSaver("youzy.txt")
        self.__fail_urls = FileSaver("fail_urls.txt")

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
        self.bs = BinSaver("youzy_job.bin")
        f = open("url_cfraction918-.txt", "r")
        while True :
            line = f.readline()
            if line.strip():
                job = {"url":line.strip()}
                self.add_job(job, True)
            else:
                break
        f.close()
        self.wait_q_breakable()
        self.add_job(None, True)

    def get_fail_cnt(self, addv):
        fc = getattr(self._curltls,'failcount',0)
        if (addv):
            fc += addv
            setattr(self._curltls, 'failcount', fc)
        return fc


    def run_job(self, jobid):
        url = jobid.get("url")
        print "url == ",url
        tid = self.get_tid()
        res = self.sessionReq.request_url(url)

        self.num_count += 1

        if res is None:
            if self.get_fail_cnt(1) < 10:
                self.add_job(jobid)
            else:
                self.__fail_urls.append(url)
                raise AccountErrors.NoAccountError("failcount = [ %d ]" % (self.get_fail_cnt(0)))
            return
        else:
            setattr(self._curltls,'failcount',0)

        if res.code == 404:
            print "%s ------ 404" % url
            return
        elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
            print "%s ------ %d " % (url,res.code)
            self.add_job(jobid)
            time.sleep(0.8)
            return
        elif res.code == 200:
            print "%s ------ saving " % url
            self.parse(res.content)
            con = []
            type = {"key":con}
            str1 = json.dumps(type)
            self.savefile.append(str1)
            #print "content======\n",res.content
            #self.bs.append(fn, res.text)
        else:
            print "#######################################UNKNOWN ERROR############################################# [ %d ]" % res.code
            #Log.error("unknown error...")
            #Log.errorbin("%s" %url, res.text)
            raise AccountErrors.NoAccountError('fatal error')


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

    def parse(self,text):
        #doc = html.fromstring(get_doc("daxue.html"))
        #print "type=========",type(doc)
        doc = html.fromstring(text)
        part1_template ='{}\t\t\t\t\t{}\t\t\t\t\t{}\t\t\t\t\t{}'
        part1_list = []
        els = doc.xpath('//select[@id]/option[@selected]')
        for el in els:
            print el
            part1_list.append(el.text_content().encode('utf-8'))

        print part1_template.format(*part1_list)
        print "================================================================================="

        header_template = '{}\t\t\t\t\t{}\t\t\t\t\t{}\t\t\t\t\t{}\t\t\t\t\t{}'
        header_list = []

        headers = doc.xpath('//table[@class="table table-hover table-bordered table-th-gray"]/thead/tr/th')
        for header in headers:
            style = header.attrib.get('style', None)
            if style:
                continue

            header_list.append(header.text_content().encode('utf-8'))

        print header_template.format(*header_list)

        bodys = doc.xpath('//table[@class="table table-hover table-bordered table-th-gray"]/tbody')

        td_list = []

        for body in bodys:
            style = body.attrib.get('style', None)
            if not style:
                trs = body.xpath('tr')

                for tr in trs:
                    tds = tr.xpath('td')
                    for td in tds:
                        style = td.attrib.get('style', None)
                        if style:
                            continue
                        td_list.append(td.text_content().encode('utf-8'))
                    print header_template.format(*td_list)



if __name__ == "__main__":
    start = time.time()
    s = YouzySpider(1)
    s.run()
    end = time.time()
    print "time : {} , count : {} ,speed : {}t/s".format((end-start) , s.num_count ,s.num_count/(end - start))
