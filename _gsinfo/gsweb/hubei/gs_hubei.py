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

uas = ["baidu",
       "firefox",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.154 Safari/537.36 LBBROWSER",
       "=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
       "=Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36 Core/1.47.163.400 QQBrowser/9.3.7175.400",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"]

class SearchGSWebHubei(SearchGSWeb):
    def __init__(self, saver):
        info = self.find_gsweb_searcher("湖北")
        SearchGSWeb.__init__(self, info)
        self.proxies ={'http': 'http://ipin:helloipin@192.168.2.90:3428', 'https': 'https://ipin:helloipin@192.168.2.90:3428'}
        # {'http': 'http://ipin:helloipin@121.41.79.4:18889', 'https': 'https://ipin:helloipin@121.41.79.4:18889'}
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
        #headers = {'Referer': self.info['url']}
        headers = {'Referer': "http://xyjg.egs.gov.cn/ECPS_HB/search.jspx",
                   "Content-Type": "application/x-www-form-urlencoded"}

        data = {"entName": kw}
        lst = None
        check_code_retry = 0
        while True:
            check_code_retry += 1
            #TODO 验证码还没有买
            #self.solve_image()
            self.get_image()
            code = raw_input("请输入验证码:")
            print "验证码:", code
            data["checkNo"] = code
            con = self.request_url("http://xyjg.egs.gov.cn/ECPS_HB/searchList.jspx", data=data, headers=headers)
            if con is None:
                print kw, " queries response is none ...结果为None "
                return None
            if u"您搜索的条件无查询结果" in con.text:
                print kw, " queries result is none ...结果为[]"
                return []
            if u"验证码不正确或已失效" in con.text:
                print code, " 验证码错误...重试..."
                continue
            if u"原因：可能访问过于频繁或非正常访问" in con.text:
                print "request exception:可能访问过于频繁或非正常访问..."
                if check_code_retry >= 3:
                    print "IP被封了...即将结束本线程..."
                    return ["stop"]
                time.sleep(check_code_retry)
                continue
            dom = None
            try:
                dom = html.fromstring(con.text)
            except Exception as e:
                print e, "search_company html.fromstring error .text=\n", con.text
                return None
            lst = dom.xpath("//div[@class='list']/ul")
            if len(lst) == 0:
                return None
            else:
                break
        out = []
        for d in lst:
            url = "http://xyjg.egs.gov.cn" + d.xpath(".//a")[0].attrib['href']
            name = d.xpath(".//a")[0].text
            regcode = d.xpath(".//span")[0].text
            out.append({"name": name, "url": url, "regcode": regcode})
        print "get out#########################################################################################:", len(out), spider.util.utf8str(out)
        #TODO
        time.sleep(5)
        return out


    def parse_investor_build_url(self, tagA, **kwargs):
        """实现方法 --- 从a标签中提取生成特定的URL并进行访问,返回html文本"""
        ref = tagA.attrib.get("onclick", '')
        m = re.search("window\.open\('(.*)'\)", ref)
        if m:
            #url = "http://qyxy.baic.gov.cn"+m.group(1)
            on = m.group(1)
            url = "http://xyjg.egs.gov.cn" + on
            print "变更信息中的URL:", url
            error_retry = 0
            while True:
                res = self.request_url(url)
                if res is None or res.code != 200 or u"访问异常" in res.text:
                    print "parse_investor_build_url", "res is None..." if res is None else " res.code=%d,res.text=%s" % (res.code, res.text)
                    error_retry += 1
                    if error_retry > 5:
                        return None
                    time.sleep(error_retry*2)
                else:
                    return res.text


    def get_detail(self, url, name, regcode):
        detail = {}
        text = self.req_detail(url)
        doc = None
        try:
            doc = html.fromstring(text)
        except Exception as e:
            print "page html.fromstring(text) ERROR:", e, "text:\n", text
            return False
        self._do_savebin(regcode, "all", text)
        ############基本信息#############
        tables = doc.xpath("//div[@id='jibenxinxi']//table[@class='detailsList']")
        if tables is not None and len(tables) != 0:
            basic_info = []
            basic_info = self.parse_basic_info(tables[0])
            print "基本信息:", spider.util.utf8str(basic_info)
            detail["basicInfo"] = basic_info

        ############股东信息#############
        trs = doc.xpath("//div[@id='invDiv']/table[@class='detailsList']/tr")
        if trs is not None and len(trs) != 0:
            investors = self.parse_investor_info(trs, theader=[u"股东", u"证照/证件类型", u"证照/证件号码", u"股东类型", u"投资详情"])
            print "股东信息:", spider.util.utf8str(investors)
            detail["investorsInfo"] = investors

        ############变更信息#############
        trs = doc.xpath("//div[@id='altDiv']/table[@id='altTab']/tr")
        if trs is not None and len(trs) != 0:
            changes = self.parse_changes_info(trs)
            print "变更信息:", spider.util.utf8str(changes)
            detail["changesInfo"] = changes

        ############主要人员信息##############
        trs = doc.xpath("//div[@id='memDiv']/table[@class='detailsList']/tr")
        if trs is not None and len(trs) != 0:
            staffs = self.parse_staffs_info(trs)
            print "主要人员信息:", spider.util.utf8str(staffs)
            detail["staffsInfo"] = staffs

        ############分支机构信息#############
        trs = doc.xpath("//div[@id='childDiv']/table[@class='detailsList']/tr")
        if trs is not None and len(trs) != 0:
            branchInfo = self.parse_branch_info(trs)
            print "分支机构信息:", spider.util.utf8str(branchInfo)
            detail["branchInfo"] = branchInfo

        print name, " 获取到信息:", spider.util.utf8str(detail)
        self.saver.fs.append(spider.util.utf8str(detail))
        return True

    def req_detail(self, url, **kwargs):
        retry = 0
        while True:
            res = self.request_url(url, **kwargs)
            if res is None or res.code != 200:
                if retry < 5:
                    print "res is None" if res is None else "res.code=%d" % res.code, url
                    continue
                else:
                    return None
            return res.text

################################################# RUN ########################################################

filter_kw = set()
filter_queries = set()

class RunHubei(Spider):

    class Saver(object):
        def __init__(self):
            self.bs = BinSaver("gsinfo_Hubei_html.bin")
            self.fs = FileSaver("gsinfo_hubei.txt")
    """
    工商网站--湖北
    """
    def __init__(self):
        spider.util.use_utf8()
        self.saver = RunHubei.Saver()
        self.is_debug = True
        if self.is_debug:
            Spider.__init__(self, 1)
            self.gsweb = SearchGSWebHubei(self.saver)
        else:
            self.proxies_dict = []
            self.read_proxy("../../_ct_proxy/proxy_040510.txt")
            Spider.__init__(self, len(self.proxies_dict))
            self._curltls = threading.local()
        self.gswebs = {}
        #已经查询成功的关键字
        self.success_kw = FileSaver("gsinfo_hubei_success_kw.txt")
        #对于查到的列表信息,爬取成功就写入到这个文本,防止重复爬取
        self.success_queries = FileSaver("gsinfo_hubei_success_queries.txt")
        #初始化已经爬过的链接
        self.init_spider_url()
        #time.sleep(2)
        self.cnt = 1
        self.run_time = time.time()
        self.cnt_q = 1


    def init_obj(self):
        threadident = str(threading.currentThread().ident)
        gsweb = SearchGSWebHubei(self.saver)
        if not self.is_debug:
            gsweb.proxies = self.proxies_dict[self.get_tid()]
        self.gswebs[threadident] = gsweb
        setattr(self._curltls, "gsweb", gsweb)
        return gsweb

    def init_spider_url(self):
        with open("gsinfo_hubei_success_kw.txt", "r") as f:
            for url in f:
                filter_kw.add(url.strip())
            print "init already spidered commpany url finished !"

        with open("gsinfo_hubei_success_queries.txt", "r") as f:
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
        with open("hubei_cname.txt", "r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                if line in filter_kw:
                    print cnt, line, " --->kw already spider!!!"
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
        gsweb = self.init_obj()
        kw = job.get("kw")
        retry = job.get("retry")
        cnt = job.get("cnt")
        out = gsweb.search_company(kw)
        if out is None:
            self.job_retry(job)
            return
        if len(out) != 0 and out[0] == "stop":
            self.job_retry(job)
            raise AccountErrors.NoAccountError("The proxy invalid , IP stop !!!")
        all = len(out)
        scs_cnt = 0
        for oi in out:
            cname = oi["name"]
            url = oi["url"]
            regcode = oi["regcode"]
            s = cname+","+str(regcode)
            if s in filter_queries:
                #如果已经爬取过了,略过
                all -= 1
                continue
            retry2 = 0
            while True:
                flag = gsweb.get_detail(url, cname, regcode)
                if flag:
                    self.record_spider_queries(s)
                    scs_cnt += 1
                    break
                else:
                    #self.get_fail_cnt(1)
                    retry2 += 1
                    if retry2 > 5:
                        break
                    else:
                        time.sleep(random.randrange(3, 8, 1))

        if scs_cnt == all:
            self.record_spider_kw(kw)
        else:
            self.job_retry(job)

        if time.time() - self.run_time > 20:
            print "speed------> ------> ------> ------> ------> ------>", self.cnt/(time.time() - self.run_time), "t/s"
            self.run_time = time.time()
            self.cnt = 1


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
            msg += "gsinfo_hubei_run finished !"
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
    #gsweb = SearchGSWebHubei(None)
    #gsweb.search_company("湖北科技")
    #gsweb.get_detail("http://xyjg.egs.gov.cn/ECPS_HB/businessPublicity.jspx?id=FC54DB58B86D17839BE260FC4CE9FD9A", "", "")
    s = RunHubei()
    #s.run()
    s.run_job({"kw": "湖北科技", "cnt": 0, "retry": 0})