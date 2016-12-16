#!/usr/bin/env python
# -*- coding:utf8 -*-
import logging
import re
import threading
import time
from datetime import datetime

from court.save import LinkSaver
from shspider import DateSpliter, ShanghaiLinkDb
from spider import spider
from spider.spider import Spider


class ShanghaiListGenerator(Spider):
    "文书网裁判文书爬虫"

    def __init__(self, thread_count=5, start=2000, split_limit=3000, name='ShanghaiSeedGenerator',
                 recover=False):
        super(ShanghaiListGenerator, self).__init__(thread_count)
        self.select_user_agent(
            '=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36'
        )
        self._name = name
        self.seeds = seeds
        self.linkdb = ShanghaiLinkDb('sh_link')
        self.page_size = 15
        self.link_saver = LinkSaver('links', 'a')
        self.lock = threading.Lock()
        self.pager_failed_count = 0
        self.recover = recover
        self.start = start
        self.split_limit = split_limit

    def dispatch(self):
        year_start = self.start
        year_end = 2008
        this_year = int(datetime.now().strftime('%Y'))
        seeds = []
        for year in range(year_start, year_end):
            start = self.get_date_str(year, 1, 1)
            end = self.get_date_str(year, 12, 31)
            if not self.recover or not self.linkdb.has_any(start.replace('-', '') + end.replace('-', '')):
                seeds.append({'type': 'main', 'start': start, 'end': end})
        for year in range(year_end, this_year):
            for month in range(1, 13):
                start = self.get_date_str(year, month, 1)
                end = self.get_date_str(year, month, self.get_end_day(year, month))
                if not self.recover or not self.linkdb.has_any(start.replace('-', '') + end.replace('-', '')):
                    seeds.append({'type': 'main', 'start': start, 'end': end})
        month_end = int(datetime.now().strftime('%m'))
        for month in range(1, month_end + 1):
            start = self.get_date_str(this_year, month, 1)
            end = self.get_date_str(this_year, month, self.get_end_day(this_year, month))
            if not self.recover or not self.linkdb.has_any(start.replace('-', '') + end.replace('-', '')):
                seeds.append({'type': 'main', 'start': start, 'end': end})
        for seed in seeds:
            self.add_main_job(seed)
        print 'add %s seeds' % len(seeds)
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    @staticmethod
    def get_date_str(year, month=None, day=None):
        if day is None:
            day = 1
        if month is None:
            month = 1
        if day < 10:
            ds = '0' + str(day)
        else:
            ds = str(day)
        if month < 10:
            ms = '0' + str(month)
        else:
            ms = str(month)
        return '%s-%s-%s' % (year, ms, ds)

    @staticmethod
    def get_end_day(year, month):
        if month > 31 or month < 1:
            return 0
        if 2 == month:
            if year % 4 == 0 and year % 400 != 0 or year % 400 == 0:
                return 29
            else:
                return 28
        elif month in [4, 6, 9, 11]:
            return 30
        else:
            return 31

    def get_url(self, pageNum, h_jarqjs='2016-05-12', h_jarqks='2000-01-01', h_fydm='', h_ah='', h_ay='', h_ajlb='',
                h_wslb='', h_title='', h_qwjs='', h_wssj='', h_yg='', h_bg='',
                h_spzz='', h_flyj=''):
        return "http://www.hshfy.sh.cn/shfy/gweb/flws_list_content.jsp?fydm=" + h_fydm + "&ah=" + h_ah \
               + "&ay=" + h_ay + "&ajlb=" + h_ajlb + "&wslb=" + h_wslb + "&title=" + h_title \
               + "&jarqks=" + h_jarqks + "&jarqjs=" + h_jarqjs + "&qwjs=" + h_qwjs + "&wssj=" + h_wssj + "&yg=" \
               + h_yg + "&bg=" + h_bg + "&spzz=" + h_spzz + "&flyj=" + h_flyj + "&pagesnum=" + str(pageNum)

    def check_exception(self, con, jobid):
        '''check if there are exception in response,true if exception are found and cannot be continue,
        false if no exception is found or exception is handled and is ok to continue'''
        if con is None:
            print 'null response'
            self.re_add_job(jobid)
            return True
        if con.text is None:
            print 'None content type'
            print con.headers
            self.re_add_job(jobid)
            return True
        if con.code >= 400:
            print con.headers
            if 502 == con.code:
                print 'Proxy Error 502', jobid
                logging.error('proxy error 502 %s', jobid)
                self.change_proxy()
                self.re_add_job(jobid)
                return True
            if 404 == con.code:
                print '啊呵,404,服务器上居然找不到这个页面', jobid
                logging.info('page not found on the server %s', jobid)
                return True
            if 410 == con.code:
                print 'resource gone', jobid
                return True
            if 500 > con.code >= 400:
                print 'request error', jobid
                self.re_add_job(jobid)
                return True
            if 600 > con.code >= 500:
                print 'server error', con.code, jobid
                cnt = jobid.get('_failcnt_', 0)
                if cnt < 47:
                    jobid['_failcnt'] = 47
                self.re_add_job(jobid)
                return True
            print '600 以上的code,涨见识了！哈哈哈！', jobid
            logging.info('failed with response code %d,%s', con.code, jobid)
            self.re_add_job(jobid)
            return True
        if re.search(u'出错了', con.text):
            print '出错了，他们服务器太弱，慢点抓吧'
            logging.error('server error,%s', jobid)
            self.re_add_job(jobid)
            return True
        return False

    def check_if_is_js_results(self, con):
        if re.search(u'访问本页面，您的浏览器需要支持JavaScript', con.text):
            m = re.search(r"<script>(.*?)</script>", con.text)
            # sc = "document = {set cookie(a){console.log(a);}}, window = {innerWidth: 1366, innerHeight: 768, screenX: 200, screenY: 100, screen: {width: 1366, height: 768}}\n"
            # sc = "document = {set cookie(a){console.log(a);}}}\n"
            sc = "document = {set cookie(a){console.log(a);}}; window={}; setTimeout=function(){};\n"
            sc += "window.open=function(e){console.log(e)};\n"
            sc += "get_result=function(e){if(e.indexOf('open')<0){console.log(eval(e.substring(e.indexOf('=')+1)))}}\n"
            sc += m.group(1) + '\n'
            var = re.search(r'\);}(\w+)=', con.text)
            sc += "get_result(%s);\n" % var.group(1)
            # sc += "\nconsole.log(dc)\n"
            print m.group(1)
            rv = spider.util.runjs(sc)
            print rv
            logging.info('nodejs result:%s', rv)
            print sc
            url = 'http://www.hshfy.sh.cn' + rv.strip()
            con = self.request_url(url, data={})
            return con

    def run_job(self, jobid):
        end = jobid['end']
        start = jobid['start']

        url = self.get_url(1, end, start)
        res = self.get_paper_count(url)
        if self.check_exception(res[1], jobid):
            return
        if res[0] > self.split_limit:
            ndays = DateSpliter.split(start, end)
            if len(ndays) > 0:
                print 'count %s, need split, %s' % (res[0], str(jobid))
                for t in ndays:
                    self.add_job({'type': 'job', 'start': t[0], 'end': t[1]})
                return
            print 'Cannot split any more', str(jobid)
        print 'count %s,page save' % res[0]
        self.linkdb.save(url, start.replace('-', '') + end.replace('-', ''),
                         str({'count': res[0], 'url': url}), int(time.time()))

    def post_for_data(self, url, data=None):
        if data is None:
            data = {}
        con = self.request_url(url, data=data, timeout=60)
        if con:
            con.text = con.content.decode('gbk')
            con.encoding = 'gbk'
        return con

    def get_page(self, url, **kwargs):
        con = self.request_url(url, **kwargs)
        if con:
            con.text = con.content.decode('gbk')
            con.encoding = 'gbk'
        return con

    def get_paper_count(self, url):
        con = self.get_page(url)
        if con is None:
            return [0, None]
        count = re.search(r'var totalPage = "(\d+)";', con.text)
        if count:
            return [int(count.group(1)), con.text]
        count = re.search(u'共有数据<strong>([\d\s]+)</strong>条', con.text)
        if count:
            return [int(count.group(1)), con]
        return [0, con]

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "Court Spider:%s\n" % self._name
            msg += "paper id failed: %d\n" % self.pager_failed_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
            logging.info('Job done,failed count %d' % (self.pager_failed_count))
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass

    def change_proxy(self):
        pass


if '__main__' == __name__:
    seeds = [
        # {'url': 'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT3D8crCJnd6PQPdcssPdcssz', 'type': 'main'},
        # {'url': 'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT3QzMrCJnd6PQPdcssPdcssz', 'type': 'main'},
        # {'url': 'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT3Q0NX+Jnd6PQPdcssPdcssz', 'type': 'main'},
        # {'url': 'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT3WqrL6Jnd6PQPdcssPdcssz', 'type': 'main'},
        # {'url': 'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT3WtNDQJnd6PQPdcssPdcssz', 'type': 'main'},
        # {'url': 'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT26o8rCJnd6PQPdcssPdcssz', 'type': 'main'},
        {'url': 'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT1BbGwmd3o9z', 'type': 'main'},
    ]
    # job = ShanghaiCourtSpider(20, paper_seeds='links', recover=True)
    # job = ShanghaiCourtSpider(1, list_only=True, seeds=read_seeds('zeros.seeds'))
    # job = ShanghaiCourtSpider(1, list_only=True, seeds='seeds')
    job = ShanghaiListGenerator(1, recover=True)
    # job = ShanghaiCourtSpider(20, list_only=False, recover=True, paper_seeds='paper_seeds')
    # job.load_proxy('proxy', 0)
    job.run()
    # data = {'fydm': '200',
    #         'ajlb': u'刑事',
    #         'wslb': u'判决书',
    #         'ah': '',
    #         'wssj': u'一审,二审,再审,减刑假释,破产,申诉,其他',
    #         'yg': '',
    #         'bg': '',
    #         'title': '',
    #         'ay': '',
    #         'jarqks': '',
    #         'jarqjs': '',
    #         'qwjs': ''
    #         }
    # data2 = {'pa': 'adHlwZT3WqrL6Jnd6PQPdcssPdcssz', 'wz': '', 'more': '1', 'toPage': '2', 'totalPage': '16737',
    #          'perPaperLink': '20', 'perPaperNum': '20'}
    # con = job.post_for_data(
    #     'http://www.hshfy.sh.cn:8081/flws/content.jsp?pa=adHlwZT1BbGwmd3o9z&wz=&more=1&toPage=1&totalPage=&perPaperLink=20&perPaperNum=20',
    #     {})
    # print job.post_for_count('adHlwZT1BbGwmd3o9z')
