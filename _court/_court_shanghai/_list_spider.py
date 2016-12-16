#!/usr/bin/env python
# -*- coding:utf8 -*-
import logging
import re
import threading
import time

from court.cspider import CourtSpider
from court.save import LinkSaver
from shspider import ShanghaiSeedStore, ShanghaiLinkDb
from spider import spider


class ShanghaiCourtSpider(CourtSpider):
    "上海裁判文书爬虫"

    def __init__(self, thread_count=5, name='ShanghaiCourtListSpider', log='list.spider.log',
                 out='links',
                 recover=False):
        CourtSpider.__init__(self, thread_count, log)

        self._name = name
        self.pagestore = ShanghaiSeedStore()
        self.linkdb = ShanghaiLinkDb('sh_link')
        self.seedb = ShanghaiLinkDb('sh_seed')
        self.link_saver = LinkSaver(out)
        self.lock = threading.Lock()
        self.pager_failed_count = 0
        self.recover = recover

    def dispatch(self):
        raw_seeds = self.linkdb.export_seeds()
        seeds = []
        for seed in raw_seeds:
            data = eval(seed['content'])
            start = self.extract_start_date(data['url'])
            end = self.extract_end_date(data['url'])
            if start is None and end is None:
                print 'invalid seed', data
                continue
            for page in range(1, (data['count'] + 8) / 15 + 1):
                if not self.recover or not self.pagestore.find_any(
                                                        self.pagestore.channel + '://' + start + end + '-%d' % page):
                    seeds.append({'type': 'main', 'start': start, 'end': end, 'page': page})
        print 'add %d seeds' % len(seeds)
        for seed in seeds:
            self.add_main_job(seed)

        time.sleep(2)
        self.wait_q()
        self.add_job(None, True)

    @staticmethod
    def extract_start_date(url):
        m = re.search(r'[?&]jarqks=(\d+-\d{2}-\d{2})', url)
        if m:
            try:
                return m.group(1).replace('-', '')
            except Exception as e:
                print e.message

    @staticmethod
    def extract_end_date(url):
        m = re.search(r'[?&]jarqjs=(\d+-\d{2}-\d{2})', url)
        if m:
            try:
                return m.group(1).replace('-', '')
            except Exception as e:
                print e.message

    @staticmethod
    def to_date(date):
        return date[:4] + '-' + date[4:6] + '-' + date[6:]

    def run_job(self, jobid):
        url = 'http://www.hshfy.sh.cn/shfy/gweb/flws_list_content.jsp?fydm=&ah=&ay=&ajlb=&wslb=&title=&jarqks=%s&jarqjs=%s&qwjs=&wssj=&yg=&bg=&spzz=&flyj=&pagesnum=%d' % (
            self.to_date(jobid['start']), self.to_date(jobid['end']), jobid['page'])
        con = self.get_page(url, timeout=45)
        time.sleep(1)
        if self.check_exception(con, jobid):
            print 'exception encounter', url
            return
        ccon = self.check_if_is_js_results(con)
        if ccon:
            print 'is js results'
            con = ccon
        urls = self.extract_paper_url(con.text)
        if len(urls) == 0:
            print 'got 0 paper'
            self.re_add_job(jobid)
            return
        list_id = '%s%s-%d' % (jobid['start'], jobid['end'], jobid['page'])
        self.pagestore.save(int(time.time()), list_id, url, con.text)
        for u in urls:
            self.seedb.save('http://www.hshfy.sh.cn/shfy/gweb/flws_view.jsp?pa=' + u, u,
                            str({'id': u, 'from': self.pagestore.channel + '://' + list_id}), int(time.time()))
        print 'add %d from list job %s' % (len(urls), url)
        logging.info('add %d from list job %s' % (len(urls), url))

    def get_page(self, url, **kwargs):
        con = self.request_url(url, **kwargs)
        if con:
            try:
                con.text = con.content.decode('gbk')
                con.encoding = 'gbk'
            except UnicodeDecodeError:
                con.text = con.content.decode('gb18030')
                con.encoding = 'gb18030'

        return con

    def on_proxy_error(self, con, jobid):
        self.change_proxy()
        self.re_add_job(jobid)
        return True

    def on_other_500_exception(self, con, jobid):
        cnt = jobid.get('_failcnt_', 0)
        if cnt < 47:
            jobid['_failcnt'] = 47
        self.re_add_job(jobid)
        return True

    def on_other_exception(self, con, jobid):
        if re.search(u'出错了', con.text):
            print '出错了，他们服务器太弱，慢点抓吧'
            logging.error('server error,%s', jobid['url'])
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

    def extract_paper_id(self, url):
        m = re.search(r'pa=([\w\d\/]+)', url)
        if m:
            return m.group(1)
        return None

    def post_for_data(self, url, data=None):
        if data is None:
            data = {}
        con = self.request_url(url, data=data)
        if con:
            con.text = con.content.decode('gbk')
            con.encoding = 'gbk'
        return con

    def post_for_count(self, url):
        con = self.post_for_data(url)
        if con is None:
            return [0, None]
        count = re.search(r'var totalPage = "(\d+)";', con.text)
        if count:
            return [count.group(1), con.text]
        count = re.search(r'<a href="#" onclick="goPage\(\'(\d+)\'\)">>></a>', con.text)
        if count:
            return [count.group(1), con.text]
        return [0, con.text]

    def extract_paper_url(self, content):
        return re.findall(r'onclick="showone\(\'([^\']+)\'', content)

    def extract_content(self, content):
        return content

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "Court Spider:%s\n" % self._name
            msg += "paper id failed: %d\n" % self.pager_failed_count
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
            logging.info('Job done,failed count %d,saved %d' % (self.pager_failed_count, self.pagestore.saved_count))
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass

    def change_proxy(self):
        pass


if '__main__' == __name__:
    seeds = [
        # 'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT1BbGwmd3o9z&wz=',
        'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT3D8crCJnd6PQPdcssPdcssz',
        'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT3QzMrCJnd6PQPdcssPdcssz',
        'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT3Q0NX+Jnd6PQPdcssPdcssz',
        'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT3WqrL6Jnd6PQPdcssPdcssz',
        'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT3WtNDQJnd6PQPdcssPdcssz',
        'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT26o8rCJnd6PQPdcssPdcssz',
        'http://www.hshfy.sh.cn:8081/flws/typelist.jsp?pa=adHlwZT1BbGwmd3o9z'
    ]
    # job = ShanghaiCourtSpider(20, paper_seeds='links', recover=True)
    job = ShanghaiCourtSpider(3, recover=True)
    # job = ShanghaiCourtSpider(20, list_only=False, recover=True,paper_seeds='paper_seeds')
    # job.load_proxy('proxy')
    # job.set_proxy('192.168.1.39:3428')
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
