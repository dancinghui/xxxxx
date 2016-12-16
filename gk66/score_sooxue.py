#coding:utf-8

import os
import urllib
import urllib2
import cookielib
import traceback
import zlib
import mongoengine
import time
import random
import re
from code_process import get_code
from proxy import get_proxy_and_confirm
import socket
socket.setdefaulttimeout(0)

from gzip import GzipFile
from StringIO import StringIO

from bs4 import BeautifulSoup

mongoengine.connect(None,alias="gaokao_score",host="mongodb://crawler:crawler@192.168.1.81,192.168.1.82,192.168.1.83/gaokao_crawler",socketKeepAlive=True,wtimeout=100000)

province_code_map={ "安徽":34, "北京":11, "重庆":50, "福建":35, "广东":44, "甘肃":62, "广西":45, "贵州":52, "河北":13, "湖北":42, "黑龙江":23, "河南":41, "湖南":43, "海南":46, "吉林":22, "江苏":32, "江西":36,
    "辽宁":21, "内蒙古":15, "宁夏":64, "青海":63, "山西":14, "上海":31, "山东":37, "四川":51, "陕西":61, "天津":12, "新疆":65, "西藏":54, "云南":53}
wenli_code_map={"文科":1,"理科":5}

account_list=[
    ["999177273","242442"],
    ["999234123","785245"],
    ["999666566","135643"]
]

class ContentEncodingProcessor(urllib2.BaseHandler):
    """A handler to add gzip capabilities to urllib2 requests """

    # add headers to requests
    def http_request(self, req):
        req.add_header("Accept-Encoding", "gzip, deflate")
        return req

    # decode
    def http_response(self, req, resp):
        old_resp = resp
        # gzip
        if resp.headers.get("content-encoding") == "gzip":
            gz = GzipFile(
                fileobj=StringIO(resp.read()),
                mode="r"
            )
            resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code)
            resp.msg = old_resp.msg
        # deflate
        if resp.headers.get("content-encoding") == "deflate":
            gz = StringIO( deflate(resp.read()) )
            resp = urllib2.addinfourl(gz, old_resp.headers, old_resp.url, old_resp.code)  # 'class to add info() and
            resp.msg = old_resp.msg
        return resp


class RedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        print "*****************302**********************"
        return urllib2.HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)

def deflate(data):   # zlib only provides the zlib compress format, not the deflate format;
    try:               # so on top of all there's this workaround:
        return zlib.decompress(data, -zlib.MAX_WBITS)
    except zlib.error:
        return zlib.decompress(data)

def _do_get(opener, url):
    req = urllib2.Request(url)
    req.add_header("User-Agent", "Mozilla/4.0 (compatible; MSIE 7.0;"
                                 " Windows NT 5.1; Trident/4.0; "
                                 ".NET CLR 2.0.50727; .N ET4.0C; .NET4.0E)")
    resp = opener.open(req)
    return resp.read()

def _do_post(opener, url, data):
    req = urllib2.Request(url, data)
    req.add_header("User-Agent", "Mozilla/4.0 (compatible; MSIE 7.0;"
                                 " Windows NT 5.1; Trident/4.0; "
                                 ".NET CLR 2.0.50727; .N ET4.0C; .NET4.0E)")
    print req.headers
    resp = opener.open(req)
    return resp.read()

class ScoreSooxue:

    def __init__(self,account_list):
        self.have_get_parm_path=os.path.join(os.path.dirname(__file__),"have_get_parm.txt")
        self.html_content_file=open(os.path.join(os.path.dirname(__file__),"html_content.txt"),'a')
        self.have_get_parm=self.get_have_get_parm()
        self.data_file=open(os.path.join(os.path.dirname(__file__),"score_sooxue_data.txt"),'a')
        self.account_list=account_list
        self.account_should_config=None
        self.current_balance=-1
        self.__VIEWSTATE=None
        self.__EVENTVALIDATION=None
        self.current_account=None

    def func_retry(self,func,**kwargs):
        retry=3
        while retry>=0:
            try:
                return func(**kwargs)
            except:
                traceback.print_exc()
                retry-=1
        raise RuntimeError("重复3次超时")

    def do_get(self,opener,url):
        content=self.func_retry(_do_get,opener=opener,url=url)
        if "window.location" in content:
            url="http://%s/%s"%("gk.sooxue.com",re.search('location="(\S*)"',content).group(1))
            print "js跳转",url
            content=self.do_get(opener,url)
        return content

    def do_post(self,opener,url,data):
        content=self.func_retry(_do_post,opener=opener,url=url,data=data)
        if "window.location" in content:
            url="http://%s/%s"%("gk.sooxue.com",re.search('location="(\S*)"',content).group(1))
            content=self.do_post(opener,url,data)
            print "js跳转",url
        return content

    def get_have_get_parm(self):
        have_get_parm=set()
        if not os.path.exists(self.have_get_parm_path):
            return set()
        with open(self.have_get_parm_path) as f:
            while True:
                line=f.readline()
                if not line:break
                have_get_parm.add(line.strip())
        return have_get_parm

    def logout(self,):
        self.do_get(self.opener,"http://gk.sooxue.com/login.aspx?action=logout")
        print "登出账号:%s"%self.current_account[0]
        self.current_account=None
        self.current_balance=-1
        self.opener=None

    def login(self,username,pawword):
        login_url="http://gk.sooxue.com/login.aspx"
        data={
            "username":username,
            "password":pawword,
            "x":49,
            "y":40
        }
        self.do_post(self.opener,login_url,urllib.urlencode(data))
        self.current_account=[username,pawword]
        print "登录账号:%s"%username

    def switch_proxy(self,opener):
        for handler in opener.handlers:
            if isinstance(handler,urllib2.ProxyHandler):
                opener.handlers.remove(handler)
        ip=get_proxy_and_confirm()
        print "设置代理:%s"%ip
        proxy = {'http':ip}
        proxy_support = urllib2.ProxyHandler(proxy)
        opener.add_handler(proxy_support)

    def init_opener(self):
        cookieJar = cookielib.CookieJar()
        handlerCookie = urllib2.HTTPCookieProcessor(cookieJar)
        handlerDebug = urllib2.HTTPHandler(debuglevel=1)
        # encoding_support = ContentEncodingProcessor()
        opener = urllib2.build_opener(handlerCookie, handlerDebug,RedirectHandler)
        self.switch_proxy(opener)
        return opener

    def switch_account(self):
        if self.current_account:
            self.logout()
        while self.account_list:
            self.opener=self.init_opener()
            username,pawword=self.account_list.pop(0)
            self.login(username,pawword)
            self.accountConfig(self.account_should_config[0],self.account_should_config[1])
            self.__VIEWSTATE,self.__EVENTVALIDATION=self.get_viewstate_for_query()
            print "账号余额:%s"%self.current_balance
            if self.current_balance>20:
                return
        print "账号已经全部用完！"
        raise RuntimeError("账号已经全部用完！")

    def accountConfig(self,province,wenli):
        province_code=province_code_map.get(province,None)
        if not province_code:
            raise RuntimeError("没有找到对应的省份")
        wenli_code=wenli_code_map.get(wenli,None)
        if not wenli_code:
            raise RuntimeError("没有找到对应的科类")
        config_url="http://gk.sooxue.com/myConfig.aspx"
        content=self.do_get(self.opener,config_url)
        soup=BeautifulSoup(content)
        # pdb.set_trace()
        viewstat=soup.find(id="__VIEWSTATE")["value"]
        eventvalidation=soup.find(id="__EVENTVALIDATION")["value"]
        data={
            "__EVENTTARGET":"",
            "__EVENTARGUMENT":"",
            "__VIEWSTATE":viewstat,
            "__EVENTVALIDATION":eventvalidation,
            "ctl00$PageContent$ssdm1":province_code,
            "ctl00$PageContent$kldm1":wenli_code,
            "ctl00$PageContent$Button1":"提交"
        }
        self.do_post(self.opener,config_url,urllib.urlencode(data))

    def get_viewstate_for_query(self):
        url="http://gk.sooxue.com/query.aspx"
        content=self.do_get(self.opener,url)
        soup=BeautifulSoup(content)
        # pdb.set_trace()
        # print content
        __VIEWSTATE=soup.find(id="__VIEWSTATE")["value"]
        __EVENTVALIDATION=soup.find(id="__EVENTVALIDATION")["value"]
        self.current_balance=int(soup.find(id="ctl00_lb_point").get_text())
        return __VIEWSTATE,__EVENTVALIDATION

    def code_processer(self,content):
        code_path=os.path.join(os.path.dirname(__file__),"code.png")
        code_url="http://gk.sooxue.com/VerifyCode.aspx?"
        content=self.do_get(self.opener,code_url)
        print u"获取验证码"
        vcode=get_code(content)
        soup=BeautifulSoup(content)
        data={
            "__VIEWSTATE":soup.find(id="__VIEWSTATE")["value"],
            "__EVENTVALIDATION":soup.find(id="__EVENTVALIDATION")["value"],
            "TextBox1":vcode,
            "Button1":"验证码校验"
        }
        url="http://gk.sooxue.com/%s"%soup.find(id="form1")["action"]
        content=self.do_post(self.opener,url,urllib.urlencode(data))
        print "sleep 10秒"
        return content

    def get_page(self,year,benzhuan,score,province,wenli,params_path):
        url="http://gk.sooxue.com/query.aspx"
        data={
                "__VIEWSTATE":self.__VIEWSTATE,
                "__EVENTVALIDATION":self.__EVENTVALIDATION,
                "ctl00$PageContent$cengci_6":benzhuan,
                "ctl00$PageContent$year_2":year,
                "ctl00$PageContent$queryType_2":"fs",
                "ctl00$PageContent$inputValue_2":score,
                "ctl00$PageContent$btnTfswcKsqx":"查看考生去向（20搜学币）"
            }
        content=self.do_post(self.opener,url,urllib.urlencode(data))
        content_dict={
            "parms":params_path.split(','),
            "content":content
        }
        self.html_content_file.write(str(content_dict)+"\n")

        while "由于操作速度过快，系统需要您输入验证码" in content:
            print "出现验证码：识别中..."
            content=self.code_processer(content)
        if "没有找到您查询分数或位次的录取信息" in content:
            return
        soup=BeautifulSoup(content)
        tables=soup.find_all("table","border4")
        self.current_balance=int(soup.find(id="ctl00_lb_point").get_text())
        for table in tables:
            batch=table.get_text()
            content=table.find_next("table")
            rows=content.find_all("tr")[1:]
            for row in rows:
                items=row.find("td")
                school_name=items[0].get_text()
                major_name=items[1].get_text()
                score_number=items[2].get_text()
                spec_number=items[3].get_text()
                print year,benzhuan,score,province,wenli,school_name,major_name,score_number,spec_number
                row={
                    "score":score,
                    "batch":batch,
                    "location":province,
                    "bz":benzhuan,
                    "school":school_name,
                    "score_number":score_number,
                    "spec":major_name,
                    "spec_number":spec_number,
                    "wl":wenli,
                    "year":year
                }
                self.data_file.write(str(row)+"\n")

    def builder_parameter(self,province_list,year_list):
        for province in province_list:
            for year in year_list:
                for wenli in ["文科","理科"]:
                    for benzhuan in ["本科","专科"]:
                        yield province,year,wenli,benzhuan

    def process(self,year,benzhuan,province,wenli):
        for score in range(0,750):
            try:
                params_path="%s,%s,%s,%s,%s"%(province,year,wenli,benzhuan,score)
                if params_path in self.have_get_parm:continue
                self.get_page(year,benzhuan,score,province,wenli,params_path)
                self.have_get_parm_file.write(params_path+"\n")
                time.sleep(random.randint(5,10))
                if self.current_balance<20:
                    print "账号:%s已经使用完,切换账号"%self.current_account[0]
                    self.switch_account()
            except:
                traceback.print_exc()
                current_account=self.current_account
                self.init_opener()
                self.login(current_account[0],current_account[1])

    def run(self,province_list,year_list):
        self.have_get_parm_file=open(self.have_get_parm_path,'a')
        for province,year,wenli,benzhuan in self.builder_parameter(province_list,year_list):
            self.account_should_config=[province,wenli]
            if not self.current_account or self.current_balance <20:
                self.switch_account()
            self.process(year,benzhuan,province,wenli)


if __name__ == '__main__':
     #import ipdb,sys
     #def info(type,value,tb):
     #    traceback.print_exception(type,value,tb)
     #    ipdb.pm()
     #sys.excepthook=info
     #ipdb.launch_ipdb_on_exception()
     soonxue=ScoreSooxue(account_list)
     province_list=["青海"]
     year_list=[2013]
     soonxue.run(province_list,year_list)
