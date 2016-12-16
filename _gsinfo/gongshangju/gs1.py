#!/usr/bin/env python
# -*- coding:utf8 -*-
import json, os, sys
import time, datetime, random
import re
import spider.util
from spider.spider import Spider
from spider.savebin import BinSaver
from spider.httpreq import SessionRequests
import hashlib

mongo_db_url = "mongodb://page_store:page_store@hadoop3/page_store"
# page_store_client = pymongo.MongoClient(mongo_db_url)
saved_count = 0

area_data = [[100000, "国家工商行政管理总局"], [110000, "北京"], [120000, "天津"], [130000, "河北"], [140000, "山西"], [150000, "内蒙古"],
             [210000, "辽宁"], [220000, "吉林"], [230000, "黑龙江"], [310000, "上海"], [320000, "江苏"], [330000, "浙江"],
             [340000, "安徽"], [350000, "福建"], [360000, "江西"], [370000, "山东"], [440000, "广东"], [450000, "广西"],
             [460000, "海南"], [410000, "河南"], [420000, "湖北"], [430000, "湖南"], [500000, "重庆"], [510000, "四川"],
             [520000, "贵州"], [530000, "云南"], [540000, "西藏"], [610000, "陕西"], [620000, "甘肃"], [630000, "青海"],
             [640000, "宁夏"], [650000, "新疆"]]


class HttpError(Exception):
    pass


class BadGatewayError(HttpError):
    pass


class NotFoundError(HttpError):
    pass


class ConnectFailError(HttpError):
    pass


class RequestError(HttpError):
    pass


class GSSPider(Spider):
    def __init__(self, tc):
        Spider.__init__(self, tc)
        self._logport = 5556
        # self.channel = 'gsid'
        # self.job_queue = 'gsid'
        self.savebin = BinSaver("gongshang.bin")
        self.faillog = open("fail_list.txt", "w+b")

    def loadhans(self, fn):
        c = ''
        with open(fn) as f:
            c = f.read().decode('utf-8')
        all = {}
        for i in c:
            if ord(i) > 0x400:
                all[i] = 1
        cc = all.keys()
        if len(cc) == 0:
            raise RuntimeError("no hans loaded")
        # print json.dumps(cc, ensure_ascii=False).encode('utf-8')
        return cc

    def query_summary(self, areacode, qword, page=1):
        # hashStr = hashlib.md5(str(time.time())).hexdigest()
        # print hashStr
        # CookieStr = hashStr[0:8]+"-"+hashStr[9:13]+"-"+hashStr[14:18]+"-"+hashStr[19:23]+"-"+hashStr[24:32]
        # print "COOKIE:%s" % CookieStr
        CookieStr = "E1F3418D-BDC7-468D-9F43-6EA13A642356"

        headers = {'User-Agent': 'Mozilla/5.0 (iPhone;8.0.2;iPhone;iPhone);Version/1.1;ISN_GSXT', "Cookie": CookieStr}
        data = {'AreaCode': areacode, 'Limit': 50, 'Page': page, 'Q': qword}
        # print data
        con = self.request_url('https://120.52.121.75:8443/QuerySummary', headers=headers, data=data, verify=False)
        # try:
        if con is None:
            Log.error("query %s, connect failed! " % qword)
            raise ConnectFailError("query %s, connect failed! " % qword)
        if "502 Bad Gateway" in con.text:
            Log.error("query %s, 502! " % qword)
            raise BadGatewayError("query %s, 502! " % qword)
        j = json.loads(con.text)
        if j.get('ERRCODE') == '0':
            rs = j["RESULT"]
            if len(rs) is 0:
                Log.error("query %s, no data!" % qword)
            return rs
        else:
            Log.error("query %s, request error! Response: %s" % (qword, j))
            raise RequestError("query %s, request error! " % qword)
            # except Exception as e:
            #     print e
            #     return None

    def query_info(self, areacode, regNo, page=1):
        CookieStr = "E1F3418D-BDC7-468D-9F43-6EA13A642356"

        headers = {'User-Agent': 'Mozilla/5.0 (iPhone;8.0.2;iPhone;iPhone);Version/1.1;ISN_GSXT', "Cookie": CookieStr}
        data = {'AreaCode': areacode, 'Limit': 50, 'Page': page, 'Q': regNo, 'EndNo': regNo}
        # print data
        con = self.request_url('https://120.52.121.75:8443/QuerySummary', headers=headers, data=data, verify=False)
        # try:
        if con is None:
            Log.error("query %s, connect failed! " % regNo)
            raise ConnectFailError("query %s, connect failed! " % regNo)
        if "502 Bad Gateway" in con.text:
            Log.error("query %s, 502! " % regNo)
            raise BadGatewayError("query %s, 502! " % regNo)
        j = json.loads(con.text)
        if j.get('ERRCODE') == '0':
            rs = j["RESULT"]
            if len(rs) is 0:
                Log.error("query %s, no data!" % regNo)
            return rs
        else:
            Log.error("query %s, request error! Response: %s" % (regNo, j))
            raise RequestError("query %s, request error! " % regNo)

    def save_qs(self, qs, qid, areacode, qw):
        for t in qs:
            print json.dumps(t, ensure_ascii=0, indent=4).encode('utf-8')
            t['qinfo'] = {'qid': qid, 'areacode': areacode, 'qw': qw}
            # self.col.update({'REGNO':t['REGNO'], 'ENTNAME':t['ENTNAME']}, t, True)

    def dispatch_hans1(self):
        self.hans = self.loadhans('hans')
        for i in self.hans:
            for k in area_data:
                # self.job_queue.put({'qw':i, 'areacode':k[0], 'tp':'w'})
                pass

    def dispatch(self):
        with open("r1k.txt", 'r') as f:
            for lines in f:
                m = re.match(u'\d+\s+(\d+)\s+(.*)', lines)
                if m:
                    code = int(m.group(1))
                    l = m.group(2)
                    if code == 0:
                        for k in area_data:
                            self.add_main_job({'qw': l, 'areacode': k[0], 'tp': 'w'})
                    else:
                        self.add_main_job({'qw': l, 'areacode': code, 'tp': 'w'})

        self.wait_q()
        self.job_queue.put(None)

    def run_job(self, job):
        self.faillog.write("%s failed.\n" % job)
        if isinstance(job, dict):
            tp = job.get('tp')
            areacode = job.get('areacode')
            qid = -1
            if tp == 'w':
                qw = job['qw']
            if tp == 'w2':
                qid = job.get('qid')
                xxx = qid / len(self.hans)
                yyy = qid % len(self.hans)
                if xxx >= yyy:
                    return True
                qw = self.hans[xxx] + self.hans[yyy]

            if tp == 'w' or tp == 'w2':
                page = job.get('page', 1)
                print qw, areacode, page
                # self.savebin.append(qw)
                try:
                    qs = self.query_summary(areacode, qw, page)
                except HttpError:
                    readd_count = job.get("readd_count", "0").strip()
                    if int(readd_count) < 10:
                        job["readd_count"] = str(int(readd_count) + 1)
                        Log.warning("readd job %s" % qw)
                        self.re_add_job(job)
                    else:
                        Log.error("job %s has run 30 times. " % qw)
                        self.faillog.write("%s failed.\n" % job)
                    time.sleep(1)
                    return
                self.savebin.append(qw, qs.__str__())
                Log.warning("%s saved" % qw)
            time.sleep(1)


def update_curproxy():
    try:
        mt = int(os.stat('curproxy').st_mtime)
    except Exception as e:
        mt = 0
    dftime = int(time.time()) - mt
    if dftime > 3600 * 12:
        os.system("chkproxy ../getjd/spider/proxy/proxy.txt  > curproxy ")
        os.system("chkproxy ../getjd/spider/proxy/curproxy  >> curproxy ")
        os.system("chkproxy ../getjd/spider/proxy/curproxy1  >> curproxy ")


if __name__ == '__main__':
    # # update_curproxy()
    # gs = GSSPider(10)
    # gs.load_proxy('../_zhilian/curproxy', force=True)
    # gs.run()
    # spider = SessionRequests()
    # data = {'AreaCode':"110000","EntId":"548F8EC2B0D74F728E8B8FFF00D28AD7","EntNo":"110105008154209","Info":"All",
    #         'Limit':50, 'Page':1, 'Q':"110105008154209"}
    # # data = {"AreaCode":"110000", "Limit":50, "Page":1, "Q":"110105008154209"}
    # headers = {'User-Agent':'Mozilla/5.0 (iPhone;8.4;iPhone;iPhone);Version/1.1;ISN_GSXT', "Cookie":r"64A14BDD-2228-40E8-BA0E-C0FBFE35ECD4",
    #            'Host':'120.52.121.75:8443', 'Connection':'keep-alive','Proxy-Connection':'keep-alive',
    #            'Accept-Language':"zh-Hans;q=1"}
    # con = spider.request_url('https://120.52.121.75:8443/QueryGSInfo', headers=headers, data=data, verify=False)
    # print con.text
    spider.util.use_utf8()
    f = open("/home/peiyuan/r1.txt","r+b")
    line = "1000000 110000 ibm 北京 no data."
    key = re.search(r"\d+ \d+ (.*) no data.", line).group(1)
    print line.replace("no data.", "").strip()
    c = key.strip()
    c = c.decode("utf-8")
    all = []
    for i in c:
        if i == "(" or i == ")":
            all.append(i)
        else:
            if ord(i) > 0x400:
                all.append(i)
    # cc = all.keys()
    # if len(cc) == 0:
    #     raise RuntimeError("no hans loaded")
    #     # print json.dumps(cc, ensure_ascii=False).encode('utf-8')
    str = "".join(all)
    print str
