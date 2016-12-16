#!/usr/bin/env python
# -*- coding:utf8 -*-

import qdata
import spider.genquery
import copy
import time
import spider.util
import re
import sys
from spider.ipin.savedb import PageStoreBase
from spider.util import htmlfind, TimeHandler
from spider.runtime import Log
from spider.httpreq import BasicRequests
import spider.misc.stacktracer

# FIXME: 时间处理有问题,页面只显示了 01-19 发布, 在跨年时存在问题.

class CData(spider.genquery.GQDataHelper):
    query_template = {
    "lang" : "c",
    "radius" : "-1",
    "lonlat" : "0,0",
    "stype" : "2",
    "dibiaoid" : "0",
    "list_type" : "0",
    "fromType" : "6",
    "jobterm" : "99",
    "ord_field" : "0",
    "postchannel" : "0000",
    "confirmdate" : "9",

    "cotype":'99',
    "degreefrom":'99',
    "companysize":'99',
    "workyear":'99',
    }
    getholes = False

    @staticmethod
    def get_url(d, page=1):
        t = copy.deepcopy(CData.query_template)
        t.update(d)
        info = (t['jobarea'], t['industrytype'], page)
        if CData.getholes:
            basicurl = "http://search.51job.com/list/%s,000000,0000,%s,4,99,%%2B,0,%d.html" % info
        else:
            basicurl = "http://search.51job.com/list/%s,000000,0000,%s,3,99,%%2B,0,%d.html" % info
        qstr = ''
        for k in t:
            qstr += k + '=' + t[k]
            qstr += '&'
        qstr = qstr[0:-1]
        return basicurl + "?" + qstr


class PageStore51(PageStoreBase):
    def __init__(self):
        PageStoreBase.__init__(self, 'jd_51job')#, dburl='mongodb://localhost/page')
        # self.testmode = 1
        self.hdoc = None

    def extract_content(self):
        content=''
        divs = htmlfind.findTag(self.get_cur_doc().cur_content, 'div', 'class="jtag inbox">')
        if divs:
            spans = re.findall(r'<span[^<>]*>(.*?)</span>', divs[0], re.S)
            if spans:
                spans = spans[:-1] # 忽略更新时间
                for span in spans:
                    content += htmlfind.remove_tag(span, True) + "#"

        if isinstance(content, unicode):
            content = content.encode('utf-8')

        hf = htmlfind(self.get_cur_doc().cur_content, '<div class="bmsg job_msg inbox">', 0)
        t2 = htmlfind.remove_tag(hf.get_node(), 1)

        if isinstance(t2, unicode):
            t2 = t2.encode('utf-8')

        return content + t2

    def page_time(self):
        tag = htmlfind.findTag(self.get_cur_doc().cur_content, 'div', 'class="jtag inbox"')
        if tag:
            m = re.search(ur'(\d*-?\d+-\d+发布)', tag[0])
            if m:
                t = TimeHandler.fmt_time(m.group(1))
                return t

    def check_should_fetch(self, jdid):
        if not PageStoreBase.check_should_fetch(self, jdid):
            return False
        if CData.getholes:
            indexUrl = "%s://%s" % (self.channel, jdid)
            if self.find_any(indexUrl):
                return False
        return True



class JD51(spider.genquery.GenQueriesLT):
    def __init__(self, thcnt):
        spider.genquery.GenQueriesLT.__init__(self, thcnt)
        self.default_headers = {'Cookie':'guide=1'}
        self.pagestore = PageStore51()
        self._name = "jd51"

    def skip_jobs(self, aq):
        #self.skip_n_jobs(aq, 1300) ###dbg.........
        return

    def init_conditions(self):
        CData.add(self, 'jobarea', qdata.jobarea)
        CData.add(self, 'industrytype', qdata.industrytype)
        CData.add(self, 'companysize', qdata.companysize)
        CData.add(self, 'cotype', qdata.cotype)
        CData.add(self, 'degreefrom', qdata.degreefrom)
        CData.add(self, 'workyear', qdata.workyear)

    def run_job(self, jobid):
        spider.genquery.GenQueries.run_job(self, jobid)
        jobtype = self.get_job_type(jobid)
        if jobtype == 'loadpage':
            url = CData.get_url(jobid.get('u'), jobid.get('p'))
            print url
            con = self.request_url(url)
            if con is not None:
                self.parse_html(con.text)
            else:
                self.re_add_job(jobid)
        elif jobtype == 'jdurl':
            url = jobid['u']
            m = re.search(r'/(\d+)\.html', url)
            if m:
                if self.pagestore.check_should_fetch(m.group(1)):
                    con = self.request_url(url)
                    if con is not None:
                        self.pagestore.save(int(time.time()), m.group(1), url, con.text)
                    else:
                        self.re_add_job(jobid)
                        Log.error("failed get url", url)
                        # self.re_add_job(jobid)
                else:
                    #Log.warning("skip fetch url:", url)
                    pass

    def parse_html(self, text):
        a = re.findall(r'http://jobs\.51job\.com/[a-z0-9A-Z_\-]*/\d+\.html', text)
        urls = spider.util.unique_list(a)
        for pageurl in urls:
            self.add_job({'type':'jdurl', 'u':pageurl, 'dontreport':1})
        a = re.findall(r'http://[a-z0-9_\.-]+.51job.com/sc/show_job_detail.php\?jobid=(\d+)', text)
        a = spider.util.unique_list(a)
        for pageid in a:
            pageurl = "http://jobs.51job.com/u/%s.html" % pageid
            self.add_job({'type':'jdurl', 'u':pageurl, 'dontreport':1})

    def need_split(self, url, level, isLast):
        ## 测试某个单项.
        #if url.get('jobarea', '') != '180000' or url.get('industrytype', '')!='03':
        #    return False
        theurl = CData.get_url(url)
        print theurl
        con = self.request_url(theurl)
        if con is None:
            Log.warning("retry url %s" % theurl )
            time.sleep(10)
            return self.need_split(url, level, isLast)
        if u'对不起，没有找到符合你条件的职位' in con.text:
            print '============no data==========='
            return False
        #find pages.
        pages = 0
        for v in spider.util.chained_regex(con.text, ur"rtPrev(.*?)rtNext", ur">(.*)<"):
            v = re.sub(ur'<.*?>|\s+', u'', v)
            m = re.match(ur'(\d+)/(\d+)', v)
            if m:
                pages = int(m.group(2))
        if pages == 0:
            return False
        elif pages >= 1400:
            return True

        self.parse_html(con.text)
        if pages > 1:
            for i in range(2, pages+1):
                self.add_job({'u': url, 'p': i, 'type': 'loadpage'})
        return False

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['wangwei@ipin.com', 'lixungeng@ipin.com'], '%s DONE' % sys.argv[0], msg)
        elif evt == 'STARTED':
            #spider.misc.stacktracer.trace_start('res.trace.html')
            pass


def test_ps():
    ps = PageStore51()
    ps.testmode = True
    br = BasicRequests()
    br.select_user_agent('firefox')
    url = "http://jobs.51job.com/beijing-hdq/70320056.html?s=0"
    con = br.request_url(url)
    ps.save(int(time.time()), "jd_51job://", url, con.text)


if __name__ == '__main__':
    j = JD51(50)
    j.load_proxy('proxy')
    if len(sys.argv) > 1 and sys.argv[1] == 'all':
        CData.getholes = True
        print "=========getting holes....============="
        j.enable_mainjob_timedlock = False
        time.sleep(3)
    j.run()


"""
T：3=近1月，1=近3天
SL：月薪范围
X：职粉、公司、全文
P：page
                             地点         地点2    职能 行业T SL     X P
http://search.51job.com/list/010000%252C00,000000,0000,01,3,99,%2B,0,1.html


http://search.51job.com/list/010000%252C00,000000,3000,01,9,99,%2B,0,1.html?lang=c&stype=2&postchannel=0000&jobterm=99&confirmdate=9&fromType=6&lonlat=0%2C0&radius=-1&ord_field=0&list_type=0&dibiaoid=0
&workyear=99&cotype=99&degreefrom=99&companysize=99

发布日期=近3天
地点  jobarea=010000
行业  industrytype=01   industrytype=37
公司性质 cotype=01
学历要求 degreefrom=02
公司规模 companysize=02
工作年限 workyear=02 workyear=03 99

jobterm 全兼职

"""
