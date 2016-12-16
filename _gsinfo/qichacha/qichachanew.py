#!/usr/bin/env python
# -*- coding:utf8 -*-

from qcclogin import QccLogin, QccData
from spider.spider import  Spider, MRLManager, AccountErrors
from qichacha import QccPageStore
import hashlib
import time
import spider.util
import json
from spider.runtime import Log

class QccSpider2(Spider):
    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        account = [{'qqno':'285259106', 'qqpwd':'123@456'}]
        self.pagestore = QccPageStore()
        self.qcc_acc_manager = MRLManager(account, self._newqcc, shared=True)

    def _newqcc(self, ac):
        a = QccLogin(ac)
        a.load_proxy('curproxy0', index=1, auto_change=False)
        return a

    def dispatch(self):
        # self.qcclogin.do_login()
        f = open("r1.txt", "rb")

        currline = 0
        skipto =  363000
        endline = 1000000

        while currline < skipto:
            f.readline()
            currline += 1

        while currline < endline:
            line = f.readline()
            if not line:
                break
            line = line.strip()
            currline += 1
            key = line.split(" ")[-1].strip()
            job = {"kw": key, "page": "1", "type": "u1", 'line':currline}
            self.add_main_job(job)
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):
        tp =self.get_job_type(jobid)
        if tp == 'u1':
            print "searching", jobid['kw'], "line:", jobid['line']
            data = {'key':jobid['kw'], 'token': hashlib.md5('f625a5b661058ba5082ca508f99ffe1b' + jobid['kw']).hexdigest(), 'type':0}
            url = 'http://qichacha.com/gongsi_getList'
            con = self.qcc_acc_manager.el_request(url, data=data, headers={'Referer':'http://qichacha.com/'})
            if con is None:
                time.sleep(10)
                self.add_job(jobid)
                return
            try:
                if con.text.strip() == 'null':
                    print "NO DATA",  jobid['kw'], "line:", jobid['line']
                    return
                j = json.loads(con.text)
                for job in j:
                    ## [{"KeyNo":"b37b1d9b84ad1ac179ddfcef5d0d533d","Name":"\u6d1b\u9633\u7261\u4e39\u901a\u8baf\u80a1\u4efd\u6709\u9650\u516c\u53f8"}]
                    kid = job["KeyNo"]
                    name = job["Name"]
                    self.add_job({'type':'u2', 'kid':kid, 'name':name})
            except:
                Log.errorbin(jobid['kw'], con.text)
        elif tp == 'u2':
            kid = jobid['kid']
            url = 'http://qichacha.com/firm_CN_' + kid
            if self.pagestore.check_should_fetch(kid):
                con = self.request_url(url)
                if con is None:
                    self.add_job(jobid)
                    return
                if self.pagestore.save(int(time.time()), kid, url, con.text):
                    print jobid['name'],  kid, "saved"
            else:
                print "skip", kid


if __name__ == '__main__':
    spider.util.use_utf8()
    r = QccSpider2(1)
    r.load_proxy('../_zhilian/curproxy0')
    r.run()
