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

class QycxbApp(Spider):
    """
    根据企业名称 访问接口 获得公司是否存在,存在则拿出其注册号和公司名称保存,不存在则忽略
    """
    def __init__(self):
        #self.proxies_dict = []
        #self.read_proxy("../spider/proxy/proxy.txt")
        #Spider.__init__(self, len(self.proxies_dict))
        Spider.__init__(self, 1)
        self.num_count = 0
        self._aes_ = CCIQ_AES()
        #APP可以拿到的公司全部信息
        self.save_success = FileSaver("exist_company.txt")
        #APP可以拿到的公司局部信息
        self.part_success = FileSaver("part_company.txt")
        #查询失败的公司名
        self.fail_name = FileSaver("fail_name.txt")

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
        with open("old-company.txt","r") as f:
            while True:
                line = f.readline().strip()
                ary = line.split(" ")
                if len(ary) == 3:
                    #print 'read company name is ', ary[2]
                    job = {"cname":ary[2]}
                    self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)


    def get_fail_cnt(self, addv):
        fc = getattr(self._curltls,'failcount',0)
        if (addv):
            fc += addv
            setattr(self._curltls, 'failcount', fc)
        return fc


    def run_job(self, jobid):
        self.select_user_agent("=CCIQ/2.0.1 (iPhone; iOS 9.1; Scale/2.00)")
        cname = jobid.get("cname")
        self.flip_over(1,cname)


    def flip_over(self , now_page , cname):
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/combine/search"
        headers = {"Content-Type": "application/json"}
        encryptedJson = {"pagesize" : "20","page" : now_page,"od_orderBy" : "0","sh_searchType" : "一般搜索","od_statusFilter" : "0","v1" : "QZOrgV004","oc_name" : cname,"sh_u_uid" : "","sh_u_name" : ""}
        extJson = {"cl_screenSize" : "640x960","cl_cookieId" : "16923697-D73E-485A-BDCF-68FAD456AC02","Org_iOS_Version" : "2.0.1"}
        param = {"encryptedJson":self._aes_.encrypt(spider.util.utf8str(encryptedJson)), "extJson": self._aes_.encrypt(spider.util.utf8str(extJson))}
        param = spider.util.utf8str(param)
        res = self.request_url(url, headers=headers, data=param)
        if res is None:
            print 'res is none -- search company name is -->',cname
            self.fail_name.append(cname)
            return
        elif res.code == 404:
            print "%s ------ 404" % cname
            return
        elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
            print "%s ------ %d " % (cname,res.code)
            self.add_job({'cname':cname})
            time.sleep(0.5)
            return
        elif res.code == 200:
            c = eval(res.text)['c']
            if len(c) == 0:
                print '-----------------------------cname %s res.text is null----------------------------'%cname
                return
            result = CCIQ_AES("BB1856A312580D41256311147089E0CC").decrypt(c)
            dic = eval(result)
            list = dic['list']
            if len(list) == 0:
                print 'cname %s result list length = 0 '%cname
                return
            print 'cname %s result ################### now get list length is %d'%(cname,len(list))
            for l in list:
                aa = {}
                for k,v in l.items():
                    aa[k]=v
                self.save_success.append(spider.util.utf8str(aa))
                x = cname+"|"+l['oc_name']+"|"+str(l['oc_area'])+"|"+str(l['oc_code'])+"|"+str(l['oc_number'])
                self.part_success.append(x)

            print "-------------------------------------------cname %s page %d finish-----------------------------------"%(cname,now_page)
            rowcount = dic['rowcount']
            print "==============cname %s=======page %d=========rowcount %d==========="%(cname, now_page, rowcount)
            # page_count = rowcount/20 if rowcount%20==0 else (rowcount/20+1)
            # if now_page < page_count:
            #     now_page += 1
            #     self.flip_over(now_page,cname)
            # time.sleep(0.1)
            now_page += 1
            time.sleep(0.1)
            self.flip_over(now_page,cname)
            return
        else:
            print "cname %s #######################################UNKNOWN ERROR############################################# [ %d ]" % (cname,res.code)


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += '企业查询宝APP爬取已经停止...'
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

    def read_proxy(self,fn):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                m =  re.match(r'(\d+\.\d+\.\d+\.\d+:\d+)', line, re.I)
                if m:
                    prstr = m.group(1)
                    proxies = {'http': 'http://' + prstr+"/", 'https': 'https://' + prstr+"/"}
                    self.proxies_dict.append(proxies)
                elif re.match('\s*#', line):
                    continue
        print " loaded [ %d ] proxis " % len(self.proxies_dict)


if __name__ == "__main__":
    s = QycxbApp()
    #s.run_job({'cname':'深圳富士康科技集团'})
    s.run()
