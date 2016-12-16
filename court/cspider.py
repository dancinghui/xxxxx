#!/usr/bin/env python
# -*- coding:utf8 -*-

# !/usr/bin/env python
# -*- coding:utf8 -*-
import Queue
import abc
import datetime
import json
import logging
import os
import random
import re
import signal
import socket
import sys
import threading
import time
import traceback

import spider
from court.sessionrequests import ATOSSessionRequests, ETOSSessionRequests
from spider import runtime
from spider.runtime import Log
from spider.spider import Spider, AccountErrors, SpiderErrors, LoginErrors


class JobSpliter():
    def __init__(self):
        pass

    def split_param(self, url):
        raise NotImplementedError('virtual function called')


class RestorableSpider(Spider):
    """
    可恢复爬虫，能恢复到中断前的状态,当前只支持通过eval(str(a))能恢复变量的job类型
    """

    def __init__(self, threadcnt, statefile='.state.spider'):
        Spider.__init__(self, threadcnt)
        self.state_file = statefile
        self.catch_signal = False

    def run_job(self, jobid):
        if self.catch_signal:
            time.sleep(3)

    def restore(self):
        with open(self.state_file, 'r') as f:
            for l in f:
                (t, j) = l.strip().split(',', 2)
                if '2' == t:
                    self.job_queue2.put(eval(j))
                else:
                    self.job_queue.put(eval(j))

    def save_state(self, a=None, b=None):
        print 'Catch Signal', a, ',', b
        if self.catch_signal:
            return
        self.catch_signal = True
        with open(self.state_file, 'w') as f:
            while True:
                try:
                    job = self.job_queue2.get_nowait()
                    self.job_queue2.task_done()
                    f.write('2,' + str(job))
                except Queue.Empty:
                    break
            while True:
                try:
                    job = self.job_queue.get_nowait()
                    self.job_queue.task_done()
                    f.write('1,' + str(job))
                except Queue.Empty:
                    break
            while True:
                try:
                    job = self.job_queue3.get_nowait()
                    self.job_queue3.task_done()
                    f.write('3,' + str(job))
                except Queue.Empty:
                    break

    def run(self, async=False, report=True):
        signal.signal(signal.SIGTERM, self.save_state)
        signal.signal(signal.SIGINT, self.save_state)
        super(RestorableSpider, self).run(async, report)


class CourtSpider(Spider):
    """
    Spider which crawl legal instrument from court website
    需要两种抓取两种页面
    main：列表页面，这类页面是搜索结果只有文书简单信息
    paper:文书详细信息页面，通过列表页面获取访问详细信息页面的接口
    爬虫线程负责网页获取、解析保存的工作
    此外还处理了通常的异常并提供子类处理这些异常的方法
    """

    def __init__(self, thcnt, log='spider.log'):
        Spider.__init__(self, thcnt)
        self.pagestore = None
        self.job_spliter = None
        logging.basicConfig(filename=os.path.join(os.getcwd(), log), level=logging.NOTSET,
                            format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                            datefmt='%m/%d %I:%M:%S %p')

    @abc.abstractmethod
    def extract_content(self, content):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def add_list_job(self, url, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def need_split(self, context, url):
        raise NotImplementedError('virtual function called')

    def split_url(self, url):
        urls = self.job_spliter.split_param(url)
        if urls is None:
            logging.warn('split failed %s' % url)
            return
        logging.info('split %s into %d urls' % (url, len(urls)))
        for u in urls:
            self.add_job({'type': 'main', 'url': u})

    @abc.abstractmethod
    def extract_paper_url(self, content):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def extract_paper_id(self, url):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def get_page_store(self):
        raise NotImplementedError()

    def run_job(self, jobid):
        jt = jobid['type']
        url = jobid['url']

        if 'paper' == jt:
            print url
            con = self.request_url(url)
            if con is None or con.text is None:
                logging.warn('failed to fetch content ' + url)
                raise Exception('falied to fetch %s' % url)
            context = self.extract_content(con.text)
            if context is not None:
                jid = self.extract_paper_id(url)
                if jid is not None:
                    self.pagestore.save(int(time.time()), jid, url, context)
                else:
                    logging.warn('failed to find paper id, paper not save %s' % url)
                print url, '=>', len(context)
            else:
                logging.warn('fail to find content for:%s' % url)
            return

        con = self.request_url(url)
        if con is None:
            logging.warn('failed to fetch content ' + url)
            raise Exception('falied to fetch %s' % url)

        if 'main' == jt:
            if self.need_split(con.text, url):
                self.split_url(url)
                return
            self.add_list_job(url, con.text)
        urls = self.extract_paper_url(con.text)
        urls = spider.util.unique_list(urls)
        logging.info('add %d papers from %s' % (len(urls), url))
        for url in urls:
            self.add_job({'type': 'paper', 'url': url})

    def request_url(self, url, **kwargs):
        try:
            return super(CourtSpider, self).request_url(url, **kwargs)
        except Exception as e:
            logging.debug('catch exception %s,%s', type(e), e.message)
            raise e

    def check_exception(self, con, jobid):
        if con is None:
            logging.warn('None type response %s', str(jobid))
            self.re_add_job(jobid)
            return True
        if con.text is None:
            logging.warn('None type response text %s', str(jobid))
            self.re_add_job(jobid)
            return True
        if 500 > con.code >= 400:
            logging.warn('client error %d,%s', con.code, str(jobid))
            print con.headers
            if 404 == con.code:
                print '啊呵,404,服务器上居然找不到这个页面', jobid
                logging.info('page not found on the server %s', str(jobid))
                return self.on_404_exception(con, jobid)
            if 410 == con.code:
                print 'resource gone', jobid
                logging.info('resource is gone from the server %s', str(jobid))
                return True
            return self.on_other_400_exception(con, jobid)
        if 600 > con.code >= 500:
            logging.warn('server error %d,%s', con.code, str(jobid))
            print con.headers
            if 502 == con.code:
                print 'Proxy Error 502', jobid
                logging.error('proxy error 502 %s', str(jobid))
                return self.on_proxy_error(con, jobid)
            return self.on_other_500_exception(con, jobid)
        if con.code > 600:
            print '600 以上的code,涨见识了！哈哈哈！', jobid
            logging.info('failed with response code %d,%s', con.code, str(jobid))
            return True
        return self.on_other_exception(con, jobid)

    def on_other_400_exception(self, con, jobid):
        self.re_add_job(jobid)
        return True

    def on_other_500_exception(self, con, jobid):
        self.re_add_job(jobid)
        return True

    def on_other_exception(self, con, jobid):
        return False

    def on_proxy_error(self, con, jobid):
        self.re_add_job(jobid)
        return True

    def on_404_exception(self, con, jobid):
        return True


class ETOSSessionSpider(ETOSSessionRequests):
    """
    每个线程单独Session的爬虫（Each Thread One Session）
    保存会话(Session的爬虫)
    这个类除了Session管理跟spider.spider.Spider不一样外其他情况都一样
    代理的改变不会引发Session的改变，这对于Session绑定IP的网站要注意，
    当然如果通过新代理访问网站返回新会话的话新会话信息会覆盖之前的Session
    """

    def __init__(self, threadcnt):
        ETOSSessionRequests.__init__(self)
        self.thread_count = threadcnt
        self.job_queue = Queue.Queue(100)
        self.job_queue2 = Queue.LifoQueue()
        self.job_queue3 = Queue.Queue()  # for failed jobs.
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
        time.sleep(1)
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
            reportstr = "prog:%s\nlast job is %s\nDONE time used:%s\n" % (
                ' '.join(sys.argv), str(self.curjobid), timespan)
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
            if time.time() < lt + 1 and self._running_count == 0:
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

        if random.randint(1, 20) == 19:  # 以5%的概率拿一个已经失败的任务
            try:
                jobid = self.job_queue3.get_nowait()
                self.job_queue3.task_done()
                return jobid, False
            except Queue.Empty:
                pass

        if self.enable_mainjob_timedlock:
            with self._mjlock:
                if self.job_queue2.qsize() > 0:
                    pass  # must try sub job first.
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
                else:  # mj is locked.
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
            time.sleep(1)  ##sleep for next report.
            if int(time.time()) % 60 == 0:
                Log.errinfo(time.strftime('%Y-%m-%d %H:%M:%S'))
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
        if not isinstance(gopt, spider.util.GetOptions):
            raise RuntimeError('invalid arg')
        if gopt.get('--singlethread'):
            self.thread_count = 1


class ATOSSessionSpider(ATOSSessionRequests):
    """
    所有线程共享Session的爬虫（All Threads One Session）
    保存会话(Session的爬虫)
    这个类除了Session管理跟spider.spider.Spider不一样外其他情况都一样
    代理的改变不会引发Session的改变，这对于Session绑定IP的网站要注意，
    当然如果通过新代理访问网站返回新会话的话新会话信息会覆盖之前的Session
    """

    def __init__(self, threadcnt, failed_limit=50):
        ATOSSessionRequests.__init__(self)
        self.thread_count = threadcnt
        self.job_queue = Queue.Queue(100)
        self.job_queue2 = Queue.LifoQueue()
        self.job_queue3 = Queue.Queue()  # for failed jobs.
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
        self.failed_limit = failed_limit

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
        time.sleep(1)
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
            reportstr = "prog:%s\nlast job is %s\nDONE time used:%s\n" % (
                ' '.join(sys.argv), str(self.curjobid), timespan)
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
            if time.time() < lt + 1 and self._running_count == 0:
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

        if random.randint(1, 20) == 19:  # 以5%的概率拿一个已经失败的任务
            try:
                jobid = self.job_queue3.get_nowait()
                self.job_queue3.task_done()
                return jobid, False
            except Queue.Empty:
                pass

        if self.enable_mainjob_timedlock:
            with self._mjlock:
                if self.job_queue2.qsize() > 0:
                    pass  # must try sub job first.
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
                else:  # mj is locked.
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
        if j is not None and not j.has_key('url'):
            pass
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
        if failcnt > self.failed_limit:
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
            time.sleep(1)  ##sleep for next report.
            if int(time.time()) % 60 == 0:
                Log.errinfo(time.strftime('%Y-%m-%d %H:%M:%S'))
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
        if not isinstance(gopt, spider.util.GetOptions):
            raise RuntimeError('invalid arg')
        if gopt.get('--singlethread'):
            self.thread_count = 1


class ATOSSessionExceptionSpider(ATOSSessionSpider):
    """异常处理爬虫"""

    def check_exception(self, con, jobid):
        if con is None:
            logging.warn('None type response %s', str(jobid))
            self.re_add_job(jobid)
            return True
        if con.text is None:
            logging.warn('None type response text %s', str(jobid))
            self.re_add_job(jobid)
            return True
        if 500 > con.code >= 400:
            logging.warn('client error %d,%s', con.code, str(jobid))
            print con.headers
            if 404 == con.code:
                print '啊呵,404,服务器上居然找不到这个页面', jobid
                logging.info('page not found on the server %s', str(jobid))
                return self.on_404_exception(con, jobid)
            if 410 == con.code:
                print 'resource gone', jobid
                logging.info('resource is gone from the server %s', str(jobid))
                return True
            return self.on_other_400_exception(con, jobid)
        if 600 > con.code >= 500:
            logging.warn('server error %d,%s', con.code, str(jobid))
            print con.headers
            if 502 == con.code:
                print 'Proxy Error 502', jobid
                logging.error('proxy error 502 %s', str(jobid))
                return self.on_proxy_error(con, jobid)
            return self.on_other_500_exception(con, jobid)
        if con.code > 600:
            print '600 以上的code,涨见识了！哈哈哈！', jobid
            logging.info('failed with response code %d,%s', con.code, str(jobid))
            return True
        return self.on_other_exception(con, jobid)

    def on_other_400_exception(self, con, jobid):
        self.re_add_job(jobid)
        return True

    def on_other_500_exception(self, con, jobid):
        self.re_add_job(jobid)
        return True

    def on_other_exception(self, con, jobid):
        return False

    def on_proxy_error(self, con, jobid):
        self.re_add_job(jobid)
        return True

    def on_404_exception(self, con, jobid):
        return True


class ETOSSessionExceptionSpider(ETOSSessionSpider):
    """异常处理爬虫"""

    def check_exception(self, con, jobid):
        if con is None:
            logging.warn('None type response %s', str(jobid))
            self.re_add_job(jobid)
            return True
        if con.text is None:
            logging.warn('None type response text %s', str(jobid))
            self.re_add_job(jobid)
            return True
        if 500 > con.code >= 400:
            logging.warn('client error %d,%s', con.code, str(jobid))
            print con.headers
            if 404 == con.code:
                print '啊呵,404,服务器上居然找不到这个页面', jobid
                logging.info('page not found on the server %s', str(jobid))
                return self.on_404_exception(con, jobid)
            if 410 == con.code:
                print 'resource gone', jobid
                logging.info('resource is gone from the server %s', str(jobid))
                return True
            return self.on_other_400_exception(con, jobid)
        if 600 > con.code >= 500:
            logging.warn('server error %d,%s', con.code, str(jobid))
            print con.headers
            if 502 == con.code:
                print 'Proxy Error 502', jobid
                logging.error('proxy error 502 %s', str(jobid))
                return self.on_proxy_error(con, jobid)
            return self.on_other_500_exception(con, jobid)
        if con.code > 600:
            print '600 以上的code,涨见识了！哈哈哈！', jobid
            logging.info('failed with response code %d,%s', con.code, str(jobid))
            return True
        return self.on_other_exception(con, jobid)

    def on_other_400_exception(self, con, jobid):
        self.re_add_job(jobid)
        return True

    def on_other_500_exception(self, con, jobid):
        self.re_add_job(jobid)
        return True

    def on_other_exception(self, con, jobid):
        return False

    def on_proxy_error(self, con, jobid):
        self.re_add_job(jobid)
        return True

    def on_404_exception(self, con, jobid):
        return True


class ATOSSessionCourtSpider(ATOSSessionExceptionSpider):
    "Spider which crawl legal instrument from court website"

    def __init__(self, thcnt, failed_limit=50):
        ATOSSessionSpider.__init__(self, thcnt, failed_limit)
        self.special_saver = None
        self.job_spliter = None
        logging.basicConfig(filename=os.path.join(os.getcwd(), 'spider.log'), level=logging.NOTSET,
                            format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                            datefmt='%m/%d %I:%M:%S %p')

    @abc.abstractmethod
    def extract_content(self, content):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def add_list_job(self, url, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def need_split(self, context, url):
        raise NotImplementedError('virtual function called')

    def split_url(self, url):
        urls = self.job_spliter.split_param(url)
        if urls is None:
            logging.warn('split failed %s' % url)
            return
        logging.info('split %s into %d urls' % (url, len(urls)))
        for u in urls:
            self.add_job({'type': 'main', 'url': u})

    @abc.abstractmethod
    def extract_paper_url(self, content):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def extract_paper_id(self, url):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def get_page_store(self):
        raise NotImplementedError()

    def run_job(self, jobid):
        jt = jobid['type']
        url = jobid['url']

        if 'paper' == jt:
            print url
            con = self.request_url(url)
            if con is None or con.text is None:
                logging.warn('failed to fetch content ' + url)
                raise Exception('falied to fetch %s' % url)
            context = self.extract_content(con.text)
            if context is not None:
                jid = self.extract_paper_id(url)
                if jid is not None:
                    self.special_saver.save(int(time.time()), jid, url, context)
                else:
                    logging.warn('failed to find paper id, paper not save %s' % url)
                print url, '=>', len(context)
            else:
                logging.warn('fail to find content for:%s' % url)
            return

        con = self.request_url(url)
        if con is None:
            logging.warn('failed to fetch content ' + url)
            raise Exception('falied to fetch %s' % url)

        if 'main' == jt:
            if self.need_split(con.text, url):
                self.split_url(url)
                return
            self.add_list_job(url, con.text)
        urls = self.extract_paper_url(con.text)
        urls = spider.util.unique_list(urls)
        logging.info('add %d papers from %s' % (len(urls), url))
        for url in urls:
            self.add_job({'type': 'paper', 'url': url})

    def request_url(self, url, **kwargs):
        try:
            return super(ATOSSessionCourtSpider, self).request_url(url, **kwargs)
        except Exception as e:
            logging.debug('catch exception %s,%s', type(e), e.message)
            raise e


class ETOSSessionCourtSpider(ETOSSessionExceptionSpider):
    "Spider which crawl legal instrument from court website"

    def __init__(self, thcnt, log='spider.log'):
        ETOSSessionSpider.__init__(self, thcnt)
        self.special_saver = None
        self.job_spliter = None
        logging.basicConfig(filename=os.path.join(os.getcwd(), log), level=logging.NOTSET,
                            format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                            datefmt='%m/%d %I:%M:%S %p')

    @abc.abstractmethod
    def extract_content(self, content):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def add_list_job(self, url, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def need_split(self, context, url):
        raise NotImplementedError('virtual function called')

    def split_url(self, url):
        urls = self.job_spliter.split_param(url)
        if urls is None:
            logging.warn('split failed %s' % url)
            return
        logging.info('split %s into %d urls' % (url, len(urls)))
        for u in urls:
            self.add_job({'type': 'main', 'url': u})

    @abc.abstractmethod
    def extract_paper_url(self, content):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def extract_paper_id(self, url):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def get_page_store(self):
        raise NotImplementedError()

    def run_job(self, jobid):
        jt = jobid['type']
        url = jobid['url']

        if 'paper' == jt:
            print url
            con = self.request_url(url)
            if con is None or con.text is None:
                logging.warn('failed to fetch content ' + url)
                raise Exception('falied to fetch %s' % url)
            context = self.extract_content(con.text)
            if context is not None:
                jid = self.extract_paper_id(url)
                if jid is not None:
                    self.special_saver.save(int(time.time()), jid, url, context)
                else:
                    logging.warn('failed to find paper id, paper not save %s' % url)
                print url, '=>', len(context)
            else:
                logging.warn('fail to find content for:%s' % url)
            return

        con = self.request_url(url)
        if con is None:
            logging.warn('failed to fetch content ' + url)
            raise Exception('falied to fetch %s' % url)

        if 'main' == jt:
            if self.need_split(con.text, url):
                self.split_url(url)
                return
            self.add_list_job(url, con.text)
        urls = self.extract_paper_url(con.text)
        urls = spider.util.unique_list(urls)
        logging.info('add %d papers from %s' % (len(urls), url))
        for url in urls:
            self.add_job({'type': 'paper', 'url': url})

    def request_url(self, url, **kwargs):
        try:
            return super(ETOSSessionCourtSpider, self).request_url(url, **kwargs)
        except Exception as e:
            logging.debug('catch exception %s,%s', type(e), e.message)
            raise e


class ShutdownableSpider(ATOSSessionExceptionSpider):
    def __init__(self, thcnt):
        super(ShutdownableSpider, self).__init__(thcnt)
        self.__shutdown = False

    def _shutdown(self):
        self.__shutdown = True

    def _on_shutdown(self, jobid):
        pass

    def run_job(self, jobid):
        if self.__shutdown:
            self._on_shutdown(jobid)
            return

    def check_shutdown(self, jobid):
        if self.__shutdown:
            self._on_shutdown(jobid)
            return True


class EShutdownableSpider(ETOSSessionExceptionSpider):
    def __init__(self, thcnt):
        super(EShutdownableSpider, self).__init__(thcnt)
        self.__shutdown = False

    def _shutdown(self):
        self.__shutdown = True

    def _on_shutdown(self, jobid):
        pass

    def run_job(self, jobid):
        if self.__shutdown:
            self._on_shutdown(jobid)
            return

    def check_shutdown(self, jobid):
        if self.__shutdown:
            self._on_shutdown(jobid)
            return True


class ProxySwapSpider(ShutdownableSpider):
    def __init__(self, thcnt, proxy_life=180):
        super(ProxySwapSpider, self).__init__(thcnt)
        self.proxy_lock = threading.RLock()
        self.proxy_life = proxy_life
        self.proxy_start_time = time.time()
        self._proxy_utils = threading.local()
        self._auto_change_proxy = False

    def load_proxy(self, fn, index=-1, auto_change=False):
        """屏蔽自动换代理,不要在外边设置代理或者过改动auto_change"""
        super(ProxySwapSpider, self).load_proxy(fn, index, False)

    def set_proxy(self, prs, index=-1, auto_change=False):
        """屏蔽自动换代理"""
        super(ProxySwapSpider, self).set_proxy(prs, index, False)

    def request_url(self, url, **kwargs):
        prs = self.sp_proxies.keys()
        setattr(self._proxy_utils, 'last_proxy', prs[self._cur_proxy_index])
        con = super(ProxySwapSpider, self).request_url(url, **kwargs)
        if con is None and self.is_proxy_error():
            self.change_proxy()
        return con

    def check_proxy(self):
        with self.proxy_lock:
            if time.time() - self.proxy_start_time > self.proxy_life:
                print 'proxy %d life exceeds limit' % self._cur_proxy_index
                self.change_proxy()

    def change_proxy(self, remove=False):
        proxy = getattr(self._proxy_utils, 'last_proxy', None)
        if self._cur_proxy_index < 0:
            print 'no proxy'
            logging.info('no proxy')
            return
        with self.proxy_lock:
            prs = self.sp_proxies.keys()
            if remove:
                if proxy == prs[self._cur_proxy_index]:
                    self.sp_proxies.pop(proxy)
                    logging.info('remove proxy %s' % proxy)
                    print 'remove proxy', proxy
                    if len(self.sp_proxies) > 0:
                        self._cur_proxy_index %= len(self.sp_proxies)
                    else:
                        self._cur_proxy_index = -1
            else:
                if proxy == prs[self._cur_proxy_index]:
                    self._cur_proxy_index = (self._cur_proxy_index + 1) % len(self.sp_proxies)
            self.reset_session()
            logging.info('change proxy %d', self._cur_proxy_index)


class EProxySwapSpider(EShutdownableSpider):
    def __init__(self, thcnt, proxy_life=180):
        super(EProxySwapSpider, self).__init__(thcnt)
        self.proxy_lock = threading.RLock()
        self.proxy_life = proxy_life
        self.proxy_start_time = time.time()
        self._proxy_utils = threading.local()
        self._auto_change_proxy = False

    def load_proxy(self, fn, index=-1, auto_change=False):
        '''屏蔽自动换代理,不要在外边设置代理或者过改动auto_change'''
        super(EProxySwapSpider, self).load_proxy(fn, index, False)

    def set_proxy(self, prs, index=-1, auto_change=False):
        '''屏蔽自动换代理'''
        super(EProxySwapSpider, self).set_proxy(prs, index, False)

    def request_url(self, url, **kwargs):
        prs = self.sp_proxies.keys()
        setattr(self._proxy_utils, 'last_proxy', prs[self._cur_proxy_index])
        con = super(EProxySwapSpider, self).request_url(url, **kwargs)
        if con is None and self.is_proxy_error():
            self.change_proxy()
        return con

    def check_proxy(self):
        with self.proxy_lock:
            if time.time() - self.proxy_start_time > self.proxy_life:
                print 'proxy %d life exceeds limit' % self._cur_proxy_index
                self.change_proxy()

    def change_proxy(self, remove=False):
        proxy = getattr(self._proxy_utils, 'last_proxy', None)
        if self._cur_proxy_index < 0:
            print 'no proxy'
            logging.info('no proxy')
            return
        with self.proxy_lock:
            prs = self.sp_proxies.keys()
            if remove:
                if proxy == prs[self._cur_proxy_index]:
                    self.sp_proxies.pop(proxy)
                    logging.info('remove proxy %s' % proxy)
                    print 'remove proxy', proxy
                    if len(self.sp_proxies) > 0:
                        self._cur_proxy_index %= len(self.sp_proxies)
                    else:
                        self._cur_proxy_index = -1
            else:
                if proxy == prs[self._cur_proxy_index]:
                    self._cur_proxy_index = (self._cur_proxy_index + 1) % len(self.sp_proxies)
            self.reset_session()
            logging.info('change proxy %d', self._cur_proxy_index)


class AbstractSleeper(object):
    def __init__(self, sleep=1.0):
        self.sleep = sleep

    def try_to_sleep(self):
        t = time.time() - self.last_sleep_time()
        if t < self.sleep:
            time.sleep(self.sleep - t)
            self.set_last_sleep(time.time())

    @abc.abstractmethod
    def last_sleep_time(self):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def set_last_sleep(self, t):
        raise NotImplementedError('virtual function called')


class Sleeper(AbstractSleeper):
    def __init__(self, sleep=1.0):
        AbstractSleeper.__init__(self, sleep)
        self.__last_sleep = time.time()

    def last_sleep_time(self):
        return self.__last_sleep

    def set_last_sleep(self, t):
        self.__last_sleep = t


class ThreadSleeper(AbstractSleeper):
    def __init__(self, sleep=1.0):
        AbstractSleeper.__init__(self, sleep)
        self.__last_sleep = threading.local()

    def last_sleep_time(self):
        t = getattr(self.__last_sleep, 'last_sleep', 0)
        return t

    def set_last_sleep(self, t):
        setattr(self.__last_sleep, 'last_sleep', t)


class HttpDispatcherSessionSpider(ATOSSessionExceptionSpider):
    """
    spider who requests web page in dispatcher with one session
    job runners are handler of the web fetched web pages
    this spider good for those website whose has low request limit
    """

    def __init__(self, thcnt, sleeper=None):
        ATOSSessionExceptionSpider.__init__(self, thcnt)
        if sleeper is not None and not isinstance(sleeper, AbstractSleeper):
            raise RuntimeError('sleeper must be None or instance of AbstractSleeper')
        self.__sleeper = sleeper

    @abc.abstractmethod
    def load_seeds(self):
        raise NotImplementedError('virtual function called')

    def request_url(self, url, **kwargs):
        if self.__sleeper:
            self.__sleeper.try_to_sleep()
        con = ATOSSessionExceptionSpider.request_url(self, url, **kwargs)
        return con

    def request_seed_content(self, seed):
        return self.request_url(seed['url'])

    def handle_seed_content(self, seed, content):
        seed['content'] = content
        self.add_main_job(seed)

    def handle_seed_exception(self, exception):
        pass

    def dispatch(self):
        seeds = self.load_seeds()
        count = 10
        while count > 0 and len(seeds) > 0:
            failed_seeds = []
            for seed in seeds:
                try:
                    con = self.request_seed_content(seed)
                except Exception as e:
                    self.handle_seed_exception(e)
                    failed_seeds.append(seed)
                    continue
                if con is None:
                    failed_seeds.append(seed)
                    continue
                self.handle_seed_content(seed, con)
            count -= 1
            seeds = failed_seeds
        time.sleep(2)
        self.wait_q()
        self.add_job(None)
