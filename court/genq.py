#!/usr/bin/env python
# -*- coding:utf8 -*-
import abc
import copy
import os
import re

import time

from court.util import remove_file
from spider import util
from spider.httpreq import BasicRequests
from spider.runtime import Log
from spider.savebin import FileSaver
from spider.spider import Spider


class PageGenQueries(BasicRequests):
    def __init__(self, saver):
        super(PageGenQueries, self).__init__()
        self.base_urls = []
        self.input_pattern = None
        self.form_pattern = None
        self.page_pattern = None
        self.page_index = 0
        self.target_index = 0
        self.ignore_inputs = []
        self.page_count = 0
        self.res = []
        self.saver = saver

    def save(self):
        if os.path.exists(self.saver):
            remove_file(self.saver)
        fs = FileSaver(self.saver)
        for r in self.res:
            fs.append(str(r))

    def run(self):
        self.res = []
        for url in self.base_urls:
            r = self.extract_inputs(url)
            if r['param']:
                self.res.append(r)

        for v in self.res:
            print v
        print 'res length', len(self.res)
        self.save()

    def extract_inputs(self, url):
        if not self.form_pattern or not self.input_pattern or not self.page_pattern:
            print 'None pattern'
            return
        con = self.request_url(url)
        if not con or not con.text:
            print 'None response content for', url
            return
        m = re.search(self.page_pattern, con.text)
        page_count = 0
        target = ''
        if m:
            page_count = m.group(self.page_index)
            target = m.group(self.target_index)
        form = re.search(self.form_pattern, con.text, re.S)
        if not form:
            print 'no form matches pattern', self.form_pattern, 'for', url
            return {'page_count': 0, 'param': [], 'url': url, 'target': target}
        params = []
        inputs = re.findall(self.input_pattern, form.group())
        for p in inputs:
            attrs = re.findall(r'((name|value)="([^"]*))', p)
            if len(attrs) > 1:
                param = {}
                for a, k, v in attrs:
                    param[k] = v
                params.append(param)
            elif len(attrs) > 0:
                for a, k, v in attrs:
                    if k == u'name':
                        params.append({k: v, u'value': ''})
        res = {}
        for p in params:
            res[p[u'name']] = p[u'value']
        for k in self.ignore_inputs:
            if res.has_key(k):
                res.pop(k)
        return {'page_count': page_count, 'param': res, 'url': url, 'target': target}


class AbstractParamSplit():
    def __init__(self, key):
        self.key = key

    @abc.abstractmethod
    def iter(self):
        raise NotImplementedError('virtual function called')

    def init(self):
        pass


class ConditionParamSpliter(AbstractParamSplit):
    def __init__(self, key, condition=None):
        AbstractParamSplit.__init__(self, key)
        if condition is None:
            condition = []
        self.condition = condition
        self.current = 0

    def iter(self):
        pass


class RangeParamSpliter(AbstractParamSplit):
    def __init__(self, key, pformat, method):
        AbstractParamSplit.__init__(self, key)
        self.param_format = pformat
        self.split_method = method

    def iter(self):
        pass


class CurrentUrlObject:
    def __init__(self, dct):
        self.url = dct.get('url')
        self.level = dct.get('level')
        self.kp = dct.get('kp', [])
        self.subidx = dct.get('subidx', -1)
        self.src = dct


class RangeGenQueries(Spider):
    def __init__(self, thread_count):
        super(RangeGenQueries, self).__init__(thread_count)
        self.conditions = []
        self.baseurl = {}
        self.oldjobs = []
        self.fs = FileSaver("res.%s.txt" % self._name)

    @abc.abstractmethod
    def init_conditions(self):
        raise NotImplementedError('virtual function called')

    def run(self, async=False, report=True):
        self.conditions = []
        self.baseurl = {}
        self.oldjobs = []
        self.init_conditions()
        try:
            sfilename = "res.%s.txt" % self._name
            with open(sfilename, 'r') as f:
                while True:
                    line = f.readline()
                    if not line:
                        break
                    line = line.strip()
                    if line not in self.oldjobs:
                        self.oldjobs.append(line)
        except Exception:
            pass
        Spider.run(self, async, report)

    def dispatch(self):
        jobid = {'type': 'co', 'url': self.baseurl, 'level': -1}
        self.add_job(jobid, True)
        time.sleep(2)
        self.wait_q()
        self.add_job(None, True)

    def run_job(self, jobid):
        if not isinstance(jobid, dict) or jobid.get('type') is not 'co':
            return
        co = CurrentUrlObject(jobid)
        newjobs = []
        for i in self._iter_more(co, self):
            newjobs.append(i)
        ns = self.need_split(co.url, co.level, len(newjobs) == 0)
        if not ns:
            if ns is 0:
                return 'end'
            self.log_url(co.url)
            return 'end'
        if len(newjobs) > 0:
            for j in newjobs:
                self.add_job(j, co.level < 0)
        else:
            if not self.process_failed_url(co.url):
                Log.error("===failed to split more : %s ===\n" % co.url)
                self.copy_split_fail(co.url)
            self.log_url(co.url)
            return 'broken'

    def copy_split_fail(self, url):
        return True

    def log_url(self, url):
        tol = util.utf8str(url).strip()
        if tol in self.oldjobs:
            return
        self.fs.append(tol)

    def process_failed_url(self, url):
        return False

    @abc.abstractmethod
    def need_split(self, url, level, isLast):
        tol = util.utf8str(url).strip()
        if tol in self.oldjobs:
            return False
        raise RuntimeError('virtual function called.')

    def compose_url(self, url, name, value):
        return self._compose_url(url, name, value)

    @staticmethod
    def _iter_more(co, gq):
        if co.level + 1 < len(gq.conddata):
            xobj = gq.conddata[co.level + 1]
            xn = gq.cond[co.level + 1]
            if isinstance(xobj, dict):
                for k in xobj:
                    url = RangeGenQueries._compose_url(co.url, xn, xobj[k]['value'])
                    kpkey = 'kp%d' % (co.level + 1)
                    newco = copy.deepcopy(co.src)
                    newco.update({'url': url, 'level': co.level + 1, kpkey: [k]})
                    yield newco
            elif isinstance(xobj, list):
                for v in xobj:
                    url = RangeGenQueries._compose_url(co.url, xn, v[0])
                    newco = copy.deepcopy(co.src)
                    newco.update({'url': url, 'level': co.level + 1})
                    yield newco
            else:
                raise RuntimeError("invalid arg")
            return
        xidx = -1
        idx = -1
        for o in gq.conddata:
            idx += 1
            if isinstance(o, dict):
                xidx += 1
                if co.subidx <= xidx:
                    kpkey = 'kp%d' % idx
                    so = RangeGenQueries._locate_obj2(o, co, kpkey)
                    if so is None or len(so) <= 0:
                        continue
                    for k in so:
                        url = RangeGenQueries._compose_url(co.url, gq.cond[idx], so[k]['value'])
                        kp = copy.deepcopy(co.src.get(kpkey))
                        kp.append(k)
                        newco = copy.deepcopy(co.src)
                        newco.update({'url': url, 'level': co.level + 1, kpkey: kp, 'subidx': xidx})
                        yield newco
                    return

    @staticmethod
    def _compose_url(url, name, value):
        if isinstance(url, unicode) or isinstance(url, str):
            if isinstance(url, unicode):
                url = url.encode('utf-8')
            m = re.search("[?&]%s=([^&]*)" % name, url)
            if m:
                return url[0:m.start(1)] + value + url[m.end(1):]
            else:
                return "%s&%s=%s" % (url, name, value)
        elif isinstance(url, dict):
            url1 = copy.deepcopy(url)
            url1[name] = value
            return url1
        else:
            raise RuntimeError("invalid url!")
