#!/usr/bin/env python
# -*- coding:utf8 -*-

import Queue
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
import random

from httpreq import BasicRequests, SessionRequests
from runtime import Log

class SpiderErrors:
    class FatalError(Exception):
        pass
    class RetryError(Exception):
        pass

class AccountErrors:
    class NoAccountError(Exception):
        pass

class LoginErrors:
    class RetryError(Exception):
        pass
    class NeedLoginError(Exception):
        pass
    class AccountHoldError(Exception):
        pass



class LimitedResource(object):
    def __init__(self, lst, shared):
        self.res = []
        self.reslock = []
        for i in lst:
            self.res.append(i)
            self.reslock.append(0)
        self.idx = 0
        self.locker = threading.RLock()
        self._shared = shared

    def get(self, checker):
        with self.locker:
            for nnn in range(0, len(self.res)):
                if not self.reslock[self.idx] and checker(self.res[self.idx]):
                    if not self._shared:
                        self.reslock[self.idx] = 1
                    rv = self.res[self.idx]
                    self.idx = (self.idx+1) % len(self.res)
                    return rv
                self.idx = (self.idx+1) % len(self.res)
        raise AccountErrors.NoAccountError("no more account")

    def unlock(self, obj):
        if self._shared:
            return
        with self.locker:
            for nnn in range(0, len(self.res)):
                if self.res[nnn] is obj:
                    self.reslock[nnn] = False
                    return True
        raise RuntimeError("no such object")


class MultiRequestsWithLogin(SessionRequests):
    def __init__(self, ac):
        SessionRequests.__init__(self)
        self.account = ac
        self.islogin = False
        self.req_count = 0
        self.isvalid = True
        self.select_user_agent('firefox')

    def set_nologin(self):
        with self.locker:
            self.islogin = 0
            self.reset_session()

    def _inc_call(self):
        with self.locker:
            self.req_count += 1
            return self.req_count

    def _dec_call(self):
        with self.locker:
            self.req_count -= 1
            return self.req_count

    def do_login(self):
        with self.locker:
            while self.req_count != 0:
                self.locker.release()
                time.sleep(1)
                self.locker.acquire()
            #now no one is req...
            first_loop = True
            while not self.islogin:
                if not self.is_valid():
                    break
                if not first_loop:
                    Log.warning("login failed, sleep 5s")
                    time.sleep(5)
                first_loop = False
                self.islogin = self._real_do_login()
            return self.islogin

    def is_valid(self):
        """检查帐号是否被封,没有被封返回True"""
        return self.isvalid

    @abc.abstractmethod
    def _real_do_login(self):
        raise NotImplementedError()

    def need_login(self, url, con, hint):
        """检查一个网络文件内容是否需要登录，必要时抛出LoginErrors里的异常"""
        pass



class MRLManager(object):
    def __init__(self, accounts, req_class, shared=False):
        assert isinstance(accounts, list)
        net_list = []
        for i in accounts:
            lp = req_class(i)
            if not isinstance(lp, MultiRequestsWithLogin):
                raise RuntimeError("initial this class with req_class = <sub class of MultiRequestsWithLogin>")
            net_list.append(lp)
        self.net_list = LimitedResource(net_list, shared)
        self._nettls = threading.local()

    def ensure_login_do(self, prechecker, caller, checker, trylimit=-1):
        """caller 调用具体函数，得到的返回值会交给checker处理，checker在必要时抛出LoginErrors里的异常"""
        retry_cnt = 0
        while retry_cnt != trylimit:
            retry_cnt += 1

            net = getattr(self._nettls, 'net', None)
            while net is None:
                net1 = self.net_list.get(lambda v:v.is_valid())
                net1.do_login()
                if net1.is_valid():
                    setattr(self._nettls, 'net', net1)
                    net = net1

            net._inc_call()
            try:
                if prechecker is not None:
                    prechecker(net)
                con = caller(net)
                if checker is not None and con is not None:
                    checker(net, con)
                net._dec_call()
                return con
            except LoginErrors.RetryError:
                net._dec_call()
                time.sleep(5)
            except (LoginErrors.AccountHoldError, SpiderErrors.FatalError):
                net.set_nologin()
                net._dec_call()
                setattr(self._nettls, 'net', None)
                self.net_list.unlock(net)
                time.sleep(5)
            except LoginErrors.NeedLoginError:
                net.set_nologin()
                net._dec_call()
                net.do_login()
                if not net.is_valid():
                    setattr(self._nettls, 'net', None)
                    self.net_list.unlock(net)
                time.sleep(5)
            except Exception:
                net._dec_call()
                raise
        return None

    def el_request(self, url, hint=None, prechecker=None, checker=None, **kwargs):
        caller = lambda net: net.request_url(url, **kwargs)
        if checker is None:
            checker = lambda net,con : net.need_login(url, con, hint)
        return self.ensure_login_do(prechecker, caller, checker)

    def set_nologin(self):
        net = getattr(self._nettls, 'net', None)
        if net is None:
            return
        if net.req_count > 0:
            Log.error("invalid function call!!")
            return
        net.set_nologin()
        setattr(self._nettls, 'net', None)
        self.net_list.unlock(net)

    def cur_worker(self):
        return getattr(self._nettls, 'net', None)

    def release_obj(self):
        net = getattr(self._nettls, 'net', None)
        if net is None:
            return
        if net.req_count > 0:
            Log.error("invalid function call!!")
            return
        setattr(self._nettls, 'net', None)
        self.net_list.unlock(net)


class ShareLimitedResource(LimitedResource):

    res = []
    reslock = []
    locker = threading.RLock()

    def __init__(self, lst, shared):
        for i in lst:
            self.res.append(i)
            self.reslock.append(0)
        self.idx = 0
        self._shared = shared


class ShareMRLManager(MRLManager):
    def __init__(self, accounts, req_class, shared=False):
        assert isinstance(accounts, list)
        net_list = []
        for i in accounts:
            lp = req_class(i)
            if not isinstance(lp, MultiRequestsWithLogin):
                raise RuntimeError("initial this class with req_class = <sub class of MultiRequestsWithLogin>")
            net_list.append(lp)
        self.net_list = ShareLimitedResource(net_list, shared)
        self._nettls = threading.local()


class Spider(BasicRequests):
    def __init__(self, threadcnt):
        BasicRequests.__init__(self)
        self.thread_count = threadcnt
        self.job_queue = Queue.Queue(100)
        self.job_queue2 = Queue.LifoQueue()
        self.job_queue3 = Queue.Queue() #for failed jobs.
        self._tls = threading.local()
        self._logport = 5555
        self._end_mark = 0
        self._mjlock = threading.RLock()
        self._mjlocktime = 0
        self._name = 'spider'
        self._threads = []
        self._reporter = None
        self._dispatcher = None
        self._worker_count = 0
        self.curjobid = 0
        self.enable_mainjob_timedlock = False
        self._start_timet = time.time()
        self._start_datetime = None
        self._running_count = 0

    def run(self, async=False, report=True):
        if (len(self._threads) > 0 or
                    self._reporter is not None or
                    self._dispatcher is not None):
            raise RuntimeError("already run??")

        self._start_datetime = datetime.datetime.now()
        self._threads = []
        self.curjobid = 0
        self._end_mark = 0
        self._worker_count = 0

        self._job_count = 0
        self._mjob_count = 0
        self._mjob_all = '?'
        self._dispatcher = threading.Thread(target=self.dispatch)
        self._dispatcher.start()
        runtime.Runtime.set_thread_name(self._dispatcher.ident, "%s.job.dispatcher" % self._name)
        if report:
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
        self._dispatcher.join()
        self._reporter.join()
        self._dispatcher = None
        self._reporter = None
        self._end_mark = 0
        self._threads = []
        if report:
            endtime = datetime.datetime.now()
            timespan = str(endtime - self._start_datetime)
            reportstr = "prog:%s\nlast job is %s\nDONE time used:%s\n" % (' '.join(sys.argv), str(self.curjobid), timespan)
            reportstr += "mj: %d aj:%d\n" % (self._mjob_count, self._job_count)
            sys.stderr.write(reportstr)
            self.event_handler('DONE', reportstr)

    def wait_q(self):
        lt = 0
        while True:
            while not self.job_queue.empty() or not self.job_queue2.empty() or not self.job_queue3.empty():
                self.job_queue.join()
                self.job_queue2.join()
                self.job_queue3.join()
            if time.time() < lt + 1 and self._running_count==0:
                return True
            time.sleep(2)
            lt = time.time()

    def _dec_worker(self):
        with self.locker:
            self._worker_count -= 1
            if self._worker_count == 0:
                self._end_mark = 1

    def _get_a_job(self):
        try:
            jobid = self.job_queue2.get_nowait()
            self.job_queue2.task_done()
            return jobid, False
        except Queue.Empty:
            pass

        if random.randint(1,20) == 19: #以5%的概率拿一个已经失败的任务
            try:
                jobid = self.job_queue3.get_nowait()
                self.job_queue3.task_done()
                return jobid, False
            except Queue.Empty:
                pass

        if self.enable_mainjob_timedlock:
            with self._mjlock:
                if self.job_queue2.qsize()>0:
                    pass #must try sub job first.
                elif time.time() >= self._mjlocktime:
                    try:
                        jobid = self.job_queue.get(True, 10)
                        self.job_queue.task_done()
                        if jobid is not None:
                            self._mjob_count += 1
                        self._mjlocktime = time.time() + 3
                        return jobid, 1
                    except Queue.Empty:
                        pass
                else: #mj is locked.
                    time.sleep(0.1)
        else:
            try:
                jobid = self.job_queue.get(True, 10)
                self.job_queue.task_done()
                if jobid is not None:
                    self._mjob_count += 1
                return jobid, 0
            except Queue.Empty:
                pass

        try:
            jobid = self.job_queue3.get_nowait()
            self.job_queue3.task_done()
            return jobid, False
        except Queue.Empty:
            pass

        return self._get_a_job()
 
    def _job_runner(self, tid):
        with self.locker:
            self._worker_count += 1
        setattr(self._tls, 'tid', tid)
        self.thread_init(tid)
        end_this_thd = False
        while not end_this_thd:
            jobid, ismainjob = self._get_a_job()
            if jobid is None:
                self.job_queue.put(None)
                self._dec_worker()
                return
            self._job_count += 1
            if isinstance(jobid, dict) and jobid.get('dontreport'):
                pass
            else:
                self.curjobid = jobid
            try:
                with self.locker:
                    self._running_count += 1
                self.run_job(jobid)
            except (AccountErrors.NoAccountError, SpiderErrors.FatalError) as e:
                Log.error(e)
                traceback.print_exc()
                end_this_thd = True
                self.add_job(jobid)
            except (LoginErrors.RetryError, SpiderErrors.RetryError) as e:
                Log.error(e)
                traceback.print_exc()
                self.add_job(jobid)
            except Exception as e:
                Log.warning(e)
                traceback.print_exc()
                self.re_add_job(jobid)
            finally:
                with self.locker:
                    self._running_count -= 1
            if ismainjob:
                with self._mjlock:
                    self._mjlocktime = 0
        self._dec_worker()

    def dump_jobid(self, jobid):
        tid = getattr(self._tls, 'tid', -1)
        header = "[tid:%d t:%s]job:" % (tid, int(time.time() - self._start_timet))
        if isinstance(jobid, unicode):
            print header, jobid.encode('utf-8')
        elif isinstance(jobid, list) or isinstance(jobid, dict):
            aa = json.dumps(jobid, ensure_ascii=False)
            if isinstance(aa, unicode):
                aa = aa.encode('utf-8')
            print header, aa
        else:
            print header, jobid

    def get_tid(self):
        tid = getattr(self._tls, 'tid', -1)
        return tid

    def get_job_type(self, job):
        if isinstance(job, dict):
            return job.get('type', None)
        return None

    def add_job(self, j, mainjob=False):
        if not mainjob:
            self.job_queue2.put(j)
            return True
        while True:
            try:
                self.job_queue.put(j, True, 30)
                return True
            except Queue.Full:
                if self._end_mark:
                    print "NO WORKER! failed to add job:", j
                    raise RuntimeError("no worker!")

    def add_main_job(self, j):
        return self.add_job(j, True)

    def re_add_job(self, j):
        if not isinstance(j, dict):
            raise RuntimeError("must be dict.")
        failcnt = j.get("_failcnt_", 0) + 1
        j['_failcnt_'] = failcnt
        if failcnt > 50:
            return False
        self.job_queue3.put(j)
        return True

    def dispatch(self):
        raise RuntimeError("virtual function called.")

    def run_job(self, jobid):
        return False

    def thread_init(self, tid):
        return

    def report(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            time.sleep(1) ##sleep for next report.
            if int(time.time()) % 60 == 0:
                Log.errinfo(time.strftime('%Y-%m-%d %H:%M:%S'))
            prog = "mj:%d/%s,aj:%d/(%d,%d,%d)" % (self._mjob_count, self._mjob_all, self._job_count,
                    self.job_queue.qsize(), self.job_queue2.qsize(), self.job_queue3.qsize())
            if isinstance(self.curjobid, dict) and self.curjobid.has_key('url'):
                cjstr = util.utf8str(self.curjobid['url'])
            else:
                cjstr = util.utf8str(self.curjobid.__str__())
            cjstr = re.sub(r'\r|\n', '', cjstr)
            if len(cjstr) > 100:
                cjstr = cjstr[0:100]
            message = "[pid=%d]job:%s prog:%s\n" % (os.getpid(), cjstr, prog)
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

    def event_handler(self, evt, msg, **kwargs):
        return

    def bindopts(self, gopt):
        if gopt is None:
            return
        if not isinstance(gopt, util.GetOptions):
            raise RuntimeError('invalid arg')
        if gopt.get('--singlethread'):
            self.thread_count = 1
