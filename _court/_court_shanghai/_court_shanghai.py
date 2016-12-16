#!/usr/bin/env python
# -*- coding:utf8 -*-
import logging
import re
import threading
import time

from court.cspider import ProxySwapSpider
from court.save import LinkSaver
from shspider import ShanghaiCourtStore
from spider import spider


class ShanghaiCourtSpider(ProxySwapSpider):
    "上海高级人民法院文书检索系统爬虫"

    def __init__(self, thread_count=5, seeds=None, start=1, name='ShanghaiCourtSpider', list_only=False,
                 paper_seeds=None,
                 recover=False):
        ProxySwapSpider.__init__(self, thread_count, proxy_life=3600)
        if seeds is None:
            seeds = []
        self._name = name
        self.seeds = seeds
        self.pagestore = ShanghaiCourtStore()
        self.page_size = 20
        self.list_only = list_only
        self.search_url_format = 'http://www.hshfy.sh.cn:8081/flws/content.jsp?wz=&pa=%s&more=1&toPage=%d&totalPage=%d&perPaperLink=%d&perPaperNum=%d'
        if self.list_only:
            self.link_saver = LinkSaver('links', 'a')
        self.paper_seeds = paper_seeds
        self.lock = threading.Lock()
        self.pager_failed_count = 0
        self.recover = recover
        self.start = start

    def dispatch(self):
        # for seed in self.seeds:
        #     self.add_main_job(seed)
        # logging.info('add %d list links' % len(self.seeds))
        # if self.paper_seeds:
        #     links = []
        #     with open(self.paper_seeds, 'r') as f:
        #         for l in f:
        #             links.append(l.strip())
        #     if self.recover:
        #         tmp = links
        #         links = []
        #         for l in tmp:
        #             if not self.pagestore.find_any(self.pagestore.channel + '://' + self.extract_paper_id(l)):
        #                 links.append(l)
        #     logging.info('add %d paper links' % len(links))
        #     for l in links:
        #         self.add_main_job({'type': 'paper', 'url': l})
        seed_id = 'adHlwZT1BbGwmd3o9z'
        total = 1060385
        pagecnt = (total + self.page_size / 2) / self.page_size + 1
        for page in range(self.start, pagecnt):
            self.add_main_job(
                {'type': 'list',
                 'url': self.search_url_format % (seed_id, page, total, self.page_size, self.page_size)})

        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

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
                print 'Proxy Error 502', jobid['url']
                logging.error('proxy error 502 %s', jobid['url'])
                self.change_proxy()
                self.re_add_job(jobid)
                return True
            if 404 == con.code:
                print '啊呵,404,服务器上居然找不到这个页面', jobid['url']
                logging.info('page not found on the server %s', jobid['url'])
                return True
            if 410 == con.code:
                print 'resource gone', jobid['url']
                return True
            if 500 > con.code >= 400:
                print 'request error', jobid['url']
                self.re_add_job(jobid)
                return True
            if 600 > con.code >= 500:
                print 'server error', con.code, jobid['url']
                cnt = jobid.get('_failcnt_', 0)
                if cnt < 47:
                    jobid['_failcnt'] = 47
                self.re_add_job(jobid)
                return True
            print '600 以上的code,涨见识了！哈哈哈！', jobid['url']
            logging.info('failed with response code %d,%s', con.code, jobid['url'])
            self.re_add_job(jobid)
            return True
        if re.search(u'出错了', con.text):
            print '出错了，他们服务器太弱，慢点抓吧'
            logging.error('server error,%s', jobid['url'])
            self.re_add_job(jobid)
            return True
        if re.search(u'访问本页面，您的浏览器需要支持JavaScript', con.text):
            m = re.search(r"<script>(.*?)</script>", con.text)
            sc = "document = {set cookie(a){console.log(a);}}, window = {innerWidth: 1366, innerHeight: 768, screenX: 200, screenY: 100, screen: {width: 1366, height: 768}}\n"
            sc += m.group(1)
            rv = spider.util.runjs(sc)
            logging.info('nodejs result:%s', rv)
            print rv
        return False

    def run_job(self, jobid):
        jt = jobid['type']
        url = jobid['url']

        if 'main' == jt:
            res = self.post_for_count(url)
            if self.check_exception(res[1], jobid):
                return
            if res[0] <= 0:
                print 'get 0 result from', url
                logging.info('get no paper from %s' % url)
                return
            seed_id = re.search(r'pa=([\w\d\+]+)', url)
            if seed_id:
                seed_id = seed_id.group(1)
                count = int(res[0])
                logging.info('there are %d paper in %s' % (count, seed_id))
                page_count = int((count + self.page_size / 2) / self.page_size)
                for page in range(1, page_count + 1):
                    self.add_job(
                        {'type': 'list',
                         'url': self.search_url_format % (seed_id, page, count, self.page_size, self.page_size)})
            else:
                logging.warn('failed to parse seed id from %s', url)
        elif 'list' == jt:
            con = self.post_for_data(jobid['url'], {})
            if self.check_exception(con, jobid):
                return
            urls = self.extract_paper_url(con.text)
            if self.list_only:
                for u in urls:
                    self.link_saver.add(u)
            else:
                for u in urls:
                    self.add_job({'type': 'paper', 'url': u})
            logging.info('add %d from list job %s' % (len(urls), url))
            if len(urls) == 0:
                pass
            print('add %d from list job %s' % (len(urls), url))

        else:
            con = self.request_url(url, timeout=45)
            if self.check_exception(con, jobid):
                return
            content = self.extract_content(con.text)
            jid = self.extract_paper_id(url)
            logging.info('saving %s,%s', jid, url)
            if content and jid:
                self.pagestore.save(int(time.time()), jid, url, content)
            else:
                with self.lock:
                    self.pager_failed_count += 1
                logging.info('failed count %d,None content or jid for %s,%s' % (self.pager_failed_count, jid, url))

    def extract_paper_id(self, url):
        m = re.search(r'pa=([\w\d\/]+)', url)
        if m:
            return m.group(1)
        return None

    def post_for_data(self, url, data=None):
        if data is None:
            data = {}
        con = self.request_url(url, data=data, timeout=60)
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
        count = re.search(u'共([\d\s]+)条', con.text)
        if count:
            return [count.group(1), con]
        return [0, con]

    def extract_paper_url(self, content):
        m = re.findall(r'onclick="showone\(\'([^\']+)\'', content)
        urls = []
        for u in m:
            urls.append('http://www.hshfy.sh.cn:8081/flws/text.jsp?pa=' + u)
        return urls

    def extract_content(self, content):
        return content

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "Court Spider:%s\n" % self._name
            msg += "Mode-list_only:%s\n" % self.list_only
            msg += "paper id failed: %d\n" % self.pager_failed_count
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
            logging.info('Job done,failed count %d,saved %d' % (self.pager_failed_count, self.pagestore.saved_count))
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


def read_seeds(sfile):
    seeds = []
    with open(sfile, 'r') as f:
        for l in f:
            seeds.append({'type': 'list', 'url': l.strip()})
    return seeds


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
    job = ShanghaiCourtSpider(1, list_only=True, seeds=seeds)
    # job = ShanghaiCourtSpider(20, list_only=False, recover=True, paper_seeds='paper_seeds')
    job.load_proxy('proxy', 0)
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
