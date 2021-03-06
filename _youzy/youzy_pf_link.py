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
from spider.savebin import FileSaver,CsvSaver
import json
from youzylogin import YouzyLogin

fixed = ['学校名称','文理科','省份','类型','选择年份']
pfcolumn = ['年份','专业名称','招生批次','选测等级','最高分','最低分','平均分','录取数']

class YouzySpiderPF(Spider):
    def __init__(self,thcnt):
        Spider.__init__(self, thcnt)
        self.sessionReq = YouzyLogin()
        self.sessionReq.do_login(5)
        self.savefile=CsvSaver("spider_zhuanke_pf.csv",fixed+pfcolumn)
        self.__fail_urls = FileSaver("spider_zhuanke_fail_pf.txt")
        self.id_count = 0
        self.url_count = 0
        self.parse_count = 0

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
        f = open("zhuanke.txt", "r")
        while True :
            line = f.readline().strip()
            if line:
                job = {"id":line,"retry":0}
                self.add_job(job, True)
            else:
                break
        f.close()
        self.wait_q_breakable()
        self.add_job(None, True)

    def run_job(self, jobid):
        if self.id_count % 11 == 0 :
            print "NOW =================================================================== \n [id_count=%d],[url_count=%d],[parse_count=%d]"%(self.id_count,self.url_count,self.parse_count)
        id = jobid.get("id")
        baseUrl = "http://www.youzy.cn/college/pfraction?courseType=-1&year=0&Id="+id;
        province = {"1","842","843","851","1128","845","834","844","848","847","855","849","850","859","837","846","839","852","860","854","840","841","1120","857","856","862","835"}
        self.id_count += 1
        for pro in province:
                url1 = baseUrl + "&provinceId="+pro
                res = self.sessionReq.request_url(url1)
                self.url_count += 1
                if res is None :
                    retry = int(jobid.get("retry"))
                    if retry < 5:
                        retry+=1
                        jobid = {"id":id,"retry":retry}
                        self.id_count -= 1
                        print "id %s retrying %d..."%(id,retry)
                        self.add_job(jobid)
                    else:
                        self.__fail_urls.append(url1)
                elif res.code == 200:
                    doc = html.fromstring(res.content)
                    values = doc.xpath('//select[@id="ddlCodes"]/option/@value')
                    if values is not None and len(values) > 0 :
                        for value in values :
                            url2 = url1+"&codeId="+value
                            self.req_local(url2,0)
                    else:
                        self.parse(res.content,url1)
                elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
                    time.sleep(1)
                    self.id_count -= 1
                    self.add_job(jobid)
                elif res.code == 404 :
                    self.__fail_urls.append(url1)
                    print "page [ %s ] is not found ! " % url1


    def parse(self,text,url):
        doc = html.fromstring(text)
        fixed_line = []
        name = doc.xpath('//div[@class="box"]/h2')
        if len(name) < 1 :
            print "page content is none, url = %s"%url
            self.__fail_urls.append(url)
            return False
        fixed_line.append(name[0].text_content().encode('utf-8'))
        options = doc.xpath('//select[@id]/option[@selected]')
        for option in options:
            fixed_line.append(option.text_content().encode('utf-8'))
        headers = doc.xpath('//table[@class="table table-hover table-bordered table-th-gray"]/thead/tr/th')
        header_column= []
        for header in headers:
            style = header.attrib.get('style', None)
            if style:
                continue
            header_column.append(header.text_content().encode('utf-8'))

        bodys = doc.xpath('//table[@class="table table-hover table-bordered table-th-gray"]/tbody')
        body_list = []
        for body in bodys:
            style = body.attrib.get('style', None)
            if not style:
                trs = body.xpath('tr')
                for tr in trs:
                    tds = tr.xpath('td')
                    td_list = []
                    for td in tds:
                        style = td.attrib.get('style', None)
                        if style:
                            continue
                        td_list.append(td.text_content().encode('utf-8'))
                    body_list.append(td_list)

        self.handle_line(body_list,header_column)
        for tr in body_list:
            line = fixed_line+tr
            self.savefile.writerline(line)
        self.parse_count += 1
        return True


    def handle_line(self,body_list,header_column):
        for tr in body_list:
            for h in pfcolumn:
                if not header_column.__contains__(h):
                    index = pfcolumn.index(h)
                    tr.insert(index,'null')

    def req_local(self, url ,retry):
        res = self.sessionReq.request_url(url)
        self.url_count += 1
        if res is None:
            if retry < 5:
                retry+=1
                self.url_count -= 1
                self.req_local(url,retry)
            else:
                self.__fail_urls.append(url)
        elif res.code == 404:
            self.__fail_urls.append(url)
            print "%s ------ 404" % url
        elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
            print "%s ------ %d " % (url,res.code)
            time.sleep(1)
            self.url_count -= 1
            self.req_local(url,retry)
        elif res.code == 200:
            self.parse(res.content,url)
        else:
            print "#######################################UNKNOWN ERROR############################################# [ %d ]" % res.code
            #raise AccountErrors.NoAccountError('fatal error')

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

if __name__ == "__main__":
    start = time.time()
    s = YouzySpiderPF(3)
    s.run()
    end = time.time()
    print "youzy_pf_link.py is finished , id_count : {}, url_count:{},parse_count:{}".format(s.id_count , s.url_count ,s.parse_count)
