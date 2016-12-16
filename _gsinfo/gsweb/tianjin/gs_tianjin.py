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

class SearchGSWebTianjin(SearchGSWeb):
    def __init__(self, saver):
        info = self.find_gsweb_searcher("天津")
        SearchGSWeb.__init__(self, info)
        #针对公司内部验证码服务　
        self.onl = OnlineOCR(info['pinyin'].lower()) #注意：陕西Shaanxi不适用
        self.onl.server = "http://192.168.1.94:3001/"
        #self.proxies = {'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'}
        #self.proxies = {}#{'http': 'http://ipin:helloipin@121.40.186.237:50001', 'https': 'https://ipin:helloipin@121.40.186.237:50001'}
        #self.proxies = {'http': 'http://ipin:helloipin@183.56.160.174:50001', 'https': 'https://ipin:helloipin@183.56.160.174:50001'}
        self.proxies = {'http': 'http://ipin:helloipin@106.75.134.190:18889', 'https': 'https://ipin:helloipin@106.75.134.190:18889'}
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
        url = "http://tjcredit.gov.cn/platform/saic/search.ftl"
        headers = {'Referer': url,
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
            #matchCondition=1&searchContent=%E5%A4%A9%E6%B4%A5%E7%A7%91%E6%8A%80&vcode=6
            data = {"matchCondition": "1", "searchContent": kw, "vcode": code}
            con = self.request_url(url, data=data, headers=headers)
            if con is None or con.code != 200:
                print kw, "search company res is None" if con is None else " search company  res.code = %d" % con.code
                time.sleep(random.randrange(1, 5, 1))
                continue
            if u"您查询的信息多于 0 条记录" in con.text:
                print kw, " search company result is none ...查询无结果 "
                return []
            if u"验证码错误" in con.text:
                print code, "search company 验证码错误...重试..."
                time.sleep(0.2)
                check_code_retry += 1
                continue

            try:
                dom = html.fromstring(con.text)
                lst = dom.xpath("//div[@class='result-item']")
                if len(lst) == 0:
                    check_code_retry += 1
                    time.sleep(random.randrange(1, 5, 1))
                    if check_code_retry > 5:
                        #return None
                        return []
                    continue
                else:
                    text = con.text
                    break
            except Exception as e:
                print e, "search_company html.fromstring error .text=\n", con.text
                return None

        out = []
        for l in lst:
            a = l.xpath("div/a")
            href = a[0].attrib['href']
            m = re.search("/platform/saic/viewBase\.ftl\?entId=(.*)", href)
            entId = None
            if m:
                entId = m.group(1)
                span = l.xpath("div[@class='result-detail']/span[@class='font-color value']")
                if len(span) == 0:
                    print "获取span失败..."
                    return None
                registID = span[0].text_content().strip()
                legal = span[1].text_content().strip()
                registOrg = span[0].text_content().strip()
                estbDate = span[0].text_content().strip()
                oi = {"entId":entId, "registID": registID, "legal": legal, "registOrg": registOrg, "estbDate": estbDate}
                out.append(oi)
                #self.get_detail(entId, registID)
            else:
                print kw, "没有获得到entId...href=", href
        print "get out######################:", len(out), spider.util.utf8str(out)
        return out


    def get_detail(self, entId, registID, retry=0):
        url_ref = "http://tjcredit.gov.cn/platform/saic/viewBase.ftl?entId="+entId
        url_dj = "http://tjcredit.gov.cn/platform/saic/baseInfo.json?entId="+entId+"&departmentId=scjgw&infoClassId=dj"
        url_ba = "http://tjcredit.gov.cn/platform/saic/baseInfo.json?entId=" + entId + "&departmentId=scjgw&infoClassId=ba"
        headers = {"X-Requested-With": "XMLHttpRequest", "Referer": url_ref}
        text_dj = self.req_detail(url_dj, headers=headers, registID=registID)
        text_ba = self.req_detail(url_ba, headers=headers, url_ba=registID)
        if text_dj is None or text_ba is None:
            print registID, "get_detail 基本信息　或　备案信息页面返回为空..."
            return False

        detail = {"basicInfo": {}, "investorInfo": [], "changesInfo": [], "staffsInfo": [], "branchInfo": []}
        doc = None
        try:
            doc = html.fromstring(text_dj)
        except Exception as e:
            print "get_detail basic page html.fromstring(text) ERROR:", e, "text:\n", text_dj
            return False

        doc2 = None
        if text_ba != u"":
            try:
                doc2 = html.fromstring(text_ba)
            except Exception as e:
                print "get_detail beian page html.fromstring(text) ERROR:", e, "text:\n", text_ba
                return False
        else:
            detail["staffsInfo"] = []
            detail["branchInfo"] = []

        #解析基本信息
        tables = doc.xpath("//table[@class='result-table']")
        if len(tables) == 0:
            print registID, "页面基本信息不存在..."
            return False

        for table in tables:
            tp = table.xpath("tr/td[@class='bg title']")[0].text_content()
            if u"基本信息" in tp:
                basic_info = self.parse_basic_info(table)
                # print "基本信息：", spider.util.utf8str(basic_info)
                detail["basicInfo"] = basic_info
            elif u"股东信息" in tp:
                trs = table.xpath("tbody[@id='table2']/tr")
                investor_info = self.parse_investor_info(trs, investor_type="tianjin")
                # print "股东信息：", spider.util.utf8str(investor_info)
                detail["investorInfo"] = investor_info
            elif u"变更信息" in tp:
                trs = table.xpath("tr")
                changes_info = self.parse_changes_info(trs, changes_type="tianjin")
                # print "变更信息：", spider.util.utf8str(changes_info)
                detail["changesInfo"] = changes_info

        if len(detail["basicInfo"]) == 0:
            print registID, "页面基本信息不存在..."
            return False
        self._do_savebin(registID, "basic", text_dj)

        if doc2 is not None:
            tables = doc2.xpath("//table[@class='result-table']")
            for table in tables:
                tp = table.xpath("tr/td[@class='bg title']|tr/th[@class='bg title']")[0].text_content()
                if u"主要人员信息" in tp:
                    trs = table.xpath("tr")
                    staffs_info = []
                    if len(trs) == 0 or len(trs) == 1:
                        print registID, 'parse_staffs_info unget tables...'
                    else:
                        staffs_info = self.parse_staffs_info(trs)
                        # print "主要人员信息：", spider.util.utf8str(staffs_info)
                    detail["staffsInfo"] = staffs_info
                elif u"分支机构信息" in tp:
                    trs = table.xpath("tr")
                    branch_info = []
                    if len(trs) == 0:
                        print registID, 'parse_branch_info unget tables...'
                    else:
                        branch_info = self.parse_branch_info(trs)
                        # print "分支机构信息：", spider.util.utf8str(branch_info)
                    detail["branchInfo"] = branch_info
                elif u"主管部门（出资人）信息" in tp:
                    if len(detail["investorInfo"]) == 0:
                        trs = table.xpath("tr")
                        investor_info = self.parse_investor_info(trs, investor_type="tianjin", theader=[u"序号", u"出资人类型", u"出资人", u"证照/证件类型", u"证照/证件号码"])
                        # print "股东信息：", spider.util.utf8str(investor_info)
                        detail["investorInfo"] = investor_info
            self._do_savebin(registID, "beian", text_ba)

        self.saver.fs.append(spider.util.utf8str(detail))
        print "获取到详情：", registID, spider.util.utf8str(detail)
        return True

    def req_detail(self, url, **kwargs):
        retry = 0
        while True:
            res = self.request_url(url, **kwargs)
            if res is None or res.code != 200:
                if retry < 10:
                    print kwargs['registID'] if "registID" in kwargs else "", "获得备案信息出错 ", "res is None " if res is None else "res.code = %d " % res.code
                    time.sleep(random.randrange(1, 8, 1))
                    retry += 1
                    continue
                else:
                    return None
            return res.text


    def parse_investor_build_url(self, tagA, **kwargs):
        """实现方法 --- 从a标签中提取生成特定的URL并进行访问,返回html文本"""
        #onclick="CheckDetail.getShareHolder('fb1950b153ee8a144238404eaeeab0d9','bfc7671853ee8a1e0a57680d152ac3e0')">
        #http://tjcredit.gov.cn/saicpf/gsgdcz?gdczid=fb1950b153ee8a144238404eaeeab0d9&entid=bfc7671853ee8a1e0a57680d152ac3e0&issaic=1&hasInfo=0
        ref = tagA.attrib.get("onclick", '')
        m = re.search("CheckDetail\.getShareHolder\('(\w+)','(\w+)'\)", ref)
        if m:
            gdczid = m.group(1)
            entId = m.group(2)
            url = "http://tjcredit.gov.cn/saicpf/gsgdcz?gdczid="+gdczid+"&entid="+entId+"&issaic=1&hasInfo=0"
            return self.req_detail(url)

################################################# RUN ########################################################

filter_kw = set()
filter_queries = set()

class RunTianjin(Spider):

    class Saver(object):
        def __init__(self):
            self.bs = BinSaver("gsinfo_Tianjin_html.bin")
            self.fs = FileSaver("gsinfo_tianjin.txt")
    """
    工商网站--天津
    """
    def __init__(self):
        spider.util.use_utf8()
        self.saver = RunTianjin.Saver()
        self.is_debug = True
        if self.is_debug:
            Spider.__init__(self, 100)
            # self.proxies_dict = [{'http': 'http://ipin:helloipin@106.75.134.189:18889',
            #                       'https': 'https://ipin:helloipin@106.75.134.189:18889'},
            #                      {'http': 'http://ipin:helloipin@106.75.134.190:18889',
            #                       'https': 'https://ipin:helloipin@106.75.134.190:18889'},
            #                      {'http': 'http://ipin:helloipin@106.75.134.191:18889',
            #                       'https': 'https://ipin:helloipin@106.75.134.191:18889'},
            #                      {'http': 'http://ipin:helloipin@106.75.134.192:18889',
            #                       'https': 'https://ipin:helloipin@106.75.134.192:18889'},
            #                      {'http': 'http://ipin:helloipin@106.75.134.193:18889',
            #                       'https': 'https://ipin:helloipin@106.75.134.193:18889'}]
            self.proxies_dict = [{'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'},
                                 {'http': 'http://ipin:helloipin@121.40.186.237:50001', 'https': 'https://ipin:helloipin@121.40.186.237:50001'}]
            #self.proxies_dict = [{}]
            self.gsweb = SearchGSWebTianjin(self.saver)
        else:
            self.proxies_dict = []
            self.read_proxy("../../_ct_proxy/proxy_040510.txt")
            Spider.__init__(self, len(self.proxies_dict))
            self._curltls = threading.local()
        self.gswebs = {}
        #已经查询成功的关键字
        self.success_kw = FileSaver("gsinfo_tianjin_success_kw.txt")
        #对于查到的列表信息,爬取成功就写入到这个文本,防止重复爬取
        self.success_queries = FileSaver("gsinfo_tianjin_success_queries.txt")
        #初始化已经爬过的链接
        self.init_spider_url()
        #time.sleep(2)
        self.cnt = 1
        self.run_time = time.time()
        self.cnt_q = 1


    def init_obj(self):
        threadident = str(threading.currentThread().ident)
        gsweb = SearchGSWebTianjin(self.saver)
        if not self.is_debug:
            gsweb.proxies = self.proxies_dict[self.get_tid()]
        else:
            num = self.get_tid() % len(self.proxies_dict)
            gsweb.proxies = self.proxies_dict[num]
        self.gswebs[threadident] = gsweb
        setattr(self._curltls, "gsweb", gsweb)
        return gsweb

    def init_spider_url(self):
        with open("gsinfo_tianjin_success_kw.txt", "r") as f:
            for url in f:
                filter_kw.add(url.strip())
            print "init already spidered commpany url finished !"

        with open("gsinfo_tianjin_success_queries.txt", "r") as f:
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
        with open("tianjin_cname.txt", "r") as f:
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
            if retry < 3:
                job["retry"] = retry + 1
                self.re_add_job(job)
            else:
                self.record_spider_kw(kw)
            return
        all = len(out)
        scs_cnt = 0
        for oi in out:
            #oi = {"entId":entId, "registID": registID, "legal": legal, "registOrg": registOrg, "estbDate": estbDate}
            entId = oi["entId"]
            registID = oi["registID"]
            if registID in filter_queries:
                print cnt, "任务执行 --- 查询详情 --- registID:", registID, "已经爬取过...", kw
                #如果已经爬取过了,略过
                all -= 1
                continue
            retry2 = 0
            while True:
                flag = gsweb.get_detail(entId, registID)
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

        #if time.time() - self.run_time > 60:
        interval = time.time() - self.run_time
        print "speed ------> ------> ------> ------> ------> ------>", self.cnt/interval, " t/s "
        #self.run_time = time.time()


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
            msg += "gsinfo_tianjin_run finished !"
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
    #gsweb = SearchGSWebTianjin(None)
    #gsweb.search_company("国药控股")
    #gsweb.get_detail("349CE9DDA8CC540DE04400306EF52828", "1111111")
    s = RunTianjin()
    s.run()
    #s.run_job({"kw": "国药控股", "retry": 0, "cnt": 888888})