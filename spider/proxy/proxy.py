#!/usr/bin/env python
# -*- coding:utf8 -*-

import base64
import hashlib
import os
import random
import re
import sys
import time

import spider.util
from spider.savebin import FileSaver
from spider.spider import Spider


class Util:
    @staticmethod
    def sel(c, a, b):
        return a if c else b
    @staticmethod
    def rot13(s):
        os = ''
        for ch in s:
            if (ch>='a' and ch<='z') or (ch>='A' and ch<='Z'):
                os += chr(ord(ch) + Util.sel(ch.lower() < 'n', 13, -13))
            else:
                os += ch
        return os

class ProxySpider(Spider):
    def __init__(self, thn, infile, ofile):
        Spider.__init__(self, thn)
        self.infile = infile
        self.outfile = ofile

    def dispatch(self):
        self.allproxies = {}
        self.checkedproxies = {}
        prs = []
        try:
            with open(self.infile) as f:
                for p in f:
                    prs.append(p.strip())
            os.unlink(self.outfile)
        except Exception as e:
            pass
        self.fs = FileSaver(self.outfile)
        for p in prs:
            self.queue_proxy(p)

        if len(sys.argv) > 1:
            for i in range(1,len(sys.argv)):
                self.add_main_job({'type':'url3', 'url':sys.argv[i]})
        else:
            self.add_main_job('haodailiip')
            self.add_main_job('xicidaili')
            self.add_main_job('kuaidaili')
            self.add_main_job('coolproxy')
            time.sleep(83)
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):
        self.dump_jobid(jobid)
        if isinstance(jobid, str):
            if jobid == 'haodailiip':
                for i in range(1, 40):
                    self.add_main_job({'type':'url1', 'url': "http://www.haodailiip.com/guonei/%d" % i })
                    time.sleep(2)
            if jobid == 'xicidaili':
                for i in range(1, 40):
                    self.add_main_job({'type':'url1', 'url': "http://www.xicidaili.com/nn/%d" % i })
                    time.sleep(2)
            if jobid == 'kuaidaili':
                for i in range(1, 40):
                    url = "http://www.kuaidaili.com/free/inha/%d/" % i
                    self.add_main_job({'type':'url1', 'url': url})
                    time.sleep(2)
            if jobid == 'coolproxy':
                for i in range(1,3+1):
                    url = "http://www.cool-proxy.net/proxies/http_proxy_list/country_code:CN/port:/anonymous:1/page:%d" % i
                    self.add_main_job({'type':'url2', 'url':url})
                    time.sleep(2)

        elif isinstance(jobid, dict) and jobid.get('type', '') == 'url1':
            res = self.request_url(jobid.get('url'))
            fa = re.findall(ur'<td>\s*(\d+\.\d+\.\d+\.\d+)\s*</td>\s*<td>\s*(\d+)\s*</td>', res.text, re.S)
            if len(fa) == 0:
                print res.text
            for p in fa:
                self.queue_proxy(p[0]+':'+p[1])
        elif isinstance(jobid, dict) and jobid.get('type', '') == 'url2':
            res = self.request_url(jobid.get('url'))
            fa = re.findall(ur'str_rot13\("([0-9a-z+/=]+)"\)\)\)</script></td>\s*<td>\s*(\d+)\s*</td>', res.text, re.S|re.I)
            if len(fa) == 0:
                print res.text
            for p in fa:
                prip = base64.b64decode(Util.rot13(p[0]))
                self.queue_proxy(prip+':'+p[1])
        elif isinstance(jobid, dict) and jobid.get('type', '') == 'url3':
            res = self.request_url(jobid.get('url'))
            fa = re.findall(ur'(\d+\.\d+\.\d+\.\d+):(\d+)@', res.text, re.S)
            if len(fa) == 0:
                print res.text
            for p in fa:
                self.queue_proxy(p[0]+':'+p[1])

        elif isinstance(jobid, dict) and jobid.get('type', None) == 'checkproxy':
            jdid = jobid.get('proxy', None)
            if jdid is not None:
                if self.check_proxy(jdid):
                    self.fs.append(jdid)
                    self.checkedproxies[jdid] = 1

    def get_checker_url(self, r, proxy):
        return "http://www.haohaogame.com/checkproxy.php?challenge=%d&proxy=%s" % (r,proxy)

    def check_proxy(self, proxy):
        r = random.randint(10000000,99999999)
        url = self.get_checker_url(r, proxy)
        proxies={'http':"http://%s"%proxy, 'https':"https://%s"%proxy}
        con = self.request_url(url,  proxies=proxies, timeout=3)
        if con is None:
            return False
        expect = hashlib.md5("com.ipin.checkproxy.salt%d" % r).hexdigest()
        if con.text.find(expect) >= 0:
            print "==proxy====%s====OK===" % proxy
            return True
        print con.text, expect
        return False

    def queue_proxy(self, pr):
        if self.allproxies.get(pr, 0) == 0:
            self.allproxies[pr] = 1
            self.add_job({'type':'checkproxy', 'proxy':pr})

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail('lixungeng@ipin.com', '%s DONE' % sys.argv[0], msg)


class HttpsChecker(ProxySpider):
    def dispatch(self):
        self.allproxies = {}
        self.checkedproxies = {}
        prs = []
        try:
            with open(self.infile) as f:
                for p in f:
                    prs.append(p.strip())
        except Exception as e:
            pass
        self.fs = FileSaver(self.outfile)
        for p in prs:
            self.queue_proxy(p)
        self.wait_q()
        self.add_main_job(None)

    def get_checker_url(self, r, proxy):
        return "https://www.haohaogame.com/checkproxy.php?challenge=%d&proxy=%s" % (r,proxy)



if __name__ == "__main__":
    httpsmode = 0
    infile = "proxy.txt"
    outfile = "proxy.txt"

    opts = spider.util.GetOptions("si:o:", [])
    if opts.get('-s') is not None:
        httpsmode = 1
        outfile = "proxy_https.txt"
    infile = opts.get("-i", infile)
    outfile = opts.get("-o", outfile)

    if httpsmode:
        s = HttpsChecker(15, infile, outfile)
        s.run()
    else:
        s = ProxySpider(20, infile, outfile)
        s.run()
