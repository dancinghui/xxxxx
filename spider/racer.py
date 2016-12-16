#!/usr/bin/env python
# -*- coding:utf8 -*-
import os
import sys
import threading
import time
import random


class TimedLock(object):
    def __init__(self, timeout=3):
        self._time = 0
        self._lock = threading.RLock()
        self._to = timeout
        self._key = 0

    def trylock(self):
        self._lock.acquire()
        nt = int(time.time())
        if nt < self._time:
            self._lock.release()
            return False
        else:
            # this key is required by reset. allow reset after unlocked.
            self._key = random.randint(10000000, 99999999)
            return self._key

    def unlock(self, lkey):
        if lkey:
            if lkey == self._key:
                self._time = int(time.time()) + self._to
            # TODO: someone request an unlock with an invalid key.
            # TODO: This might be a BUG. Should I report it?
        self._lock.release()

    def reset(self, key):
        if key == 0:
            return False
        with self._lock:
            if key == self._key and self._key > 0:
                self._time = 0
                return True
        return False

    def set_timeout(self, timeout):
        with self._lock:
            if int(time.time()) >= self._time:
                self._to = timeout
                return True
        return False


class RaceValueByKey:
    def __init__(self):
        self.locker = threading.RLock()
        self._dict = {}
        self._lockinfo = {}
        self._serial = 0
    def _getValue(self, key, func, force):
        with self.locker:
            if key in self._dict and not force:
                return self._dict[key]
            retry = 0
            while self._lockinfo.get(key, False):
                #this key is locked. we should wait.
                self.locker.release()
                time.sleep(1)
                self.locker.acquire()
                retry = 1
            if retry:
                pass #go out to end of with.
            else:
                self._lockinfo[key] = True
                self._serial += 1
                value = self._serial
                self.locker.release()
                try:
                    func(key)
                except:
                    self.locker.acquire()
                    if key in self._dict:
                        del self._dict[key]
                    if key in self._lockinfo:
                        del self._lockinfo[key]
                    raise
                self.locker.acquire()
                self._dict[key] = value
                self._lockinfo[key] = False
                return value
        return self._getValue(key, func, force)

    def getValue(self, key, func):
        return self._getValue(key, func, False)

    def delValueChecked(self, key, value):
        with self.locker:
            if self._dict.get(key) == value:
                del self._dict[key]

    def delValue(self, key):
        with self.locker:
            if key in self._dict:
                del self._dict[key]

    def oldValue(self, key):
        with self.locker:
            return self._dict.get(key, None)

    def sleepAlign(self, al):
        nt = time.time()
        nnt = int(nt) + al + al
        nnt = nnt/al
        nnt = nnt*al
        st = nnt-nt
        if st > 0:
            time.sleep(nnt - nt)

class AssemblyPoint:
    def __init__(self, cnt, timeout=300):
        self._cnt = cnt
        self._timeout = timeout
        self._curcnt = 0
        self._cond = threading.Condition()
        self._lcnt = 0
        self._serialno = 0

    def goAndTimeout(self):
        self._cond.acquire()
        sys.stderr.write("===[ptid:%d,%d][%d] go and timeout===\n" % (os.getpid(), threading.current_thread().ident, int(time.time())))
        self._curcnt += 1
        self._serialno += 1
        mid = self._serialno
        if self._curcnt == self._cnt:
            self._lcnt = self._curcnt - 1
            self._cond.notify_all()
            self._curcnt = 0
            self._cond.release()
            return
        else:
            while self._lcnt==0:
                self._cond.wait(self._timeout)
                if self._lcnt == 0 and mid == self._serialno:
                    #make a timeout.
                    self._lcnt = self._curcnt - 1
                    self._cond.notify_all()
                    self._curcnt = 0
                    self._cond.release()
                    return
            self._lcnt -= 1
            self._cond.release()
            return
    def go(self):
        self._cond.acquire()
        sys.stderr.write("===[pid:%d,%d][%d] go and timeout===\n" % (os.getpid(), threading.current_thread().ident, int(time.time())))
        self._curcnt += 1
        self._serialno += 1
        mid = self._serialno
        if self._curcnt == self._cnt:
            self._lcnt = self._curcnt - 1
            self._cond.notify_all()
            self._curcnt = 0
            self._cond.release()
            return
        else:
            while self._lcnt==0:
                self._cond.wait()
            self._lcnt -= 1
            self._cond.release()
            return


class TempFileNames:
    def __init__(self):
        self.names = []
        self.locker = threading.RLock()
        self.index = 0
    def get_name(self):
        with self.locker:
            if len(self.names)>0:
                return self.names.pop()
            self.index += 1
            return "%d.tmp" % self.index
    def release_name(self, name):
        with self.locker:
            self.names.insert(0, name)



if __name__ == '__main__':
    RaceValueByKey().sleepAlign(10)
