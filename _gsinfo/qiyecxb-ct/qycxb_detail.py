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

class QycxbDetail(Spider):
    """
    根据企业名称.查询企业列表 121.40.186.237:18889:ipin:helloipin
    """
    def __init__(self):
        self._can_use_proxy_num = 0
        self.is_debug = False
        if self.is_debug:
            Spider.__init__(self, 1)
        else:
            self.proxies_dict = []
            self.read_proxy("proxy_032512.txt")
            Spider.__init__(self, len(self.proxies_dict))

        self._aes_ = CCIQ_AES()
        #成功的
        self.query_success = FileSaver("c_query_detail.txt")
        #失败的
        self.query_failure = FileSaver("c_query_detail_failure.txt")
        #已经爬取过的
        self.already_cname_list = FileSaver("c_already_detail.txt")
        #初始化已经爬过的公司
        self.init_cname()

        #self.extJson = self._aes_.encrypt(spider.util.utf8str({"cl_screenSize": "640x960", "cl_cookieId": "B200BA9D-A3A0-4140-A293-9A1A671BA5CE", "Org_iOS_Version": "2.0.1"}))
        # self.extJson = "Hoi6oX70l9whauZmjq8jVAmoe3UspXXhX9mPG+KAeqs1rKZVr/uapICH92P/Crryt63u28aP4QP665AzcT/jN5Go1o3bvwMvVIkuN9e60k6WI2pVFBrwZMvxwW6BnQukSzDSlyPvEhgpR5DIHQEV6C51hMgp4Zc3OkTSsyezAm4="
        # self.select_user_agent("=CCIQ/2.0.1 (iPhone; iOS 9.1; Scale/2.00)")
        self.bloom = set()

        self.extJsons = ["Hoi6oX70l9whauZmjq8jVAmoe3UspXXhX9mPG+KAeqs1rKZVr/uapICH92P/Crryt63u28aP4QP665AzcT/jN5Go1o3bvwMvVIkuN9e60k6WI2pVFBrwZMvxwW6BnQukSzDSlyPvEhgpR5DIHQEV6C51hMgp4Zc3OkTSsyezAm4=",
                         "ctlCXDvoyaH2pCIArrgvXp7zrZTzpz2Q5rukh+aWvupEFABw6P2AvbmaN+HJ7IZgDJ/kgBkJt/rLppSGitYCPKGR2IGv6OXZsrJGgbRB3G3Ac4K8xpX3aMB5s8Ci2a/YpTpioZxAvptqJsQUCoNn0tLCOVM4XxMJQWbrErkOcl4=",
                         "ctlCXDvoyaH2pCIArrgvXp7zrZTzpz2Q5rukh+aWvupEFABw6P2AvbmaN+HJ7IZgDJ/kgBkJt/rLppSGitYCPKGR2IGv6OXZsrJGgbRB3G1U2wdOlL49/aDwt3NZNp4TGa5iBFpYLm69F/6PPFoXIR/Aw5p48//8OgZFpddDUwQ="]

        self.user_agents = ["=CCIQ/2.0.1 (iPhone; iOS 9.1; Scale/2.00)",
                            "=CCIQ/2.0.1 (iPhone; iOS 8.1.3; Scale/2.00)",
                            "=CCIQ/2.0.1 (iPhone; iOS 8.4; Scale/2.00)"]
        self.is_first = True
        self.init_time = 0

    def req_all(self, url, encryptedJson):
        #time.sleep(random.randrange(5, 11, 1))
        #time.sleep(2)
        number = random.randrange(0, 3, 1)
        self.select_user_agent(self.user_agents[number])
        param = spider.util.utf8str({"encryptedJson":self._aes_.encrypt(spider.util.utf8str(encryptedJson)), "extJson":self.extJsons[number]})
        param = param.replace('/', "\/")
        if self.is_first:
            self.init_time = time.time()
            print '初始化时间',self.init_time
            self.is_first = False
        if self.is_debug:
            res = self.request_url(url, headers={"Content-Type": "application/json"}, data=param, proxies={'http': 'http://ipin:helloipin@121.41.79.4:18889', 'https': 'https://ipin:helloipin@121.41.79.4:18889'})
            #res = self.request_url(url, headers={"Content-Type": "application/json"}, data=param, proxies={'http': 'http://137.135.166.225:8120', 'https': 'https://137.135.166.225:8120'})
        else:
            res = self.request_url(url, headers={"Content-Type": "application/json"}, data=param, proxies=self.proxies_dict[self.get_tid()])
        return res

    def init_cname(self):
        with open("c_already_detail.txt","r") as f:
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
        #with open("a_queried_company_list.txt","r") as f:
        with open("un_spider_queries.txt", "r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                if line in filter_name:
                    print cnt, "already spider!!!"
                    continue
                job = {"line":line, "cnt":cnt, "retry":0}
                self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)


    def record_spider(self, line, cname):
        """
        已经爬过的,无论成功失败都算爬过.
        """
        filter_name.add(line)
        self.already_cname_list.append(line)
        self.bloom.add(cname)

    def run_job(self, jobid):
        line = jobid.get("line")
        cnt = jobid.get("cnt")
        retry = jobid.get("retry")
        self.get_detail(line, cnt, retry)

    def get_detail(self, line, cnt, retry):
        tid = self.get_tid()
        try:
            param = eval(line)
        except Exception as err:
            print 'tid=%d --- cnt=%d --- data is not json, return'%(tid, cnt)
            self.record_spider(line,'UNKNOW')
            return
        cname = param['oc_name']
        if cname in self.bloom:
            cname = param['query_name']
            if cname in self.bloom:
                print 'query_name:%s aleready crawler...'%cname
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
        if res is None :
            if self.get_fail_cnt(1, 'failcount-none') < 10:
                self.re_add_job({'line':line,'cnt':cnt, 'retry':retry})
                print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d " % (tid, cnt, cname, retry, res_code)
                return
            else:
                # if retry > 5:
                #     self.query_failure.append(line)
                #     self.record_spider(line, cname)
                #     return
                # else:
                self.re_add_job({'line':line,'cnt':cnt, 'retry':(retry+1)})
                self._can_use_proxy_num -= 1
                raise AccountErrors.NoAccountError("Maybe the proxy invalid,failcount-none = [ %d ]" % self.get_fail_cnt(0, 'failcount-none'))
        else:
            setattr(self._curltls, 'failcount-none', 0)

        res_code = res.code
        if (res_code >= 400 and res_code < 500) or res_code == 202 :
            #print time.time(),"出现################",(time.time()-self.init_time), " res.code=", res_code
            # if retry > 20:
            #     self.query_failure.append(line)
            #     self.record_spider(line, cname)
            # else:
            self.re_add_job({'line':line,'cnt':cnt, 'retry':(retry+1)})
            print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d " % (tid, cnt, cname, retry, res_code)
            if self.get_fail_cnt(1, 'failcount-400') > 30:
                self._can_use_proxy_num -= 1
                raise AccountErrors.NoAccountError("Maybe the proxy invalid,failcount-400 = [ %d ]" % self.get_fail_cnt(0, 'failcount-400'))
            return
        else:
            setattr(self._curltls, 'failcount-400', 0)

        if res_code >= 500:
            # if retry > 5:
            #     self.query_failure.append(line)
            #     self.record_spider(line, cname)
            # else:
            self.re_add_job({'line':line,'cnt':cnt, 'retry':(retry+1)})
            print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d " % (tid, cnt, cname, retry, res_code)
            time.sleep(2)
            return
        elif res_code == 200:
            try:
                c = eval(res.text)['c']
            except Exception as err:
                print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d  exception res.text " % (tid, cnt, cname, retry, res_code)
                #print "exception res.text:\n", res.text
                self.query_failure.append(line)
                self.record_spider(line, cname)
                return
            if len(c) == 0:
                print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d   --- exception 'C' IS NULL" % (tid, cnt, cname, retry, res_code)
                self.query_failure.append(line)
                self.record_spider(line, cname)
                return
            result = CCIQ_AES("BF1856A312580D41256311147089E1CC").decrypt(c)
            try:
                detail = eval(result)
            except Exception as err:
                print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d  --- exception result:%s" % (tid, cnt, cname, retry, res_code, result)
                self.query_failure.append(line)
                self.record_spider(line, cname)
                return

            #print 'tid=', tid, 'proxy=', self.proxies_dict[tid], ' detail=',spider.util.utf8str(detail)
            #print 'tid=', tid, ' detail=',spider.util.utf8str(detail)

            #股东信息
            listGD = self.get_gd(carea, ccode, cname, 0)
            if listGD is not None:
                #print "tid=",tid," listGD=",spider.util.utf8str(listGD)
                detail['listGD'] = listGD['listGD']

            #投资信息
            list_inversted = self.get_inversted(cname, 0)
            if list_inversted is not None:
                #print "tid=",tid," list_inversted=",spider.util.utf8str(list_inversted)
                detail['inversted'] = list_inversted['inversted']

            #获取分支机构信息
            list_branch = self.get_branch(cname, 1, {"Branch": []}, 0)
            if list_branch is not None:
                #print "tid=",tid," list_branch=",spider.util.utf8str(list_branch)
                detail['Branch'] = list_branch['Branch']

            self.query_success.append(spider.util.utf8str(detail))
            self.record_spider(line, cname)

            print "tid=%d --- proxy=%s --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d  --- success:\n %s" % (tid,self.proxies_dict[tid], cnt, cname, retry, res_code, spider.util.utf8str(detail))
        else:
            self.query_failure.append(line)
            self.record_spider(line, cname)
            print "tid=%d --- cnt=%d --- cname=%s --- retry=%d --- res.code=%d  --- exception UNKNOW ERROR" % (tid, cnt, cname, retry, res_code)
            return



    def get_gd(self, area, code, cname, retry):
        """
        获取股东信息
        """
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/gd/detail"
        encryptedJson = {
            "bl_oc_area" : area, #4107
            "v1" : "QZOrgV005",
            "bl_oc_code" : code #672867774
        }
        res = self.req_all(url, encryptedJson)
        res_code = 0
        if res is None or (res.code >= 400 and res.code < 500):
            if res is not None:
                res_code = res.code
            print "get_gd --- cname=%s --- retry=%d --- res.code=%d" % (cname, retry, res_code)
            if retry < 5:
                time.sleep(0.1)
                return self.get_gd(area, code, cname, (retry+1))
            else:
                return None
        res_code = res.code
        if res_code >= 500:
            print "get_gd --- cname=%s --- retry=%d --- res.code=%d" % (cname, retry, res_code)
            time.sleep(1)
            return self.get_gd(area, code, cname, retry)
        elif res_code == 200:
            try:
                c = eval(res.text)['c']
            except Exception as err:
                print "get_gd --- cname=%s --- retry=%d --- res.code=%d  " % (cname, retry, res_code)
                print "get_gd --- exception res.text:\n", res.text
                if retry < 5:
                    time.sleep(0.1)
                    return self.get_gd(area, code, cname, (retry+1))
                else:
                    return None
            if len(c) == 0:
                print "get_gd --- cname=%s --- retry=%d --- res.code=%d  len(c)=0" % (cname, retry, res_code)
                if retry < 5:
                    time.sleep(0.1)
                    return self.get_gd(area, code, cname, (retry+1))
                else:
                    return None
            result = CCIQ_AES("BF1856A312580D41256311147089E1CC").decrypt(c)
            try:
                list_gd = eval(result)
            except Exception as err:
                print "get_gd --- cname=%s --- retry=%d --- res.code=%d " % (cname, retry, res_code)
                print 'get_gd --- eval(result) exception , result:\n',result
                if retry < 5:
                    time.sleep(0.1)
                    return self.get_gd(area, code, cname, (retry+1))
                else:
                    return None
            return list_gd
        else:
            print "get_gd --- cname=%s --- retry=%d --- res.code=%d ---UNKNOW ERROR" % (cname, retry, res_code)
            if retry < 5:
                time.sleep(0.1)
                return self.get_gd(area, code, cname, (retry+1))
            else:
                return None


    def get_inversted(self, cname, retry):
        """
        查询投资信息
        """
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/map/invesment"
        encryptedJson = {
            "input" : cname,
            "v1" : "QZOrgV005"
        }

        res = self.req_all(url, encryptedJson)
        res_code = 0
        if res is None or (res.code >= 400 and res.code < 500):
            if res is not None:
                res_code = res.code
            print "get_inversted --- cname=%s --- retry=%d --- res.code=%d" % (cname, retry, res_code)
            if retry < 5:
                return self.get_inversted(cname, (retry+1))
            else:
                return None

        res_code = res.code
        if res_code >= 400 and res_code < 500:
            print "get_inversted --- cname=%s --- retry=%d --- res.code=%d" % (cname, retry, res_code)
            if retry < 5:
                return self.get_inversted(cname, (retry+1))
            else:
                return None
        elif res_code >= 500:
            print "get_inversted --- cname=%s --- retry=%d --- res.code=%d" % (cname, retry, res_code)
            time.sleep(1)
            return self.get_inversted(cname, retry)
        elif res.code == 200:
            try:
                c = eval(res.text)['c']
            except Exception as err:
                print "get_inversted --- cname=%s --- retry=%d --- res.code=%d" % (cname, retry, res_code)
                print "get_inversted --- exception res.text:\n", res.text
                if retry < 5:
                    time.sleep(0.1)
                    return self.get_inversted(cname, (retry+1))
                else:
                    return None
            if len(c) == 0:
                print "get_inversted --- cname=%s --- retry=%d --- res.code=%d" % (cname, retry, res_code)
                if retry < 5:
                    time.sleep(0.1)
                    return self.get_inversted(cname, (retry+1))
                else:
                    return None
            result = CCIQ_AES("BF1856A312580D41256311147089E1CC").decrypt(c)
            try:
                list_inversted = eval(result)
            except Exception as err:
                print "get_inversted --- cname=%s --- retry=%d --- res.code=%d" % (cname, retry, res_code)
                print 'get_inversted --- eval(result) exception , result:\n', result
                if retry < 5:
                    time.sleep(0.1)
                    return self.get_inversted(cname, (retry+1))
                else:
                    return None
            return list_inversted
        else:
            print "get_inversted --- cname=%s --- retry=%d --- res.code=%d ---UNKNOW ERROR" % (cname, retry, res_code)
            if retry < 5:
                time.sleep(0.1)
                return self.get_inversted(cname, (retry+1))
            else:
                return None


    def get_branch(self,cname, now_page, list_branch, retry):
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
        res_code = 0
        if res is None or (res.code >= 400 and res.code < 500):
            if res is not None:
                res_code = res.code
            print "get_branch --- cname=%s --- retry=%d --- now_page=%d --- res.code=%d" % (cname, retry, now_page , res_code)
            if retry < 5:
                time.sleep(0.1)
                return self.get_branch(cname,now_page, list_branch, (retry+1))
            else:
                return None

        res_code = res.code
        if res_code >= 500:
            print "get_branch --- cname=%s --- retry=%d --- now_page=%d --- res.code=%d" % (cname, retry, now_page , res_code)
            time.sleep(1)
            return self.get_branch(cname, now_page, list_branch, (retry+1))
        elif res_code == 200:
            try:
                c = eval(res.text)['c']
            except Exception as err:
                print "get_branch --- cname=%s --- retry=%d --- now_page=%d --- res.code=%d" % (cname, retry, now_page , res_code)
                print "get_branch --- exception res.text:\n", res.text
                if retry < 5:
                    time.sleep(0.1)
                    return self.get_branch(cname, now_page, list_branch, (retry+1))
                else:
                    return None
            if len(c) == 0:
                print "get_branch --- cname=%s --- retry=%d --- now_page=%d --- res.code=%d --- len(c)=0" % (cname, retry, now_page , res_code)
                if retry < 5:
                    time.sleep(0.1)
                    return self.get_branch(cname, now_page, list_branch, (retry+1))
                else:
                    return None
            result = CCIQ_AES("BF1856A312580D41256311147089E1CC").decrypt(c)
            temp = eval(result)
            if temp is not None:
                for t in temp['Branch']:
                    list_branch['Branch'].append(t)
                if len(temp['Branch']) == 10:
                    now_page += 1
                    # if now_page >= 10:
                    #     return list_branch
                    return self.get_branch(cname, now_page, list_branch, 0)
                else:
                    return list_branch
            else:
                print "get_branch --- cname=%s --- retry=%d --- now_page=%d --- res.code=%d --- Branch is NULL" % (cname, retry, now_page , res_code)
                return None
        else:
            print "get_branch --- cname=%s --- retry=%d --- now_page=%d --- res.code=%d --- UNKNOW ERROR" % (cname, retry, now_page , res_code)
            if retry < 5:
                time.sleep(1)
                return self.get_branch(cname, now_page, list_branch, (retry+1))
            else:
                return None



    def get_fail_cnt(self, addv , type):
        fc = getattr(self._curltls,type,0)
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
                # m = re.match(r'(\d+\.\d+\.\d+\.\d+:\d+)', line, re.I)
                # m1 = re.match(r'(\d+\.\d+\.\d+\.\d+:\d+:\w+:\w+)', line, re.I)
                # if m:
                #     prstr = m.group(1)
                #     proxies = {'http': 'http://' + prstr+"/", 'https': 'https://' + prstr+"/"}
                #     self.proxies_dict.append(proxies)
                # elif re.match('\s*#', line):
                #     continue
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
    s = QycxbDetail()
    s.run()
