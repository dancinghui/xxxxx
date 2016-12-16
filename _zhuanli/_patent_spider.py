#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import json
import logging
import os
import re
import threading
import time
from collections import OrderedDict
from datetime import datetime
from urllib import quote

import sys

from court.save import FailedJobSaver, LinkSaver
from court.util import KuaidailiProxyManager, Main
from spider import spider
from spider.httpreq import CurlReq
from zlspider import ZhuanliBaseSpider, ZhuanliBaseStore


class PatentAbstractStore(ZhuanliBaseStore):
    def __init__(self, channel='abstract'):
        ZhuanliBaseStore.__init__(self, channel)

    def extract_content(self):
        m = re.search(r'<div class="main">(.*)<!--footer-->', self.get_cur_doc().cur_content, re.S)
        if m:
            return m.group(1)
        return self.get_cur_doc().cur_content

    def page_time(self):
        return int(time.time() * 1000)


class PropertiesManager():
    def __init__(self, fn='setting.properties'):
        self._fname = fn
        self._properties = {}

    def load(self):
        with open(self._fname, 'r') as f:
            res = f.read()
            self._properties = eval(res.strip())

    def get(self, name, default=None):
        return self._properties.get(name, default)

    def set(self, name, value):
        self._properties[name] = value

    def save(self):
        with open(self._fname, 'w') as f:
            f.write(json.dumps(self._properties, indent=4))


class PatentAbstractSpider(ZhuanliBaseSpider, Main):
    """专利摘要爬虫"""

    def __init__(self, thcnt, mode='id', recover=True, seeds='seed.dat'):
        ZhuanliBaseSpider.__init__(self, thcnt, recover, timeout=90)
        Main.__init__(self)
        self.short_tag = 't:m:s:r:o:h:v:'
        self.tags = ['recover=', 'threads=', 'mode=', 'seeds=', 'output=']
        self.seeds = seeds
        self.page_size = 20  # 3或者10,20
        self.pagestore = PatentAbstractStore('abstract')
        self.failed_saver = FailedJobSaver('failed_job.txt')
        self.seed_saver = LinkSaver('seed.year.txt', 'a+')
        self.job_log = LinkSaver('abstract.%s.log' % mode, 'a+')
        self.mode = mode
        self.__version = '1.0.0'
        self.utils = threading.local()
        self.sp_errors = OrderedDict()
        self.pre_save_count = 0
        self.properties = PropertiesManager()
        self.can_load_seed = True

    def output(self, args):
        print '_patent_spider.py: %s' % args

    def version(self):
        print '_patent_spider.py %s' % self.__version

    def usage(self):
        print '_patent_spider.py usage:'
        print '-h, --help: print help message.'
        print '-v, --version: print script version'
        print '-o, --output: input an output verb'
        print '-t, --threads: thread count '
        print '-m, --mode: mode,if not id then will be abstract mode'
        print '-r, --recover: recover,1 or True for recover mode'
        print '-s, --seeds: seeds file'

    def _set_proxy(self, kwargs, selproxy):
        super(PatentAbstractSpider, self)._set_proxy(kwargs, selproxy)
        setattr(self.utils, 'proxy', selproxy)

    def handle(self, opts):
        for o, a in opts:
            if o in ('-h', '--help'):
                self.usage()
                sys.exit(1)
            elif o in ('-v', '--version'):
                self.version()
                sys.exit(0)
            elif o in ('-o', '--output'):
                self.output(a)
                sys.exit(0)
            elif o in ('-t', '--threads'):
                self.thread_count = int(a)
            elif o in ('-m', '--mode'):
                self.mode = a
            elif o in ('-s', '--seeds'):
                self.seeds = a
            elif o in ('-r', '--recover'):
                self.recover = True if (a == '1' or a == 'True') else False
            else:
                print 'unhandled option'
                sys.exit(3)
        if self.mode != 'id':
            self.mode = 'abs'
        if self.mode != 'id' and not os.path.exists(self.seeds):
            print 'seed file %s not exists' % self.seeds
            sys.exit(1)
        count = 3
        while count > 0:
            self.sp_proxies = OrderedDict()
            if self.mode == 'id':
                # self.set_proxy('183.111.169.203:8080', len(job.sp_proxies))
                self.set_proxy('192.168.1.39:3428:ipin:helloipin', len(job.sp_proxies))
            else:
                proxies = KuaidailiProxyManager.load_proxy(100)
                print 'load %d proxies from kuaidaili' % proxies['data']['count']
                if proxies['data']['count'] > 0:
                    self.set_proxy(proxies['data']['proxy_list'], 15 if (proxies['data']['count'] > 15) else 0)
            # proxies = KuaidailiProxyManager.load_proxy(50)
            # print 'load %d proxies from kuaidaili' % proxies['data']['count']
            # if proxies['data']['count'] > 0:
            #     self.set_proxy(proxies['data']['proxy_list'], 15 if (proxies['data']['count'] > 15) else 0)
            self.run()
            count -= 1

    def load_proxy(self, fn, index=-1, auto_change=True):
        super(PatentAbstractSpider, self).load_proxy(fn, index, auto_change)
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
        super(PatentAbstractSpider, self).set_proxy(prs, index, auto_change)

    @staticmethod
    def gen_list_seed():
        now = datetime.now()
        this_year = int(now.strftime('%Y'))
        this_month = int(now.strftime('%m'))
        types = ['fmgb', 'fmsq', 'xxsq', 'wgsq']
        seeds = []
        for year in range(1985, this_year):
            for month in range(1, 13):
                for t in types:
                    seeds.append(
                        {'type': t, 'index': 1, 'time': '%s%s' % (year, (month if month > 9 else '0%s' % month))})
        for month in range(1, this_month):
            for t in types:
                seeds.append(
                    {'type': t, 'index': 1, 'time': '%s%s' % (this_year, (month if month > 9 else '0%s' % month))})
        return seeds

    def load_abstract_seeds(self, seed_file, limit=1000000):
        seeds = []
        last_position = self.properties.get('position', 0)
        f = open(seed_file, 'r')
        count = 0
        f.seek(last_position)
        while count < limit:
            l = f.readline()
            if not l:
                # 文件结束,不能再读
                self.can_load_seed = False
                break
            res = l.strip().split(',')
            if len(res) < 3:
                print 'invalid seeds:', l
            else:
                seeds.append({'type': res[1], 'id': res[0], 'code': res[2]})
                count += 1
        last_position = f.tell()
        self.properties.set('position', last_position)
        self.properties.save()
        f.close()
        return seeds

    def get_id_seeds(self):
        raw_seeds = self.gen_list_seed()
        rds = self.job_log.readlines()
        '''get done jobs'''
        done_jobs = {}
        for job in rds:
            if '[' == job[0]:
                continue
            js = job.strip().split('-')
            done_jobs['%s-%s' % (js[0], js[1])] = {}
            done_jobs['%s-%s' % (js[0], js[1])]['pages'] = int(js[2])
            done_jobs['%s-%s' % (js[0], js[1])]['current'] = 1
        '''load done seeds'''
        dss = self.seed_saver.readlines()
        for ds in dss:
            sd = ds.strip().split(',')
            if len(sd) < 4:
                print 'invalid seed', ds
                continue
            js = sd[3].split('-')
            sid = '%s-%s' % (js[0], js[1])
            page = int(js[2])
            if done_jobs.has_key(sid) and done_jobs[sid]['current'] < page:
                done_jobs[sid]['current'] = page
        seeds = []
        for seed in raw_seeds:
            sid = seed['time'] + '-' + seed['type']
            if done_jobs.has_key(sid):
                if done_jobs[sid]['pages'] > done_jobs[sid]['current'] > 1:
                    for page in range(done_jobs[sid]['current'] + 1, done_jobs[sid]['pages'] + 1):
                        s = copy.deepcopy(seed)
                        s['index'] = page
                        seeds.append(s)
            else:
                seeds.append(seed)

        logging.info('load %s list seeds', len(seeds))
        return seeds

    def get_abstract_seeds(self, limit=100000):
        rawseeds = self.load_abstract_seeds(self.seeds, limit)
        seeds = []
        for s in rawseeds:
            if not self.recover or not self.pagestore.find_any(self.pagestore.channel + '://' + s['id']):
                seeds.append(s)
                if len(seeds) >= limit:
                    break
        logging.info('load %d abstract seeds', len(seeds))
        return seeds

    def report(self):
        super(PatentAbstractSpider, self).report()
        self.job_log.flush()
        self.seed_saver.flush()
        count = self.pagestore.saved_count - self.pre_save_count
        self.pre_save_count = self.pagestore.saved_count
        print 'save %d doc in this minute' % count

    def dispatch(self):
        self.failed_saver.tag()
        if self.mode == 'id':
            seeds = self.get_id_seeds()
            for seed in seeds:
                self.add_main_job(seed)
        else:
            count = 10
            ever_loaded = False
            while count > 0 and self.can_load_seed:
                seeds = self.get_abstract_seeds()
                if len(seeds) > 0:
                    ever_loaded = True
                    for seed in seeds:
                        self.add_main_job(seed)
                    time.sleep(2)
                    self.wait_q()
                elif ever_loaded:
                    count -= 1
                    time.sleep(100)

        time.sleep(2)
        self.wait_q()
        self.add_job(None)

    @staticmethod
    def extract_seed_id(pub, app, count):
        return '%s-%s/%s-%s/%s' % (
            pub[0], pub[1], app[0] if (app[0] != '-') else '', app[1] if (app[1] != '-') else '', count)

    @staticmethod
    def parse_seed(seed):
        v = seed.split(',')
        if len(v) != 7:
            print 'invalid seed', seed
            return []
        return [[v[1][1:], v[2][:-1]], [v[3][1:], v[4][:-1]], int(v[6])]

    @staticmethod
    def get_query_word(jobid):
        word = '公开（公告）日=%s' % jobid['time']
        return word

    def _on_shutdown(self, jobid):
        self.failed_saver.save('2,%s' % str(jobid))
        return

    def handle_id_job(self, jobid):
        strword = self.get_query_word(jobid)
        url = self.form_query_url(strword, page=jobid['index'], size=self.page_size, selected=jobid['type'], showtype=0)
        con = self.request_url(url, timeout=self.timeout)
        if self.check_exception(con, jobid):
            print 'exception encounter', jobid
            return
        if re.search(u'<title>错误页面</title>', con.text):
            print '错误页面', jobid
            if not self.re_add_job(jobid):
                self.failed_saver.save(str(jobid))
            return
        patents = re.findall(r'<a href="javascript:zl_xm\(\'([\d\w]+)\',\'(\w+)\',\'([\w\d]+)\'\);">[\d\w]+</a>',
                             con.text)
        print '[%d]%s-%s-%s' % (len(patents), jobid['time'], jobid['type'], jobid['index'])
        if 0 == len(patents):
            self.job_log.add('[%d]%s-%s-%s,%s' % (len(patents), jobid['time'], jobid['type'], jobid['index'], con.code))
            self.re_add_job(jobid)
            return
        for p in patents:
            if len(p) != 3:
                logging.warn('invalid pattern matched:%s,%s', str(p), str(jobid))
                self.failed_saver.save('1,%s' % str(jobid))
            else:
                self.seed_saver.add(
                    '%s,%s,%s,%s-%s-%d' % (p[0], p[1], p[2], jobid['time'], jobid['type'], jobid['index']))
        if 1 == jobid['index']:
            m = re.search(r'javascript:if\(event.keyCode == 13\) zl_tz\((\d+)\)', con.text)
            if m:
                pagecnt = int(m.group(1))
                print '[%d][%d]%s-%s-%d' % (len(patents), pagecnt, jobid['time'], jobid['type'], jobid['index'])
                self.job_log.add('%s-%s-%s' % (jobid['time'], jobid['type'], pagecnt))
                for page in range(2, pagecnt + 1):
                    job = copy.deepcopy(jobid)
                    job['_failcnt_'] = 0
                    job['index'] = page
                    self.add_job(job)
            else:
                print 'failed to find count[%d]%s-%s-[%d]' % (len(patents), jobid['time'], jobid['type'], 0)
                logging.warn('failed to find page count:%s-%s-%s', jobid['time'], jobid['type'], jobid['index'])

    def handle_abstract_seed(self, jobid):
        qword = quote('申请号=\'%s\' and %s=1' % (jobid['id'], jobid['code']))
        url = 'http://epub.sipo.gov.cn/patentdetail.action?strSources=%s&strWhere=%s&strLicenseCode=&pageSize=6&pageNow=1' % (
            jobid['type'], qword)
        con = self.request_url(url, timeout=self.timeout)
        if self.check_exception(con, jobid):
            print 'exception encounter', jobid
            return
        if re.search(u'<title>错误页面</title>', con.text):
            print '错误页面', jobid
            if not self.re_add_job(jobid):
                self.failed_saver.save(str(jobid))
            return
        print 'success:%s-%s-%s' % (jobid['id'], jobid['type'], jobid['code'])
        self.pagestore.save(int(time.time()), jobid['id'], url, con.text)

    def run_job(self, jobid):
        if self.check_shutdown(jobid):
            return
        try:
            if self.mode == 'id':
                self.handle_id_job(jobid)
            else:
                self.handle_abstract_seed(jobid)
        except RuntimeError as e:
            if 'no proxy' in e.message:
                self.re_add_job(jobid)
                self.reload_proxy()
                return
            else:
                raise

    def reload_proxy(self):
        prs = {}
        count = 3
        while count > 0:
            if 'id' == self.mode:
                prs = KuaidailiProxyManager.load_proxy(20)
            else:
                prs = KuaidailiProxyManager.load_proxy(100)
            if prs['data']['count'] > 0:
                break
            count -= 1
        if count <= 0 or not prs.has_key('data') or not prs['data'].has_key('count') or \
                        prs['data'][
                            'count'] <= 0:
            self._shutdown()
            logging.error('cannot load any proxy')
            spider.util.sendmail(['shibaofeng@ipin.com'], 'Proxy Error',
                                 'Cannot load any proxy:%s,%s' % (self._name, self.mode))
            return
        print 'load %d proxies from kuaidaili' % prs['data']['count']
        self.set_proxy(prs['data']['proxy_list'], 15 if (prs['data']['count'] > 15) else 0)

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            self.job_log.flush()
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)

    def proxy_error(self):
        proxy = getattr(self.utils, 'proxy')
        if proxy is not None:
            with self.locker:
                try:
                    if self.sp_errors[proxy] < 5:
                        self.sp_errors[proxy] += 1
                    else:
                        self.sp_proxies.pop(proxy)
                        if len(self.sp_proxies) == 0:
                            self.reload_proxy()
                except KeyError:
                    pass

    def on_proxy_error(self, con, jobid):
        self.proxy_error()
        self.re_add_job(jobid)
        return True

    def on_other_400_exception(self, con, jobid):
        if con.code == 403:
            self.proxy_error()
        self.re_add_job(jobid)
        return True

    def on_other_500_exception(self, con, jobid):
        if 504 == con.code and re.search('proxy', con.text, re.I):
            self.proxy_error()
            self.re_add_job(jobid)
            return True
        else:
            return super(PatentAbstractSpider, self).on_other_500_exception(con, jobid)


if __name__ == '__main__':
    CurlReq.DEBUGREQ = 1
    job = PatentAbstractSpider(10, recover=True)
    job.main(sys.argv)
