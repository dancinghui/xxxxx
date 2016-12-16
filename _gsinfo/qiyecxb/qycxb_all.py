#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
#sys.path.append(sys.path[0]+"/..")
sys.path.extend([sys.path[0]+"/../../", sys.path[0]+"/.."])
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

class QycxbApp(Spider):
    """
    根据企业名称 查询公司列表(可能多个,可能不存在) , 存在则根据每条数据内容查询详情detail,查询完详情再请求股东信息,跟详情拼接在一起存储到文件detail_company.txt
    """
    def __init__(self):
        self.proxies_dict = []
        self.read_proxy("proxy_20160218.txt")
        Spider.__init__(self, len(self.proxies_dict))

        self.num_count = 0
        #self.filter_name = []
        self._aes_ = CCIQ_AES()
        #根据公司名字查询到的公司列表全部信息
        self.query_company_info = FileSaver("query_company_info.txt")
        #根据公司名字查询到的公司列表局部信息
        self.query_company_info_part = FileSaver("query_company_info_part.txt")
        #根据公司名字查询到的公司列表信息失败的
        self.query_company_info_failure = FileSaver("query_company_info_failure.txt")
        #已经爬取过的公司名
        self.already_cname = FileSaver("already_cname.txt")
        #初始化已经爬过的公司
        self.init_cname()
        #查询详情失败的公司名
        self.detail_failure = FileSaver("detail_failure1.txt")
        #APP可以拿到的公司全部信息 包含股东信息
        self.detail_company = FileSaver("detail_company.txt")
        self.extJson = self._aes_.encrypt(spider.util.utf8str({"cl_screenSize": "640x960", "cl_cookieId": "16923697-D73E-485A-BDCF-68FAD456AC02", "Org_iOS_Version": "2.0.1"}))
        self.select_user_agent("=CCIQ/2.0.1 (iPhone; iOS 9.1; Scale/2.00)")

    def init_cname(self):
        with open("already_cname.txt","r") as f:
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
        with open("corp_name.txt","r") as f:
            cnt = 0
            while True:
                line = f.readline().strip()
                cnt+=1
                if line is None:
                    break
                if line in filter_name:
                    print line," already spider~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
                    continue
                job = {"line":line,"cnt":cnt,"retry":0}
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
        line = jobid.get("line")
        cnt = jobid.get("cnt")
        retry = jobid.get("retry")
        if line is None:
            print 'line = ',cnt,' is None ,break~'
            return
        ary = line.split(" ")
        if len(ary) == 4:
            cname = ary[3]
            flag = self.flip_over(1, cname, line, cnt, retry)
            #爬取结束,加入到set并写入文件
            if flag :
                filter_name.add(line)
                self.already_cname.append(line)
                print cnt,' execute perfect~~~~~~~~~~~~~~~~~~~~~~~'
        else:
            print '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ company data line is error @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@',cnt

    #根据公司名查询公司列表,翻页
    def flip_over(self , now_page , cname, line , cnt, retry):
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/combine/search"
        headers = {"Content-Type": "application/json"}
        encryptedJson = {"pagesize" : "20","page" : now_page,"od_orderBy" : "0","sh_searchType" : "一般搜索","od_statusFilter" : "0","v1" : "QZOrgV004","oc_name" : cname,"sh_u_uid" : "","sh_u_name" : ""}
        param = {"encryptedJson":self._aes_.encrypt(spider.util.utf8str(encryptedJson)), "extJson": self.extJson}
        param = spider.util.utf8str(param)
        res = self.request_url(url, headers=headers, data=param, proxies=self.proxies_dict[self.get_tid()])
        if res is None:
            if self.get_fail_cnt(1) < 10:
                print "%d-----%s ------ res is None" % (cnt,cname)
                self.add_job({'line':line,'cnt':cnt})
                return False
            else:
                print "id is [ %s ] thread and [ %s ] proxy will be close and drop." % (self.get_tid(),self.proxies_dict[self.get_tid()])
                #self.query_company_info_failure.append(line)
                self.add_job({'line':line,'cnt':cnt})
                raise AccountErrors.NoAccountError("Maybe the proxy[ %s ] invalid,failcount = [ %d ]" % (self.proxies_dict[self.get_tid()],self.get_fail_cnt(0)))

        elif res.code == 404 or res.code == 403:
            if self.get_fail_cnt(1) < 20:
                print "%d-----%s ------ %d" % (cnt,cname,res.code)
                self.add_job({'line':line,'cnt':cnt})
                return False
            else:
                print "id is [ %s ] thread and [ %s ] proxy will be close and drop." % (self.get_tid(),self.proxies_dict[self.get_tid()])
                self.add_job({'line':line,'cnt':cnt})
                raise AccountErrors.NoAccountError("Maybe the proxy[ %s ] invalid,failcount = [ %d ]" % (self.proxies_dict[self.get_tid()],self.get_fail_cnt(0)))

        elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
            print "%d------%s ------ %d " % (cnt,cname,res.code)
            self.add_job({'line':line,'cnt':cnt})
            time.sleep(1)
            return False
        elif res.code == 200:
            c = eval(res.text)['c']
            if len(c) == 0:
                print '-----------------------------cname %s res.text is null----------------------------'%cname
                self.query_company_info_failure.append(line)
                return True
            result = CCIQ_AES("BB1856A312580D41256311147089E0CC").decrypt(c)
            dic = eval(result)
            list = dic['list']
            if len(list) == 0:
                print 'cname %s result list length = 0 '%cname
                self.query_company_info_failure.append(line)
                return True
            print 'cname %s result ###################  list length ------ %d'%(cname,len(list))
            for l in list:
                aa = {}
                for k,v in l.items():
                    aa[k]=v
                self.query_company_info.append(spider.util.utf8str(aa))
                part = cname+"|"+l['oc_name']+"|"+str(l['oc_area'])+"|"+str(l['oc_code'])+"|"+str(l['oc_number'])
                self.query_company_info_part.append(part)
                self.get_detail(l['oc_name'], l['oc_code'], l['oc_area'])
            if len(list) < 20:
                return True
            elif len(list) == 20:
                now_page += 1
                self.flip_over(now_page,cname,line,cnt)
        else:
            print "cname %s #######################################UNKNOWN ERROR############################################# [ %d ]" % (cname,res.code)
            self.query_company_info_failure.append(line)
            return True


    #查询详细信息
    def get_detail(self, cname, code, area):
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/combine/detail"
        headers = {"Content-Type": "application/json"}
        encryptedJson = {
            "bl_oc_code" : code,  #"71526726X"
            "v1" : "QZOrgV004",
            "isDirect" : "1",
            "bl_oc_name" : cname,  #"腾讯科技"
            "bl_oc_area" : area #"4403"
        }

        param = {"encryptedJson":self._aes_.encrypt(spider.util.utf8str(encryptedJson)), "extJson": self.extJson}
        param = spider.util.utf8str(param)
        res = self.request_url(url, headers=headers, data=param, proxies=self.proxies_dict[self.get_tid()])

        if res is None:
            print 'res is none -- encryptedJson -->',str(encryptedJson)
            self.detail_failure.append(cname+"|"+str(code)+"|"+str(area))
            return
        elif res.code == 404:
            print "404 ------ ", code
            self.detail_failure.append(cname+"|"+str(code)+"|"+str(area))
            return
        elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
            print res.code,'------',code
            time.sleep(0.5)
            self.get_detail(cname,code,area)
            return
        elif res.code == 200:
            c = eval(res.text)['c']
            if len(c) == 0:
                print '-----------------------------code ', code, ' res.text is null----------------------------'
                self.detail_failure.append(cname+"|"+str(code)+"|"+str(area))
                return
            result = CCIQ_AES("BB1856A312580D41256311147089E0CC").decrypt(c)
            detail = eval(result)
            listGD = self.get_gd(area,code)
            if listGD is not None:
                detail['listGD'] = listGD['listGD']
            print 'detail=================================', spider.util.utf8str(detail)
            self.detail_company.append(spider.util.utf8str(detail))
            return
        else:
            print "cname %s #######################################UNKNOWN ERROR############################################# [ %d ]" % (cname,res.code)

    #获取股东信息
    def get_gd(self, area,code):
        url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/gd/detail"
        headers = {"Content-Type": "application/json"}

        encryptedJson = {
            "bl_oc_area" : area, #4107
            "v1" : "QZOrgV004",
            "bl_oc_code" : code #672867774
        }

        param = {"encryptedJson":self._aes_.encrypt(spider.util.utf8str(encryptedJson)), "extJson": self.extJson}
        param = spider.util.utf8str(param)
        res = self.request_url(url, headers=headers, data=param, proxies=self.proxies_dict[self.get_tid()])

        if res is None:
            print 'res is none -- search gd code is -->',code
            return None
        elif res.code == 404:
            print "404 ------ ",code
            return None
        elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
            print res.code, '------', code
            time.sleep(0.5)
            return self.get_gd(area, code)
        elif res.code == 200:
            c = eval(res.text)['c']
            if len(c) == 0:
                print '-----------------------------gd code', code, ' res.text is null----------------------------'%cname
                return None
            result = CCIQ_AES("BB1856A312580D41256311147089E0CC").decrypt(c)
            list_gd = eval(result)
            #print 'gd infos =======================',spider.util.utf8str(list_gd)
            return list_gd
        else:
            print code,"#######################################UNKNOWN ERROR#############################################", res.code
        return None



    def get_inversted(self,url, encryptedJson):
        """
        通用请求方法
        """

        param = spider.util.utf8str({"encryptedJson": self._aes_.encrypt(spider.util.utf8str(encryptedJson)), "extJson":self.extJson})

        res = self.request_url(url, headers={"Content-Type": "application/json"}, data=param, proxies=self.proxies_dict[self.get_tid()])

        if res is None:
            print 'res is none -- search gd code is -->',code
            return None
        elif res.code == 404:
            print "404 ------ ",code
            return None
        elif res.code == 503 or res.code == 500 or res.code == 502 or res.code == 504:
            print res.code, '------', code
            time.sleep(0.5)
            return self.get_gd(area, code)
        elif res.code == 200:
            c = eval(res.text)['c']
            if len(c) == 0:
                print '-----------------------------gd code', code, ' res.text is null----------------------------'%cname
                return None
            result = CCIQ_AES("BB1856A312580D41256311147089E0CC").decrypt(c)
            list_gd = eval(result)
            #print 'gd infos =======================',spider.util.utf8str(list_gd)
            return list_gd
        else:
            print code,"#######################################UNKNOWN ERROR#############################################", res.code
        return None


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += '企业查询宝APP[公司名]和[组织机构代码]爬取已经停止...'
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
