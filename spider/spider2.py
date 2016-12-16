#!/usr/bin/env python
# -*- coding:utf8 -*-


import abc
import datetime
import json
import os
import socket
import sys
import threading
import time
import traceback
import util
import runtime
import re
import cutil
import pycurl

from runtime import Log
from httpreq import CurlReq, BasicRequests, SessionRequests, ProxyError
from spider import AccountErrors, SpiderErrors, LoginErrors, LimitedResource, MultiRequestsWithLogin, MRLManager
from savebin import FileSaver
from genquery import CurrentUrlObject, GQDataHelper, GQPrivate


class Spider2(object):
    class Stats:
        def __init__(self):
            self.job_count = 0
            self.mjob_count = 0
            self.start_time = time.time()
            self.start_date = datetime.datetime.now()
            self.curjobstr = ""
            self.curjob = {}
        def report_str(self):
            timespan = str(datetime.datetime.now() - self.start_date)
            reportstr = "prog:%s\nlast job is %s\nDONE time used:%s\n" % (' '.join(sys.argv), self.curjobstr, timespan)
            reportstr += "mj: %d aj:%d\n" % (self.mjob_count, self.job_count)
            return reportstr
        def msg_str(self, mqsz, qsz):
            progargs = (self.mjob_count, mqsz, self.job_count, qsz)
            prog = "mj:%d/%d,aj:%d/%d" % progargs
            if self.curjob.has_key('url'):
                cjstr = util.utf8str(self.curjob['url'])
            else:
                cjstr = util.utf8str(self.curjob)
            cjstr = re.sub(r'\r|\n', '', cjstr)
            if len(cjstr) > 100:
                cjstr = cjstr[0:100]
            return "[pid=%d]job:%s prog:%s\n" % (os.getpid(), cjstr, prog)

    def __init__(self, threadcnt):
        self.networker = BasicRequests()
        self.thread_count = threadcnt
        self._tls = threading.local()
        self._logport = 6666
        self._name = 'spider'
        self._threads = []
        self._reporter = None
        self._worker_count = 0
        self._stat = None
        self._end_mark = 0
        self._running_count = 0 #正在执行任务的线程数量.
        self.locker = threading.RLock()
        self.job_mask = 'mnf'
        self.condtion = threading.Condition()
        self._jobq = None
        self._no_more_wait_job = False # 这个变量用于通知wait_for_condition函数,不会再有新的任务来了,不要再等了.

    def request_url(self, url, **kwargs):
        return self.networker.request_url(url, **kwargs)

    def run(self, async=False):
        if (len(self._threads) > 0 or self._reporter is not None):
            raise RuntimeError("already run??")

        self._threads = []
        self._worker_count = 0
        self._stat = Spider2.Stats()

        self._jobq = cutil.JobQueue('%s.job.bin' % self._name)
        if self._jobq.get_size() == 0:
            self.init_jobs()
        self._reporter = threading.Thread(target=self.report)
        self._reporter.start()
        runtime.Runtime.set_thread_name(self._reporter.ident, "%s.job.reporter" % self._name)

        for i in range(0, self.thread_count):
            t = threading.Thread(target=self._job_runner, args=(i,))
            t.start()
            runtime.Runtime.set_thread_name(t.ident, "%s.worker.%d" % (self._name, i))
            self._threads.append(t)

        self.event_handler('STARTED', '')
        if not async:
            self.wait_run(True)

    def wait_run(self, report=False):
        for t in self._threads:
            t.join()
        self._end_mark = 1
        self._reporter.join()
        self._reporter = None
        self._end_mark = 0
        self._threads = []
        if report:
            reportstr = self._stat.report_str()
            sys.stderr.write(reportstr)
            self.event_handler('DONE', reportstr)

    def wait_q(self):
        while self._jobq.get_size() != 0 or self._running_count != 0:
            time.sleep(1)

    def _dec_worker(self):
        with self.locker:
            self._worker_count -= 1
            if self._worker_count == 0:
                self._end_mark = 1

    def _job_runner(self, tid):
        with self.locker:
            self._worker_count += 1
        setattr(self._tls, 'tid', tid)
        self.thread_init(tid)
        end_this_thd = False

        while not end_this_thd:
            wflag = self.wait_job()
            with self.locker:
                self._running_count += 1
            jobstr, ismainjob = self._jobq.get_job(threading.current_thread().ident)
            if jobstr is None:
                with self.locker:
                    self._running_count -= 1
                # quit this thread when wait returns False, mean "no job" and actually no job.
                if not wflag:
                    break
            with self.locker:
                self._stat.job_count += 1
                if ismainjob:
                    self._stat.mjob_count += 1
            job = json.loads(jobstr)
            assert isinstance(job, dict)

            if not job.get('dontreport', False):
                self._stat.curjobstr = jobstr
                self._stat.curjob = job

            try:
                self.run_job(job)
            except (AccountErrors.NoAccountError, SpiderErrors.FatalError) as e:
                Log.error(e)
                traceback.print_exc()
                self.add_job(job)
                end_this_thd = True
            except (LoginErrors.RetryError, SpiderErrors.RetryError) as e:
                Log.error(e)
                traceback.print_exc()
                self.add_job(job)
            except Exception as e:
                Log.warning(e)
                traceback.print_exc()
                self.re_add_job(job)
            finally:
                with self.locker:
                    self._running_count -= 1

        self._dec_worker()

    def dump_job(self, job):
        header = "[tid:%d t:%s]job:" % (self.get_tid(), int(time.time() - self._stat.start_time))
        jobstr = util.utf8str(job)
        print header, jobstr

    def get_tid(self):
        tid = getattr(self._tls, 'tid', -1)
        return tid

    def get_job_type(self, job):
        if isinstance(job, dict):
            return job.get('type', None)
        return None

    def add_main_job_range(self, j, begin, end, step=1):
        assert isinstance(j, dict)
        r = self._jobq.add_main_job_range(util.utf8str(j), begin, end, step)
        self.condtion.acquire()
        self.condtion.notifyAll()
        self.condtion.release()
        return r

    def add_main_job_file(self, j, filename, begline=0, endline=0):
        assert isinstance(j, dict)
        r = self._jobq.add_main_job_file(util.utf8str(j), filename, begline, endline)
        self.condtion.acquire()
        self.condtion.notifyAll()
        self.condtion.release()
        return r

    def add_main_job(self, j):
        jobstr = json.dumps(j, ensure_ascii=0, sort_keys=1)
        if isinstance(jobstr, unicode):
            jobstr = jobstr.encode('utf-8')
        r = self._jobq.add_main_job(jobstr)
        self.condtion.acquire()
        self.condtion.notifyAll()
        self.condtion.release()
        return r

    def add_job(self, j):
        jobstr = json.dumps(j, ensure_ascii=0, sort_keys=1)
        if isinstance(jobstr, unicode):
            jobstr = jobstr.encode('utf-8')
        r = self._jobq.add_job(jobstr)
        self.condtion.acquire()
        self.condtion.notifyAll()
        self.condtion.release()
        return r

    def re_add_job(self, j):
        jobstr = json.dumps(j, ensure_ascii=0, sort_keys=1)
        if isinstance(jobstr, unicode):
            jobstr = jobstr.encode('utf-8')
        r = self._jobq.readd_job(jobstr)
        self.condtion.acquire()
        self.condtion.notifyAll()
        self.condtion.release()
        return r

    @abc.abstractmethod
    def run_job(self, job):
        return False

    def thread_init(self, tid):
        return

    def event_handler(self, evt, msg, **kwargs):
        return

    def wait_job(self):
        # By default we don't wait for external jobs.
        # However, if there is a threading running,
        # the thread may add some jobs.
        while self._jobq.get_size() == 0:
            if self._running_count == 0:
                return False
            time.sleep(1)
        return True

    @abc.abstractmethod
    def init_jobs(self):
        return

    def wait_job_by_condition(self):
        # This is the method that waits for external jobs.
        # Child classes implement wait_job method and call this method to enable waiting for external jobs.
        self.condtion.acquire()
        while self._jobq.get_size() == 0 and not self._no_more_wait_job:
            self.condtion.wait(10.0)
        self.condtion.release()
        if self._jobq.get_size() != 0:
            return True
        # 如果已经通知不再等任务,但还有线程正在运行任务,则要等一下这些线程,看他们是否会添加新的任务.
        # 否则直接退出减少线程数,而其它任务添加了大量任务,则不够线程继续处理.
        if self._no_more_wait_job:
            while self._jobq.get_size() == 0:
                if self._running_count == 0:
                    return False
                time.sleep(1)
            return True
        return False

    def report(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            time.sleep(1) ##sleep for next report.
            if int(time.time()) % 60 == 0:
                Log.errinfo(time.strftime('%Y-%m-%d %H:%M:%S'))
            message = self._stat.msg_str(self._jobq.get_mqsz(), self._jobq.get_size())
            try:
                sock.sendto(message, ("127.0.0.1", self._logport))
            except Exception as e:
                pass
            if self._end_mark:
                message = "[pid=%d] DONE\n" % os.getpid()
                try:
                    sock.sendto(message, ("127.0.0.1", self._logport))
                except:
                    pass
                return

    def bindopts(self, gopt):
        assert isinstance(gopt, util.GetOptions)
        if gopt.get('--singlethread'):
            self.thread_count = 1


class GenQueries2(Spider2):
    def __init__(self, thcnt=20):
        Spider2.__init__(self, thcnt)
        self.base_param = {}
        self.conddata = []
        self.cond = []
        self._select_jobs = None

    def init_jobs(self):
        jobid = {'type': 'co', 'url': self.base_param, 'level': -1}
        co = CurrentUrlObject(jobid)
        newjobs = []
        for i in GQPrivate.iter_more(co, self):
            newjobs.append(i)
        newjobs2 = []
        for jx in newjobs:
            co1 = CurrentUrlObject(jx)
            for i in GQPrivate.iter_more(co1, self):
                newjobs2.append(i)
        if self._select_jobs:
            newjobs2 = self._select_jobs(newjobs2)
        for j in newjobs2:
            self.add_main_job(j)

    def run(self, async=False):
        self.conddata = []
        self.cond = []
        self.oldjobs = []
        self.init_conditions()
        self.fs = FileSaver("res.%s.txt" % self._name)
        Spider2.run(self, async)

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

    def run_job(self, jobid):
        if not isinstance(jobid, dict) or jobid.get('type') != 'co':
            return
        co = CurrentUrlObject(jobid)
        newjobs = []
        for i in GQPrivate.iter_more(co, self):
            newjobs.append(i)
        ns = self.need_split(co.url, co.level, len(newjobs) == 0)
        if not ns:
            if ns is 0:
                return 'end'
            self.log_param(co.url)
            return 'end'
        if len(newjobs) > 0:
            for j in newjobs:
                self.add_job(j)
        else:
            if not self.process_failed_url(co.url):
                Log.error("===failed to split more : %s ===\n" % co.url)
            self.log_param(co.url)
            return 'broken'

    def log_param(self, param):
        tol = util.utf8str(param).strip()
        self.fs.append(tol)

    def process_failed_url(self, url):
        return False

    @abc.abstractmethod
    def need_split(self, param, level, isLast):
        raise RuntimeError('virtual function called.')

    def compose_url(self, url, name, value):
        return GQPrivate._compose_url(url, name, value)

    def bindopts(self, gopt):
        Spider2.bindopts(self, gopt)
        assert isinstance(gopt, util.GetOptions)
        pageinfo = gopt.get('--page')
        if pageinfo:
            m = re.match(r'(\d+)/(\d+)$', pageinfo)
            if m is not None:
                a, b = int(m.group(1)), int(m.group(2))
                self._name += '_%d_%d' % (a,b)
                self._select_jobs = lambda v : util.Pager.select_by_pager(v, a, b)
            else:
                raise RuntimeError('invalid arg --page')


class AioRunner(object):
    def __init__(self, curl, selproxy, idx):
        self.master = None
        self.proxyerr = 0
        self.sleepstate = 0
        self.job = None
        self.idx = idx
        self.selproxy = selproxy

    def prepare_req(self, job, curl, proxies):
        if self.proxyerr > 10:
            return 'exit'
        if self.sleepstate == 0 and self.proxyerr>0:
            self.sleepstate = 1
            return 'sleep 5'
        else:
            self.sleepstate = 0
        self.job = job
        return None

    def on_result(self, curl, resp):
        self.proxyerr =0
        return None

    def on_error(self, curl, errcode, errmsg):
        errobj = curl._error_obj(errcode, errmsg)
        if isinstance(errobj, ProxyError):
            self.proxyerr += 1
        self.master.re_add_job(self.job)

class AioSpider(object):
    def __init__(self, runnercls, name='aiospider'):
        self.proxies = []
        self._name = name
        self._jobq = None
        self._handles = {}
        self._end_mark = 0
        self._stat = None
        self._logport = 6666
        self._pending_job = None
        self.runner = runnercls

    @abc.abstractmethod
    def init_jobs(self):
        pass

    def add_job(self, j):
        assert isinstance(j, dict)
        return self._jobq.add_job(util.utf8str(j))

    def add_main_job(self, j):
        assert isinstance(j, dict)
        return self._jobq.add_main_job(util.utf8str(j))

    def add_main_job_range(self, j, begin, end, step=1):
        assert isinstance(j, dict)
        return self._jobq.add_main_job_range(util.utf8str(j), begin, end, step)

    def add_main_job_file(self, j, filename, begline=0, endline=0):
        assert isinstance(j, dict)
        return self._jobq.add_main_job_file(util.utf8str(j), filename, begline, endline)

    def re_add_job(self, j):
        assert isinstance(j, dict)
        return self._jobq.readd_job(util.utf8str(j))

    def load_proxy(self, fn):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                if re.match('\s*#', line):
                    continue
                self.proxies.append(line)
        print "==== %d proxies loaded ====" % len(self.proxies)

    def run(self):
        self._jobq = cutil.JobQueue('%s.job.bin' % self._name)
        if self._jobq.get_size() == 0:
            self.init_jobs()

        self._end_mark = 0
        self._stat = Spider2.Stats()
        self._reporter = threading.Thread(target=self.report)
        self._reporter.start()
        runtime.Runtime.set_thread_name(self._reporter.ident, "%s.job.reporter" % self._name)

        try:
            self._run_jobs()
        except Exception as e:
            Log.error("fatal error:", str(type(e)), str(e))
            traceback.print_exc()

        self._end_mark = 1
        self._reporter.join()
        self._end_mark = 0

    def _run_jobs(self):
        self._handles = {}
        curls = []
        idx = 0
        mobj = pycurl.CurlMulti()

        for selproxy in self.proxies:
            curl = CurlReq(None)
            curl.select_user_agent('baidu')
            curls.append(curl)
            m = re.match('([0-9.]+):(\d+):([a-z0-9]+):([a-z0-9._-]+)$', selproxy, re.I)
            if m:
                prstr = '%s:%s@%s:%s' % (m.group(3), m.group(4), m.group(1), m.group(2))
                proxies = {'http': 'http://' + prstr, 'https': 'https://' + prstr}
            elif selproxy == 'none':
                proxies = None
            else:
                proxies = {'http': 'http://' + selproxy, 'https': 'https://' + selproxy}
            runner = self.runner(curl, selproxy, idx)
            assert  isinstance(runner, AioRunner)
            runner.master = self
            self._handles[curl.curl] = [curl, proxies, runner, idx]
            idx += 1

        numrun = 0
        for i in curls:
            if self._call_next_req(i.curl):
                numrun += 1
                assert self._handles[i.curl][0] is i
                mobj.add_handle(i.curl)
            else:
                break
        pendings = {}
        while True:
            ret, numhds = self._perform(mobj)
            if numhds != numrun:
                msgs, oks, fails =  mobj.info_read()
                self._check_got(oks, fails)
                numrun = numhds # numrun - len(oks) - len(fails)
                numrun += self._add_tasks(mobj, oks, fails, pendings)
            if numrun == 0 and len(pendings.keys()) == 0:
                break
            mobj.select(1.0)
        # 拆除交叉引用，好像不是非常必要。
        for i, v in self._handles.items():
            v[2].master = None
        self._handles = None

    def _check_got(self, oks, fails):
        for i in oks:
            cr, proxy, runner, idx = tuple(self._handles[i])
            runner.on_result(cr, cr._build_result())
        for i in fails:
            cr, proxy, runner, idx = tuple(self._handles[i[0]])
            runner.on_error(cr, i[1], i[2])

    def _perform(self, mobj):
        while True:
            r, nh = mobj.perform()
            if r != pycurl.E_CALL_MULTI_PERFORM:
                return r, nh

    def _add_tasks(self, mobj, la, lb, pendings):
        lx = []
        lx.extend(la)
        for i in lb:
            lx.append(i[0])
        self._merge_by_time(lx, pendings)
        numok = 0
        for i in lx:
            cn = self._call_next_req(i)
            if cn is True:
                numok += 1
                mobj.remove_handle(i)
                mobj.add_handle(i)
            elif cn == 'exit':
                Log.error("Delete proxy:%d=>errcnt:%d"%(self._handles[i][2].idx, self._handles[i][2].proxyerr))
                mobj.remove_handle(i)
            elif isinstance(cn, str) and cn[0:5] == 'sleep':
                sv = float(cn[5:] or '5')
                if sv<2.0:
                    sv = 2.0
                pendings[i] = time.time() + sv
                Log.error("Sleep:%d=>errcnt:%d"%(self._handles[i][2].idx, self._handles[i][2].proxyerr))
            elif cn is None or cn is False:
                pendings[i] = time.time() - 1.0
            else:
                raise RuntimeError("prepare req must returns one of: True/False/None/'exit'/'sleep' ")
        return numok

    def _merge_by_time(self, lx, pendings):
        # 这里的逻辑是对pendings中的对象，间隔10s以上，加入重用逻辑。
        ks = pendings.keys()
        time_ = time.time()
        for k in ks:
            if time_ > pendings[k]:
                lx.append(k)
                del pendings[k]

    def _call_next_req(self, _curl):
        curl, proxies, runner, idx = tuple(self._handles[_curl])
        if self._pending_job is None:
            jobstr, ismain = self._jobq.get_job(idx)
            if jobstr is None:
                Log.error("Get None job.")
                return 'exit'
            j = json.loads(jobstr)
            if ismain:
                self._stat.mjob_count += 1
            self._stat.job_count += 1
            if not j.get('dontreport', False):
                self._stat.curjob = j
                self._stat.curjobstr = jobstr
            self._pending_job = j
        rv = runner.prepare_req(self._pending_job, curl, proxies)
        if rv:
            self._pending_job = None
        return rv

    def report(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            time.sleep(1) ##sleep for next report.
            if int(time.time()) % 60 == 0:
                Log.errinfo(time.strftime('%Y-%m-%d %H:%M:%S'))
            message = self._stat.msg_str(self._jobq.get_mqsz(), self._jobq.get_size())
            try:
                sock.sendto(message, ("127.0.0.1", self._logport))
            except Exception as e:
                pass
            if self._end_mark:
                message = "[pid=%d] DONE\n" % os.getpid()
                try:
                    sock.sendto(message, ("127.0.0.1", self._logport))
                except:
                    pass
                return
