#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
from spider.httpreq import BasicRequests, SessionRequests
import json
import time
import random
from spider.runtime import Log
import spider.util
import urlparse
import imghdr
from spider.captcha.onlineocr import OnlineOCR
from hashlib import md5
from lxml import html
from gsconfig import ConfigData
from lxml import html
from spider.savebin import BinSaver,FileSaver


class ImgUrlProcess(spider.util.StateMachine):
    def __init__(self):
        spider.util.StateMachine.__init__(self, [['$',0,1],['$',1,0]])
        self.ourl = ''
        self.var = ''
    def in_state(self, c):
        if self.state == 0:
            self.ourl += c
        elif self.state == 1:
            self.var += c

    def eval_var(self, var):
        if var == 'TIME':
            return str(int(time.time() * 1000))
        elif var == 'RND':
            return str(random.random())
        elif re.match(r'^RND\d+$', var):
            v = int(var[3:])
            return str(random.randint(v/10, v-1))
        else:
            Log.error("unknown variable", var)
            return ""

    def chg_state(self, sc):
        if sc[2] == 1:
            self.var = ''
        if sc[2] == 0:
            if self.var == '':
                self.ourl += '$'
            else:
                self.ourl += self.eval_var(self.var)

    def out_value(self):
        return self.ourl


class SearchGSWeb(SessionRequests):
    def __init__(self, info):
        SessionRequests.__init__(self)
        self.info = info
        self.select_user_agent('firefox')
        self._con = None
        self.onl = OnlineOCR(info['prov'])
        port = int(info['prov'])/10000 + 8000
        #self.onl.server = "http://win.haohaogame.com:%d/codeocr" % port
        self.onl.server = "http://192.168.0.10:%d/codeocr" % port
        self.code = None

    def reset(self):
        self.reset_session()
        self._con = self.request_url(self.info['url'])

    def get_image(self, dbgdata=None):
        headers = {'Referer': self.info['url']}
        con = None
        while True:
            imgurl = ImgUrlProcess().process(self.info['imgurl'])
            self.select_user_agent("=Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko LBBROWSER")
            con = self._con = self.request_url(imgurl, headers=headers, timeout=30)
            if con is not None and con.code == 200:
                if dbgdata is not None and isinstance(dbgdata, dict):
                    dbgdata["imgUrl"] = imgurl
                break
            time.sleep(random.randrange(1, 5, 1))
            print "获取验证码出错,http-code:%d , 正在重新获取......" % (0 if con is None else con.code)
            time.sleep(0.5)
            # if con is None or con.code != 200:
            #     time.sleep(random.randrange(1, 5, 1))
            #     print "获取验证码出错,http-code:%d" % (con.code if con is None else 0)
            #     continue
                #return None
        imgtype = imghdr.what(None, con.content)
        if imgtype in ['gif', 'jpeg', 'jpg', 'png', 'bmp']:
            #TODO 正式跑请注释
            spider.util.FS.dbg_save_file("pic."+imgtype, con.content)
            return con.content
        else:
            if con.content[0:1] != '<':
                Log.error("invalid image type")
                print "request captcha code error:content=%s" % con.content
            return None

    def search_company(self, kw):
        raise RuntimeError('not implemented')

    def solve_image(self, dbgdata=None):
        code = self.onl.resolve(self.get_image, dbgdata)
        return code


    def parse_basic_info(self, table):
        """
        解析基本信息
        table为xpath元素
        基本信息解析,格式符合以下标准:
        <tr><th>基本信息</th></tr>  -- 此行会自动忽略
        <tr><th>注册号</th><td>11011082608053</td></tr>
        <tr><th>类型</th><td>有限责任公司(自然人投资或控股)</td><th法定代表人</th><td>赵菊花</td></tr>
        ......
        <th>输出为Key,<td>输出为value,整体返回{"key":"value",...}
        """
        trs = table.xpath("tr")
        basic_info = {}
        for tr in trs:
            if len(tr) % 2 == 1:
                continue
            i = 1
            a = ''
            b = ''
            for t in tr:
                if i%2 == 1:
                    a = "" if t.text_content() is None else t.text_content().strip()
                else:
                    b = "" if t.text_content() is None else t.text_content().strip()
                    if a == "" and b == "":
                        continue
                    basic_info[a] = b
                i += 1
        #print "公用方法-提取到基本信息为:", spider.util.utf8str(basic_info)
        return basic_info


    def parse_investor_info(self, trs, **kwargs):
        """
        解析投资人信息
        传入table中已经选中的tr
        trs = doc.xpath("//tbody[@id='table2']/tr")
        """
        investors = []
        header = []
        if "theader" in kwargs:
            header = kwargs['theader']
        else:
            header = [u"股东类型", u"股东", u"证照/证件类型", u"证照/证件号码", u"投资详情"]
        for tr in trs:
            ths = tr.xpath("th")
            if len(ths) != 0 and len(ths) != 1:
                x = 0
                for th in ths:
                    if len(header) == x:
                        header.append("" if th.text_content() is None else th.text_content().strip())
                    else:
                        header[x] = "" if th.text_content() is None else th.text_content().strip()
                    x += 1
                #print "header:", spider.util.utf8str(header)
            tds = tr.xpath("td")
            if len(tds) == 0 or len(tds)+1 < len(header):
                continue
            if u"股东类型" in tds[0].text_content():
                continue
            i = 0
            investor = {}
            for td in tds:
                tagA = td.xpath("a")
                if len(tagA) != 0:
                    html_text = self.parse_investor_build_url(tagA[0], **kwargs)
                    if html_text is None:
                        investor[header[i]] = ""
                    else:
                        doc = html.fromstring(html_text)
                        if 'investor_type' in kwargs and "guangzhou" == kwargs['investor_type']:
                            trs = doc.xpath("//div[@id='jibenxinxi']/table[@class='detailsList']/tr")
                            header1 = [u"股东", u"股东类型", u"认缴出资额", u"出资方式", u"认缴出资日期", u"实缴出资额（万元）", u"出资方式", u"实缴出资时间"]
                            investor_detail = {}
                            for tr in trs:
                                tds = tr.xpath("td")
                                if len(tds) < len(header1):
                                    continue
                                j = 0
                                for td in tds:
                                    key = header1[j]#.decode("utf-8")
                                    investor_detail[key] = "" if td.text_content() is None else td.text_content().strip()
                                    j += 1
                            #print "公共方法-出资详情:", spider.util.utf8str(investor_detail)
                            investor[header[i]] = investor_detail
                        elif 'investor_type' in kwargs and "hunan" == kwargs['investor_type']:
                            investor_detail = {}

                            m1 = re.search('investor\.invName\s*=\s*"(.*)";', html_text)
                            if m1:
                                investor_detail[u"股东"] = m1.group(1)
                            else:
                                investor_detail[u"股东"] = ""   ##

                            m2 = re.search('invt\.subConAm\s*=\s*"(.*)";', html_text)
                            if m2:
                                investor_detail[u"认缴额（万元）"] = m2.group(1)
                            else:
                                investor_detail[u"认缴额（万元）"] = ""  ##

                            m3 = re.search('invtActl\.acConAm\s*=\s*"(.*)";', html_text)
                            if m3:
                                investor_detail[u"实缴额（万元）"] = m3.group(1)
                            else:
                                investor_detail[u"实缴额（万元）"] = ""  ##

                            m4 = re.search('invt\.conForm\s*=\s*"(.*)";', html_text)
                            if m4:
                                investor_detail[u"认缴出资方式"] = m4.group(1)
                            else:
                                investor_detail[u"认缴出资方式"] = "" ##

                            m5 = re.search('invt\.subConAm\s*=\s*"(.*)";', html_text)
                            if m5:
                                investor_detail[u"认缴出资额（万元）"] = m5.group(1)
                            else:
                                investor_detail[u"认缴出资额（万元）"] = "" ##

                            m6 = re.search('invt\.conDate\s*=\s*"(.*)";', html_text)
                            if m6:
                                investor_detail[u"认缴出资日期"] = m6.group(1)
                            else:
                                investor_detail[u"认缴出资日期"] = "" ##

                            m7 = re.search('invtActl\.conForm\s*=\s*"(.*)";', html_text)
                            if m7:
                                investor_detail[u"实缴出资方式"] = m7.group(1)
                            else:
                                investor_detail[u"实缴出资方式"] = "" ##

                            m8 = re.search('invtActl\.acConAm\s*=\s*"(.*)";', html_text)
                            if m8:
                                investor_detail[u"实缴出资额（万元）"] = m8.group(1)
                            else:
                                investor_detail[u"实缴出资额（万元）"] = "" ##

                            m9 = re.search('invtActl\.conDate\s*=\s*"(.*)";', html_text)
                            if m9:
                                investor_detail[u"实缴出资日期"] = m9.group(1)
                            else:
                                investor_detail[u"实缴出资日期"] = "" ##

                            investor[header[i]] = investor_detail
                        elif 'investor_type' in kwargs and "tianjin" == kwargs['investor_type']:
                            trs = doc.xpath("//table[@class='result-table']/tr")
                            header1 = [u"股东", u"认缴额（万元）", u"实缴额（万元）", u"认缴出资方式", u"认缴出资额（万元）", u"认缴出资日期", u"实缴出资方式", u"实缴出资额（万元）", u"实缴出资日期"]
                            investor_detail = {}
                            tds = trs[3].xpath("td")
                            j = 0
                            for td in tds:
                                key = header1[j]
                                investor_detail[key] = "" if td.text_content() is None else td.text_content().strip()
                                j += 1
                            if len(trs) < 5:
                                n = len(trs)-1
                                while n < len(header1):
                                    investor_detail[header1[n]] = ""
                                    n += 1
                            else:
                                tds = trs[4].xpath("td")
                                for td in tds:
                                    key = header1[j]
                                    investor_detail[key] = "" if td.text_content() is None else td.text_content().strip()
                                    j += 1
                            investor[header[i]] = investor_detail
                        else:
                            #trs = doc.xpath("//div[@id='sifapanding']/table[@class='detailsList']/tr")
                            trs = doc.xpath("//table[@class='detailsList']/tr")
                            if len(trs) == 0:
                                trs = doc.xpath("//table[@class='detailsList ']/tr")
                            header1 = [u"股东", u"认缴额（万元）", u"实缴额（万元）", u"认缴出资方式", u"认缴出资额（万元）", u"认缴出资日期", u"实缴出资方式", u"实缴出资额（万元）", u"实缴出资日期"]
                            investor_detail = {}
                            for tr in trs:
                                tds = tr.xpath("td")
                                if len(tds) < len(header1):
                                    continue
                                j = 0
                                for td in tds:
                                    key = header1[j]#.decode("utf-8")
                                    investor_detail[key] = "" if td.text_content() is None else td.text_content().strip()
                                    j += 1
                            #print "公共方法-出资详情:", spider.util.utf8str(investor_detail)
                            investor[header[i]] = investor_detail
                    i += 1
                else:
                    investor[header[i]] = "" if td.text_content is None else td.text_content().strip()
                    i += 1
            investors.append(investor)
        #print "公共方法-获取到投资人信息:", spider.util.utf8str(investors)
        return investors

    def parse_investor_build_url(self, tagA, **kwargs):
        """子类覆盖方法:实现从a标签中取出链接访问并返回html-->针对股东信息中出资详情页面提取-变更信息页面详情提取"""
        pass


    def parse_changes_info(self, trs, **kwargs):
        """
        解析变更信息
        """
        #trs = doc.xpath("//table[@class='detailsList']/tr")
        header = ["sequence", "changeItem", "changeBefore", "changeAfter", "changeDate"]
        changes = []
        tianjin = -1
        for tr in trs:
            tianjin += 1
            if "changes_type" in kwargs and kwargs["changes_type"] == "tianjin" and tianjin == 1:
                continue
            tds = tr.xpath("td")
            i = 1
            if len(tds) == 5:
                #如果有5个td则证明有"序号"这个表头
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
                    else:
                        #解析变更信息中的具体信息
                        doc = html.fromstring(html_text)
                        trs = doc.xpath("//div[@id='jibenxinxi']/table[@class='detailsList']/tr")
                        subjoins = []
                        header1 = []
                        for tr in trs:
                            ths = tr.xpath("th")
                            if len(ths) == 1:
                                continue
                            for th in ths:
                                header1.append("" if th.text is None else th.text.strip())
                            tds = tr.xpath("td")
                            if tds is None or len(tds) == 0:
                                continue
                            subjoin = {}
                            j = 0
                            for td in tds:
                                subjoin[header1[j]] = "" if td.text_content() is None else td.text_content().strip()
                                j += 1
                            subjoins.append(subjoin)
                        #print "公共方法-变更信息中的具体信息:", spider.util.utf8str(subjoins)
                        change[header[i]] = subjoins
                    i += 1
                    continue
                change[header[i]] = "" if td.text_content() is None else td.text_content().strip()
                i += 1
            changes.append(change)
        #print "公共方法-获取到变更信息:", spider.util.utf8str(changes)
        return changes


    def parse_staffs_info(self,trs):
        """解析主要人员信息"""
        header = [u"序号", u"姓名", u"职务"]
        staffs = []
        for tr in trs:
            tds = tr.xpath("td")
            if len(tds) % 3 == 0:
                i = 0
                while i < len(tds):
                    td1 = "" if tds[i].text is None else tds[i].text.strip()
                    td2 = "" if tds[i+1].text is None else tds[i+1].text.strip()
                    td3 = "" if tds[i+2].text is None else tds[i+2].text.strip()
                    if td1 == "" and td2 == "" and td3 == "":
                        i += 3
                        continue
                    staff = {u"序号":"" if tds[i].text is None else tds[i].text.strip(),
                             u"姓名":"" if tds[i+1].text is None else tds[i+1].text.strip(),
                             u"职务":"" if tds[i+2].text is None else tds[i+2].text.strip()}
                    i += 3
                    staffs.append(staff)
        return staffs


    def parse_branch_info(self, trs, **kwargs):
        #trs = doc.xpath("//tbody[@id='table2']/tr")
        branches = []
        header = None
        if "header" in kwargs:
            header = kwargs["header"]
        else:
            header = [u"序号", u"注册号", u"名称", u"登记机关"]
        for tr in trs:
            ths = tr.xpath("th")
            if len(ths) > 1:
                header = []
                for th in ths:
                    header.append(th.text_content().strip())
            else:
                tds = tr.xpath("td")
                if len(tds) == 1 or len(tds) == 0:
                    continue
                if u"序号" in tds[0].text_content():
                    continue
                branch = {}
                i = 0
                for td in tds:
                    branch[header[i]] = "" if td.text_content() is None else td.text_content().strip()
                    i += 1
                branches.append(branch)
        return branches
        #print "分支机构:", spider.util.utf8str(branches)


class SearchGSWebJilin(SearchGSWeb):
    def get_image(self):
        con = SearchGSWeb.get_image(self)
        if con is None and self._con is not None and self._con.content[0:1] == '<':
            m = re.search(r"<script>(.*?)</script>", self._con.text)
            sc = "document={}, window={location:{reload:function(){console.log(document.cookie)}}}\n"
            sc += m.group(1)
            sc += "\nchallenge()\n"
            rv = spider.util.runjs(sc)
            # rv : ROBOTCOOKIEID                   =a2744fd2492cee23d5a143453449ecc3ce99b38f; max-age=600 ; path=/
            domain = urlparse.urlparse(self.info['imgurl']).netloc
            self.add_cookie_line(domain, rv.strip())
            con = SearchGSWeb.get_image(self)
        return con


class SearchGSWebAnhui(SearchGSWeb):
    def get_image(self):
        con = SearchGSWeb.get_image(self)
        if con is None and self._con is not None and self._con.content[0:1] == '<':
            m = re.search(r"<script>(.*?)</script>", self._con.text)
            sc = "document={}; window={}; setTimeout=function(){}\n"
            sc += m.group(1)
            sc += "\nconsole.log(dc)\n"
            rv = spider.util.runjs(sc)
            domain = urlparse.urlparse(self.info['imgurl']).netloc
            self.add_cookie_line(domain, rv.strip())
            con = SearchGSWeb.get_image(self)
        return con


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


# 湖南省
class SearchGSWebHunan(SearchGSWeb):
    def check_captcha(self, token):
        headers={'Referer': self.info['url']}
        while True:
            self.code = self.solve_image()
            mm = self.request_url("http://gsxt.hnaic.gov.cn/notice/security/verify_captcha",
                         data = {"captcha":self.code, "session.token":token}, headers=headers)
            print "code=",self.code, "result=", mm.text
            if mm.text == 0:
                continue
            elif mm.text == 1:
                return True
        raise RuntimeError("failed")

    def search_company(self, kw):
        try:
            token = None
            if self._con:
                m = re.search('name: "session.token",code: "(.*?)",data:', self._con.text)
                if m:
                    token = m.group(1)
            if token is None:
                self.reset()
            print "token = ", token
            if not self.check_captcha(token):
                return False
            headers={'Referer': self.info['url']}
            infourl = "http://gsxt.hnaic.gov.cn/notice/search/ent_info_list"
            si = self.request_url(infourl, data={"captcha":self.code, "session.token":token, "condition.keyword":kw}, headers=headers)
            dom = html.fromstring(si.text, infourl)
            out = []
            for d in dom.xpath("//div[@class='list-item']"):
                a1 = d.xpath(".//a")[0]
                s1 = d.xpath(".//span")[0]
                oi = {"name": a1.text_content(),
                      "url": a1.attrib['href'],
                      "regcode":s1.text_content()}
                out.append(oi)
            print json.dumps(out, indent=4, ensure_ascii=0).encode('utf-8')
            return out
        except:
            return False






# 北京市
class SearchGSWebBeijing(SearchGSWeb):
    def search_company(self, kw):
        headers={'Referer': self.info['url']}
        ticket = None
        if self._con:
            m = re.search('credit_ticket.*value="(.*?)"', self._con.text)
            if m:
                ticket = m.group(1)
        if ticket is None:
            self.reset()
        data = {"credit_ticket":ticket, "currentTimeMillis":int(time.time()*1000), "keyword":kw}
        data["checkcode"] = self.solve_image()
        con = self.request_url("http://qyxy.baic.gov.cn/gjjbj/gjjQueryCreditAction!getBjQyList.dhtml", data=data, headers=headers)
        if con is None:
            return False
        if u"您搜索的条件无查询结果" in con.text:
            return []
        dom = html.fromstring(con.text)
        lst = dom.xpath("//div[@class='list']/ul")
        if len(lst) == 0:
            # 验证码错误
            return False
        out = []
        for d in lst:
            href = d.xpath(".//a")[0].attrib['onclick']
            href = re.sub(';\s*', '', href)
            name, entid, regcode, cc = eval(re.sub('openEntInfo', '', href))
            url = 'http://qyxy.baic.gov.cn/gjjbj/gjjQueryCreditAction!openEntInfo.dhtml?entId={}&credit_ticket={}&entNo={}&timeStamp={}'
            url = url.format(entid, cc, regcode, int(time.time()*1000))
            self.get_detail(url)
            out.append({"name":name, "url":url, "regcode":regcode})
        return out


    def get_detail(self, url):
        res = self.request_url(url)
        if res is not None and res.code == 200:
            print res.text
        else:
            print "---none---" if res is None else res.code

    def parse_investor_build_url(self, tagA):
        onclick = tagA[0].attrib.get("onclick", '')
        m = re.search("viewInfo\('(.*)'\)", onclick)
        if m:
            param = m.group(1)


def test_parse():
    doc = None
    with open("reginster.html", 'rb') as f:
        text = f.read()
        doc = html.fromstring(text)



    m = re.search('"entityVo\.pripid":\'(\w+)\'', text)
    if m:
        pripid = m.group(1)
        print pripid
    else:
        print "----"




if __name__ == '__main__':
    #info = find_gsweb_searcher("北京")
    #gsweb = get_gsweb_searcher(info)
    # print spider.util.utf8str(gsweb.search_company('腾讯科技'))
    test_parse()

    # search_company 应当返回False,如果查询是失败的
    # 应该返回[],如果查询成功了,但确实没有数据
    # info = find_gsweb_searcher("广东")
    # gsweb = get_gsweb_searcher(info)
    # gsweb.file_init()
    #gsweb.get_QyxyDetail("","http://www.szcredit.com.cn/web/GSZJGSPT/QyxyDetail.aspx?rid=0f8eee502c834f1b99bdc89930869b9f","")
    # #gsweb.run_get_detail('腾讯科技')
    #gsweb.get_GSpublicityList("","http://gsxt.gdgs.gov.cn/aiccips/GSpublicity/GSpublicityList.html?service=entInfo_73bZ9gfiF4QL7xjoE8ybc7rCMYkO84xLk4AYJLJlQdvzOmA43CX967XrxGFt5Fwr-7kW54gFL28iQmsO8Qn3cTA==","")
    #gsweb.get_entityShow("", "http://gsxt.gzaic.gov.cn/search/search!entityShow?entityVo.pripid=MAypu_BXpG0l0YTCP0wv3O1j9KPbKTVpxYX6U1Jgymo=","")



