#!/usr/bin/env python
# -*- coding:utf8 -*-

import threading

import time

import signal

from spider import runtime


class Test:
    def __init__(self, thcnt):
        self._tls = threading.local()
        self.thread_cnt = thcnt
        self.threads = []
        self._name = 'thread-test'
        self._print_lock = threading.RLock()

    def runner(self, tid):
        setattr(self._tls, 'tid', tid)
        time.sleep(5)
        with self._print_lock:
            print 'thread-1', tid, getattr(self._tls, 'tid', -1)
        time.sleep(5)
        with self._print_lock:
            print 'thread-2', tid, getattr(self._tls, 'tid', -1)

    def run(self):
        setattr(self._tls, 'tid', -2)
        for tid in range(0, self.thread_cnt):
            t = threading.Thread(target=self.runner, args=(tid,))
            runtime.Runtime.set_thread_name(t.ident, "%s.worker.%d" % (self._name, tid))
            self.threads.append(t)
        print 'start', len(self.threads), 'threads'
        for t in self.threads:
            t.start()
        time.sleep(2)
        for t in self.threads:
            t.join()

        print 'all thread stop'


class ChildTest(Test):
    def __init__(self, thdcnt):
        Test.__init__(self, thdcnt)

    def run(self):
        Test.run(self)
        print 'child test', getattr(self._tls, 'tid', -1)


class SignalThreadTest:
    def __init__(self, thdcnt=3, name='test'):
        self.threads = []
        self.thread_cnt = thdcnt
        self._name = name

    def runner(self, jid):
        count = 0
        while True:
            print jid, count
            count += 1
            time.sleep(1)

    def run(self):
        signal.signal(signal.SIGSTOP, self.on_finish)
        signal.signal(signal.SIGINT, self.on_finish)
        signal.signal(signal.SIGTERM, self.on_finish)
        for tid in range(0, self.thread_cnt):
            t = threading.Thread(target=self.runner, args=(tid,))
            runtime.Runtime.set_thread_name(t.ident, "%s.worker.%d" % (self._name, tid))
            self.threads.append(t)
        print 'start', len(self.threads), 'threads'
        for t in self.threads:
            t.start()
        time.sleep(1)

    def on_finish(self, a=None, b=None):
        print 'on finish', self._name
        for t in self.threads:
            t.join()

        print 'all thread stop'


if __name__ == '__main__':
    test = SignalThreadTest(4)
    test.run()
