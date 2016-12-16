#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
import sys
import time

import spider.util
from spider.ipin.savedb import PageStoreBase, Bin2DB
from spider.savebin import FileSaver
from spider.spider import Spider
from spider.runtime import Log
from spider.util import htmlfind
import spider.misc.stacktracer

class CData:
    getholes = False

class ZhilianPageStore(PageStoreBase):
    def __init__(self):
        PageStoreBase.__init__(self, 'jd_zhilian')
        self.hdoc = None
        # self.testmode = True

    def extract_content(self):

        content = ''
        uls = htmlfind.findTag(self.get_cur_doc().cur_content, 'ul', 'class="terminal-ul clearfix"')
        if len(uls):
            strongs = re.findall(r'<strong[^<>]*>(.*?)</strong>', uls[0], re.S)
            for index, strong in enumerate(strongs):
                if 2 == index:  # updateTime 忽略
                    continue
                content += htmlfind.remove_tag(strong, True) + "#"

        m = re.search(ur'''<div class="tab-inner-cont">(.*?)</button>''', self.get_cur_doc().cur_content, re.S)
        if m:
            a = re.sub(ur'<[a-zA-Z/!][^<>]*>', '', m.group(1))
            content += a.strip()
            return content

        Log.error(self.get_cur_doc().cur_url, "no content")
        return None

    def page_time(self):
        m = re.search(ur'''<span id="span4freshdate">\s*(\d+-\d+-\d+)''', self.get_cur_doc().cur_content)
        if m:
            t = time.mktime(time.strptime(m.group(1), '%Y-%m-%d'))
            return int(t) * 1000
        return None

    def check_should_fetch(self, jdid):
        if CData.getholes:
            indexUrl = "%s://%s" % (self.channel, jdid)
            if self.find_any(indexUrl):
                return False
        return PageStoreBase.check_should_fetch(self, jdid)


class ZLBin2DB(Bin2DB):
    def __init__(self):
        self.pagestore = ZhilianPageStore()

    def parse_name(self, n):
        m = re.match('zhilian_(\d+)_(\d+)', n)
        if m:
            return m.group(2), m.group(1)
        return None, None

    def get_pagestore(self):
        return self.pagestore


class MProxySpider(Spider):
    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        self.prlist = []

    def useproxy(self, fn):
        fd = open(fn, 'r')
        assert fd is not None
        for i in fd.readlines():
            self.prlist.append(i.strip())
        fd.close()
        #self.thread_count = len(self.prlist)

    def prequest_url(self, kw, url, **kwargs):
        pr = self.prlist[self.get_tid() % len(self.prlist)]
        self._set_proxy(kwargs, pr)
        con = self.request_url(url, **kwargs)
        if con is not None and con.code != 200:
            return None
        if kw not in con.text:
            return None
        return con


class ZLSpider(MProxySpider):
    def __init__(self, thcnt):
        MProxySpider.__init__(self, thcnt)
        self.pagestore = ZhilianPageStore()
        self.enable_mainjob_timedlock = False
        self.prlist = []

    def dispatch(self):
        llidx = 0
        skipto = 0
        with open("zhilian_queries.txt", 'rb') as f:
            for lines in f:
                llidx += 1
                ll = lines.strip()
                if llidx >= skipto:
                    self.add_main_job({'type':'u1', 'url':ll})
                else:
                    self._mjob_count += 1
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        url = jobid.get('url')
        tp = jobid.get('type')

        if tp == 'jd':
            m = re.search("(\d+)\.htm", url)
            jdid = m.group(1)
            if self.pagestore.check_should_fetch(jdid):
                con = self.request_url(url)
                if con is None or con.text.strip() == "":
                    self.add_job(jobid)
                    return
                self.pagestore.save(int(time.time()), jdid, url, con.text)
            return

        con = self.prequest_url(u'智联招聘', url)
        if con is None:
            return
        if tp == 'u1':
            #add sub pages.
            sgparam = ''
            m = re.search(u'sou.zhaopin.com/jobs[^"]*(&sg=[0-9a-f]+)', con.text, re.I)
            if m:
                sgparam = m.group(1).encode('utf-8')
            m = re.search(ur"(?:共|多于)<em>(\d+)</em>个职位满足条件", con.text)
            if m:
                pagecnt =  (int(m.group(1))+59)/60
                for i in range (2, pagecnt+1):
                    self.add_job({'type':'u2', 'url':url + sgparam + ("&p=%d"%i)})
                if pagecnt==0: #no record found.
                    Log.error("%s => NO_PAGES!" % url)
                    return
            else:
                Log.error("%s => changed html!" % url)
        if tp == 'u1' or tp == 'u2':
            if re.search(ur"对不起，暂时无符合您条件的职位", con.text):
                print "====%s=== has no jds." % url
                return
            print self.get_tid(), url
            #parse jd ids.
            urls = re.findall(ur'(http://jobs.zhaopin.com/\d+\.htm)', con.text)
            urls = spider.util.unique_list(urls)
            for link in urls:
                self.add_job({'type':'jd', 'url':link})

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['lixungeng@ipin.com', 'wangwei@ipin.com'], '%s DONE' % sys.argv[0], msg)
        elif evt == 'STARTED':
            #spider.misc.stacktracer.trace_start('res.trace.html')
            pass


if __name__ == "__main__":
    s = ZLSpider(30)
    if len(sys.argv)>1 and sys.argv[1] == 'all':
        CData.getholes = True
        print '=========get holes==========='
        time.sleep(3)
    s.useproxy('proxy')
    #s.load_proxy('curproxy')
    s.run()
