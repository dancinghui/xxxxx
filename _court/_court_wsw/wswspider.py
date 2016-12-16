#!/usr/bin/env python
# -*- coding:utf8 -*-
import logging
import os
import re
import socket
import threading
from collections import OrderedDict
from urllib import unquote, quote

import time

from court.cspider import CourtSpider, ShutdownableSpider, EShutdownableSpider, ProxySwapSpider
from court.save import CourtStore
from court.sessionrequests import ETOSSessionRequests
from court.util import KuaidailiProxyManager
from spider import spider
from spider.runtime import Log


class WenshuCourtStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'ws_court')

    def extract_content(self):
        m = re.search(r'<input type="hidden" id="hidCaseInfo" value=\'([^\']*)\'', self.get_cur_doc().cur_content)
        if m:
            return m.group(1)
        else:
            return self.get_cur_doc().cur_content

    def parse_time(self):
        m = re.search(ur'发布日期：(\d-\d-\d)', self.get_cur_doc().cur_content)
        if m:
            return m.group(1)
        else:
            return None


class WenshuSpider(ProxySwapSpider):
    """文书网基本爬虫"""

    def __init__(self, thcnt, proxy_count=20, recover=False, name='WenshuSpider', log='wenshu.log', life=3600):
        super(WenshuSpider, self).__init__(thcnt, proxy_life=life)
        self._name = name
        self.recover = recover
        self.test_mode = False
        self.store = None
        self.utils = threading.local()
        self.sp_errors = OrderedDict()
        self.proxy_count = proxy_count
        self.proxy_loading_lock = threading.RLock()
        self.prev_count = 0
        self._start_time = int(time.time())
        logging.basicConfig(filename=os.path.join(os.getcwd(), log), level=logging.NOTSET,
                            format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                            datefmt='%m/%d %I:%M:%S %p')

    def on_404_exception(self, con, jobid):
        self.re_add_job(jobid)
        return True

    @staticmethod
    def to_list_seed_id(seed):
        return '%s/%s/%s/%s' % (seed['key'], seed['start'], seed['end'], seed['index'])

    @staticmethod
    def extract_paper_id(url):
        m = re.search(r'DocID=([\w\d-]+)', url)
        if m:
            return m.group(1)
        return None

    @staticmethod
    def extract_paper_url(content):
        m = re.findall(r'<a href="(/content/content[^"]*)', content)
        urls = []
        for u in m:
            urls.append('http://wenshu.court.gov.cn/' + u)
        return urls

    @staticmethod
    def extract_content(content):
        return content

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "Court Spider:%s\n" % self._name
            if self.store is not None:
                msg += "saved: %d\n" % self.store.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass

    def post_search(self, url, data):
        con = self.request_url(url, data=data)
        if con:
            print con.text

    @staticmethod
    def to_dict(query):
        conds = query.split('&conditions=')
        data = []
        for cond in conds[1:]:
            p = cond.split('+')
            data.append({
                'type': p[0],
                'value': p[1],
                'sign': p[2],
                'pid': p[3],
                'condition': p[4],
            })
        return data

    def do_search(self, url, index=1, page=5, order=u'裁判日期', direction='asc'):
        listparam = self.get_param(url)
        if self.test_mode:
            print listparam
        return self.request_results(listparam, index, page, order, direction)

    @staticmethod
    def get_param(url):
        param = WenshuSpider.to_dict(url[url.find('&conditions='):])
        listparam = ''
        for p in param:
            listparam += unquote(p['condition']) + ','
        return listparam

    def request_results(self, param, index=1, page=5, order=u'裁判日期', direction='asc'):
        con = self.request_url('http://wenshu.court.gov.cn/List/ListContent',
                               data={'Param': param, 'Index': index, 'Page': page, 'Order': order,
                                     'Direction': direction})
        if self.test_mode:
            print param
        return con

    def get_count(self, param):
        con = self.request_results(param, page=1)
        res = eval(con.text[1:-1].replace('\\"', '"'))
        if len(res) > 0:
            return int(res[0]['Count'])
        return 0

    @staticmethod
    def seed_date_to_param(seed_date):
        return u'裁判日期:%s-%s-%s TO %s-%s-%s' % (
            seed_date[:4], seed_date[4:6], seed_date[6:8], seed_date[8:12], seed_date[12:14],
            seed_date[14:])

    @staticmethod
    def seed2param(seed):
        return u'法院名称:%s,上传日期:%s TO %s' % (seed['court'].decode('utf-8'), seed['start'], seed['end'],)

    def load_proxy(self, fn, index=-1, auto_change=True):
        super(WenshuSpider, self).load_proxy(fn, index, auto_change)
        with self.locker:
            self.sp_errors.clear()
            for proxy in self.sp_proxies.iterkeys():
                self.sp_proxies[proxy] = 0

    def set_proxy(self, prs, index=-1, auto_change=True):
        with self.locker:
            if isinstance(prs, list):
                for p in prs:
                    self.sp_errors[p] = 0
            elif isinstance(prs, str) or isinstance(prs, unicode):
                self.sp_errors[prs] = 0
        super(WenshuSpider, self).set_proxy(prs, index, auto_change)

    def reload_proxy(self):
        with self.locker:
            if len(self.sp_proxies) <= 0:
                prs = {}
                count = 3
                while count > 0:
                    prs = KuaidailiProxyManager.load_proxy(self.proxy_count)
                    if prs['data']['count'] > 0:
                        break
                    count -= 1
                if count <= 0 or not prs.has_key('data') or not prs['data'].has_key('count') or \
                                prs['data'][
                                    'count'] <= 0:
                    self._shutdown()
                    logging.error('cannot load any proxy')
                    spider.util.sendmail(['shibaofeng@ipin.com'], 'Proxy Error',
                                         'Cannot load any proxy:%s,%s' % (self._name, self.proxy_count))
                    return
                print 'load %d proxies from kuaidaili by %s' % (
                    prs['data']['count'], threading.current_thread().getName())
                self.set_proxy(prs['data']['proxy_list'], 15 if (prs['data']['count'] > 15) else 0)
            else:
                logging.info('proxies has been loaded by other thread')
                print 'proxies has been loaded by other thread:', threading.current_thread().getName()

    def proxy_error(self):
        if not isinstance(self, ProxySwapSpider):
            proxy = getattr(self.utils, 'proxy', None)
            if proxy is not None:
                with self.locker:
                    try:
                        if self.sp_errors[proxy] < 5:
                            self.sp_errors[proxy] += 1
                        else:
                            self.sp_proxies.pop(proxy)
                            self.sp_errors.pop(proxy)
                            if len(self.sp_proxies) == 0:
                                self.reload_proxy()
                    except KeyError:
                        pass
        else:
            self.change_proxy()

    def on_proxy_error(self, con, jobid):
        self.proxy_error()
        self.re_add_job(jobid)
        return True

    def _set_proxy(self, kwargs, selproxy):
        super(WenshuSpider, self)._set_proxy(kwargs, selproxy)
        setattr(self.utils, 'proxy', selproxy)

    @staticmethod
    def check_js(con):
        return u'请开启JavaScript并刷新该页' in con.text

    def handle_js(self, con, ):
        sc = "document = {set cookie(a){console.log(a);}}, window = {innerWidth: 1024, innerHeight: 768, screenX: 200, screenY: 100, screen: {width: 1024, height: 768}}\n"
        mj = re.search(r'<script[^>]*>(.*?)</script>', con.text, re.S)
        sc += mj.group(1)
        rv = spider.util.runjs(sc)
        print rv
        for ck in re.split('\n', rv):
            ck = ck.strip()
            if ck:
                self.add_cookie_line('wenshu.court.gov.cn', ck)
        return True

    def thread_init(self, tid):
        super(WenshuSpider, self).thread_init(tid)
        if isinstance(self, ETOSSessionRequests):
            con = self.request_url('http://wenshu.court.gov.cn')
            print '[%s]==>%s' % (tid, con.cookies)

    def report_job_one_minute(self):
        if self.store is not None:
            count = self.store.saved_count - self.prev_count
            self.prev_count = self.store.saved_count
            Log.errinfo(time.strftime('%Y-%m-%d %H:%M:%S') + ' ==> %s' % count)
        else:
            Log.errinfo(time.strftime('%Y-%m-%d %H:%M:%S'))

    def form_report_message(self):
        prog = "mj:%d/%s,aj:%d/(%d,%d,%d)" % (self._mjob_count, self._mjob_all, self._job_count,
                                              self.job_queue.qsize(), self.job_queue2.qsize(),
                                              self.job_queue3.qsize())
        if isinstance(self.curjobid, dict) and self.curjobid.has_key('url'):
            cjstr = spider.util.utf8str(self.curjobid['url'])
        else:
            cjstr = spider.util.utf8str(self.curjobid.__str__())
        cjstr = re.sub(r'\r|\n', '', cjstr)
        if len(cjstr) > 100:
            cjstr = cjstr[0:100]
        if self.store:
            speed = self.store.saved_count / (int(time.time()) - self._start_time)
        else:
            speed = '-1'
        return "[pid=%d]speed:%s job:%s prog:%s\n" % (os.getpid(), speed, cjstr, prog)

    def report(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            time.sleep(1)  ##sleep for next report.
            if int(time.time()) % 60 == 0:
                self.report_job_one_minute()
            message = self.form_report_message()
            try:
                sock.sendto(message, ("127.0.0.1", self._logport))
            except Exception as e:
                pass
            if self._end_mark:
                message = "[pid=%d] DONE\n" % (os.getpid())
                try:
                    sock.sendto(message, ("127.0.0.1", self._logport))
                except:
                    pass
                return
