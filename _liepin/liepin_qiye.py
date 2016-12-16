#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
import sys
import time
from page_store import PageStoreLP
from spider.spider import Spider, SpiderErrors
import spider.util
from spider.runtime import Log
import spider.misc.stacktracer
from spider.racer import TimedLock
from spider.captcha.lianzhong import LianzhongCaptcha


class LiepinQiyeTodaySpider(Spider):
    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        self.pagestore = PageStoreLP()
        self.chklock = TimedLock(20)

    def dispatch(self):
        #self._logport = 5554
        nowtime = time.localtime()
        #self.bs = BinSaver("lp_qiye_%02d%02d.bin" %(nowtime.tm_mon, nowtime.tm_mday))
        with open("lp_qiye_queries.txt", 'rb') as f:
            for lines in f:
                ll = lines.strip()
                self.add_main_job({'type':'u1', 'url':ll})
        self.wait_q()
        self.add_main_job(None)

    def check_image(self, con):
        key = self.chklock.trylock()
        if key:
            try:
                lz = LianzhongCaptcha()
                if not lz.point_check():
                    Log.error("no image resolver")
                    raise SpiderErrors.FatalError("no image resovler")
                hf = spider.util.htmlfind(con.text, "<form", 0)
                a, b = hf.process_form()
                while True:
                    image = self.request_url("https://passport.liepin.com/captcha/randomcode/?time=%d" % int(time.time()*1000))
                    vcode = a["verifycode"] = lz.resolve(image.content, 4, 4)
                    if not vcode:
                        continue
                    vcodecc = re.search("verifycode=([0-9a-f]+)", image.headers)
                    headers = {'Referer':con.request.url,  'X-Requested-With': 'XMLHttpRequest', "Cookie":"verifycode=%s"%vcodecc.group(1)}
                    con1 = self.request_url("https://passport.liepin.com/inspect/validate.json", headers=headers, data=a)
                    if con1.text[0:1] == '{' and u'验证码填写有误，请重新填写' in con1.text:
                        pass
                    else:
                        break
            finally:
                self.chklock.unlock(key)
        else:
            time.sleep(10)

    def run_job(self, jobid):

        # jobid = {'type':'jd', 'url':'https://job.liepin.com/478_4781083/'}

        print "job is ", jobid
        if isinstance(jobid, dict):
            url = jobid.get('url')
            tp = jobid.get('type')
            con = self.request_url(url)
            if tp == 'u1':
                #add sub pages.
                m = re.search(ur'curPage=(\d+)" title="末页"', con.text)
                if m:
                    for i in range (2, int(m.group(1))+1):
                        self.add_job({'type':'u2', 'url':url + "&curPage=%d"%i})
            if tp == 'u1' or tp == 'u2':
                if u'系统检测到异常浏览行为，建议您立即进行验证' in con.text:
                    Log.error("IP需要图形验证码验证")
                    self.check_image(con)
                    return self.run_job(jobid)
                #parse jd ids.
                m = re.search(ur'"sojob-list">(.*)</ul>', con.text, re.S)
                if m:
                    con1 = m.group(1)
                    jdlist = re.findall(ur'(https://job.liepin.com/.*?_\d+/)', con1, re.S)
                    for jl in jdlist:
                        print "==========%s======" % jl
                        self.add_job({'type':'jd', 'url':jl})
            if tp == 'jd':
                m = re.search(".*?_(\d+)", url)
                lpid = m.group(1)
                #self.bs.append("lp_qiye_%s_%d" % (lpid , int(time.time())), con.text)
                self.pagestore.save(int(time.time()), lpid, url, con.text)

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'STARTED':
            pass
            # spider.misc.stacktracer.trace_start('res.liepin_qiye.html')
        if evt == 'DONE':
            msg += "saved : %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['lixungeng@ipin.com', 'wangwei@ipin.com'], '%s DONE' % sys.argv[0], msg)

if __name__ == "__main__":
    s = LiepinQiyeTodaySpider(15)
    s.load_proxy('proxy')
    # s.set_proxy(['106.75.134.189:18889:ipin:helloipin'], index=0, auto_change=False)
    s.run()
