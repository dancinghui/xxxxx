#!/usr/bin/env python
# -*- coding:utf8 -*-
import logging
import re
import threading
import time

from court.cspider import EProxySwapSpider, EShutdownableSpider, ShutdownableSpider
from court.util import KuaidailiProxyManager
from shspider import ShanghaiLinkDb, ShanghaiCourtStore
from spider import spider
from spider.genquery import GenQueries
from spider.httpreq import BasicRequests


class FormParamParser(BasicRequests):
    def __init__(self, url):
        BasicRequests.__init__(self)
        self.url = url

    def run(self):
        con = self.request_url(self.url)
        if con is None or con.text is None:
            print 'failed to fetch page', self.url
            return
        forms = re.findall(r'<form.*?</form>', con.text, re.S | re.I)
        res = []
        for f in forms:
            res.append(FormParamParser.parse_form(f))
        return res

    @staticmethod
    def parse_form(form):
        # 解析表单名称和动作或者url和方法
        params = re.findall(r'[?\s](\w+)=([\'"].*?[\'"])', re.search(r'<form[^>]*>', form, re.I).group())
        data = {}
        for key, value in params:
            data[key] = value[1:-1]
        data['selects'] = FormParamParser.parse_for_select(form)
        data['inputs'] = FormParamParser.parse_for_input(form)
        return data

    @staticmethod
    def parse_for_select(form):
        m = re.findall(r'<select.*?</select>', form, re.S | re.I)
        selects = []
        for s in m:
            params = re.findall(r'[?\s](\w+)=([\'"].*?[\'"])', re.search(r'<select[^>]*>', s, re.I).group())
            data = {}
            for key, value in params:
                data[key] = value[1:-1]
            options = re.findall(r'<option[^>]*>', s, re.I)
            data['options'] = []
            for option in options:
                params = re.findall(r'\s(\w+)=([\'"].*?[\'"])', option)
                opt = {}
                for key, value in params:
                    opt[key] = value[1:-1]
                data['options'].append(opt)
            selects.append(data)
        return selects

    @staticmethod
    def parse_for_input(form):
        params = re.findall(r'<input[^>]*>', form)
        inps = []
        for inp in params:
            inpvars = re.findall(r'[?\s](\w+)=([\'"].*?[\'"])', inp, re.I)
            inps.append(inpvars)
        return inps


class SHGenQ(GenQueries):
    def __init__(self, threadcnt=20):
        super(SHGenQ, self).__init__(threadcnt)

    def init_conditions(self):
        pass


def test_form_parser(url='http://www.hshfy.sh.cn/shfy/gweb/flws_list.jsp'):
    p = FormParamParser(url)
    res = p.run()
    for form in res:
        print '-------------------------'
        for k, v in form.items():
            if k == 'selects':
                print 'select:'
                for select in v:
                    print ''
                    for sk, sv in select.items():
                        if 'options' == sk:
                            print '\toptions:'
                            for option in sv:
                                print '\t\t', option
                        else:
                            print '\t%s:%s' % (sk, sv)
            else:
                print k, ':', v


def read_seeds(sfile):
    seeds = []
    with open(sfile, 'r') as f:
        for l in f:
            seeds.append({'type': 'list', 'url': l.strip()})
    return seeds


class ShanghaiSpider(ShutdownableSpider):
    "上海高级人民法院文书检索系统爬虫"

    def __init__(self, thread_count=5, name='ShanghaiCourtSpider', recover=False):
        super(ShanghaiSpider, self).__init__(thread_count)

        self.select_user_agent(
            '=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36'
        )
        self._name = name
        self.pagestore = ShanghaiCourtStore('shanghai_court')
        self.seeddb = ShanghaiLinkDb('sh_seed')
        self.page_size = 15
        self.search_url_format = 'http://www.hshfy.sh.cn:8081/flws/content.jsp?wz=&pa=%s&more=1&toPage=%d&totalPage=%d&perPaperLink=%d&perPaperNum=%d'
        self.lock = threading.Lock()
        self.pager_failed_count = 0
        self.recover = recover
        self.timeout = 60

    def dispatch(self):
        seeds = []
        raw_seeds = self.seeddb.export_seeds()
        for item in raw_seeds:
            rseed = eval(item)
            seed = rseed['id']
            if not self.recover or not self.pagestore.find_any(self.pagestore.channel + '://' + seed):
                seeds.append(seed)

        print 'add %d seeds' % len(seeds)
        for seed in seeds:
            self.add_main_job({'type': 'main', 'id': seed})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def on_other_exception(self, con, jobid):
        if not re.search('<P class="nrtxt">', con.text) and re.search(u'出错了', con.text):
            print '出错了，他们服务器太弱，慢点抓吧'
            logging.error('server error,%s', str(jobid))
            self.re_add_job(jobid)
            return True
        return False

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

    def check_if_is_js_results(self, con):
        if u'访问本页面，您的浏览器需要支持JavaScript' in con.text:
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
            con = self.get_page(url, timeout=self.timeout)
            return con

    def handle_js_request(self, jobid, content):
        m = re.search('<script>(.*?)<script>', content)
        if not m:
            return None

    def run_job(self, jobid):
        url = 'http://www.hshfy.sh.cn/shfy/gweb/flws_view.jsp?pa=' + jobid['id']
        time.sleep(1.25)
        con = self.get_page(url, timeout=self.timeout)
        if self.check_exception(con, jobid):
            print 'exception encounter', url
            return
        cons = self.check_if_is_js_results(con)
        if cons:
            if self.check_exception(con, jobid):
                print 'exception encounter', url
                return
            elif u'访问本页面，您的浏览器需要支持JavaScript' in con.text:
                self.re_add_job(jobid)
                print 'js not solved'
                return
            con = cons
        content = self.extract_content(con.text)
        logging.info('saving %s,%s', jobid['id'], url)
        if content and jobid['id']:
            self.pagestore.save(int(time.time()), jobid['id'], url, content)
        else:
            with self.lock:
                self.pager_failed_count += 1
            logging.info('failed count %d,None content or jid for %s,%s' % (self.pager_failed_count, jobid['id'], url))

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
            con.text = con.content.decode('gb18030')
            con.encoding = 'gb18030'

        return con

    def get_page(self, url, **kwargs):
        con = self.request_url(url, **kwargs)
        if con:
            con.text = con.content.decode('gb18030')
            con.encoding = 'gb18030'
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

    def extract_paper_url(self, content):
        m = re.findall(r'onclick="showone\(\'([^\']+)\'', content)
        urls = []
        for u in m:
            urls.append('http://www.hshfy.sh.cn/shfy/gweb/flws_view.jsp?pa=' + u)
        return urls

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

    def change_proxy(self, remove=False):
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
    count = 3
    while count > 0:
        count -= 1
        try:
            job = ShanghaiSpider(20, recover=True)
            # job = ShanghaiCourtSpider(20, list_only=False, recover=True, paper_seeds='paper_seeds')
            # proxies = KuaidailiProxyManager.load_proxy(30)
            # print 'load %d proxies from kuaidaili' % proxies['data']['count']
            # if proxies['data']['count'] > 0:
            #     job.set_proxy(proxies['data']['proxy_list'], 15 if (proxies['data']['count'] > 15) else 0)
            job.run()
            time.sleep(300)
        except Exception as e:
            msg = str(type(e)) + '\n'
            msg += e.message + '\n'
            spider.util.sendmail(['shibaofeng@ipin.com'], 'ShanghaiSpider Failed:%d' % count, msg)
