#!/usr/bin/env python
# -*- coding:utf8 -*-
import sys
sys.path.append(sys.path[0]+"/..")
import spider.util
from _gsinfo.gsweb.gsconfig import ConfigData
from lxml import html
from _gsinfo.gsweb.gswebimg import SearchGSWeb
import time
from spider.spider import Spider, AccountErrors
import re
from spider.savebin import FileSaver, BinSaver
import spider.util
import threading
import random
import json
from spider.captcha.onlineocr import OnlineOCR
from urllib import quote


uas = ["baidu",
       "firefox",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.154 Safari/537.36 LBBROWSER",
       "=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
       "=Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36 Core/1.47.163.400 QQBrowser/9.3.7175.400",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"]

class SearchGSWebChongqing(SearchGSWeb):
    def __init__(self, saver):
        info = self.find_gsweb_searcher("重庆")
        SearchGSWeb.__init__(self, info)
        #针对公司内部验证码服务　
        self.onl = OnlineOCR(info['pinyin'].lower()) #注意：陕西Shaanxi不适用
        self.onl.server = "http://192.168.1.94:3001/"
        #self.proxies = {'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'}
        #self.proxies = {}#{'http': 'http://ipin:helloipin@121.40.186.237:50001', 'https': 'https://ipin:helloipin@121.40.186.237:50001'}
        #self.proxies = {'http': 'http://ipin:helloipin@183.56.160.174:50001', 'https': 'https://ipin:helloipin@183.56.160.174:50001'}
        self.proxies = {}#{'http': 'http://ipin:helloipin@106.75.134.189:18889', 'https': 'https://ipin:helloipin@106.75.134.189:18889'}
        self.saver = saver
        #self.ua = self.useragent_random()
        self.ua = uas[random.randrange(0, len(uas), 1)]
        self.select_user_agent(self.ua)

    def useragent_random(self):
        uas = []
        with open("../../_ct_proxy/UA.txt", "r") as f:
            for ua in f:
                ua = "="+ua
                uas.append(ua)
        result = uas[random.randrange(0, len(uas), 1)]
        return result

    def find_gsweb_searcher(self, name):
        for info in ConfigData.gsdata:
            if info["name"] == name:
                return info
            if info["pinyin"] == name:
                return info
        return None

    def request_url(self, url, **kwargs):
        if self.proxies is not None and len(self.proxies) != 0:
            try:
                kwargs.update({"proxies": self.proxies})
            except Exception as e:
                print e
        return super(SearchGSWeb, self).request_url(url, **kwargs)

    def _do_savebin(self, regist_code, content_type, text):
        """存入bin文件,key:注册号.类型.时间 , 由于一个公司详情有多个页面返回,用一个特定类型区分"""
        fn = '%s.%s.%d' % (regist_code, content_type, int(time.time()))
        self.saver.bs.append(fn, text)


    def search_company(self, kw):
        url = "http://gsxt.cqgs.gov.cn/search.action"
        headers = {'Referer': "http://gsxt.cqgs.gov.cn/",
                   "Content-Type": "application/x-www-form-urlencoded",
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        check_code_retry = 0
        text = None
        dom = None
        lst = None
        while True:
            check_code_retry += 1
            #TODO 用的公司内部验证码服务器　还不稳定
            dbgdata = {"type": "inner_server"}
            code = self.solve_image(dbgdata=dbgdata)
            data = {"key": kw, "code": code}
            con = self.request_url(url, data=data, headers=headers)
            if con is None or con.code != 200:
                print kw, "search company res is None" if con is None else " search company  res.code = %d" % con.code
                time.sleep(random.randrange(1, 5, 1))
                continue
            if u"您搜索的条件无查询结果" in con.text:
                print kw, " search company result is none ...查询无结果 "
                return []
            if u"验证码不正确" in con.text:
                print code, "search company 验证码错误...重试..."
                time.sleep(0.2)
                check_code_retry += 1
                continue

            try:
                dom = html.fromstring(con.text)
                lst = dom.xpath("//div[@id='result']/div[@class='item']")
                if len(lst) == 0:
                    check_code_retry += 1
                    time.sleep(random.randrange(1, 5, 1))
                    if check_code_retry > 7:
                        return None
                    continue
                else:
                    text = con.text
                    break
            except Exception as e:
                print e, "search_company html.fromstring error .text=\n", con.text
                return None

        out = []
        for l in lst:
            a = l.xpath("a")
            if len(a) != 0:
                oid = a[0].attrib['data-entid']  #信用代码
                registID = a[0].attrib['data-id']  #注册码
                cname = a[0].text_content().strip()  #公司名
                dtype = a[0].attrib['data-type']
                oi = {"oid": oid, "registID": registID, "cname": cname, "dtype": dtype}
                #self.get_detail(oid, registID, cname, dtype)
                out.append(oi)
            else:
                print kw, "查询公司　没有获得到字段..."
        print "get out######################:", len(out), spider.util.utf8str(out)
        return out


    def get_detail(self, oid, registID, cname, dtype, retry=0):

        url = "http://gsxt.cqgs.gov.cn/search_ent"
        data = {"id": registID, "type": dtype, "name": cname, "entId": oid}
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Referer": "http://gsxt.cqgs.gov.cn/search.action"}
        text1 = self.req_detail(url, data=data, headers=headers)
        dt = None
        try:
            dom = html.fromstring(text1)
            hl = dom.xpath("//html[@id='ng-app']")
            ng = hl[0].attrib['ng-init']
            #id='500000400017012';type='10';name='重庆顶津食品有限公司';entId='5009020000002706';seljyyl=false;selccjcinfo=false
            m = re.search("id='(.*)';type='(\w+)';name='(.*)';entId='(.*)';seljyyl=", ng)
            if m:
                dt = m.group(2)
            else:
                print "获取第二个链接使用的参数失败......."
        except Exception as e:
            print "获取第二个链接使用的参数出现异常．．．text:\n", text1
            return False


        url = "http://gsxt.cqgs.gov.cn/search_getEnt.action?_c"+str(int(time.time()*1000))+"=_c"+str(random.randrange(100000, 1000000, 1))+"&entId="+oid+"&id="+quote(registID.encode("utf-8"))+"&type="+quote(dtype[0:1] if dt is None else dt.encode("utf-8"))

        headers = {"X-Requested-With": "XMLHttpRequest", "Referer": "http://gsxt.cqgs.gov.cn/search_ent"}

        text = self.req_detail(url, headers=headers)
        if text == '{"code":-1}':
            print "系统暂时不可用  或　参数传递错误...", cname, url
            self.saver.fail.append(cname + "," +url)
            return True
        jtext = text[5:]
        detail = {}
        try:
            detail = json.loads(jtext)
        except Exception as e:
            print "******************************************响应文本转换出错，非json格式******************************************\n", text
            return False
        base = detail["base"]
        if len(base) == 0:
            print "该页面没有基本信息．．．", cname, registID, "text:\n", text
            return False
        self.saver.fs.append(spider.util.utf8str(detail))
        print "获取到详情：", cname, registID, spider.util.utf8str(detail)
        return True

    def req_detail(self, url, **kwargs):
        retry = 0
        while True:
            res = self.request_url(url, **kwargs)
            if res is None or res.code != 200:
                if retry < 10:
                    print kwargs['registID'] if "registID" in kwargs else "", "获取信息出错 ", "res is None " if res is None else "res.code = %d " % res.code
                    time.sleep(random.randrange(1, 8, 1))
                    retry += 1
                    continue
                else:
                    return None
            return res.text


################################################# RUN ########################################################

filter_kw = set()
filter_queries = set()

class RunChongqing(Spider):

    class Saver(object):
        def __init__(self):
            #self.bs = BinSaver("gsinfo_Chongqing_html.bin")
            self.fs = FileSaver("gsinfo_Chongqing.txt")
            self.fail = FileSaver("gsinfo_Chongqing_fail.txt")
    """
    工商网站--重庆
    """
    def __init__(self):
        spider.util.use_utf8()
        self.saver = RunChongqing.Saver()
        self.is_debug = True
        if self.is_debug:
            Spider.__init__(self, 100)
            self.proxies_dict = [#{'http': 'http://ipin:helloipin@106.75.134.189:18889', 'https': 'https://ipin:helloipin@106.75.134.189:18889'},
                                 {'http': 'http://ipin:helloipin@106.75.134.190:18889', 'https': 'https://ipin:helloipin@106.75.134.190:18889'},
                                 {'http': 'http://ipin:helloipin@106.75.134.191:18889', 'https': 'https://ipin:helloipin@106.75.134.191:18889'},
                                 {'http': 'http://ipin:helloipin@106.75.134.192:18889', 'https': 'https://ipin:helloipin@106.75.134.192:18889'},
                                 {'http': 'http://ipin:helloipin@106.75.134.193:18889', 'https': 'https://ipin:helloipin@106.75.134.193:18889'}]
            self.gsweb = SearchGSWebChongqing(self.saver)
        else:
            self.proxies_dict = []
            self.read_proxy("../../_ct_proxy/proxy_040510.txt")
            Spider.__init__(self, len(self.proxies_dict))
            self._curltls = threading.local()
        self.gswebs = {}
        #已经查询成功的关键字
        self.success_kw = FileSaver("gsinfo_Chongqing_success_kw.txt")
        #对于查到的列表信息,爬取成功就写入到这个文本,防止重复爬取
        self.success_queries = FileSaver("gsinfo_Chongqing_success_queries.txt")
        #初始化已经爬过的链接
        self.init_spider_url()
        #time.sleep(2)
        self.cnt = 1
        self.run_time = time.time()
        self.cnt_q = 1


    def init_obj(self):
        threadident = str(threading.currentThread().ident)
        gsweb = SearchGSWebChongqing(self.saver)
        if not self.is_debug:
            gsweb.proxies = self.proxies_dict[self.get_tid()]
        else:
            tid = self.get_tid()
            l = len(self.proxies_dict)
            num = tid % l
            gsweb.proxies =self.proxies_dict[num]
        self.gswebs[threadident] = gsweb
        setattr(self._curltls, "gsweb", gsweb)
        return gsweb

    def init_spider_url(self):
        with open("gsinfo_Chongqing_success_kw.txt", "r") as f:
            for url in f:
                filter_kw.add(url.strip())
            print "init already spidered commpany url finished !"

        with open("gsinfo_Chongqing_success_queries.txt", "r") as f:
            for name in f:
                filter_queries.add(name.strip())
            print "init already spidered commpany queries finished !"

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
        with open("chongqing_cname.txt", "r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                if line in filter_kw:
                    print cnt, "任务调度 --- line:", line, "已经爬取过..."
                    continue
                job = {"cnt": cnt, "retry": 0, "kw": line}
                self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)

    def record_spider_kw(self, kw):
        """
        记录已经爬过的关键字
        """
        filter_kw.add(kw)
        self.success_kw.append(kw)
        self.cnt += 1
        setattr(self._curltls, "failcnt", 0)

    def record_spider_queries(self, line):
        """记录已经爬取成功的查询列表某一条"""
        filter_queries.add(line)
        self.success_queries.append(line)
        self.cnt_q += 1
        setattr(self._curltls, "failcnt", 0)

    def run_job(self, job):
        gsweb = getattr(self._curltls, "gsweb", None)
        if gsweb is None:
            gsweb = self.init_obj()
        kw = job.get("kw")
        retry = job.get("retry")
        cnt = job.get("cnt")
        out = gsweb.search_company(kw)
        if out is None:
            self.job_retry(job)
            return
        if len(out) == 0:
            if retry < 1:
                job["retry"] = retry + 1
                self.re_add_job(job)
            else:
                self.record_spider_kw(kw)
            return
        all = len(out)
        scs_cnt = 0
        for oi in out:
            #oi = {"oid": oid, "registID": registID, "cname": cname, "dtype": dtype}
            oid = oi["oid"]
            registID = oi["registID"]
            cname = oi["cname"]
            dtype = oi["dtype"]
            if registID in filter_queries:
                print cnt, "任务执行 --- 查询详情 --- cname:", cname, "已经爬取过...", kw
                #如果已经爬取过了,略过
                all -= 1
                continue
            retry2 = 0
            while True:
                flag = gsweb.get_detail(oid, registID, cname, dtype)
                if flag:
                    self.record_spider_queries(registID)
                    scs_cnt += 1
                    break
                else:
                    retry2 += 1
                    if retry2 > 5:
                        break
                    else:
                        time.sleep(random.randrange(1, 5, 1))

        if scs_cnt == all:
            self.record_spider_kw(kw)
        else:
            self.job_retry(job)

        interval = time.time() - self.run_time
        print "speed ------> ------> ------> ------> ------> ------>", self.cnt/interval, " t/s "


    def job_retry(self, job):
        retry = job.get("retry")
        cnt = job.get("cnt")
        kw = job.get("kw")
        retry += 1
        print "第%d行 - 关键字:%s 将要重试第%d次 ... "%(cnt, kw, retry)
        job.update({"retry": retry})
        self.re_add_job(job)
        #self.get_fail_cnt(1)

    def get_fail_cnt(self, addv):
        fc = getattr(self._curltls, "failcnt", 0)
        if fc > 10:
            raise AccountErrors.NoAccountError("Maybe the proxy invalid,failcnt = [ 10 ]")
        else:
            if addv:
                fc += addv
                setattr(self._curltls, "failcnt", fc)
            #return fc

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "gsinfo_Chongqing_run finished !"
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

    def read_proxy(self, fn):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                self._match_proxy(line)
        self._can_use_proxy_num = len(self.proxies_dict)
        print " loaded [ %d ] proxis " % self._can_use_proxy_num

    def _match_proxy(self, line):
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

if __name__ == '__main__':
    spider.util.use_utf8()
    #gsweb = SearchGSWebChongqing(None)
    #gsweb.search_company("重庆科技")
    #gsweb.get_detail("5009020000002706", "500000400017012", "重庆顶津食品有限公司", "1001")
    s = RunChongqing()
    s.run()
    #s.run_job({"kw": "重庆鑫斌集团", "retry": 0, "cnt": 888888})