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

class SearchGSWebSichuan(SearchGSWeb):
    def __init__(self, saver):
        info = self.find_gsweb_searcher("四川")
        SearchGSWeb.__init__(self, info)
        #针对公司内部验证码服务　
        self.onl = OnlineOCR(info['pinyin'].lower()) #注意：陕西Shaanxi不适用
        self.onl.server = "http://192.168.1.94:3001/"
        self.proxies = {'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'}
        #self.proxies = {'http': 'http://ipin:helloipin@haohr.com:50001', 'https': 'https://ipin:helloipin@haohr.com:50001'}
        #self.proxies = {'http': 'http://ipin:helloipin@106.75.134.190:18889', 'https': 'https://ipin:helloipin@106.75.134.190:18889'}
        self.saver = saver
        #self.ua = self.useragent_random()
        self.ua = uas[random.randrange(0, len(uas), 1)]
        self.select_user_agent(self.ua)
        #self.index_url = "http://gsxt.scaic.gov.cn/ztxy.do?method=index&random="+str(int(time.time()*1000))
        #self.request_url(self.index_url, headers={"Referer": "http://gsxt.scaic.gov.cn/"})

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
        try:
            entname = kw.encode("gbk")
        except Exception as e:
            print "查询接口　　转码错误．．．", kw
            return
        tag = "请输入营业执照注册号或统一社会信用代码".encode("gbk")
        headers = {'Referer': "http://gsxt.scaic.gov.cn/ztxy.do?method=index&random="+str(int(time.time()*1000)),
                   "Content-Type": "application/x-www-form-urlencoded",
                   "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        # data = {"currentPageNo": 1, "maent.entname": entname, "pName": "请输入营业执照注册号或统一社会信用代码".encode("gbk"),
        #         "BA_ZCH": "请输入营业执照注册号或统一社会信用代码".encode("gbk")}
        check_code_retry = 0
        none_retry = 0
        url = None
        text = None
        dom = None
        while True:
            check_code_retry += 1
            #TODO 用的公司内部验证码服务器　还不稳定
            dbgdata = {"type": "inner_server"}
            code = self.solve_image(dbgdata=dbgdata)
            code = code.encode("gbk")
            #self.get_image()
            #code = raw_input("请输入验证码:")
            #print "验证码:", code
            #data["yzm"] = code
            data = "currentPageNo=1&yzm="+code+"&maent.entname="+entname+"&pName="+tag+"&BA_ZCH="+tag
            url = "http://gsxt.scaic.gov.cn/ztxy.do?method=list&djjg=&random="+str(int(time.time()*1000))
            con = self.request_url(url, data=data, headers=headers)
            if con is None or con.code != 200:
                print kw, " queries response is none ...res is None "
                #return None
                time.sleep(random.randrange(1, 5, 1))
                continue
            if u"您搜索的条件无查询结果" in con.text:
                print kw, " queries result is none ...查询无结果 ",  none_retry
                #有时候一个关键字是有结果的，但是提示搜索无结果，重试几次会拿到结果．
                if none_retry > 3:
                    return []
                else:
                    time.sleep(random.randrange(1, 4, 1))
                    none_retry += 1
                    continue
            if u"验证码不正确或已失效" in con.text: #u"验证码错误" or u"验证码已过期" in con.text 这个正常有数据页面也有
                print code, " 验证码错误...重试..."
                time.sleep(0.2)
                check_code_retry += 1
                if check_code_retry > 5:
                    return None
                continue
            try:
                dom = html.fromstring(con.text)
                lst = dom.xpath("//li[@class='font16']/a")
                if len(lst) == 0:
                    #可能是验证码错误，上面的［验证码不正确或已失效］判断可能有误
                    check_code_retry += 1
                    print "页面找不到查询结果,可能是验证码错误,上面的［验证码不正确或已失效］判断可能有误...重试...", check_code_retry
                    time.sleep(random.randrange(1, 5, 1))
                    if check_code_retry > 5:
                        return None
                    continue
                else:
                    text = con.text
                    break
            except Exception as e:
                print e, "search_company html.fromstring error .text=\n", con.text
                return None

        out = []
        self.parse_query(out, text, kw)
        pages = dom.xpath("//div[@class='list-a']/a")
        pageNum = 2
        while pageNum <= len(pages):
            headers["Referer"] = url
            url = "http://gsxt.scaic.gov.cn/ztxy.do?method=list&djjg=&yzmYesOrNo=no&random=%s&pageNum=%d" % (str(int(time.time()*1000)), pageNum)
            data = {"currentPageNo": "", "yzm": "", "cxym":"cxlist", "maent.entname": entname}
            res = self.request_url(url, data=data, headers=headers)
            if res is not None and res.code == 200:
                self.parse_query(out, res.text, kw)
                pageNum += 1
            else:
                print "关键字　%s 翻第 %d 页 失败...原因：%s" % (kw, pageNum, "res is None" if res is None else ("res.code:%d"%(res.code)))
        print "get out######################:", len(out), spider.util.utf8str(out)
        return out


    def parse_query(self, out, text, kw):
        try:
            dom = html.fromstring(text)
        except Exception as e:
            print kw, "ERROR:", e, " ---> search_company html.fromstring error, text=\n", text
            return
        lst = dom.xpath("//li[@class='font16']/a")
        for a in lst:
            onclick = a.attrib.get("onclick", '')
            name = a.text_content().strip()
            m = re.search("openView\('(.*)','(.*)','(.*)'\)", onclick)
            if m:
                oi = {"name": name, "pripid": m.group(1), "entbigtype": m.group(2)}
                #self.get_detail(oi["pripid"], oi["entbigtype"], oi["name"])
                out.append(oi)
            else:
                print "关键字　%s 搜索结果中　[ %s ] 没有匹配到pripid和entbigtype" % (kw, name)



    def parse_investor_build_url(self, tagA, **kwargs):
        """实现方法 --- 从a标签中提取生成特定的URL并进行访问,返回html文本"""
        ref = tagA.attrib.get("onclick", '')
        m = re.search("showRyxx\('(.*)','(.*)'\)", ref)
        if m:
            #data = {"method": "tzrCzxxdetial", "maent.xh": m.group(1), "maent.pripid": m.group(2), "random": str(int(time.time()*1000))}
            data = "method=tzrCzxxDetial&maent.xh="+m.group(1)+"&maent.pripid="+m.group(2)+"&random="+str(int(time.time()*1000))
            url = "http://gsxt.scaic.gov.cn/ztxy.do"
            headers = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                       "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                       "Referer": url, "Content-Type": "application/x-www-form-urlencoded"}
            self.select_user_agent("=Mozilla/5.0 (Windows NT 10.0; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0")
            error_retry = 0
            #self.add_cookie_line("gsxt.scaic.gov.cn", "CNZZDATA1000300163=1774173223-1462949393-%7C1462949393")
            while True:
                res = self.request_url(url, data=data, headers=headers)
                if res is None or res.code != 200 or u"访问异常" in res.text:
                    print "parse_investor_build_url", "res is None..." if res is None else " res.code=%d,res.text=%s" % (res.code, res.text)
                    error_retry += 1
                    #if error_retry > 10:
                    #    return None
                    time.sleep(random.randrange(1, 8, 1))
                else:
                    return res.text


    def get_detail(self, pripid, entbigtype, name, retry=0):
        url = "http://gsxt.scaic.gov.cn/ztxy.do"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"method": "qyInfo", "djjg": "", "maent.pripid": pripid, "maent.entbigtype": entbigtype, "random": str(int(time.time()*1000))}
        detail = {}
        text = self.req_detail(url, data=data, headers=headers)
        doc = None
        try:
            doc = html.fromstring(text)
        except Exception as e:
            print "get_detail page html.fromstring(text) ERROR:", e, "text:\n", text
            return False

        #解析基本信息
        tables = doc.xpath("//div[@id='jibenxinxi']//table[@class='detailsList']")
        #print "基本信息：", spider.util.utf8str(basic_info)
        if len(tables) == 0:
            print name, "页面连基本信息都没有..."
            if retry < 3:
                return self.get_detail(pripid, entbigtype, name, retry=retry+1)
            return False
        basic_info = self.parse_basic_info(tables[0])
        detail["basicInfo"] = basic_info

        data2 = {"method": "baInfo", "maent.pripid": pripid, "czmk": "czmk2", "random": str(int(time.time()*1000))}
        text2 = self.req_detail(url, data=data2, headers=headers)
        doc2 = None
        try:
            doc2 = html.fromstring(text2)
        except Exception as e:
            print "get_detail page2 html.fromstring(text) ERROR:", e, "text:\n", text
            return False

        #解析股东信息
        trs = doc.xpath("//table[@id='table_fr']/tr")
        #TODO 获取投资详情的链接访问失败　
        investor_info = self.parse_investor_info(trs)
        #print "股东信息：", spider.util.utf8str(investor_info)
        detail["investorInfo"] = investor_info

        #解析变更信息
        trs = doc.xpath("//table[@id='table_bg']/tr")
        changes_info = self.parse_changes_info(trs)
        #print "变更信息：", spider.util.utf8str(changes_info)
        detail["changesInfo"] = changes_info

        #解析主要人员信息
        trs = doc2.xpath("//table[@id='table_ry1']/tr")
        if len(trs) == 0:
            print name, 'parse_staffs_info unget tables...'
        else:
            staffs_info = self.parse_staffs_info(trs)
            #print "主要人员信息：", spider.util.utf8str(staffs_info)
            detail["staffsInfo"] = staffs_info

        #解析分支机构信息
        trs = doc2.xpath("//table[@id='table_fr2']/tr")
        if len(trs) == 0:
            print name, 'parse_branch_info unget tables...'
        else:
            branch_info = self.parse_branch_info(trs)
            #print "分支机构信息：", spider.util.utf8str(branch_info)
            detail["branchInfo"] = branch_info

        self._do_savebin(pripid, "basic", text)
        self._do_savebin(pripid, "beian", text2)
        self.saver.fs.append(spider.util.utf8str(detail))
        print "获取到详情：", name, spider.util.utf8str(detail)
        return True

    def req_detail(self, url, **kwargs):
        retry = 0
        while True:
            res = self.request_url(url, **kwargs)
            if res is None or res.code != 200:
                if retry < 5:
                    print "res is None" if res is None else "res.code=%d" % res.code, url
                    time.sleep(0.5)
                    continue
                else:
                    return None
            return res.text

################################################# RUN ########################################################

filter_kw = set()
filter_queries = set()

class RunSichuan(Spider):

    class Saver(object):
        def __init__(self):
            self.bs = BinSaver("gsinfo_Sichuan_html.bin")
            self.fs = FileSaver("gsinfo_sichuan.txt")
    """
    工商网站--四川
    """
    def __init__(self):
        spider.util.use_utf8()
        self.saver = RunSichuan.Saver()
        self.is_debug = True
        if self.is_debug:
            Spider.__init__(self, 1)
            self.gsweb = SearchGSWebSichuan(self.saver)
        else:
            self.proxies_dict = []
            self.read_proxy("../../_ct_proxy/proxy_040510.txt")
            Spider.__init__(self, len(self.proxies_dict))
            self._curltls = threading.local()
        self.gswebs = {}
        #已经查询成功的关键字
        self.success_kw = FileSaver("gsinfo_sichuan_success_kw.txt")
        #对于查到的列表信息,爬取成功就写入到这个文本,防止重复爬取
        self.success_queries = FileSaver("gsinfo_sichuan_success_queries.txt")
        #初始化已经爬过的链接
        self.init_spider_url()
        #time.sleep(2)
        self.cnt = 1
        self.run_time = time.time()
        self.cnt_q = 1


    def init_obj(self):
        threadident = str(threading.currentThread().ident)
        gsweb = SearchGSWebSichuan(self.saver)
        if not self.is_debug:
            gsweb.proxies = self.proxies_dict[self.get_tid()]
        self.gswebs[threadident] = gsweb
        setattr(self._curltls, "gsweb", gsweb)
        return gsweb

    def init_spider_url(self):
        with open("gsinfo_sichuan_success_kw.txt", "r") as f:
            for url in f:
                filter_kw.add(url.strip())
            print "init already spidered commpany url finished !"

        with open("gsinfo_sichuan_success_queries.txt", "r") as f:
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
        with open("sichuan_cname.txt", "r") as f:
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
            # if retry < 3:
            #     job["retry"] = retry + 1
            #     self.re_add_job(job)
            # else:
            self.record_spider_kw(kw)
            return
        all = len(out)
        scs_cnt = 0
        for oi in out:
            cname = oi["name"]
            pripid = oi["pripid"]
            entbigtype = oi["entbigtype"]
            s = cname+","+str(pripid)
            if s in filter_queries:
                #如果已经爬取过了,略过
                all -= 1
                continue
            retry2 = 0
            while True:
                flag = gsweb.get_detail(pripid, entbigtype, cname)
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
                        time.sleep(random.randrange(1, 5, 1))

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
    #gsweb = SearchGSWebSichuan(None)
    #gsweb.search_company("科技")
    #gsweb.get_detail("CD79586289", "11", "四川华西集团物流有限公司")
    s = RunSichuan()
    s.run()
    #s.run_job({"kw": "湖北科技", "cnt": 0, "retry": 0})