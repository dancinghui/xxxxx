#!/usr/bin/env python
# encoding:utf-8
import sys
import re
import threading
import sqlite3
import abc
import time
import spider.util

def myfac(x):
    return unicode(x)

class ProgressRecorder(object):
    NOT_FOUND=-1
    PROCESSING=0
    FINISHED=1

    def __init__(self, name='progress.db'):
        self._conn = sqlite3.connect(name, check_same_thread=False)
        ###print self._conn.text_factory
        ###self._conn.text_factory = myfac
        self.c = self._conn.cursor()
        self._lock = threading.RLock()
        try:
            self.c.execute("create table if not exists progress (id text primary key, catlog text key, prog int, info text)")
        except Exception as e:
            pass
        self.jobtrans = lambda v: unicode(v)

    def commit(self):
        with self._lock:
            self._conn.commit()

    def begin_process(self, catlog, job, info = None):
        values = self.jobtrans(job), unicode(catlog), self.PROCESSING, unicode(info)
        with self._lock:
            try:
                self.c.execute("insert into progress values (?,?,?,?)", values)
                #self._conn.commit()
            except sqlite3.IntegrityError:
                pass

    def end_process(self, job, info=None):
        if info is not None:
            values = unicode(info), self.FINISHED, self.jobtrans(job)
            with self._lock:
                self.c.execute("update progress set info=?,prog=? where job=?", values)
                #self._conn.commit()
        else:
            values = self.FINISHED, self.jobtrans(job)
            with self._lock:
                self.c.execute("update progress set prog=? where job=?", values)
                #self._conn.commit()

    def edit_info(self, job, info):
        values = unicode(info), self.jobtrans(job)
        with self._lock:
            self.c.execute("update progress set info=? where job=?", values)
            #self._conn.commit()

    def end_all(self, catlog):
        values = self.FINISHED, unicode(catlog)
        with self._lock:
            self.c.execute("update progress set prog=? where catlog=?", values)
            #self._conn.commit()

    def query(self, job):
        values = self.jobtrans(job),
        with self._lock:
            sql = "select prog,info from progress where id=?"
            self.c.execute(sql, values)
            #self.c.execute("select prog,info from progress where id=?", sqlite3.Binary(values))
            obj = self.c.fetchone()
            if obj is not None:
                return obj
        return self.NOT_FOUND, None


class JobPager(object):
    def __init__(self, pages, jfn, prog, name='jobpager'):
        jobs = []
        with open(jfn) as f:
            while True:
                l = f.readline()
                if not l:
                    break
                l = l.strip()
                jobs.append(l)
        self._pagesize = (len(jobs) + pages-1) / pages
        self._jobs = jobs
        self._prog = prog
        self._name = name

    def get_job(self, pageno, index):
        while True:
            xind = (pageno-1) * self._pagesize + index
            if xind >= len(self._jobs) or xind >= (pageno+1) * self._pagesize:
                return index, None
            job = self._jobs[xind]
            if not self.is_finished(pageno, job):
                catlog = '%s_%d'%(self._name, pageno)
                self._prog.end_all(catlog)
                self._prog.begin_process(catlog, job)
                index += 1
                self._prog.commit()
                return index, job
            index += 1

    def end_job(self, job, info=None):
        self._prog.end_process(job, info)

    def is_finished(self, pageno, job):
        catlog = '%s_%d'%(self._name, pageno)
        state, info = self._prog.query(job)
        if state < 0:
            return False
        if state == 0:
            return False
        return True


class MTRunBase(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._tid = 0
        self._mgr = None
        self._index = 0



    def endjob(self,job, info=None):
        self._mgr.jobpager.end_job(job, info)

    def run(self):
        while True:
            self._index, job = self._mgr.jobpager.get_job(self._tid, self._index)
            if job is None:
                print self._tid, "breaking............"
                break
            self.run_job(job)

    @abc.abstractmethod
    def run_job(self, jobline):
        #time.sleep(0.1)
        with self._mgr._lock:
            print jobline


class MTRunner(object):
    def __init__(self, target_class, thdcnt, jobfn, name='mtrun'):
        self._rcls = target_class
        self._thdcnt = thdcnt
        prog = ProgressRecorder()
        self.jobpager = JobPager(thdcnt, jobfn, prog, name)
        self._lock = threading.RLock()

    def run(self):
        threads = []
        for i in range(self._thdcnt):
            t = self._rcls()
            assert isinstance(t, MTRunBase)
            t._mgr = self
            t._tid = i+1
            threads.append(t)
            t.start()
        for t in threads:
            t.join()


if __name__ == '__main__':
    spider.util.use_utf8()
    r = MTRunner(MTRunBase, 2, 'r1k.txt')
    r.run()
