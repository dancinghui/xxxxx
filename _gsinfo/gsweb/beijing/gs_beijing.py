#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
import time
import random
from spider.spider import AccountErrors
import spider.util
from _gsinfo.gsweb.gsconfig import ConfigData
from lxml import html
from _gsinfo.gsweb.gswebimg import SearchGSWeb
import threading

uas = ["baidu",
       "firefox",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.154 Safari/537.36 LBBROWSER",
       "=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
       "=Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36 Core/1.47.163.400 QQBrowser/9.3.7175.400",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"]

class SearchGSWebBeijing(SearchGSWeb):
    def __init__(self, saver):
        info = self.find_gsweb_searcher("北京")
        SearchGSWeb.__init__(self, info)
        self.proxies = {'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'}
        # {'http': 'http://ipin:helloipin@121.41.79.4:18889', 'https': 'https://ipin:helloipin@121.41.79.4:18889'}
        self.saver = saver
        #self.ua = self.useragent_random()
        #self.ua = uas[random.randrange(0, len(uas), 1)]
        #self.select_user_agent(self.ua)#"=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/49.0.2623.108 Chrome/49.0.2623.108 Safari/537.36")

        self._proxy_error = threading.local()

    def useragent_random(self):
        uas = []
        with open("../../_ct_proxy/UA.txt", "r") as f:
            for ua in f:
                ua = "="+ua
                uas.append(ua)
        result = uas[random.randrange(0, len(uas), 1)]
        #print "#########################################", result
        return result

    def count_proxy_error(self, error_type):
        cnt = getattr(self._proxy_error, "proxy_error_cnt", 0)
        if error_type:
            setattr(self._proxy_error, "proxy_error_cnt", 0)
        else:
            if cnt > 10:
                raise AccountErrors.NoAccountError("THE PROXY IS INVALID ! ! !")
            else:
                setattr(self._proxy_error, "proxy_error_cnt", (cnt+1))

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
                kwargs["timeout"] = 10
            except Exception as e:
                print e
        #self.select_user_agent(uas[random.randrange(0, len(uas), 1)])
        return super(SearchGSWeb, self).request_url(url, **kwargs)

    def _do_savebin(self, regist_code, content_type, text):
        """存入bin文件,key:注册号.类型.时间 , 由于一个公司详情有多个页面返回,用一个特定类型区分"""
        fn = '%s.%s.%d' % (regist_code, content_type, int(time.time()))
        self.saver.bs.append(fn, text)

    def search_company(self, kw):
        #headers = {'Referer': self.info['url']}
        headers = {'Referer': self.info['url'],
                   #"Origin": "http://qyxy.baic.gov.cn",
                   #"Upgrade-Insecure-Requests": "1",
                   "Content-Type": "application/x-www-form-urlencoded"}
        ticket = None
        while ticket is None:
            self.reset()
            if self._con:
                m = re.search('credit_ticket.*value="(.*?)"', self._con.text)
                if m:
                    ticket = m.group(1)

        data = {"credit_ticket": ticket, "keyword": kw} #"currentTimeMillis": int(time.time()*1000),
        lst = None
        check_code_retry = 0
        while True:
            check_code_retry += 1
            dbgdata = {}
            data["checkcode"] = self.solve_image(dbgdata=dbgdata)
            if "imgUrl" in dbgdata:
                imgurl = dbgdata["imgUrl"]
                m = re.search("http://qyxy\.baic\.gov\.cn/CheckCodeCaptcha\?currentTimeMillis=(\d+)&num=\d+", imgurl)
                if m:
                    data["currentTimeMillis"] = m.group(1)
            else:
                data["currentTimeMillis"] = int(time.time()*1000)

            #print "关键字查询验证码:", data["checkcode"]
            con = self.request_url("http://qyxy.baic.gov.cn/gjjbj/gjjQueryCreditAction!getBjQyList.dhtml", data=data, headers=headers)
            if con is None:
                print kw, " queries response is none ...结果为None "
                return None
            if u"您搜索的条件无查询结果" in con.text:
                print kw, " queries result is none ...结果为[]"
                return []
            if u"原因：可能访问过于频繁或非正常访问。" in con.text:
                print "request exception:可能访问过于频繁或非正常访问..."
                if check_code_retry >= 10:
                    #IP被封了...
                    print "IP被封了...即将结束本线程..."
                    return ["stop"]
                #time.sleep(check_code_retry)
                time.sleep(random.randrange(5, 15, 1))
                continue
            dom = None
            try:
                dom = html.fromstring(con.text)
            except Exception as e:
                print e, "search_company html.fromstring error .", con.text
                return None
            lst = dom.xpath("//div[@class='list']/ul")
            if len(lst) == 0 and u"请输入企业名称或注册号" in con.text:
                #TODO 返回到了原始搜索页面 不知道什么情况...
                credit_ticket = dom.xpath("//input[@id='credit_ticket']")[0].value
                data['credit_ticket'] = credit_ticket
                print "页面跳到原始搜索页面了,重新查询中...", kw
                time.sleep(1)
                continue
                #self.reset()
                #if check_code_retry >= 5:
                    #return None
                #print kw, " query's checkcode error... retrying...", check_code_retry
            else:
                break
        out = []
        for d in lst:
            href = d.xpath(".//a")[0].attrib['onclick']
            href = re.sub(';\s*', '', href)
            name, entid, regcode, cc = eval(re.sub('openEntInfo', '', href))
            url = 'http://qyxy.baic.gov.cn/gjjbj/gjjQueryCreditAction!openEntInfo.dhtml?entId={}&credit_ticket={}&entNo={}&timeStamp='
            url = url.format(entid, cc, regcode)
            #print "url=", url
            #self.get_detail(entid, name, regcode, url)
            out.append({"name": name, "url": url, "regcode": regcode, "entid": entid})
        print "get out#########################################################################################:", len(out), spider.util.utf8str(out)
        time.sleep(5)
        return out


    def get_detail(self, entId, name, regcode, url):
        detail = {}
        timestr = "%f" % (time.time() * 1000)
        url1 = url + timestr.split(".")[0]
        headers = {"Referer": url1}
        #拉取基本信息
        text1 = self.req_detail(url1)
        if text1 is None:
            return False

        #拉取股东信息
        timestr = "%f" % (time.time() * 1000)
        url2 = "http://qyxy.baic.gov.cn/gjjbj/gjjQueryCreditAction!tzrFrame.dhtml?ent_id=" + entId + "&entName=&clear=true&timeStamp=" + \
               timestr.split(".")[0]
        text2 = self.req_detail(url2, headers=headers)
        if text2 is None:
            return False

        #拉取变更信息
        timestr = "%f" % (time.time() * 1000)
        url3 = "http://qyxy.baic.gov.cn/gjjbj/gjjQueryCreditAction!biangengFrame.dhtml?ent_id=" + entId + "&clear=true&timeStamp=" + \
               timestr.split(".")[0]
        text3 = self.req_detail(url3, headers=headers)
        if text3 is None:
            return False

        #拉取主要人员信息
        timestr = "%f" % (time.time() * 1000)
        url4 = "http://qyxy.baic.gov.cn/gjjbj/gjjQueryCreditAction!zyryFrame.dhtml?ent_id=" + entId + "&clear=true&timeStamp=" + \
               timestr.split(".")[0]
        text4 = self.req_detail(url4)
        if text4 is None:
            return False

        #拉取分支机构信息
        timestr = "%f" % (time.time() * 1000)
        url5 = "http://qyxy.baic.gov.cn/gjjbj/gjjQueryCreditAction!fzjgFrame.dhtml?ent_id=" + entId + "&clear=true&timeStamp=" + \
               timestr.split(".")[0]
        text5 = self.req_detail(url5)
        if text5 is None:
            return False

        self._do_savebin(regcode, "basicInfo", text1)
        self._do_savebin(regcode, "investorsInfo", text2)
        self._do_savebin(regcode, "changesInfo", text3)
        self._do_savebin(regcode, "staffsInfo", text4)
        self._do_savebin(regcode, "branchInfo", text5)

        ###############################解析＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃＃

        #解析基本信息
        doc1 = None
        try:
            doc1 = html.fromstring(text1)
        except Exception as e:
            print "basicInfo ERROR:", e, "text:", text1
            return False
        tables = doc1.xpath("//table[@class='detailsList']")
        if tables is None or len(tables) == 0:
            print "not found basic info table .\n", text1
            return False
        basic_info = []
        try:
            basic_info = self.parse_basic_info(tables[0])
        except Exception as e:
            print e, "parse basicInfo error,text=\n", text1
            return False
        #print "基本信息:", spider.util.utf8str(basic_info)
        detail["basicInfo"] = basic_info

        #解析股东信息
        doc2 = None
        try:
            doc2 = html.fromstring(text2)
        except Exception as e:
            print "investor ERROR:", e, "text:", text2
            return False
        trs = doc2.xpath("//tbody[@id='table2']/tr")
        investors = self.parse_investor_info(trs)
        #print "股东信息:", spider.util.utf8str(investors)
        detail["investorsInfo"] = investors


        #解析变更信息
        doc3 = None
        try:
            doc3 = html.fromstring(text3)
        except Exception as e:
            print "investor ERROR:", e, "text:", text3
            return False
        trs = doc3.xpath("//tr[@id='tr1']")
        changes = self.parse_changes_info(trs)
        #print "变更信息:", spider.util.utf8str(changes)
        detail["changesInfo"] = changes

        #解析主要人员信息
        doc4 = None
        try:
            doc4 = html.fromstring(text4)
        except Exception as e:
            print "staffsInfo ERROR:", e, "text:", text4
            return False
        trs = doc4.xpath("//tbody[@id='table2']/tr")
        staffs = self.parse_staffs_info(trs)
        #print "主要人员信息:", spider.util.utf8str(staffs)
        detail["staffsInfo"] = staffs

        #解析分支机构信息
        doc5 = None
        try:
            doc5 = html.fromstring(text5)
        except Exception as e:
            print "branchInfo ERROR:", e, "text:", text5
            return False
        trs = doc5.xpath("//tbody[@id='table2']/tr")
        branchInfo = self.parse_branch_info(trs)
        #print "分支机构信息:", spider.util.utf8str(branchInfo)
        detail["branchInfo"] = branchInfo

        print name, regcode, "========获得详情:", spider.util.utf8str(detail)
        self.saver.fs.append(spider.util.utf8str(detail))
        return True


    def req_detail(self, url, **kwargs):
        retry = 0
        while True:
            res = self.request_url(url, **kwargs)
            if res is None or res.code != 200:
                if retry < 5:
                    print "res is None" if res is None else "res.code=%d" % res.code, url
                    time.sleep(random.randrange(5, 15, 1))
                    continue
                else:
                    return None
            if u"您停留的时间过长，请重新查询后再查看企业详细，如还不能访问请与技术人员联系" in res.text:
                print "您停留的时间过长，请重新查询后再查看企业详细，如还不能访问请与技术人员联系..."
                return None
            if u"可能访问过于频繁或非正常访问" in res.text:
                print "可能访问过于频繁或非正常访问..."
                return None
            return res.text


    def parse_investor_build_url(self, tagA, **kwargs):
        """实现方法 --- 从a标签中提取生成特定的URL并进行访问,返回html文本"""
        ref = tagA.attrib.get("onclick", '')
        m = re.search("showDialog(\(.*\))", ref)
        if m:
            #url = "http://qyxy.baic.gov.cn"+m.group(1)
            on = eval(m.group(1))[0]
            url = "http://qyxy.baic.gov.cn" + on
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


    def parse_changes_info(self, trs, **kwargs):
        """
        解析变更信息--此链接变更信息与一般 不同 需要重写解析方法
        """
        #trs = doc.xpath("//table[@class='detailsList']/tr")
        header = ["changeItem", "changeBefore", "changeAfter", "changeDate"]
        changes = []
        for tr in trs:
            tds = tr.xpath("td")
            i = 0
            if len(tds) < 3:
                continue
            change = {}
            for td in tds:
                a = td.xpath("a")
                if a is not None and len(a) == 1:
                    html_text = self.parse_investor_build_url(a[0], **kwargs)
                    if html_text is None:
                        change[header[i]] = ""
                        i += 1
                        change[header[i]] = ""
                    else:
                        #解析变更信息中的具体信息
                        doc = html.fromstring(html_text)
                        tables = doc.xpath("//table[@id='tableIdStyle']")
                        if len(tables) == 0:
                            change[header[i]] = ""
                            i += 1
                            change[header[i]] = ""
                        else:
                            change[header[i]] = self.parse_changes_info2(tables[0])
                            i += 1
                            change[header[i]] = self.parse_changes_info2(tables[1])
                    i += 1
                    continue
                change[header[i]] = "" if td.text_content() is None else td.text_content().strip()
                i += 1
            changes.append(change)
        return changes

    def parse_changes_info2(self, table):
        """解析变更信息a链接详情页"""
        #tables = doc.xpath("//table[@id='tableIdStyle']")
        header = []
        trs = table.xpath("tr")
        changes = []
        for tr in trs:
            ths = tr.xpath("th")
            if len(ths) != 0:
                for th in ths:
                    header.append(th.text_content().strip())
            else:
                tds = tr.xpath("td")
                if len(tds) == 1:
                    continue
                change = {}
                i = 0
                for td in tds:
                    change[header[i]] = "" if td.text_content() is None else td.text_content().strip()
                    i += 1
                changes.append(change)
        #print "变更:", spider.util.utf8str(changes)
        return changes


def test_parse():
    doc = None
    with open("reginster3.html", 'rb') as f:
        text = f.read()
        doc = html.fromstring(text)


    tables = doc.xpath("//table[@class='detailsList']")
    trs = tables[0].xpath("tr")
    basic_info = {}
    for tr in trs:
        if len(tr) % 2 == 1:
            continue
        i = 1
        a = ''
        b = ''
        for t in tr:
            if i%2 == 1:
                a = "" if t.text is None else t.text_content().strip()
            else:
                b = "" if t.text is None else t.text_content().strip()
                if a == "" and b == "":
                    continue
                basic_info[a] = b
                print a, b
            i += 1
    print "公用方法-提取到基本信息为:", spider.util.utf8str(basic_info)
    #return basic_info






import os, sys
from spider.httpreq import BasicRequests

if __name__ == '__main__':
    spider.util.use_utf8()
    #info = find_gsweb_searcher("广东")
    #gsweb = get_gsweb_searcher(info)
    #gsweb.file_init()
    #gsweb.get_QyxyDetail("","http://www.szcredit.com.cn/web/GSZJGSPT/QyxyDetail.aspx?rid=0f8eee502c834f1b99bdc89930869b9f","")
    gsweb = SearchGSWebBeijing(None)
    gsweb.search_company("腾讯科技（北京）有限公司")
    #gsweb.search_company("北京京东世纪贸易有限公司")
    #gsweb.get_entityShow("", "http://gsxt.gzaic.gov.cn/search/search!entityShow?entityVo.pripid=g-J7cvop7btqH0SYdg-RjaSL3M2Yr8WjhU6SwHkMOyE=", "")
    #gsweb.search_company("广州爱拼")
    #test_parse()