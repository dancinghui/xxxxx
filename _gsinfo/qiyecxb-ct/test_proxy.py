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
from spider.savebin import FileSaver
from qycxb_AES import CCIQ_AES

filter_name = set()

class Test_proxy(Spider):
    """
    根据企业名称.查询企业列表
    """
    def __init__(self):
        Spider.__init__(self, 20)
        self._aes_ = CCIQ_AES()

        #self.select_user_agent("=CCIQ/2.0.1 (iPhone; iOS 8.4; Scale/2.00)")
        self.proxy_filter = FileSaver("proxy_filter_030309_detail1.txt")


        self.extJsons = ['"Hoi6oX70l9whauZmjq8jVAmoe3UspXXhX9mPG+KAeqs1rKZVr\/uapICH92P\/Crryt63u28aP4QP665AzcT\/jN5Go1o3bvwMvVIkuN9e60k6WI2pVFBrwZMvxwW6BnQukSzDSlyPvEhgpR5DIHQEV6C51hMgp4Zc3OkTSsyezAm4="',
                         '"ctlCXDvoyaH2pCIArrgvXp7zrZTzpz2Q5rukh+aWvupEFABw6P2AvbmaN+HJ7IZgDJ\/kgBkJt\/rLppSGitYCPKGR2IGv6OXZsrJGgbRB3G3Ac4K8xpX3aMB5s8Ci2a\/YpTpioZxAvptqJsQUCoNn0tLCOVM4XxMJQWbrErkOcl4="',
                         '"ctlCXDvoyaH2pCIArrgvXp7zrZTzpz2Q5rukh+aWvupEFABw6P2AvbmaN+HJ7IZgDJ\/kgBkJt\/rLppSGitYCPKGR2IGv6OXZsrJGgbRB3G1U2wdOlL49\/aDwt3NZNp4TGa5iBFpYLm69F\/6PPFoXIR\/Aw5p48\/\/8OgZFpddDUwQ="']

        self.user_agents = ["=CCIQ/2.0.1 (iPhone; iOS 9.1; Scale/2.00)",
                            "=CCIQ/2.0.1 (iPhone; iOS 8.1.3; Scale/2.00)",
                            "=CCIQ/2.0.1 (iPhone; iOS 8.4; Scale/2.00)"]

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
        with open("proxy_030309.txt","r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                m = re.match(r'(\d+\.\d+\.\d+\.\d+:\d+)', line, re.I)
                if m:
                    prstr = m.group(1)
                    if prstr in filter_name:
                        print 'proxy ', prstr, 'already exist!'
                        continue
                    else:
                        job = {"cnt":cnt, "proxy":prstr}
                        self.add_job(job, True)
                        filter_name.add(prstr)
                elif re.match('\s*#', line):
                    continue
        self.wait_q_breakable()
        self.add_job(None, True)

    def run_job(self, job):
        proxy = job.get("proxy")
        cnt = job.get("cnt")
        proxies = {'http': 'http://' + proxy+"/", 'https': 'https://' + proxy+"/"}
        number = random.randrange(0, 3, 1)
        self.select_user_agent(self.user_agents[number])
        extJson = self.extJsons[number]

        # param = '{"encryptedJson":"ZlWT15DsXFm0Y4QnYoK2ufXYi39Plo9\/yhwguqs9FWAHRqkKsKobDI+ai8+GR4NTJNeaHC7hDsivmsbOkOQ\/0lHsES3Wl5kF+pLW98YratGzlf4Tc5qnXiNDVUrc0WaqJD8obqeFhJLQsocfxB8REE6XpIbzthyB+CHX3TQpcJskJEZkJOyPxRdg9PTsCjTLPmgNHuWq3fSNyd3DpR6RIl\/AJNb+Ex70Uf0QDarg3koMErtDXwvcnEtxblp3kaMu2QmXxnDbkClaGASOP6ZsuKgVu6LXdW\/KOHk6cP+\/tEQ=","extJson":'+extJson+'}'
        # url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/combine/search"
        # #res = self.request_url(url, headers={"Content-Type": "application/json"}, data=param, proxies={'http': 'http://ipin:helloipin@121.41.79.4:18889', 'https': 'https://ipin:helloipin@121.41.79.4:18889'})
        # res = self.request_url(url, headers={"Content-Type": "application/json", "Accept-Language": "zh-Hans-CN;q=1"}, data=param, proxies=proxies)
        # # ipin:helloipin@121.41.79.4:18889  104.236.48.178:8080
        # if res is None :
        #     print cnt, proxy, '------------appsvc.res is none!'
        # elif res.code == 200:
        #     print cnt, proxy, '------------appsvc success!\n', res.text
        #     self.proxy_filter.append(proxy)
        # elif res.code >=500:
        #     self.re_add_job(job)
        #     print cnt, proxy, '------------retry ------ appsvc.res is ',res.code
        #     time.sleep(1)
        # else:
        #     print cnt, proxy, "------------appsvc.code=====",res.code



        param = '{"encryptedJson":"Q+jHyxoblFXYOTYKkkbeOQa6oISRDgp7DRbo5qqTuNJKO\/WHBesV4wdSgb5k99A6lbpcUZtCcK2ZCVRbj9jeAho2vjtcbOnORTJ6mxuUGxmZItFRPgl4KnE1iSLdTuwR3sp3TEI+FJaf5txip5QnPeVu4uPpCNc9LEy7Tf4fQ3H6rVlmAbtCO6bXe+79q0WUO1QUt5bEhglyG5PAFvRrEka8wrOUs1WZjGGslOvdZMw=","extJson":'+extJson+'}'
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/combine/detail"
        res = self.request_url(url, headers={"Content-Type": "application/json", "Accept-Language": "zh-Hans-CN;q=1"}, proxies=proxies, data=param)#{'http': 'http://ipin:helloipin@121.41.79.4:18889', 'https': 'https://ipin:helloipin@121.41.79.4:18889'})
        if res is None :
            print cnt, proxy, '------------appsvc.res is none!'
        elif res.code == 200:
            print cnt, proxy, '------------appsvc success!',res.text
            self.proxy_filter.append(proxy)
        elif res.code >=500:
            self.re_add_job(job)
            print cnt, proxy, '------------retry ------ appsvc.res is ',res.code
            time.sleep(1)
        else:
            print cnt, proxy, "------------appsvc.code=====",res.code


def check_already_spider():
    filter = set()
    with open("guangzhou_company_list_already.txt", "r") as f:
        for line in f:
            line = line.strip()
            filter.add(line)

    un = 0
    al = 0
    with open("guangzhou.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                al += 1
                print al, 'already spiders!'
            else:
                un += 1
                filter.add(line)
                print un, "-------------------un spiders !"
    print "已经爬过的:", al, ",没有爬过的:", un

def test_1():
    filter = set()
    filter_name = set()
    re_self = 0
    re_name = 0
    with open("guangzhou_company_list.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                re_self += 1
                print re_self, "自身重复..."
            else:
                try:
                    detail = eval(line)
                    if isinstance(detail, dict):
                        cname = detail["oc_name"]
                        if cname in filter_name:
                            re_name += 1
                            print re_name, "名字重复..."
                        else:
                            filter_name.add(cname)
                except Exception as e:
                    print "ERROR:", e, line
    print "自身重复数:", re_self, "名字重复:", re_name
    time.sleep(1)
    re1 = 0
    new = 0
    with open("guangzhou.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter_name:
                re1 += 1
                print re1, "已经爬过..."
            else:
                new += 1
                print new, "没有爬过..."
    print "爬到的名字数量:", re1, "没有爬到的数量:", new

def test_read1():
    filter = set()
    with open("beijing_query_detail1.txt", "r") as f:
        i = 0
        j = 0
        for line in f:
            r = line.strip()
            if r in filter:
                j += 1
                print j, 'already exist!!!'
            else:
                filter.add(r)
                i += 1
                print "第", i, "行:", r #utf8str(r)

    print '重复条数:', j, "去重后条数:", i

def filter_self():
    filter = set()
    save = FileSaver("../qichacha/query_success_detail1.txt")
    with open("../qichacha/query_success_detail.txt", "r") as f:
        i = 0
        j = 0
        for line in f:
            r = line.strip()
            if r in filter:
                j += 1
                print j, 'already exist!!!'
            else:
                filter.add(r)
                i += 1
                save.append(r)
                print "第", i, "行:", r #utf8str(r)

    print '重复条数:', j, "去重后条数:", i

def test_2():
    filter = set()
    filter_name = set()
    re_self = 0
    new_self = 0
    with open("../qichacha/query_success_name.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter_name:
                re_self += 1
                print re_self, "自身重复..."
            else:
                new_self += 1
                filter_name.add(line)
    print "自身重复数:", re_self, "成功数量:", new_self
    time.sleep(1)
    re1 = 0
    new = 0
    unnew = 0
    with open("../qichacha/query_success_detail.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                re1 += 1
                print re1, "详情自身重复..."
            else:
                filter.add(line)
                r = eval(line)
                if isinstance(r, list):
                    cname = r[0]
                    if cname in filter_name:
                        new += 1
                        print new, "匹配-----------------"
                    else:
                        unnew += 1
                        filter_name.add(cname)

    print "爬取成功公司名数:", new_self, "详情自身重复:", re1, "匹配上的数量:", new, "未匹配上的数量:", unnew, "匹配比例:", round(new/new_self,2)

if __name__ == "__main__":
    # s = Test_proxy()
    # s.run()
    #check_already_spider()
    test_read1()
