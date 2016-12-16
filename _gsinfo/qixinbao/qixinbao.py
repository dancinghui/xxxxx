#! /usr/bin/env python
# encoding:utf-8
import base64
import json
import os
import re
import sys
import time
import traceback
from urllib import quote
from spider.ipin.savedb import PageStoreBase
from spider.spider import Spider, MultiRequestsWithLogin
import spider.runtime


class QxbLogin(MultiRequestsWithLogin):
    def __init__(self, acc):
        MultiRequestsWithLogin.__init__(self, acc)
        self.header = {}

    def _real_do_login(self):
        start_url = r"http://www.qixin.com/login"
        con = self.request_url(start_url)
        jsstr = con.text.replace("<script>", "").replace("</script>", "").replace("document.cookie=dc",
                                                                                  "console.log(dc)")
        f = open("login.js", "w+b")
        f.write(jsstr)
        f.close()
        os.system("nodejs login.js > cookiestr.txt")
        cookiestr = open("cookiestr.txt", "r+b").readline().strip().split(";")[0]
        timestr = str(int(time.time() * 1000))
        header = {"Cookie": cookiestr}
        con2 = self.request_url("http://www.qixin.com/service/getCaptcha?_=" + timestr, headers=header)
        imagestr = base64.decodestring(re.findall(r'imgSrc":"(.*?)"', con2.text)[0])
        f = open("validcode.jpg", "wb")
        f.write(imagestr)
        f.close()
        print "input valid code:"
        imagecode = sys.stdin.readline().strip()
        md5str = re.findall(r'"code":"(.*?)"', con2.text)[0]

        data = {"userAcct": self.account["username"], "userPassword": self.account["password"], "userQrCode": imagecode,
                "md5String": md5str}
        con3 = self.request_url("http://www.qixin.com/service/login?returnURL=http%3A%2F%2Fwww.qixin.com%2F", data=data, headers=header, allow_redirects=False)
        userinfo = json.loads(con3.text).get("data", None)
        if userinfo is None or userinfo.get("status") != 0:
            spider.runtime.Log.warning("Logging failed!!!!!!!!!!!!! No user info return!")
            return False
        else:
            spider.runtime.Log.warning("account " + self.account["username"] + " logging success.")
        userdata = userinfo.get("data", None)
        header["Cookie"] = header["Cookie"] + ";userKey=" + userdata.get("userKey") + ";userValue=" + userdata.get("userValue")
        con4 = self.request_url("http://www.qixin.com/login?returnURL=http%3A%2F%2Fwww.qixin.com%2F", data={"account":self.account["username"], "password":self.account["password"]}, headers=header)
        self.header = header
        return True


class QxbPageStore(PageStoreBase):
    def getopath(self):
        dirs = ['/home/peiyuan/data/qixinbao', '/opt/_test_store_']
        for di in dirs:
            if os.path.isdir(di) and os.access(di, os.W_OK):
                return di
        raise RuntimeError("no dir to write files.")
    
    def __init__(self):
        PageStoreBase.__init__(self, "qixinbao")

    def page_time(self):
        return 1450346105*1000

    def check_should_fetch(self, cpid):
        indexUrl = "%s://%s" % (self.channel, cpid)
        if self.find_any(indexUrl):
            return False
        return True

    def extract_content(self):
        m = re.search(ur'工商基本信息(.*?)您可能感兴趣的企业', self.get_cur_doc().cur_content, re.S)
        if m:
            a = re.sub(ur'<[a-zA-Z/!][^<>]*>', '', m.group(1))
            return a.strip()
        spider.runtime.Log.error(self.get_cur_doc().cur_url, "no content")
        return None

class QxbSpider(Spider):
    def __init__(self, acc, threadcnt):
        Spider.__init__(self, threadcnt)
        self.qxbLogin = QxbLogin(acc)
        self.pagestore = QxbPageStore()
        self.qxbLogin.do_login()
        
    def dispatch(self):
        f = open("/home/peiyuan/r1.txt", "rb")
        currline = 0
        skip = 0
        endline = 100
        while currline < skip:
            line = f.readline()
            currline += 1
        
        while currline < endline:
            line = f.readline()
            key = line.strip().split(" ")[-1].strip()
            job = {"key":key, "type":"u1"}
            self.add_main_job(job)
            currline += 1
        self.wait_q()
        self.add_main_job(None)
        
        
    def run_job(self, job):
        spider.runtime.Log.info("running job:" + job.__str__())
        time.sleep(3)
        if job["type"] == "u1":
            self.qxbLogin.header["Referer"] = r"http://www.qixin.com/?from=wap"
            con = self.qxbLogin.request_url("http://www.qixin.com/searchengine/suggestion?key="+quote(job["key"])+"&_=" + 
                                            str(int(time.time() * 1000)), headers=self.qxbLogin.header)
            if con is None :
                spider.runtime.Log.error("Request return None! job:" + job.__str__())
                self.re_add_job(job)
                return
            if con.text.strip() is "":
                spider.runtime.Log.error("Request return empty text! job:" + job.__str__())
                self.re_add_job(job)
                return
            
            if ur"重新载入页面以获取源代码"  in con.text:
                spider.runtime.Log.error("to login......job:"+ job.__str__())
                self.qxbLogin.set_nologin()
                self.qxbLogin.do_login()
                self.re_add_job(job)
                return
            try:
                list_back = json.loads(con.text.strip())
            except Exception as e:
                traceback.print_exc()
            if len(list_back) == 0:
                spider.runtime.Log.error("No data! job:" + job.__str__())
                return
            else:
                for item in list_back:
                    corp_name = item["name"]
                    corp_eid = item["eid"]
                    jobb = {"corp_name":corp_name, "corp_eid":corp_eid, "type":"u2"}
                    self.add_job(jobb)
        
        if job["type"] == "u2":
            if not self.pagestore.check_should_fetch(job["corp_eid"]):
                print "skip", job["corp_eid"]
                return
            con = self.qxbLogin.request_url("http://www.qixin.com/company/gongsi_CN_" + job["corp_eid"], headers=self
                                            .qxbLogin.header)
            if con is None :
                spider.runtime.Log.error("Request return None! job:" + job.__str__())
                self.re_add_job(job)
                return
            if con.text.strip() is "":
                spider.runtime.Log.error("Request return empty text! job:" + job.__str__())
                self.re_add_job(job)
                return
            
            if ur"可查看更多信息"  in con.text:
                #未登录
                self.qxbLogin.set_nologin()
                self.re_add_job(job)
                self.qxbLogin.do_login()
                return
            if ur"您当日的访问次数过多"  in con.text:
                self.qxbLogin.set_nologin()
                spider.runtime.Log.error("账号%s被限制\n"  % self.qxbLogin.account["username"])
                exit()
            if job["corp_name"] in con.text:
                if self.pagestore.save(int(time.time()), job["corp_eid"], "http://www.qixin.com/company/gongsi_CN_" + job["corp_eid"], con.text):
                    print job['corp_name'],  job["corp_eid"], "saved"
                else:
                    print "skip:", job['corp_name'], job['corp_eid']
            else:
                spider.runtime.Log.error("Can not find corp_name:%s in content ...." % job["corp_name"])
                print con.text
                self.re_add_job(job)
                
            
            
            
        
if __name__ == "__main__":
    spider.util.use_utf8()
    qxbspider = QxbSpider({"username":"18664657206", "password":"138138"}, 1)
    qxbspider.run()
