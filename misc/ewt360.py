#!/usr/bin/env python
# -*- coding:utf8 -*-

import copy
import json
import re

from lxml import html

from spider.racer import RaceValueByKey
from spider.savebin import BinSaver, BinReader, FileSaver
from spider.spider import Spider, AllPossibilities

class EWTSpider(Spider):
    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        self._user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:42.0) Gecko/20100101 Firefox/42.0'
        self.baseurl = 'http://www.ewt360.com/LNLQXX/SearchResult?act=mark'
        self.headers = {'Referer':self.baseurl}
        #scores = range(450,750+1) + range(449, 0, -1) + [0]
        scores =  range(750, 0, -1) + [0]
        self.possmap = {'Years':range(2009,2014+1), 'WL': ['l', 'w'], 'BZ':['b','z'], 'PiCi':0, 'Score':scores, 'ProvinceCode':0, 'page':1}
        self.bs = BinSaver("fo.bin")
        self.racer = RaceValueByKey()
        ##stacktracer.trace_start("trace.html")

    def doLogin(self):
        self.cookies = {}
        self.request_url('http://passport.ewt360.com/login/prelogin?callback=cb&sid=2&username=BOBOYI&password=1122333&fromurl=%2F&code=&isremember=1')
        print self.cookies
        return len(self.cookies.keys())

    def dispatch(self):
        self.racer.getValue('login', lambda v:self.doLogin())
        ## load saved list.
        savedlist = {}
        try:
            with open("ks") as f:
                for lines in f:
                    savedlist[lines.strip()] = 1
        except Exception as e:
            pass
        a = AllPossibilities(self.possmap, ['WL', 'BZ', 'Years', 'Score'])
        for i in a.all():
            keys = ['WL', 'BZ', 'Years', 'Score', 'page']
            ss = "%s.%s.%s.%s.%s" % (i[keys[0]],i[keys[1]],i[keys[2]],i[keys[3]],i[keys[4]])
            if ss not in savedlist:
                self.add_job({'tp':'mj', 'v':i}, True)
        self.wait_q()
        self.add_job(None, True)

    def dispatch2(self):
        with open('errlog.txt') as f:
            for lines in f:
                jm = json.loads(lines.strip())
                self.add_job({'tp':'mi', 'v':jm}, True)
        self.wait_q()
        self.add_job(None, True)

    def run_job(self,jobid):
        if isinstance(jobid, dict):
            self.dump_jobid(jobid)
            xxvalue = self.racer.oldValue('login')
            con = self.request_url(self.baseurl, params=jobid['v'], headers = self.headers)
            if con is None:
                return self.run_job(jobid)
            if re.search(u'<title>登录系统</title>', con.text) or re.search(u'您的账号未登陆或超时，请重新登', con.text):
                self.racer.delValueChecked('login', xxvalue)
                self.racer.sleepAlign(10)
                print "=======================relogin==================="
                self.racer.getValue('login', lambda v:self.doLogin())
                return self.run_job(jobid)
                #raise RuntimeError("need login")
            if jobid['tp'] == 'mj':
                m = re.search(ur'page=(\d+)[^<>]*>尾页', con.text)
                if m:
                    lp = int(m.group(1))
                    for page in range(2, lp+1):
                        v2 = copy.deepcopy(jobid['v'])
                        v2['page'] = page
                        self.add_job({'tp':'mi', 'v':v2})
            if jobid['tp'] == 'mj' or jobid['tp'] == 'mi':
                key = json.dumps(jobid['v'], ensure_ascii=0).encode('utf-8')
                self.bs.append(key, con.text)

class ParseBin:
    def __init__(self):
        self.nfs = BinSaver("parsed.bin")
        self.nks = {}
        self.errlog = FileSaver("errlog.txt")

    def get_nkey(self,jn):
        keys = ['WL', 'BZ', 'Years', 'Score', 'page']
        ss = "%s.%s.%s.%s.%s" % (jn[keys[0]],jn[keys[1]],jn[keys[2]],jn[keys[3]],jn[keys[4]])
        return ss

    def save(self, k, v):
        if k in self.nks:
            return True
        self.nks[k] = 1
        self.nfs.append(k,v)

    def isRed(self, col):
        hcode = html.tostring(col)
        m = re.search(ur'color\s*:\s*Red', hcode, re.I)
        if m:
            return True
        return False

    def go_(self, fr):
        while True:
            n,v = fr.readone()
            if n is None:
                return
            jn = json.loads(n)
            nkey = self.get_nkey(jn)
            print nkey
            if '系统检索不到您所查询的相关信息' in v:
                self.save(nkey, 'None')
                continue
            try:
                doc = html.fromstring(v)
                tbl = doc.xpath("//table[@id='tablecloth']")[0]

                otbl = []
                rowno = 0
                for rows in list(tbl):
                    rowno += 1
                    if rowno == 1:
                        continue
                    currow = []
                    colid = 0
                    for cols in rows:
                        colid += 1
                        t = re.sub(ur'\s+', u' ', cols.text_content().strip())
                        if colid == 4 and self.isRed(cols):
                            t += ".red"
                        currow.append(t)
                    otbl.append(currow)
                #print nkey, json.dumps(otbl, ensure_ascii=0).encode('utf8')
                self.save(nkey, json.dumps(otbl, ensure_ascii=0).encode('utf8'))
            except Exception as e:
                print v
                raise

    def go(self):
        fns = ['fo.bin']
        for fn in fns:
            fr = BinReader(fn)
            self.go_(fr)

if __name__ == '__main__':
    if 1:
        s = EWTSpider(4)
        s.run()
    else:
        ParseBin().go()
