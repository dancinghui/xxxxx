#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
import json
import time
import random
from spider.runtime import Log
from spider.spider import AccountErrors
from spider.spider import SessionRequests
import spider.util
import urlparse
import threading
from _gsinfo.gsweb.gsconfig import ConfigData
from lxml import html
from spider.savebin import BinSaver, FileSaver
from _gsinfo.gsweb.gswebimg import SearchGSWeb
uas = ["baidu",
       "firefox",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.86 Safari/537.36",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.154 Safari/537.36 LBBROWSER",
       "=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586",
       "=Mozilla/5.0 (iPhone; CPU iPhone OS 9_1 like Mac OS X) AppleWebKit/601.1.46 (KHTML, like Gecko) Version/9.0 Mobile/13B143 Safari/601.1",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36 Core/1.47.163.400 QQBrowser/9.3.7175.400",
       "=Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
       "=Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/7.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C; .NET4.0E; InfoPath.2; GWX:RESERVED)"]

# 广东省
class SearchGSWebGuangdong(SearchGSWeb):
    def __init__(self, saver):
        info = find_gsweb_searcher("广东")
        SearchGSWeb.__init__(self, info)
        #self.proxies = {'http': 'http://107.151.142.123:80', 'https': 'https://107.151.142.123:80'}
        self.proxies = {}#{'http':'http://ipin:helloipin@106.75.134.193:18889', 'https':'https://ipin:helloipin@106.75.134.193:18889'}
        self.saver = saver
        #self.ua = self.useragent_random()
        self.ua = uas[random.randrange(0, len(uas), 1)]
        self.select_user_agent(self.ua)
        #self.select_user_agent("=Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.154 Safari/537.36 LBBROWSER")

        self._proxy_error = threading.local()


    def useragent_random(self):
        uas = []
        with open("../../../_ct_proxy/UA.txt", "r") as f:
            for ua in f:
                ua = "="+ua
                uas.append(ua)
        result = uas[random.randrange(0, len(uas), 1)]
        #print "#########################################", result
        return result

    def find_gsweb_searcher(name):
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
        #self.ua = uas[random.randrange(0, len(uas), 1)]
        #self.select_user_agent(self.ua)
        return super(SearchGSWeb, self).request_url(url, **kwargs)

    def _do_savebin(self, regist_code, url_type, content_type, text):
        """存入bin文件,key:注册号.类型.时间 , 由于一个公司详情有多个页面返回,用一个特定类型区分"""
        fn = '%s.%s.%s.%d' % (regist_code, url_type, content_type, int(time.time()))
        #self.bs.append(fn, text)
        self.saver.bs.append(fn, text)

    def encode_kw(self, kw):
        headers = {'Referer': self.info['url']}
        kw = spider.util.utf8str(kw)
        while True:
            self.code = self.solve_image()
            mm = self.request_url("http://gsxt.gdgs.gov.cn/aiccips/CheckEntContext/checkCode.html",
                        data={"code": self.code, "textfield": kw}, headers=headers, timeout=50)
            if mm is None:
                return None
            if u"PROXY-ERROR:" in mm.text:
                return "PROXY-ERROR"
            if u"您输入的验证码不正确" in mm.text:
                print "code=", self.code, "result=", mm.text
                continue
            jmm = json.loads(mm.text)
            if int(jmm['flag']) == 1:
                return jmm["textfield"]
        raise RuntimeError("failed")

    def count_proxy_error(self, error_type):
        cnt = getattr(self._proxy_error, "proxy_error_cnt", 0)
        if error_type:
            setattr(self._proxy_error, "proxy_error_cnt", 0)
        else:
            if cnt > 10:
                raise AccountErrors.NoAccountError("THE PROXY IS INVALID ! ! !")
            else:
                setattr(self._proxy_error, "proxy_error_cnt", (cnt+1))


    def search_company(self, kw):
        try:
            cname = kw
            headers={'Referer': self.info['url']}
            # 广东省方案: 对提效的查询词进行类似于AES的加密,16字节block, ecb模式, 所以可以批量加密明文.
            kw = self.encode_kw(kw)
            if kw is None:
                return None
            elif kw == "PROXY-ERROR":
                return ["PROXY-ERROR"]
            infourl = "http://gsxt.gdgs.gov.cn/aiccips/CheckEntContext/showInfo.html"
            si = self.request_url(infourl, data={"code": self.code, "textfield": kw}, headers=headers, timeout=50)
            dom = html.fromstring(si.text, infourl)
            out = []
            for d in dom.xpath("//div[@class='list']"):
                a1 = d.xpath(".//a")[0]
                s1 = d.xpath(".//span")[0]
                oi = {"name": a1.text_content(),
                      "url": urlparse.urljoin(infourl, a1.attrib['href']),
                      "regcode": s1.text_content()}
                out.append(oi)
            print "get############################:", cname, len(out), "----------------->", out #, spider.util.utf8str(self.proxies)
            print json.dumps(out, indent=4, ensure_ascii=0).encode('utf-8')
            #self.run_get_detail(out)
            return out
        except Exception as e:
            print "查询公司列表出现异常:", e
            return None

    def parse_investor_build_url(self, tagA, **kwargs):
        """实现方法 --- 从a标签中提取生成特定的URL并进行访问,返回html文本"""
        url_type = kwargs["url_type"]
        investor_text = None
        if url_type == "QyxyDetail":
            investor_url = "http://www.szcredit.com.cn/web/GSZJGSPT/"+tagA.get("href")
            error_retry = 0
            param_retry = 0
            while True:
                res = self.request_url(investor_url)
                if res is not None and res.code == 200:
                    investor_text = res.content.decode('gb18030').encode('utf-8')
                    if '尊敬的用户：参数错误' in investor_text:
                        param_retry += 1
                        if param_retry > 10:
                            return None
                        print "params error ... retrying..."
                        time.sleep(2)
                        continue
                    else:
                        return investor_text
                else:
                    error_retry += 1
                    if error_retry > 5:
                        return None
                    time.sleep(error_retry*2)
        elif url_type == "GSpublicityList":
            onclick = tagA.attrib.get("onclick", '')
            m = re.search("return alert\('(.*)'\);", onclick)
            m1 = re.search("window\.open\('(.*)'\)", onclick)
            if m:
                return None
            elif m1:
                url = m1.group(1)
                while True:
                    error_retry = 0
                    res = self.request_url(url)
                    if res is not None and res.code == 200:
                        return res.text
                    else:
                        error_retry += 1
                        if error_retry > 5:
                            return None
                        time.sleep(error_retry*2)
            else:
                print "parse_investor_build_url GSpublicityList unknow onclick type , onclick=", onclick
                return None
        elif url_type == "entityShow":
            ref = tagA.attrib.get("onclick", '')
            m = re.search("window\.open\('(.*)'\)", ref)
            if m:
                url = m.group(1)
                #print "找到详情链接 ", url
                error_retry = 0
                while True:
                    res = self.request_url(url)
                    if res is not None and res.code == 200:
                        #print "找到详情数据 ", res.text
                        return res.text
                    else:
                        error_retry += 1
                        if error_retry > 5:
                            return None
                        time.sleep(error_retry*2)
            #暂时没有找到有链接的
            #print "parse_investor_build_url entityShow have tagA--->href=", tagA.get("href"), "onclick=", tagA.attrib.get("onclick", '')
        elif url_type == "GSpublicityList_Changes":
            ref = tagA.attrib.get("onclick", '')
            m = re.search("window\.open\('(.*)'\)", ref)
            if m:
                url = m.group(1)
                error_retry = 0
                while True:
                    res = self.request_url(url)
                    if res is not None and res.code == 200:
                        return res.text
                    else:
                        error_retry += 1
                        if error_retry > 5:
                            return None
                        time.sleep(error_retry*2)
        elif url_type == "QyxyDetail_Changes":
            #暂时未找到相关变更信息页面  -- 如果找到相应页面,记得返回的html需要 decode('gb18030')
            #text = res.text.decode('gb18030')
            print "parse_investor_build_url QyxyDetail_Changes have tagA--->href=", tagA.get("href"), "onclick=", tagA.attrib.get("onclick", '')

    def parse_investor_build_url_retry(self, tagA, **kwargs):
        """访问标签中URL的重试机制"""
        if 'retry' in kwargs:
            retry = int(kwargs['retry'])
            if retry < 3:
                kwargs.update({"retry": retry})
                return self.parse_investor_build_url(tagA, **kwargs)
        else:
            kwargs.update({"retry": 1})
            return self.parse_investor_build_url(tagA, **kwargs)


    def get_QyxyDetail(self, cnt,  cname, url, regist_code, retry=0, tid=-1):
        """
        第一种情况:针对[市场主体]QyxyDetail类系统
        两个链接,第二个是变更信息,第一个是除变更信息外所有信息
        """
        detail = {}
        #url = "http://www.szcredit.com.cn/web/GSZJGSPT/QyxyDetail.aspx?rid=0f8eee502c834f1b99bdc89930869b9f"
        res = None
        sleeptime = 1
        text = None
        while True:
            res = self.request_url(url)
            if res is None or res.code != 200:
                print cname, "get_QyxyDetail page1 res is error,code=", 0 if res is None else res.code, "url=", url
                #return False
                return "proxy_error"
            try:
                text = res.content.decode('gb18030').encode('utf-8')
            except Exception as e:
                print e, " 转码错误 "#, res.content
                #return False
                return "code_error"
            if "/App_Themes/Default/Images/error.jpg" in text: #or "地址：深圳市福田区竹子林益华大厦四楼 站长统计  建议使用1024*768分辨率以上的显示器和IE浏览器" in text:
                print cname, "url=", url, "返回的页面错误..."
                #return False
                return "return_error"
            if "您的查询过于频繁，请稍候再查！" in text or "您的查询间隔时间过短，请稍候再查！" in text:
                #TODO 可能是被封了!
                print "您的查询过于频繁，请稍候再查 --- >此IP可能已经被封..."
                #return False
                time.sleep(random.randrange(1, 5, 1))
                return "page_error"
                #sleeptime *= 2
                #print cname, "查询太频繁...sleep:", sleeptime
                #if sleeptime > 15:
                    #return False
                #time.sleep(sleeptime)
                #continue
            else:
                break
        self._do_savebin(regist_code, "QyxyDetail", "basic", text)

        if not self.parse_QyxyDetail_basic(text, regist_code, detail, url, cname, tid=tid):
            return "page_error"

        doc = html.fromstring(text)
        __VIEWSTATE = doc.xpath("//input[@id='__VIEWSTATE']")[0].value
        __VIEWSTATEGENERATOR = doc.xpath("//input[@id='__VIEWSTATEGENERATOR']")[0].value

        headers = {"origin":"http://www.szcredit.com.cn",
                   "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
                   "Cache-Control":"no-cache",
                   "X-Requested-With":"XMLHttpRequest",
                   "XMLHttpRequest":"Delta=true",
                   "Referer":url
                   }

        data = {"ScriptManager1":"biangengxinxi|Timer2",
                "__EVENTTARGET":"Timer2",
                "__EVENTARGUMENT":"",
                "__VIEWSTATE":__VIEWSTATE,
                "__VIEWSTATEGENERATOR":__VIEWSTATEGENERATOR,
                "__ASYNCPOST":"true",
                "":""}

        res = self.request_url(url, headers=headers, data=data)
        if res is None:
            print "res is error"
            Log.error("response is none," + url)
            return self.get_QyxyDetail(cnt, cname, url, regist_code)
        elif res.code != 200:
            Log.error("QyxyDetail, regist code = "+regist_code+",response code = " + str(res.code) + " ,url = " + url)
            print cname, "get_QyxyDetail page2 res is error --->res.code=", res.code
            #return False
            return "proxy_error"
        text = res.content
        self._do_savebin(regist_code, "QyxyDetail", "changes", text)
        text = text.decode('gb18030')
        doc = html.fromstring(text)
        trs = doc.xpath("//table[@class='detailsList']/tr")
        detail["changesInfo"] = self.parse_changes_info(trs, url_type="QyxyDetail_Changes")
        print cnt, cname, "QyxyDetail--->", spider.util.utf8str(detail), url
        self.saver.fs_QyxyDetail.append(spider.util.utf8str(detail))
        #return True
        return "success"


    def parse_QyxyDetail_basic(self, text, regist_code, detail, url, cname, tid=-1):
        #解析基本信息
        doc = None
        try:
            doc = html.fromstring(text)
        except Exception as e:
            print "QyxyDetail parse_basic error--->", e, text
            return False
        basic_info = []
        tables = doc.xpath("//div[@id='jibenxinxi']/table[@class='detailsList']")
        if len(tables) != 0:
            try:
                basic_info = self.parse_basic_info(tables[0])
            except Exception as e:
                print "ERROR:", e, "get_QyxyDetail-parse_basic_info ,url=", url, "text--->", text
                return False
            if basic_info[u"名称"] == u"深圳市龙岗区新概念主义鱼餐厅":
                print tid, "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", self.ua
                return False
            detail["basicInfo"] = basic_info
        else:
            print "get_QyxyDetail-parse_basic_info tables length=0"
            return False

        #股东信息
        trs = doc.xpath("//tbody[@id='table2']/tr")
        investors = self.parse_investor_info(trs, url_type="QyxyDetail")
        detail["investorsInfo"] = investors

        #解析经营范围信息
        run_info = {}
        try:
            run_scope = doc.xpath("//tr[@id='RegInfo_SSDJCBuItem_tr1']/th")[0].text_content()
            run_content = doc.xpath("//span[@id='RegInfo_SSDJCBuItem_labCBuItem']")[0].text_content()
            run_info = {"run_scope": "" if run_scope is None else run_scope.strip(), "run_content": "" if run_content is None else run_content.strip()}
        except Exception as e:
            print "ERROR:", e, "get_QyxyDetail-parse_run_info, url=", url#, " ,text--->", text
        detail["runInfo"] = run_info
        #print "QyxyDetail经营范围信息:", spider.util.utf8str(run_info)

        #解析主要人员信息:
        trs = doc.xpath("//table[@id='t30']/tr")
        detail["staffsInfo"] = self.parse_staffs_info(trs)#staffs
        #print "QyxyDetail主要人员信息:", spider.util.utf8str(staffs)

        #解析分支机构信息
        trs = doc.xpath("//table[@id='t31']/tr")
        if len(trs) == 0:
            detail["branchInfo"] = []
        else:
            detail["branchInfo"] = self.parse_branch_info(trs)
        #print "分支机构信息:",spider.util.utf8str(detail)


        #清算信息暂时找不到
        #基本信息v-股东信息v-变更信息v 主要人员信息v-分支机构信息v-清算信息
        return True



    def get_entityShow(self, cnt, cname, url, regist_code, retry=0):
        """
        第二种情况:这种类型的链接只从html中解析出基本信息,其他信息需要访问另外4个链接,这4个链接返回都是json
        """
        detail = {}
        headers = {"Referer":"http://gsxt.gzaic.gov.cn/search/guard.jsp"}
        result = None
        res = None
        retry_req = 0
        while True:
            retry_req += 1
            res = self.request_url(url, headers=headers, timeout=30.0)
            if res is not None:
                break
            if retry_req > 5:
                print cname, "get_entityShow basic page failure,url=", url
                #return False
                return "proxy_error"
            print "get_entityShow basic page retry = ", retry
        if res.code == 521:
            jscode = """
            function setTimeout(a, t){}
            window={}
            document={}
            document.attachEvent = function(a, b){b();}
            Object.defineProperty(document, "cookie", { set: function (a) { console.log(a); } });
            document.createElement = function(a){
                var r = new Object();
                r.name = a;
                r.firstChild = {href:'http://gsxt.gzaic.gov.cn/'}
                return r;
            }
            """
            text = res.text[8:-10]
            jscode += text
            cookie = spider.util.runjs(jscode)
            self.add_cookie_line('gsxt.gzaic.gov.cn', cookie)
            return self.get_entityShow(cnt, cname, url, regist_code, retry=(retry+1))
        elif res.text is None:
            print url, "--->res.code:", res.code
            if retry < 5:
                print "get_entityShow ---> res.text is none ,retry..."
                return self.get_entityShow(cnt, cname, url, regist_code, retry=(retry+1))
            else:
                print "get_entityShow ---> page1 res is none ,stop"
                #return False
                return "proxy_error"
        elif u"根据下图内容进行判断，输入汉字或算术题计算结果" in res.text:
            headers['Content-Type'] = "application/x-www-form-urlencoded"
            result = self.add_entityShow_cookie(url, headers)
        if result is not None:
            if u'查询过于频繁' in result or u'请稍候再查！' in result:
                time.sleep(retry+1)
                return self.get_entityShow(cnt, cname, url, regist_code, retry=(retry+1))
            # m = re.search('<h2[\s\S]*注册号：(.*)</h2>',result)
            # if m:
            #     regist_code = m.group(1)
            self._do_savebin(regist_code, "entityShow", "basic", result)
            # 解析html中的信息
            doc = html.fromstring(result)
            tables = doc.xpath("//div[@id='jibenxinxi']//table[@class='detailsList']")
            if tables is None or len(tables) == 0:
                Log.error("entityShow, regist code = "+regist_code+",parse_entityShow len(tables) = 0 and text:"+result + " ,url = " + url)
                print "basic info is not exist . text :\n", result
            else:
                basic_info = []
                try:
                    basic_info = self.parse_basic_info(tables[0])
                except Exception as e:
                    print "ERROR:", e, "get_entityShow-parse_basic_info text--->", result
                detail["basicInfo"] = basic_info
            m = re.search('"entityVo\.pripid":\'(\w+)\'', result)
            if m:
                pripid = m.group(1)
                #拉取投资信息/变更信息/主要人员信息/分支信息
                types = {"investorListShow":"investorList", "changeListShow":"changeList", "staffListShow":"staffList", "branchListShow":"branchList"}
                for k, v in types.items():
                    url = "http://gsxt.gzaic.gov.cn/search/search!"+k+"?_="+str(int(time.time()*1000))+"&entityVo.curPage=1&entityVo.pripid="+pripid+"&where=+where+1%3D1"
                    g = self.request_entityShow_all(regist_code, url, pripid)
                    try:
                        r = g.replace(u':null,', u':"",')
                        self._do_savebin(regist_code, "entityShow", k, spider.util.utf8str(r))
                        j = eval(r)
                        detail[v] = j[v]
                    except Exception as e:
                        print "ERROR:", e, "get_entityShow-", v, "text--->", g.decode("utf-8")
            else:
                #Log.error("entityShow, regist code = "+regist_code+",no contais entityVo.pripid..." + " ,url = " + url)
                print cname+","+regist_code+",no contais entityVo.pripid...text:\n", result
            self.saver.fs_entityShow.append(spider.util.utf8str(detail))
            print cnt, "entityShow --->", spider.util.utf8str(detail)
            #return True
            return "success"
        else:
            #Log.error("entityShow, regist code = "+ regist_code + ",  cname:"+cname+",result is None" + " ,url = " + url)
            print "entityShow page3, regist code = "+ regist_code + ", cname:" + cname+",result is None" + " ,url = " + url
            #return False
            return "proxy_error"

    def add_entityShow_cookie(self, url, headers):
        dbgdata = {}
        code = None
        while code is None:
            code = self.onl.resolve(self.get_search_image, dbgdata)
        code = spider.util.utf8str(code)
        #spider.util.FS.dbg_append_file("img_%s.jpg" % code, dbgdata['content'])
        #print "验证码--------------------------------------------------->", code, type(code)
        data = {"url": url, "code": code}
        res = None
        retry_check = 0
        while True:
            retry_check += 1
            print spider.util.utf8str(data)
            res = self.request_url("http://gsxt.gzaic.gov.cn/search/search!verify", headers=headers, data=data, timeout=15.0)
            if res is not None:
                break
            elif retry_check > 5:
                return None
            else:
                print "add_entityShow_cookie 验证码校验第[ %d ]次..."%retry_check
        if res is None:
            raise RuntimeError('entityShow ---> web down')
        #print res.code, res.text
        if res.code == 200:
            if u"根据下图内容进行判断，输入汉字或算术题计算结果" in res.text:
                print 'entityShow ---> add cookie check code retry...'
                return self.add_entityShow_cookie(url, headers)
            else:
                return res.text
        else:
            print 'entityShow ---> check code ---> res.code!=200 retry...'
            return self.add_entityShow_cookie(url, headers)


    def request_entityShow_all(self, regist_code, url, pripid, retry=0):
        res = self.request_url(url)
        if res is None:
            if retry < 5:
                retry += 1
                return self.request_entityShow_all(regist_code, url, pripid, retry=retry)
            Log.error("entityShow, regist code = "+regist_code+",request_entityShow_all resp none" + " ,url = " + url)
            print "request_entityShow_all -->", regist_code+",response none,"+url
        if res.code == 200:
            return res.text
        else:
            if retry < 5:
                time.sleep(1)
                retry += 1
                return self.request_entityShow_all(regist_code, url, pripid, retry=retry)
            Log.error("entityShow, regist code = "+regist_code+",request_entityShow_all res.code"+str(res.code) + " ,url = " + url)
            print "request_entityShow_all -->", regist_code+",response none,"+url+","+str(res.code)


    def get_search_image(self):
        url = "http://gsxt.gzaic.gov.cn/search/verify.html?random=" + str(random.random())
        headers={}
        con = self.request_url(url, headers=headers)
        if con is None:
            return None
        return con.content


#############################  GUANGZHOU  new ##########################################################

    def get_guangzhou(self, cnt, cname, url, regist_code, retry=0, qname=None):
        """
        http://gsxt.gzaic.gov.cn/aiccips/GSpublicity/GSpublicityList.html?service=entInfo_v0aMi7tSLsoEDkCy7V3bR0OgZSlziwda/oQqfoB0GjE=-50aS1uze1DaXd8Gk5PFw0A==
        """
        detail = {}
        headers = {"referer": "http://gsxt.gdgs.gov.cn/aiccips/CheckEntContext/showInfo.html"}
        result = None
        res = None
        retry_req = 0
        code = 0
        while True:
            retry_req += 1
            res = self.request_url(url, headers=headers, timeout=20.0)
            if res is not None:
                #print "code=======", res.code, self.proxies
                code = res.code
                if code == 502 or code == 503:
                    print "code=", code, "ua=", self.ua, "proxy:", self.proxies
                    time.sleep(random.randrange(0, 10, 1))
                    continue
                break
            if retry_req > 5:
                print cname, "get_guangzhou basic page failure,url=", url
                #return False
                return "proxy_error"
            print "get_guangzhou basic page retry = ", retry_req
        if code == 555 or code == 403:
            print "--- res.code=%d ---  finish...ua=%s" % (res.code, self.ua)
            #return False
            return "proxy_error"
        elif code == 404 or code == 500:
            return "page_error"
        elif code == 521:
            jscode = """
            function setTimeout(a, t){}
            window={}
            document={}
            document.attachEvent = function(a, b){b();}
            Object.defineProperty(document, "cookie", { set: function (a) { console.log(a); } });
            document.createElement = function(a){
                var r = new Object();
                r.name = a;
                r.firstChild = {href:'http://gsxt.gzaic.gov.cn/'}
                return r;
            }
            """
            text = res.text[8:-10]

            jscode += text
            try:
                cookie = spider.util.runjs(jscode)
                self.add_cookie_line('gsxt.gzaic.gov.cn', cookie)
            except Exception as e:
                print "运行node.js出现异常,", e, " res.text:\n", res.text, "获得的文本js:\n", text
                #return False
                return "page_error"
            return self.get_guangzhou(cnt, cname, url, regist_code, retry=(retry+1), qname=qname)
        elif code == 200:
            if res.text is None:
                if retry < 5:
                    print "get_guangzhou ---> res.text is none ,retry..."
                    return self.get_guangzhou(cnt, cname, url, regist_code, retry=(retry+1), qname=None)
                else:
                    print "get_guangzhou ---> basic info page res is none ,drop the task . "
                    #return False
                    return "page_error"
            else:
                result = res.text
        else:
            print cnt, cname, "广州  返回未知错误码:", code, url
            #return False
            return "proxy_error"

        if result is not None:
            if u'查询过于频繁' in result or u'请稍候再查！' in result:
                time.sleep(retry+1)
                return self.get_guangzhou(cnt, cname, url, regist_code, retry=(retry+1), qname=None)
            if "http://gsxt.gzaic.gov.cn/aiccips//images/errorinfo_new2.gif" in result:
                print cname, "The system can't display 系统无法显示", url
                #return False
                return "notdisplay"
            # m = re.search('<h2[\s\S]*注册号：(.*)</h2>',result)
            # if m:
            #     regist_code = m.group(1)
            # 解析html中的信息
            if u"该网站未在接入商腾讯云上备案" in result:
                print cnt, cname, "该网站未在接入商腾讯云上备案...", url
                return "page_error"
            doc = None
            try:
                doc = html.fromstring(result)
            except Exception as e:
                print "html.fromstring(result)发生错误:", e, " result = \n", result
                #return False
                return "page_error"
            #解析基本信息
            tables = doc.xpath("//div[@id='jibenxinxi']//table[@class='detailsList']")
            basic_info = []
            if tables is None or len(tables) == 0:
                Log.error("entityShow, regist code = "+regist_code+",parse_entityShow len(tables) = 0 and text:"+result + " ,url = " + url)
                print "basic info is not exist . text :\n", result
            else:
                try:
                    basic_info = self.parse_basic_info(tables[0])
                except Exception as e:
                    print "ERROR:", e, "get_guangzhou-parse_basic_info text--->", result
            detail["basicInfo"] = basic_info

            #股东信息
            trs = doc.xpath("//table[@id='touziren']/tr")
            investors = self.parse_investor_info(trs, url_type="entityShow", investor_type="guangzhou")
            detail["investorsInfo"] = investors
            #print "investors_info--->", spider.util.utf8str(investors)

            #变更信息
            trs = doc.xpath("//div[@id='biangeng']//table[@class='detailsList']/tr")
            changes_info = self.parse_changes_info(trs)
            detail["changesInfo"] = changes_info
            #print "changes_info--->", changes_info

            #备案信息页面
            #2.拉取备案信息
            entNo = doc.xpath("//input[@id='entNo']")[0].value
            entType = doc.xpath("//input[@id='entType']")[0].value
            regOrg = doc.xpath("//input[@id='regOrg']")[0].value
            url2 = "http://gsxt.gzaic.gov.cn/aiccips/GSpublicity/GSpublicityList.html?service=entCheckInfo"
            headers = {"Content-Type":"application/x-www-form-urlencoded",
                           "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                           "Referer":url
                           }
            data = {"entNo": entNo, "entType": entType, "regOrg": regOrg}
            res2 = self.req_GSpublicityList(cnt, cname, url2, data=data, headers=headers)
            if res2 is None:
                #return False
                return "proxy_error"
            elif res2 == "notdisplay":
                return "notdisplay"
            elif res2 == "frequently":
                return "page_error"
            self._do_savebin(regist_code, "guangzhou", "basic", result)
            self._do_savebin(regist_code, "guangzhou", "beian", res2.text)
            doc2 = html.fromstring(res2.text)

            #主要人员信息
            tables = doc2.xpath("//div[@id='zyry']/table[@class='detailsList']")
            staffs = []
            if len(tables) >= 1:
                trs = tables[0].xpath("tr")
                staffs = self.parse_staffs_info(trs)
                #print "--->", spider.util.utf8str(staffs)
            detail["staffsInfo"] = staffs

            #分支机构信息
            tables = doc2.xpath("//div[@id='branch']/table[@class='detailsList']")
            branch_info = []
            if len(tables) >= 1:
                trs = tables[0].xpath("tr")
                if len(trs) > 0:
                    branch_info = self.parse_branch_info(trs)
                #print "branch_info--->", spider.util.utf8str(branch_info)
            detail["branchInfo"] = branch_info

            self.saver.fs_guangzhou.append(spider.util.utf8str(detail))
            print cnt, "get_guangzhou --->", qname, spider.util.utf8str(detail)
            #return True
            return "success"
        else:
            #Log.error("entityShow, regist code = "+ regist_code + ",  cname:"+cname+",result is None" + " ,url = " + url)
            print "get_guangzhou page2, regist code = "+ regist_code + ", cname:" + cname+",result is None" + " ,url = " + url
            #return False
            return "page_error"

#######################################################################################


    def req_GSpublicityList(self, cnt, cname, url, **kwargs):
        #如果跑太快会导致其一直超时,所以把这里超时时间缩短进行多次重试
        timeout_retry = 1
        while True:
            kwargs['timeout'] = 50
            res = self.request_url(url, **kwargs)
            if res is None or res.code != 200:
                print cnt, cname, "get_GSpublicityList page1 request failure ,retry:", timeout_retry, "url=", url
                timeout_retry += 1
                if timeout_retry > 1:
                    #Log.error(cname+",get_GSpublicityList page1 request failure ,"+url)
                    return None
                else:
                    time.sleep(timeout_retry*2)
            else:
                if u'<img src="http://gsxt.gdgs.gov.cn/aiccips//images/errorinfo_new2.gif">' in res.text:
                    #<img src="http://gsxt.gdgs.gov.cn/aiccips//images/controlinfo_new2.gif"> 操作过于频繁,请稍后再试
                    print cname, "The system can't display 系统无法显示", url
                    return "notdisplay"
                elif '<img src="http://gsxt.gdgs.gov.cn/aiccips//images/controlinfo_new2.gif">' in res.text:
                    print cnt, "The Opreation too frequent,please try again later 操作过于频繁,请稍后再试", url
                    return "frequently"
                return res

    def get_GSpublicityList(self, cnt,  cname, url, regist_code, retry=0):
        """
        第三种情况:GSpublicityList此链接是get[基本信息]和post[备案信息]完全分开的,从第一个链接中可提取出访问备案信息所需的参数:entNo,entType,regOrg
        基本信息包含:基本信息v-股东信息v-变更信息v
        备案信息包含:主要人员信息v-分支机构信息-清算信息
        先将三个页面全部拉取下来,再进行解析,防止每次在前面的数据写入bin文件后,后面的链接又抓不到而重试的时候反复写入bin文件.
        """
        detail = {}
        #1.拉取基本信息
        content = None
        res = self.req_GSpublicityList(cnt, cname, url)
        if res is None:
            #return False
            return "proxy_error"
        elif res == "notdisplay":
            return "notdisplay"
        elif res == "frequently":
            return "page_error"
        doc = None
        # m = re.search(r"aiccips/Inform/InformLogin\.html\?regNo=(.*)&entName", res.text)
        # if m:
        #     regist_code = m.group(1)
        try:
            doc = html.fromstring(res.text)
        except Exception as e:
            print cnt, e, " ---> get_GSpublicityList basic info pages error:", res.text
            #return False
            return "page_error"

        #解析基本信息
        tables = doc.xpath("//table[@id='baseinfo']")
        if tables is None or len(tables) == 0:
            if retry < 5:
                time.sleep(2)
                return self.get_GSpublicityList(cnt, cname, url, regist_code, retry=(retry+1))
            else:
                print cnt, "get_GSpublicityList-parse_basic_info  no datas ,text--->", res.text
                #return False
                return "page_error"
        basic_info = []
        try:
            basic_info = self.parse_basic_info(tables[0])
        except Exception as e:
            print cnt, "ERROR:", e, "get_GSpublicityList-parse_basic_info ,text--->", res.text
        detail["basicInfo"] = basic_info
        self._do_savebin(regist_code, "GSpublicityList", "basic", res.text)

        #2.拉取备案信息
        entNo = doc.xpath("//input[@id='entNo']")[0].value
        entType = doc.xpath("//input[@id='entType']")[0].value
        regOrg = doc.xpath("//input[@id='regOrg']")[0].value
        #TODO 这是备案信息页 分支机构信息-清算信息 在这个页面 但未找到可解析页面 -- 目前只能拉回页面储存
        url2 = "http://gsxt.gdgs.gov.cn/aiccips/GSpublicity/GSpublicityList.html?service=entCheckInfo"
        headers = {"Content-Type":"application/x-www-form-urlencoded",
                       "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                       "Referer":url
                       }
        data = {"entNo":entNo, "entType":entType, "regOrg": regOrg}
        res2 = self.req_GSpublicityList(cnt, cname, url2, data=data, headers=headers)
        if res2 is None:
            #return False
            return "proxy_error"
        elif res2 == "notdisplay":
            return "notdisplay"
        elif res2 == "frequently":
            return "page_error"
        self._do_savebin(regist_code, "GSpublicityList", "beian", res2.text)
        doc2 = html.fromstring(res2.text)
        #解析分支机构信息
        tables = doc2.xpath("//table[@class='detailsList']")
        branchInfo = []
        flag = False
        for table in tables:
            if flag:
                break
            trs = table.xpath("tr")
            if len(trs) > 0:
                for tr in trs:
                    ths = tr.xpath("th")
                    if len(ths) == 1:
                        if ths[0].text_content().strip() == u"分支机构信息":
                            branchInfo = self.parse_branch_info(trs)
                            flag = True
                            break
        detail["branchInfo"] = branchInfo

        #3.拉取主要人员信息(备案信息页有这个信息,但是如果人员信息太多需要翻页,使用此链接可一次性取完)
        url3 = "http://gsxt.gdgs.gov.cn/aiccips/GSpublicity/vipInfoPage"
        headers = {"Content-Type":"	application/x-www-form-urlencoded; charset=UTF-8",
                   "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                   "Referer":"http://gsxt.gdgs.gov.cn/aiccips/GSpublicity/GSpublicityList.html?service=entCheckInfo",
                   "X-Requested-With":"XMLHttpRequest"
                   }
        data = {"entNo":entNo, "pageNo":1, "regOrg":regOrg}
        res3 = self.req_GSpublicityList(cnt, cname, url3, data=data, headers=headers)
        if res3 is None:
            #return False
            return "proxy_error"
        elif res3 == "notdisplay":
            return "notdisplay"
        elif res3 == "frequently":
            return "page_error"
        self._do_savebin(regist_code, "GSpublicityList", "staffsInfo", res3.text)

        #解析股东信息 --> 记得实现parse_investor_build_url(tagA,**kwargs)方法
        trs = doc.xpath("//table[@id='touziren']/tr")
        detail["investorsInfo"] = self.parse_investor_info(trs, url_type="GSpublicityList")
        #解析变更信息
        trs = doc.xpath("//div[@id='biangeng']/table[@class='detailsList']/tr")
        detail["changesInfo"] = self.parse_changes_info(trs, url_type="GSpublicityList_Changes")
        #解析主要人员信息 -->提取出JSON字符串
        m = re.search(',"list":(.*),"pageNo":', res3.content)
        result = []
        if m:
            content = m.group(1)
            content = content.replace(u':null,', u':"",')
            result = eval(content)
        list = []
        for resu in result:
            one = {}
            for k, v in resu.items():
                one[k] = v.decode("utf-8")
            list.append(one)
        detail["staffsInfo"] = list
        self.saver.fs_GSpublicityList.append(spider.util.utf8str(detail))
        print cnt, "GSpublicityList--->", spider.util.utf8str(detail)
        #return True
        return "success"



def get_gsweb_searcher(info):
    a = None
    try:
        clsname = 'SearchGSWeb' + info['pinyin']
        a = eval('%s(info)' % clsname)
    except:
        a = SearchGSWeb(info)
    a.reset()
    return a

def find_gsweb_searcher(name):
    for info in ConfigData.gsdata:
        if info["name"] == name:
            return info
        if info["pinyin"] == name:
            return info
    return None

class Saver(object):
    def __init__(self):
        self.bs = BinSaver("gsinfo_Guangdong_html.bin")
        self.fs_QyxyDetail = FileSaver("gsinfo_guangdong_QyxyDetail.txt")
        self.fs_GSpublicityList = FileSaver("gsinfo_guangdong_GSpublicityList.txt")
        self.fs_entityShow = FileSaver("gsinfo_guangdong_entityShow.txt")
        self.fs_guangzhou = FileSaver("gsinfo_guangdong_guangzhou.txt")

if __name__ == '__main__':
    spider.util.use_utf8()
    #info = find_gsweb_searcher("广东")
    #gsweb = get_gsweb_searcher(info)
    #gsweb.file_init()
    #gsweb.get_QyxyDetail("","http://www.szcredit.com.cn/web/GSZJGSPT/QyxyDetail.aspx?rid=22452b4b64014143a1432e60193d8b7c","")
    gsweb = SearchGSWebGuangdong(Saver())
    #gsweb.get_QyxyDetail("","http://www.szcredit.com.cn/web/GSZJGSPT/QyxyDetail.aspx?rid=22452b4b64014143a1432e60193d8b7c","")
    #gsweb.get_GSpublicityList("","http://gsxt.gdgs.gov.cn/aiccips/GSpublicity/GSpublicityList.html?service=entInfo_pmAWZFLysvgm3DMeAsrguLtyduqYP8a0GCh5pM7UU3z2BNr8wZHmPuRoHR0Baglm-7vusEl1hPU+qjV70QwcUXQ==","")
    #gsweb.get_entityShow("", "http://gsxt.gzaic.gov.cn/search/search!entityShow?entityVo.pripid=piZjxM7qgm8eemHf5OSGFe23Fn7T83uQJhcDa75KWdU=", "")
    #gsweb.get_guangzhou("", "", "http://gsxt.gzaic.gov.cn/aiccips/GSpublicity/GSpublicityList.html?service=entInfo_qhyuOa26FAfBIITUYW93OWCE3x5IUwx7ina/G5jZJbo=-50aS1uze1DaXd8Gk5PFw0A==","")
    gsweb.search_company("广州爱拼")
    #gsweb.test_parse()