#!/usr/bin/env python
# -*- coding:utf8 -*-

import copy
import os
import re
import sys
import time
import util
import Queue
import abc
import json

from savebin import FileSaver
from spider import Spider
from runtime import Log

class AllPossibilities:
    def __init__(self, pm, sq=None):
        if not sq:
            sq = []
        self.pm = pm
        self.keys = self._sort_by(pm.keys(), sq)

    def _sort_by(self, q, sq):
        oq = []
        for x in sq:
            if x not in q:
                raise RuntimeError("invalid preordered queue")
            oq.insert(0, x)
        for x in q:
            if x not in sq:
                oq.insert(0, x)
        return oq

    def _all_posibilities(self, index, vals):
        if index == len(self.keys):
            omp = {}
            for i in range(0, len(self.keys)):
                omp[self.keys[i]] = vals[i]
            print omp
            return
        lst = self.pm[self.keys[index]]
        if isinstance(lst, list):
            for v in lst:
                vals.append(v)
                self._all_posibilities(index + 1, vals)
                vals.pop()
        else:
            vals.append(lst)
            self._all_posibilities(index + 1, vals)
            vals.pop()

    def print_all_posibilities(self):
        self._all_posibilities(0, [])

    def _xlen(self, obj):
        if isinstance(obj, list):
            return len(obj)
        return 1

    def _xobj(self, obj, ind):
        if isinstance(obj, list):
            return obj[ind]
        return obj

    def _add_stack(self, stack, ind):
        if ind < 0:
            return False
        stack[ind] += 1
        if stack[ind] >= self._xlen(self.pm[self.keys[ind]]):
            stack[ind] = 0
            return self._add_stack(stack, ind - 1)
        return True

    def all(self):
        stack = [0] * len(self.keys)
        while True:
            ro = {}
            for i in range(0, len(stack)):
                ro[self.keys[i]] = self._xobj(self.pm[self.keys[i]], stack[i])
            yield ro
            if not self._add_stack(stack, len(self.keys) - 1):
                break
                # done.


"""
jobdict = {'desc':'xx', 'value':'vv', 'children':{'k1':<jobdict>_1, 'k2':<jobdict>_2, ...}
jobroot = {'ka':<jobdict>_a, 'kb':<jobdict>_b, ...}
"""


class GQDataHelper:
    @staticmethod
    def add(obj, key, value):
        obj.cond.append(key)
        obj.conddata.append(value)

    @staticmethod
    def qlist(*x):
        outv = []
        for i in x:
            outv.append([i])
        return outv


class CurrentUrlObject:
    def __init__(self, dct):
        self.url = dct.get('url')
        self.level = dct.get('level')
        self.kp = dct.get('kp', [])
        self.subidx = dct.get('subidx', -1)
        self.src = dct


class GQPrivate:
    @staticmethod
    def _locate_obj(rd, co):
        obj = rd
        for k in co.kp:
            obj = obj[k].get('children', None)
        return obj

    @staticmethod
    def _locate_obj2(rd, co, kpkey):
        obj = rd
        for k in co.src.get(kpkey):
            obj = obj[k].get('children', None)
        return obj

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

    @staticmethod
    def iter_more(co, gq):
        if co.level+1 < len(gq.conddata):
            xobj = gq.conddata[co.level+1]
            xn   = gq.cond[co.level+1]
            if isinstance(xobj, dict):
                for k in xobj:
                    url = GQPrivate._compose_url(co.url, xn, xobj[k]['value'])
                    kpkey = 'kp%d' % (co.level+1)
                    newco = copy.deepcopy(co.src)
                    newco.update( {'url': url, 'level': co.level+1, kpkey:[k]} )
                    yield newco
            elif isinstance(xobj, list):
                for v in xobj:
                    url = GQPrivate._compose_url(co.url, xn, v[0])
                    newco = copy.deepcopy(co.src)
                    newco.update({'url': url, 'level': co.level+1})
                    yield  newco
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
                    so = GQPrivate._locate_obj2(o, co, kpkey)
                    if so is None or len(so) <= 0:
                        continue
                    for k in so:
                        url = GQPrivate._compose_url(co.url, gq.cond[idx], so[k]['value'])
                        kp = copy.deepcopy(co.src.get(kpkey))
                        kp.append(k)
                        newco = copy.deepcopy(co.src)
                        newco.update({'url': url, 'level': co.level+1, kpkey:kp, 'subidx':xidx})
                        yield newco
                    return


class GenQueries(Spider):
    def __init__(self, thdcnt=20):
        Spider.__init__(self, thdcnt)
        self.baseurl = {}
        self.conddata = []
        self.cond = []
        self.oldjobs = []

    def run(self, async=False):
        self.conddata = []
        self.cond = []
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
        self.fs = FileSaver("res.%s.txt" % self._name)
        Spider.run(self, async)

    @abc.abstractmethod
    def init_conditions(self):
        raise RuntimeError("virtual function called.")
        # self.cond = ['a','b','c']
        # self.conddata = [a,b,c] a,b,c is list or dict {key:{desc:'xx',value='vv',children:{}}}

    def get_max_count(self):
        mc = 1l
        for i in self.conddata:
            mc = mc * len(i)
        return mc

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
        for i in GQPrivate.iter_more(co, self):
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
        return GQPrivate._compose_url(url, name, value)


class GenQueriesLT(GenQueries):
    """
    GetQueriesLT, LT=Long Time
    对于长时间的任务. 把queries前两级默认拆开. 作为串行主任务, 从而可以从任意一点启动.
    """
    def __init__(self, thcnt=20):
        GenQueries.__init__(self, thcnt)
        self.enable_mainjob_timedlock = True
        self.mjob_page_info = [1, 1]

    def skip_n_jobs(self, aq, n):
        i=0
        while i+1<n:
            i+=1
            aq.get_nowait()
            aq.task_done()
            self._mjob_count += 1
        return True

    def skip_to_job(self, aq, job):
        while True:
            try:
                jx = aq.get_nowait()
                aq.task_done()
                self._mjob_count += 1
                if callable(job):
                    if job(jx):
                        self.add_main_job(jx)
                        return True
                elif jx == job:
                    self.add_main_job(jx)
                    return True
            except Queue.Empty:
                break
        return False

    def a_pof_b(self, a, b):
        for k,v in a.items():
            #TODO: BUG: if v is from dict, v must be parent of b.get(k)
            if b.has_key(k) and v==b.get(k):
                pass
            else:
                return False
        return True

    def skip_by_old(self, aq):
        """如果一个任务是最后一个任务的父级，则放行，否则跳过
        """
        if self.oldjobs is None or len(self.oldjobs) == 0:
            return
        lastjob = json.loads(self.oldjobs[-1])
        while True:
            try:
                curjob = aq.get_nowait()
                aq.task_done()
                if self.a_pof_b(curjob['url'], lastjob):
                    self.add_main_job(curjob)
                    return
                else:
                    self._mjob_count += 1
            except Queue.Empty:
                return

    def skip_jobs(self, aq):
        return

    def dispatch(self):
        jobid = {'type': 'co', 'url': self.baseurl, 'level': -1}
        co = CurrentUrlObject(jobid)
        newjobs = []
        for i in GQPrivate.iter_more(co, self):
            newjobs.append(i)
        newjobs2 = []
        for jx in newjobs:
            co1 = CurrentUrlObject(jx)
            for i in GQPrivate.iter_more(co1, self):
                newjobs2.append(i)

        _mjob_all = len(newjobs2)
        pagesize = (_mjob_all+self.mjob_page_info[1]-1)/self.mjob_page_info[1]
        aq = Queue.Queue()
        idx = 0
        for jx in newjobs2:
            idx += 1
            page = (idx+pagesize-1) / pagesize
            if page == self.mjob_page_info[0]:
                aq.put(jx)

        self._mjob_all = aq.qsize()
        self.skip_jobs(aq)
        while True:
            try:
                jx = aq.get_nowait()
                self.add_main_job(jx)
                aq.task_done()
            except Queue.Empty:
                break
        time.sleep(2)
        self.wait_q()
        self.add_main_job(None)

    def bindopts(self, gopt):
        GenQueries.bindopts(self, gopt)
        if gopt is None:
            return
        if not isinstance(gopt, util.GetOptions):
            raise RuntimeError('invalid arg')
        pageinfo = gopt.get('--page')
        if pageinfo:
            m = re.match(r'(\d+)/(\d+)$', pageinfo)
            if m is not None:
                self.mjob_page_info = [int(m.group(1)), int(m.group(2)) ]
                self._name += '_%d_%d' % tuple(self.mjob_page_info)
            else:
                raise RuntimeError('invalid arg --page')
        if gopt.get('--mjparellel'):
            self.enable_mainjob_timedlock = False


class GenQueriesLegacy(GenQueries):
    def run_job(self, jobd):
        if not isinstance(jobd, dict) or jobd.get('type') is not 'co':
            return
        co = CurrentUrlObject(jobd)

        ll = co.level
        if co.level == -1:
            ll = 0
            co.kp = []
        elif isinstance(self.conddata[co.level], dict):
            if GQPrivate._locate_obj(self.conddata[co.level], co) is None:
                co.kp = []
                ll += 1
        elif isinstance(self.conddata[co.level], list):
            co.kp = []
            ll += 1
        else:
            raise RuntimeError("invalid conddata")

        # now deal with this object.
        if not self.need_split(co.url, co.level, ll >= len(self.cond)):
            self.log_url(co.url)
            return

        if ll >= len(self.cond):
            if not self.process_failed_url(co.url):
                Log.error("===failed to split more : %s ===" % co.url)
            self.log_url(co.url)
            return

        if isinstance(self.conddata[ll], dict):
            xobj = GQPrivate._locate_obj(self.conddata[ll], co)
            for k in xobj:
                url = GQPrivate._compose_url(co.url, self.cond[ll], xobj[k]['value'])
                kp = copy.deepcopy(co.kp)
                kp.append(k)
                newco = {'type': 'co', 'url': url, 'level': ll, 'kp': kp}
                self.add_job(newco, ll == 0)
        elif isinstance(self.conddata[ll], list):
            for i in range(0, len(self.conddata[ll])):
                url = GQPrivate._compose_url(co.url, self.cond[ll], self.conddata[ll][i][0])
                newco = {'type': 'co', 'url': url, 'level': ll}
                self.add_job(newco, ll == 0)
