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
bloom = set()
class QycxbSpider(Spider):
    """
    根据企业基本信息查询详情 121.40.186.237:18889:ipin:helloipin

    ipin:helloipin@haohr.com:50001
    """
    def __init__(self):
        self._can_use_proxy_num = 0
        self.is_debug = True
        if self.is_debug:
            Spider.__init__(self, 200)
            self.proxy_error_cnt = 0
        else:
            self.proxies_dict = []
            self.read_proxy("../../_ct_proxy/proxy_all_filter.txt")
            Spider.__init__(self, len(self.proxies_dict))

        self._aes_ = CCIQ_AES()
        #成功拿到的详情
        self.query_success = FileSaver("beijing_query_detail1.txt")
        #失败的
        self.query_failure = FileSaver("beijing_query_detail_failure1.txt")
        #已经爬取过的列表
        self.already_cname_list = FileSaver("beijing_already_detail1.txt")
        #初始化已经爬过的公司
        self.init_cname()

        self.extJsons = ["Hoi6oX70l9whauZmjq8jVAmoe3UspXXhX9mPG+KAeqs1rKZVr/uapICH92P/Crryt63u28aP4QP665AzcT/jN5Go1o3bvwMvVIkuN9e60k6WI2pVFBrwZMvxwW6BnQukSzDSlyPvEhgpR5DIHQEV6C51hMgp4Zc3OkTSsyezAm4=",
                         "ctlCXDvoyaH2pCIArrgvXp7zrZTzpz2Q5rukh+aWvupEFABw6P2AvbmaN+HJ7IZgDJ/kgBkJt/rLppSGitYCPKGR2IGv6OXZsrJGgbRB3G3Ac4K8xpX3aMB5s8Ci2a/YpTpioZxAvptqJsQUCoNn0tLCOVM4XxMJQWbrErkOcl4=",
                         "ctlCXDvoyaH2pCIArrgvXp7zrZTzpz2Q5rukh+aWvupEFABw6P2AvbmaN+HJ7IZgDJ/kgBkJt/rLppSGitYCPKGR2IGv6OXZsrJGgbRB3G1U2wdOlL49/aDwt3NZNp4TGa5iBFpYLm69F/6PPFoXIR/Aw5p48//8OgZFpddDUwQ="]

        self.user_agents = ["=CCIQ/2.0.1 (iPhone; iOS 9.1; Scale/2.00)",
                            "=CCIQ/2.0.1 (iPhone; iOS 8.1.3; Scale/2.00)",
                            "=CCIQ/2.0.1 (iPhone; iOS 8.4; Scale/2.00)"]
        self.is_first = True
        self.init_time = 0
        self.lock = threading.Lock()

    def req_all(self, url, encryptedJson, retry=0):
        number = random.randrange(0, 3, 1)
        self.select_user_agent(self.user_agents[number])
        param = spider.util.utf8str({"encryptedJson":self._aes_.encrypt(spider.util.utf8str(encryptedJson)), "extJson":self.extJsons[number]})
        param = param.replace('/', "\/")
        res = None
        if self.is_first:
            self.init_time = time.time()
            print '初始化时间',self.init_time
            self.is_first = False
        if self.is_debug:
            res = self.request_url(url, headers={"Content-Type": "application/json"}, timeout=20, data=param, proxies={'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'})
           # res = self.request_url(url, headers={"Content-Type": "application/json"}, timeout=20, data=param, proxies={'http': 'http://ipin:helloipin@haohr.com:50001', 'https': 'https://ipin:helloipin@haohr.com:50001'})
            #res = self.request_url(url, headers={"Content-Type": "application/json", "Accept-Language": "zh-Hans-CN;q=1"}, data=param, proxies={'http': 'http://ipin:helloipin@106.75.134.191:18889', 'https': 'https://ipin:helloipin@106.75.134.191:18889'})
        else:
            res = self.request_url(url, headers={"Content-Type": "application/json"}, data=param, proxies=self.proxies_dict[self.get_tid()])
        if res is None or res.code != 200:
            print "访问错误", "res is none" if res is None else "res.code=%d" % (res.code)
            self.error_add()
            if retry < 7:
                time.sleep(random.randrange(1, 5, 1))
                return self.req_all(url, encryptedJson, retry=(retry+1))
        return res

    def init_cname(self):
        with open("beijing_already_detail1.txt", "r") as f:
            for line in f:
                filter_name.add(line.strip())


    def count_proxy_error(self, error_type):
        pass

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
        with open("all_company_list.txt", "r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                if line in filter_name or line is None or line == "None" or line == "":
                    #print cnt, "already spider!!!"
                    continue
                job = {"line": line, "cnt": cnt, "retry": 1}
                self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)


    def record_spider(self, line, cname):
        """
        已经爬过的,无论成功失败都算爬过.
        """
        filter_name.add(line)
        self.already_cname_list.append(line)
        bloom.add(cname)
        self.proxy_error_cnt = 0

    def error_add(self):
        pass
        # with self.lock:
        #     self.proxy_error_cnt += 1
        #     if self.proxy_error_cnt > 200:
        #         self.restart_jb()

    def restart_jb(self):
        if self.proxy_error_cnt < 200:
            return
        self.proxy_error_cnt = 0
        print "=============================重新启动拨号脚本================================="
        os.system("sshpass -p 'helloipin' ssh ipin@192.168.2.90 /home/ipin/bin/redial")
        time.sleep(10)
        os.system("sshpass -p 'helloipin' ssh ipin@192.168.2.90 /home/ipin/bin/getip")
        print "=============================重新启动拨号脚本成功=============================="


    def run_job(self, jobid):
        line = jobid.get("line")
        cnt = jobid.get("cnt")
        retry = jobid.get("retry")
        self.get_detail(line, cnt, retry)

    def get_detail(self, line, cnt, retry):
        tid = self.get_tid()
        param = None
        try:
            param = eval(line)
        except Exception as err:
            print 'tid=%d --- cnt=%d --- data is not json, return , line=%s'%(tid, cnt, line)
            self.record_spider(line, 'UNKNOW')
            return
        cname = param['oc_name']
        if cname in bloom:
            cname = param['query_name']
            if cname in bloom:
                print 'query_name:%s aleready crawler...' % cname
                return
        ccode = param['oc_code']
        carea = param['oc_area']
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/combine/detail"
        encryptedJson = {
            "bl_oc_code" : ccode,#code,  #"71526726X"
            "v1" : "QZOrgV005",
            "isDirect" : "0",
            "bl_oc_name" : cname,#cname,  #"腾讯科技"
            "bl_oc_area" : carea #area #"4403"
        }
        res = self.req_all(url, encryptedJson)
        res_code = 0
        if res is None:
            print cname, "get detail     res is None !!"
            return

        try:
            if u"服务不可用。" in res.text or u"Unauthorized!" in res.text:
                self.re_add_job({'cname': cname, 'cnt': cnt, 'retry': retry})
                print "系统不可用...", cname, res.text
                return
            c = eval(res.text)['c']
        except Exception as err:
            print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d  exception  res.text=%s " % (tid, cnt, cname, retry, res_code, spider.util.utf8str(res.text))
            self.re_add_job({'line': line, 'cnt': cnt, 'retry': retry})
            return
        if len(c) == 0:
            print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d   --- exception 'C' IS NULL" % (tid, cnt, cname, retry, res_code)
            param["error_type"] = "c=0"
            self.query_failure.append(spider.util.utf8str(param))
            self.record_spider(line, cname)
            return
        result = CCIQ_AES("BF1856A312580D41256311147089E1CC").decrypt(c)
        try:
            detail = eval(result)
        except Exception as err:
            print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d  --- exception result:%s" % (tid, cnt, cname, retry, res_code, result)
            param["error_type"] = "result_error"
            self.query_failure.append(spider.util.utf8str(param))
            self.record_spider(line, cname)
            return

        #股东信息
        listGD = self.get_gd(carea, ccode, cname)
        if listGD is not None:
            #print "tid=", tid, " listGD=", spider.util.utf8str(listGD)
            detail['listGD'] = listGD['listGD']

        #投资信息
        list_inversted = self.get_inversted(cname)
        if list_inversted is not None:
            #print "tid=", tid, " list_inversted=", spider.util.utf8str(list_inversted)
            detail['inversted'] = list_inversted['inversted']

        #获取分支机构信息
        branch = []
        list_branch = self.get_branch(cname, list_branch=branch)
        if list_branch is not None:
            #print "tid=", tid, " list_branch=", spider.util.utf8str(list_branch)
            detail['Branch'] = list_branch #['Branch']

        self.query_success.append(spider.util.utf8str(detail))
        self.record_spider(line, cname)

        print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d  @@@ success:\n %s" % (tid, cnt, cname, retry, res_code, spider.util.utf8str(detail))



    def get_gd(self, area, code, cname, retry=0):
        """
        获取股东信息
        """
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/gd/detail"
        encryptedJson = {
            "bl_oc_area" : area,
            "v1" : "QZOrgV005",
            "bl_oc_code" : code
        }
        res = self.req_all(url, encryptedJson)
        if res is None:
            return None
        if res.code == 200:
            try:
                c = eval(res.text)['c']
                if len(c) == 0:
                    print "get_gd --- cname=%s --- retry=%d --- reason:len(c)=0" % (cname, retry)
                    return None
                result = CCIQ_AES("BF1856A312580D41256311147089E1CC").decrypt(c)
                return eval(result)
            except Exception as err:
                print "get_gd --- cname=%s --- retry=%d --- reason:%s" % (cname, retry, err)
                if retry < 5:
                    retry += 1
                    time.sleep(retry*1.5)
                    return self.get_gd(area, code, cname, retry=retry)
                else:
                    return None
        else:
            print "get_gd --- cname=%s --- retry=%d --- res.code=%d" % (cname, retry, res.code)
            if retry < 5:
                retry += 1
                time.sleep(retry*1.5)
                return self.get_gd(area, code, cname, retry=retry)
            else:
                return None



    def get_inversted(self, cname, retry=0):
        """
        查询投资信息
        """
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/map/invesment"
        encryptedJson = {
            "input" : cname,
            "v1" : "QZOrgV005"
        }

        res = self.req_all(url, encryptedJson)
        if res is None:
            return None
        if res.code == 200:
            try:
                c = eval(res.text)['c']
                if len(c) == 0:
                    print "get_inversted --- cname=%s --- retry=%d --- reason:len(c)=0" % (cname, retry)
                    return None
                result = CCIQ_AES("BF1856A312580D41256311147089E1CC").decrypt(c)
                return eval(result)
            except Exception as err:
                print "get_inversted --- cname=%s --- retry=%d --- reason:%s" % (cname, retry, err)
                if retry < 5:
                    retry += 1
                    time.sleep(retry*1.5)
                    return self.get_inversted(cname, retry=retry)
                else:
                    return None
        else:
            print "get_inversted --- cname=%s --- retry=%d --- res.code=%d" % (cname, retry, res.code)
            if retry < 5:
                retry += 1
                time.sleep(retry*1.5)
                return self.get_inversted(cname, retry=retry)
            else:
                return None


    def get_branch(self,cname, now_page=1, list_branch=[], retry=0):
        """
        查询分支机构
        """
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/branch/select/page"
        encryptedJson = {
            "companyName" : cname,
            "v1" : "QZOrgV005",
            "page" : now_page,
            "pagesize" : "10"
        }

        res = self.req_all(url, encryptedJson)
        if res is None:
            return None
        if res.code == 200:
            try:
                c = eval(res.text)['c']
                if len(c) == 0:
                    print "get_branch --- cname=%s --- retry=%d --- reason:len(c)=0" % (cname, retry)
                    return None
                result = CCIQ_AES("BF1856A312580D41256311147089E1CC").decrypt(c)
                temp = eval(result)
                if temp is not None:
                    for t in temp['Branch']:
                        list_branch.append(t)
                    if len(temp['Branch']) == 10:
                        if now_page > 3:
                            return list_branch
                        now_page += 1
                        print cname, "翻页 -----------------------------------> now_page", now_page
                        return self.get_branch(cname, now_page=now_page, list_branch=list_branch, retry=retry)
                    else:
                        return list_branch
                else:
                    print "get_branch --- cname=%s --- retry=%d --- now_page=%d --- res.code=%d --- Branch is NULL" % (cname, retry, now_page)
                    return None
            except Exception as err:
                print "get_branch --- cname=%s --- retry=%d --- reason:%s" % (cname, retry, err)
                if retry < 5:
                    retry += 1
                    time.sleep(retry*1.5)
                    return self.get_branch(cname, now_page=now_page, list_branch=list_branch, retry=retry)
                else:
                    return None
        else:
            print "get_branch --- cname=%s --- retry=%d --- res.code=%d" % (cname, retry, res.code)
            if retry < 5:
                retry += 1
                time.sleep(retry*1.5)
                return self.get_branch(cname, now_page=now_page, list_branch=list_branch, retry=retry)
            else:
                return None



    def get_fail_cnt(self, addv , type):
        fc = getattr(self._curltls, type, 0)
        if (addv):
            fc += addv
            setattr(self._curltls, type, fc)
        return fc

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += '企业查询宝APP公司详情detail查询已经停止...'
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

    def read_proxy(self,fn):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                self._match_proxy(line)
        print " loaded [ %d ] proxis " % len(self.proxies_dict)


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
    s = QycxbSpider()
    s.run()
    #s.get_branch("江苏武进建工集团有限公司")
