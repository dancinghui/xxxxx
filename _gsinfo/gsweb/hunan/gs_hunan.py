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
       #"=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",
       #"=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.154 Safari/537.36 LBBROWSER",
       #"=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
       #"=Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1",
       #"=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36 Core/1.47.163.400 QQBrowser/9.3.7175.400",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"]

class SearchGSWebHunan(SearchGSWeb):
    def __init__(self, saver):
        info = self.find_gsweb_searcher("湖南")
        SearchGSWeb.__init__(self, info)
        self.proxies = {}#{'http': 'http://ipin:helloipin@106.75.134.192:18889', 'https': 'https://ipin:helloipin@106.75.134.192:18889'}
        # {'http': 'http://ipin:helloipin@121.41.79.4:18889', 'https': 'https://ipin:helloipin@121.41.79.4:18889'}
        self.saver = saver
        #self.ua = self.useragent_random()
        self.ua = uas[random.randrange(0, len(uas), 1)]
        self.select_user_agent(self.ua)

        self._proxy_error = threading.local()

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

    def count_proxy_error(self, error_type):
        cnt = getattr(self._proxy_error, "proxy_error_cnt", 0)
        if error_type:
            setattr(self._proxy_error, "proxy_error_cnt", 0)
        else:
            if cnt > 10:
                raise AccountErrors.NoAccountError("THE PROXY IS INVALID ! ! !")
            else:
                setattr(self._proxy_error, "proxy_error_cnt", (cnt+1))

    def request_url(self, url, **kwargs):
        if self.proxies is not None and len(self.proxies) != 0:
            try:
                kwargs.update({"proxies": self.proxies})
            except Exception as e:
                print "SearchGSWebHunan request_url Exception:", e
        return super(SearchGSWeb, self).request_url(url, **kwargs)

    def _do_savebin(self, regist_code, content_type, text):
        """存入bin文件,key:注册号.类型.时间 , 由于一个公司详情有多个页面返回,用一个特定类型区分"""
        fn = '%s.%s.%d' % (regist_code, content_type, int(time.time()))
        self.saver.bs.append(fn, text)


    # def check_captcha(self, token):
    #     headers={'Referer': self.info['url']}
    #     while True:
    #         self.code = self.solve_image()
    #         mm = self.request_url("http://gsxt.hnaic.gov.cn/notice/security/verify_captcha",
    #                      data = {"captcha": self.code, "session.token": token}, headers=headers)
    #         print "code=", self.code, "result=", mm.text
    #         if mm.text == 0:
    #             continue
    #         elif mm.text == 1:
    #             return True
    #     raise RuntimeError("failed")


    def search_company(self, kw):
        token = None
        while True:
            if self._con:
                #m = re.search('name: "session.token",code: "(.*?)",data:', self._con.text)
                m = re.search('"session.token": "(.*)"', self._con.text)
                if m:
                    token = m.group(1)
            if token is None:
                self.reset()
            else:
                #print "token = ", token
                break
        #self.get_image()
        #self.code = raw_input("请输入验证码:")
        #print "验证码:", self.code
        headers = {'Referer': self.info['url']}
        infourl = "http://gsxt.hnaic.gov.cn/notice/search/ent_info_list" #self.code
        pageNo = 1
        captcha = random.randrange(-10, 82, 1)
        out = []
        names = ""
        while True:
            #print "翻页,第", pageNo, "页,验证码:", captcha
            si = self.request_url(infourl, data={"captcha": captcha, "condition.insType": "", "condition.keyword": kw,  "condition.pageNo":pageNo, "session.token": token}, headers=headers)
            if si is None or si.code != 200:
                return None
            try:
                dom = html.fromstring(si.text, infourl)
                list_item = dom.xpath("//div[@class='list-item']")
                if u"出错了" in si.text:
                    print "查询条件出错:", kw
                    return ["drop"]
                if u"您搜索的条件无查询结果" not in si.text and len(list_item) == 0:
                    #-->既每页显示无结果,list又为0,则返回的页面错误,需要重试
                    if len(out) == 0:
                        return None
                    return out
                if u"您搜索的条件无查询结果" in si.text:
                    #-->查询确实无结果
                    return out
                temp_names = ""
                temp_out = []
                for d in list_item:
                    a1 = d.xpath(".//a")[0]
                    s1 = d.xpath(".//span")[0]
                    temp_names += a1.text_content()
                    oi = {"name": a1.text_content(),
                          "url": a1.attrib['href'],
                          "regcode": s1.text_content()}
                    self.get_detail(oi["url"], oi["name"], oi["regcode"])
                    temp_out.append(oi)
                if names != "" and temp_names == names:
                    return out
                out += temp_out
                if len(out) != 0 and len(out) % 10 == 0:
                    pageNo += 1
                    print "翻页查询:", pageNo, kw
                    names = temp_names
                else:
                    print "------------->", kw, "本次获得", len(out), "条结果:", spider.util.utf8str(out)
                    return out
            except Exception as e:
                print "查询公司名错误:", e, "文本如下:\n", si.text
                return None
        return None


    def parse_investor_build_url(self, tagA, **kwargs):
        """实现方法 --- 从a标签中提取生成特定的URL并进行访问,返回html文本"""
        ref = tagA.attrib.get("href", '')
        error_retry = 0
        while True:
            res = self.request_url(ref)
            if res is None or res.code != 200 or u"访问异常" in res.text:
                print "parse_investor_build_url", "res is None..." if res is None else " res.code=%d,res.text=%s" % (
                res.code, res.text)
                error_retry += 1
                if error_retry > 5:
                    return None
                time.sleep(error_retry * 2)
            else:
                return res.text

        #m = re.search("window\.open\('(.*)'\)", ref)
        # if m:
        #     #url = "http://qyxy.baic.gov.cn"+m.group(1)
        #     on = m.group(1)
        #     url = "http://xyjg.egs.gov.cn" + on
        #     print "变更信息中的URL:", url
        #     error_retry = 0
        #     while True:
        #         res = self.request_url(url)
        #         if res is None or res.code != 200 or u"访问异常" in res.text:
        #             print "parse_investor_build_url", "res is None..." if res is None else " res.code=%d,res.text=%s" % (res.code, res.text)
        #             error_retry += 1
        #             if error_retry > 5:
        #                 return None
        #             time.sleep(error_retry*2)
        #         else:
        #             return res.text


    def get_detail(self, url, name, regcode):
        detail = {}
        text = self.req_detail(url)
        # text = None
        # with open("reginster.html", 'rb') as f:
        #     text = f.read()
        doc = None
        try:
            doc = html.fromstring(text)
        except Exception as e:
            print "page html.fromstring(text) ERROR:", e, "text:\n", text
            return False
        self._do_savebin(regcode, "all", text)
        ###########基本信息#############
        tables = doc.xpath("//table[@class='info m-bottom m-top']")
        basic_info = {}
        if tables is not None and len(tables) != 0:
            for table in tables:
                ths = table.xpath("tr/th")
                if len(ths) > 0 and ths[0].text.strip() == u"基本信息":
                    basic_info = self.parse_basic_info(table)
                    break
                # else:
                #     print "解析不到基本信息...", url
            if len(basic_info) == 0:
                print name, "未获取到基本信息...", url
                return False
            #print "基本信息:", spider.util.utf8str(basic_info)
            detail["basicInfo"] = basic_info

        ###########股东信息#############
        trs = doc.xpath("//table[@id='investorTable']/tr")
        if trs is not None and len(trs) != 0:
            investors = self.parse_investor_info(trs, investor_type="hunan")
            #print "股东信息:", spider.util.utf8str(investors)
            detail["investorsInfo"] = investors

        ############变更信息#############
        trs = doc.xpath("//table[@id='alterTable']/tr")
        if trs is not None and len(trs) != 0:
            changes = self.parse_changes_info(trs)
            #print "变更信息:", spider.util.utf8str(changes)
            detail["changesInfo"] = changes

        ############主要人员信息##############
        trs = doc.xpath("//table[@id='memberTable']/tr")
        if trs is not None and len(trs) != 0:
            staffs = self.parse_staffs_info(trs)
            #print "主要人员信息:", spider.util.utf8str(staffs)
            detail["staffsInfo"] = staffs

        ############分支机构信息#############
        trs = doc.xpath("//table[@id='branchTable']/tr")
        if trs is not None and len(trs) != 0:
            branchInfo = self.parse_branch_info(trs)
            #print "分支机构信息:", spider.util.utf8str(branchInfo)
            detail["branchInfo"] = branchInfo

        if len(detail) == 0:
            print name, "未能获取到详情..."
            return False
        print "获取详情######:", name, spider.util.utf8str(detail)
        self.saver.fs.append(spider.util.utf8str(detail))
        return True

    def req_detail(self, url, **kwargs):
        retry = 0
        while True:
            res = self.request_url(url, **kwargs)
            if res is None or res.code != 200:
                if retry < 5:
                    print "res is None" if res is None else "res.code=%d" % res.code, url
                    time.sleep(random.randrange(3, 10, 1))
                    continue
                else:
                    return None
            return res.text

################################################# RUN ########################################################

filter_kw = set()
filter_queries = set()

class RunHunan(Spider):

    class Saver(object):
        def __init__(self):
            self.bs = BinSaver("gsinfo_Hunan_html.bin")
            self.fs = FileSaver("gsinfo_hunan.txt")
    """
    工商网站--湖南
    """
    def __init__(self):
        spider.util.use_utf8()
        self.saver = RunHunan.Saver()
        self.is_debug = True
        if self.is_debug:
            Spider.__init__(self, 1)
            self.gsweb = SearchGSWebHunan(self.saver)
        else:
            self.proxies_dict = []
            self.read_proxy("../../_ct_proxy/proxy_041412.txt")
            Spider.__init__(self, len(self.proxies_dict))
            self._curltls = threading.local()
        self.gswebs = {}
        #已经查询成功的关键字
        self.success_kw = FileSaver("gsinfo_hunan_success_kw.txt")
        #对于查到的列表信息,爬取成功就写入到这个文本,防止重复爬取
        self.success_queries = FileSaver("gsinfo_hunan_success_queries.txt")
        #初始化已经爬过的链接
        self.init_spider_url()
        #time.sleep(2)
        self.cnt = 0
        self.run_time = time.time()
        self.cnt_q = 0


    def init_obj(self):
        threadident = str(threading.currentThread().ident)
        gsweb = SearchGSWebHunan(self.saver)
        if not self.is_debug:
            gsweb.proxies = self.proxies_dict[self.get_tid()]
        self.gswebs[threadident] = gsweb
        setattr(self._curltls, "gsweb", gsweb)
        return gsweb

    def init_spider_url(self):
        i = 0
        with open("gsinfo_hunan_success_kw.txt", "r") as f:
            for url in f:
                i += 1
                filter_kw.add(url.strip())
            print "init already spidered commpany url finished !", i
        j = 0
        with open("gsinfo_hunan_success_queries.txt", "r") as f:
            for name in f:
                j += 1
                filter_queries.add(name.strip().decode("utf-8"))
            print "init already spidered commpany queries finished !", j

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
        with open("../_ct_inc_name/hunan_cname.txt", "r") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                cnt += 1
                if line in filter_kw:
                    #print cnt, line, " --->kw already spider!!!"
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
        #kw = "湖南蚁坊"
        out = gsweb.search_company(kw)
        if out is None:
            self.job_retry(job)
            return
        if len(out) != 0 and out[0] == "drop":
            self.record_spider_kw(kw)
            return
            #self.job_retry(job)
            #raise AccountErrors.NoAccountError("The proxy invalid , IP stop !!!")
        all = len(out)
        scs_cnt = 0
        for oi in out:
            cname = oi["name"]
            url = oi["url"]
            regcode = oi["regcode"]
            s = cname+","+str(regcode)
            if s in filter_queries:
                print "查询结果:", s, "已经爬过...忽略..."
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
                    self.get_fail_cnt(1)
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
            print "query speed------> ------> ------> ------> ------> ------>", self.cnt/(time.time() - self.run_time), "t/s"
            print "detail speed------> ------> ------> ------> ------> ------>", self.cnt_q / (time.time() - self.run_time), "t/s"
            self.run_time = time.time()
            self.cnt = 0
            self.cnt_q = 0


    def job_retry(self, job):
        retry = job.get("retry")
        cnt = job.get("cnt")
        kw = job.get("kw")
        retry += 1
        print "第%d行 - 关键字:%s 将第%d次重新加入任务队列 ... "%(cnt, kw, retry)
        job.update({"retry": retry})
        self.re_add_job(job)
        self.get_fail_cnt(1)

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
    gsweb = SearchGSWebHunan(RunHunan.Saver())
    gsweb.search_company("蓝思科技")
    #gsweb.get_detail("http://gsxt.hnaic.gov.cn/notice/notice/view?uuid=Qs91JOPG82WqlvzgXkDOe6m7ZseNt3Gt&tab=01", "郴州天甲保理创新基金企业(有限合伙)", "91431000329420270H")
    #gsweb.get_detail("http://xyjg.egs.gov.cn/ECPS_HB/businessPublicity.jspx?id=FC54DB58B86D17839BE260FC4CE9FD9A", "", "")
    #s = RunHunan()
    #s.run()