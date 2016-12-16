#!/usr/bin/env python
# encoding:utf8
from spider.spider import Spider
from spider.httpreq import SessionRequests, CurlReq
import spider.util
import pycurl
import cutil
import json
import abc
from spider.runtime import Log
import time

class TestXXLogin(SessionRequests):
    def do_login(self):
        url = "http://www.youzy.cn/ajaxpro/Zero.Web.Pc.AjaxServices.Users.Auth,Zero.Web.Pc.ashx"
        param = {"input":{"Username":"nameanmesfdsdf","Password":"passwordsdf"}}
        headers={'Content-Type': 'text/plain; charset=UTF-8', 'X-AjaxPro-Method': 'Login', "Referer": "http://www.youzy.cn/hunan"}
        con = self.request_url(url, data=spider.util.utf8str(param), headers=headers)
        print con.text


class TestSpider(Spider):
    def dispatch(self):
        self.add_main_job('hehe')
        self.wait_q()
        self.add_main_job(None)
    def run_job(self, jobid):
        if jobid is 'hehe':
            con = self.request_url('http://jobs.51job.com/shanghai-pdxq/66595374.html')
            print "text length=", len(con.text.encode('utf-8'))
            print con.request.headers
            print con.text


from spider.spider2 import AioSpider, AioRunner


class MyRunner(AioRunner):
    def __init__(self, a, b,c):
        AioRunner.__init__(self, a, b, c)
        self.baset = time.time()
    def dbg(self, r):
        if '8.8' in self.selproxy:
            Log.error("dbg", r, time.time() - self.baset)
    def prepare_req(self, job, curl, proxies):
        self.dbg('prepare')
        pa = AioRunner.prepare_req(self, job, curl, proxies)
        if pa is not None:
            return pa

        if 'value' in job:
            url = "https://www.linkedin.com/jobs2/view/%d" % job['value']
        else:
            url = job['url']
        print "[%d] prepare %s proxies=" % (self.idx, url), proxies
        headers={}
        if 'ip.cn' in url:
            headers['User-Agent'] = 'curl/7.20.1'
        curl.prepare_req(url, headers=headers, proxies=proxies)
        return True

    def on_result(self, curl, resp):
        self.dbg('result')
        AioRunner.on_result(self, curl, resp)
        print resp.request.url, resp.code

    def on_error(self, curl, errcode, errmsg):
        self.dbg('error')
        AioRunner.on_error(self, curl, errcode, errmsg)
        print "[%d] error, proxy_errcnt=%d" % (self.idx, self.proxyerr)
        print "with: code=%d msg=%s" % (errcode, errmsg)


class MyMulti(AioSpider):
    def __init__(self):
        AioSpider.__init__(self, MyRunner)
        self.proxies = []
        #self.proxies.append('183.61.111.233:18888:ipin:ipin1234')
        #self.proxies.extend('122.13.71.178:18888:ipin:ipin1234')
        self.proxies.append('211.157.100.8:18889:ipin:helloipin')
        self.proxies.append('211.157.100.10:18889:ipin:helloipin')
        self.proxies.append('211.157.100.12:18889:ipin:helloipin')
        self.proxies.append('8.8.8.8:8888')

    def init_jobs(self):
        #self.add_job({'url': 'http://baidu.com/'})
        #self.add_job({'url': 'http://youtube.com/'})
        self.add_main_job_range({}, 1, 200)


import base64
from Crypto.Cipher import AES

class CCIQ_AES:
    def __init__( self, key = None ):
        self.key = key
        if self.key is None:
            self.key = "9BF70E91907CA25135B36B5328AF36C4"
        BS = 16
        self.pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
        self.unpad = lambda s : s[:-ord(s[len(s)-1:])]

    def encrypt(self, raw):
        iv = "\0" * 16
        raw = self.pad(raw)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(raw))

    def decrypt( self, enc ):
        iv = "\0" * 16
        enc = base64.b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.unpad(cipher.decrypt(enc))


req = {"extJson":"ctlCXDvoyaH2pCIArrgvXp7zrZTzpz2Q5rukh+aWvupEFABw6P2AvbmaN+HJ7IZgDJ\/kgBkJt\/rLppSGitYCPKGR2IGv6OXZsrJGgbRB3G1U2wdOlL49\/aDwt3NZNp4TGa5iBFpYLm69F\/6PPFoXIR\/Aw5p48\/\/8OgZFpddDUwQ=","encryptedJson":"YiQM\/+Gilfpd5l8S4MfvN6RLeBPNGQ0D679BdYtPzcgEQJl\/rWzuWabMkEvWHt691rkxaY1+wlhTo4pRilRYiZt3eB7j1DU69dn890P6RNQ="}
vv = {"c":"tAsfsEjYbL65f0IRxdRqSg+KsHdR/zlH3aSQhnW40wTjUNJlJULuYY+T+X/cJfrTlYrTECBYLV1Cbo7VpIHL+7dh1Zx0CoE08DcsGJQL0vHzfrzikDdm0cIpjgnLKrmmigCOo/8s7LTVYoNwXfBDXhXwStJ2nBmpLBA+3PlGB2EfWOBDW4Sw8lR/i6N4F5+Wtb/rOUKMRhMpjOjxWLqeqDG32ce5m/bpKBzUQQCfv8sgitVhcMZWLbIKybmg0WLkhq+1QyLrlKMnOXre+TTNzghQbq/59KohIUNyghGCrpZzeIcXJrVmCD2XwH7wP80MtmPQpX/HW3arXpjm9i5FlLOb+ptFMah31yp4XstZY8rEwV8Mum1C+ItAsnXhkPtwHC/eurASU5Pae6dVWwV8G+/RF8KP+s43Q24ry4feThUB2wGJTh+m0fVCMPT/ivLesCJKDMGimObDuv1gOY9bCfKlw0P3VOkqIfcfGS4Lxo/GrQYaCamFP2anezJFfrKJ5Itb8y+9FIZFutXW1RWLtnC6GZ4lkWKsZCqlHOvYlsIehz2ibt87ZnBcXUQU6AexoPeAIWFjGbffpg4P3696bNKQS8dxhddNdrhTKrJ7o1UE82keCVix4VJaA8FjcZUCAXmg1HVBJMpnBTtHXoApXg6x3eBqi8nb99mv9YN1gzjs71eryQ0h5grYz84UxlDdMkebcFEqAWeRlwt02cq8sn6jJJ9D2oldCsQ0IUTPX+Q69LY7dcy3HlkHKcE+BIvXKKSdo0aELF2S3918k8A4buyz+GPJbcgJG9hCtkxQRltGnU8tOe9RpUb6ZMu+dWC3m0CIPnFwSYPEH7kfTD7fKAYC0+tTUnhkHI8Y9DQxxprSAmhtDA0Ryft1tdH/nHyTfqLwJIUjDmNg46NET/Kpy+cYWItaMuRswJnxn9kj8du4U02HaR0AijzU3vk5naB2BP4MC9j7S0cglgHSbyQ0YS2Jlttbbrkkj6k+A5EFUNcCgFIl8Z48/1T799i51NWPSBjfTo6Ep6uOUf5RFRVJ0Y3cPhCkqBWwPKvQ54x5nLkjogsWmtG4pDBJYO42rm++vuR/ncm4/2ul2PHmboFsS6YCfHQbQnLGwiT4cmtJNkGuRwPlP5eUE8AiTcZqC7YsAYD28/R4z33S2+XfWdU0y66KOfTxhN9YjOGm+qTfO1kPeSe70mtMtnutN6XJdgA4LcZmXYDRr+TlDR1TEq8/WZEKdfVxkjaQ+R7sc/Q1flI=","v":"m2JSqrBtIXdQ4Vq6LTC1kw==","m":"BsRioKDdMi3oPdq2Klc/Bw=="}

if __name__ == '__main__':
    for n, v in req.items():
        print n, "=", CCIQ_AES().decrypt(v)

    for n in ["v", "m", "c"]:
        o = CCIQ_AES().decrypt(vv[n])
        print n, "=", len(o), o

    o = CCIQ_AES("BB1856A312580D41256311147089E0CC").decrypt(vv['c'])
    print len(o), o

