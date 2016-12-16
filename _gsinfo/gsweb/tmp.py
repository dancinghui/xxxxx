#!/usr/bin/env python
# -*- coding:utf8 -*-

import pypinyin
import re
from spider.httpreq import BasicRequests
import json
import spider.util
from spider.spider import Spider
from gsconfig import ConfigData
import os
from gswebimg import get_gsweb_searcher

def pinyin(s):
    if isinstance(s, str):
        s = s.decode('utf-8')
    py = pypinyin.pinyin(s,0)
    rs = ''
    for x in py:
        for y in x:
            rs += y.encode('utf-8')
    rs = rs[0:1].upper() + rs[1:]
    return rs

def extendx(x):
    orig = x.group()
    sp = re.sub(r'\S.*', '', orig)
    name = x.group(1)
    py = pinyin(name)
    orig += sp + '"pinyin": "%s",' % py
    return orig


def init_data():
    br = BasicRequests()
    br.select_user_agent('firefox')
    s = open('af').read(64*1024)
    odata = []
    for m in re.finditer('<a (.*?)>(.*?)</a>', s, re.S):
        name = m.group(2)
        attrs = m.group(1)
        url = None
        prov = None
        for m1 in re.finditer('([a-z][a-z0-9]+)="(.*?)"', attrs, re.S):
            n, v = m1.group(1), m1.group(2)
            if n == 'href':
                url = v
            if n == "prov":
                prov = v
        con = br.request_url(url)
        siteurl = 'unknown'
        if con is not None:
            siteurl = con.request.url
        print name, con.request.url
        odata.append({'name':name, 'url':siteurl, 'imgurl':'', 'prov':prov})
    print json.dumps(odata, ensure_ascii=0, indent=4)



class GetImages(Spider):
    def dispatch(self):
        for ss in ConfigData.gsdata:
            self.add_main_job({'type':'mj', 'info':ss})
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, job):
        if self.get_job_type(job) == 'mj':
            info = job['info']
            provname = info['name']
            os.system("mkdir %s" % provname)
            sr = get_gsweb_searcher(info)
            sr.reset()
            count = 0
            while True:
                try:
                    os.stat("%s/%d.jpg" % (provname, count+1))
                    count += 1
                except:
                    break
            failcnt = 0
            sr.set_proxy("106.75.134.189:18889:ipin:helloipin", -1, 0)
            sr.load_proxy("sproxy", -1, 0)
            while count < 10000:
                img = sr.get_image()
                if img is None:
                    Log.error("invalid image of", provname)
                    sr.reset()
                    failcnt += 1
                    if failcnt > 10:
                        failcnt = 0
                        sr._cur_proxy_index += 1
                else:
                    failcnt = 0
                    count += 1
                    with open("%s/%d.jpg" % (provname, count), 'wb') as imgfo:
                        imgfo.write(img)

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail('lixungeng@ipin.com', 'get image done', msg)


def main():
    ii = open('gsconfig.py').read()
    ii = re.sub(r'\s*"name"\s*:\s*"(.*?)",', lambda x: extendx(x), ii)
    print ii
