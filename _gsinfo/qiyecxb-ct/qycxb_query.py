#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider, AccountErrors
import re
import random
import spider.util
from spider.savebin import FileSaver
from qycxb_AES import CCIQ_AES

filter_name = set()

class QycxbQuery(Spider):
    """
    根据企业名称.查询企业列表------针对900多万的公司名查询
    """
    def __init__(self):
        self.is_debug = False
        self._can_use_proxy_num = 0
        if self.is_debug:
            Spider.__init__(self, 1)
        else:
            self.proxies_dict = []
            self.read_proxy("../../_ct_proxy/proxy_all_filter.txt")
            Spider.__init__(self, len(self.proxies_dict))
        self.error_cnt = 0
        self._aes_ = CCIQ_AES()
        #根据公司名字查询到的公司列表全部信息
        self.query_company_list = FileSaver("all_company_list.txt")

        #已经爬取过的公司名
        self.already_cname_list = FileSaver("all_company_list_already.txt")

        #爬过的 错误类型
        self.already_error_type = FileSaver("all_already_error_type.txt")

        #初始化已经爬过的公司
        self.init_cname()
        self.extJsons = ["Hoi6oX70l9whauZmjq8jVAmoe3UspXXhX9mPG+KAeqs1rKZVr/uapICH92P/Crryt63u28aP4QP665AzcT/jN5Go1o3bvwMvVIkuN9e60k6WI2pVFBrwZMvxwW6BnQukSzDSlyPvEhgpR5DIHQEV6C51hMgp4Zc3OkTSsyezAm4=",
                         "ctlCXDvoyaH2pCIArrgvXp7zrZTzpz2Q5rukh+aWvupEFABw6P2AvbmaN+HJ7IZgDJ/kgBkJt/rLppSGitYCPKGR2IGv6OXZsrJGgbRB3G3Ac4K8xpX3aMB5s8Ci2a/YpTpioZxAvptqJsQUCoNn0tLCOVM4XxMJQWbrErkOcl4=",
                         "ctlCXDvoyaH2pCIArrgvXp7zrZTzpz2Q5rukh+aWvupEFABw6P2AvbmaN+HJ7IZgDJ/kgBkJt/rLppSGitYCPKGR2IGv6OXZsrJGgbRB3G1U2wdOlL49/aDwt3NZNp4TGa5iBFpYLm69F/6PPFoXIR/Aw5p48//8OgZFpddDUwQ="]

        self.user_agents = ["=CCIQ/2.0.1 (iPhone; iOS 9.1; Scale/2.00)",
                            "=CCIQ/2.0.1 (iPhone; iOS 8.1.3; Scale/2.00)",
                            "=CCIQ/2.0.1 (iPhone; iOS 8.4; Scale/2.00)"]

        self.bloom = set()

    def req_all(self, encryptedJson):
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/combine/search"
        number = random.randrange(0, 3, 1)
        self.select_user_agent(self.user_agents[number])
        param = spider.util.utf8str({"encryptedJson": self._aes_.encrypt(spider.util.utf8str(encryptedJson)), "extJson": self.extJsons[number]})
        param = param.replace('/', "\/")
        try:
            if self.is_debug:
                res = self.request_url(url, headers={"Content-Type": "application/json", "Accept-Language": "zh-Hans-CN;q=1"}, data=param, proxies={'http': 'http://ipin:helloipin@121.41.79.4:18889', 'https': 'https://ipin:helloipin@121.41.79.4:18889'})
                #res = self.request_url(url, headers={"Content-Type": "application/json"}, data=param, proxies={'http': 'http://104.236.48.178:8080', 'https': 'https://104.236.48.178:8080'})
            else:
                res = self.request_url(url, headers={"Content-Type": "application/json", "Accept-Language": "zh-Hans-CN;q=1"}, data=param, proxies=self.proxies_dict[self.get_tid()])
            if res is not None and res.code == 200:
                time.sleep(random.randrange(30, 50, 1))
            else:
                time.sleep(5)
            return res
        except Exception as err:
            proxies = self.proxies_dict[self.get_tid()]
            print proxies['http'],"@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@\n error = ", err

    def init_cname(self):
        with open("all_company_list_already.txt", "r") as f:
            for line in f:
                filter_name.add(line.strip())

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
        with open("beijing_cname.txt", "r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                if line in filter_name:
                    #print cnt, line, "already spider!!!"
                    continue
                job = {"cname": line, "cnt": cnt, "retry": 0}
                self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)


    def record_spider(self,line):
        """
        已经爬过的,无论成功失败都算爬过.
        """
        filter_name.add(line)
        self.already_cname_list.append(line)

    def run_job(self, job):
        cname = job.get("cname")
        cnt = job.get("cnt")
        retry = job.get("retry")
        if cname is None:
            print 'cname = ', cnt, ' is None ,break~'
            return
        self.flip_over(1, cname, cnt, retry)


    def flip_over(self , now_page , cname , cnt , retry):
        tid = self.get_tid()
        """
        根据公司名查询公司列表,翻页
        """
        encryptedJson = {
  "pagesize" : "20",
  "page" : now_page,
  "od_orderBy" : "0",
  "sh_searchType" : "一般搜索",
  "sh_oc_areaName" : "",
  "od_statusFilter" : "0",
  "v1" : "QZOrgV005",
  "oc_name" : cname,
  "sh_u_uid" : "",
  "sh_u_name" : ""
}
        r_result = {"cname": cname}
        res = self.req_all(encryptedJson)
        res_code = 0
        if res is None:
            if self.get_fail_cnt('failcount-none', 1) < 10:
                self.re_add_job({'cname': cname, 'cnt': cnt, 'retry': retry})
                print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d --- now_page:%d" % (tid, cnt, cname, retry, res_code, now_page)
                return
            else:
                # if retry > 5:
                #     r_result["type"] = "None"
                #     self.already_error_type.append(spider.util.utf8str(r_result))
                #     self.record_spider(cname)
                #     print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d --- now_page:%d" % (tid, cnt, cname, retry, res_code, now_page)
                # else:
                #     self.re_add_job({'cname':cname,'cnt':cnt, 'retry':(retry+1)})
                self.re_add_job({'cname': cname, 'cnt': cnt, 'retry': retry})
                raise AccountErrors.NoAccountError("Maybe the proxy invalid,failcount-none = [ %d ],tid=[ %d ]" % (self.get_fail_cnt('failcount-none', 0), tid))
        else:
            setattr(self._curltls, 'failcount-none', 0)

        res_code = res.code

        if (res_code >= 400 and res_code < 500) or res_code == 202:
            if self.get_fail_cnt('failcount-400', 1) < 5:
                self.re_add_job({'cname': cname, 'cnt': cnt, 'retry': retry})
                print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d --- now_page:%d" % (tid, cnt, cname, retry, res_code, now_page)
                return
            else:
                if retry > 5:
                    r_result["type"]="400+"
                    self.already_error_type.append(spider.util.utf8str(r_result))
                    self.record_spider(cname)
                else:
                    self.re_add_job({'cname': cname,'cnt': cnt, 'retry': (retry+1)})
                    self._can_use_proxy_num -= 1
                raise AccountErrors.NoAccountError("Maybe the proxy invalid,failcount-400 = [ %d ],tid=[ %d ]" % (self.get_fail_cnt('failcount-400', 0), tid))
        else:
            setattr(self._curltls, 'failcount-400', 0)

        if res_code >= 500:
            # if retry > 2:
            #     r_result["type"]="500"
            #     self.already_error_type.append(spider.util.utf8str(r_result))
            #     self.record_spider(cname)
            # else:
            self.re_add_job({'cname': cname,'cnt': cnt, 'retry': retry})
            print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d  --- now_page:%d " % (tid, cnt, cname, retry, res_code, now_page)
            time.sleep(random.randrange(1, 10, 1))
            return
        elif res_code == 200:
            try:
                c = eval(res.text)['c']
            except Exception as err:
                print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d  --- now_page:%d --- exception res.text - %s" % (tid, cnt, cname, retry, res_code, now_page, err)
                # r_result["type"] = "res_error"
                # self.already_error_type.append(spider.util.utf8str(r_result))
                # self.record_spider(cname)
                # self.error_cnt += 1
                self.re_add_job({'cname': cname, 'cnt': cnt, 'retry': retry})
                return
            if len(c) == 0:
                print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d  --- now_page:%d --- exception 'C' IS NULL" % (tid, cnt, cname, retry, res_code, now_page)
                r_result["type"] = "c=0"
                self.already_error_type.append(spider.util.utf8str(r_result))
                self.record_spider(cname)
                self.error_cnt += 1
                return
            result = CCIQ_AES("BF1856A312580D41256311147089E1CC").decrypt(c)
            try:
                dic = eval(result)
            except Exception as err:
                print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d  --- now_page:%d --- exception result:%s" % (tid, cnt, cname, retry, res_code, now_page, result)
                r_result["type"] = "result_error"
                self.already_error_type.append(spider.util.utf8str(r_result))
                self.record_spider(cname)
                self.error_cnt += 1
                return
            list = dic['list']
            if len(list) == 0:
                print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d --- now_page:%d --- exception len(list)=0" % (tid, cnt, cname, retry, res_code, now_page)
                r_result["type"] = "list=0"
                self.already_error_type.append(spider.util.utf8str(r_result))
                self.record_spider(cname)
                self.error_cnt += 1
                return
            #print "tid=%d ### cnt=%d ### cname=%s ### retry=%d ### res.code=%d ### now_page:%d ### success:len(list):%d " % (tid, cnt, cname, retry, res_code, now_page, len(list))
            for l in list:
                aa = {"query_name": cname}
                for k, v in l.items():
                    aa[k] = v
                self.query_company_list.append(spider.util.utf8str(aa))
            print "******", len(list), spider.util.utf8str(list)
            if len(list) < 20:
                # r_result["type"] = "success"
                # self.already_error_type.append(spider.util.utf8str(r_result))
                self.record_spider(cname)
                return
            elif len(list) == 20:
                if now_page > 100:
                    self.already_error_type.append(spider.util.utf8str(r_result))
                    self.record_spider(cname)
                    return
                now_page += 1
                self.flip_over(now_page, cname, cnt, retry)
        else:
            print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d --- now_page:%d --- exception UNKNOW ERROR" % (tid, cnt, cname, retry, res_code, now_page)
            if retry < 3:
                self.re_add_job({'cname': cname,'cnt': cnt, 'retry': (retry+1)})
                return
            r_result["type"]="unknown_error"
            self.already_error_type.append(spider.util.utf8str(r_result))
            self.record_spider(cname)
            return


    def get_fail_cnt(self, type_key, addv):
        fc = getattr(self._curltls, type_key, 0)
        if (addv):
            fc += addv
            setattr(self._curltls, type_key, fc)
        return fc

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += '企业查询宝APP公司列表查询已经停止...错误数:'+str(self.error_cnt)
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

    def read_proxy(self,fn):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                self._match_proxy(line)
        self._can_use_proxy_num = len(self.proxies_dict)
        print " loaded [ %d ] proxis " % self._can_use_proxy_num

    def _match_proxy(self,line):
        m = re.match('([0-9.]+):(\d+):([a-z0-9]+):([a-z0-9._-]+)$', line, re.I)
        m1 = re.match('([0-9.]+):(\d+):([a-z0-9]+)$', line, re.I)
        if m:
            prstr = '%s:%s@%s:%s' % (m.group(3), m.group(4), m.group(1), m.group(2))
            proxies = {'http': 'http://' + prstr, 'https': 'https://' + prstr}
        elif m1:
            prstr = '%s:%s' % (m1.group(1), m1.group(2))
            proxies = {'http': 'http://' + prstr, 'https': 'https://' + prstr}
        else:
            proxies = {'http': 'http://' + line, 'https': 'https://' + line}
        self.proxies_dict.append(proxies)

if __name__ == "__main__":
    s = QycxbQuery()
    s.run()
