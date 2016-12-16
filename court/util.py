#!/usr/bin/env python
# -*- coding:utf8 -*-
import abc
import codecs
import copy
import datetime
import getopt
import json
import os
import re
import sys
import threading
import pymongo

from spider.httpreq import BasicRequests


def ym_cs2num(in_str):
    if re.match(ur'^[一二三四五六七八九十]', in_str):
        in_str = re.sub(ur'一|十', '1', in_str)
        in_str = re.sub(u'二', '2', in_str)
        in_str = re.sub(u'三', '3', in_str)
        in_str = re.sub(u'四', '4', in_str)
        in_str = re.sub(u'五', '5', in_str)
        in_str = re.sub(u'六', '6', in_str)
        in_str = re.sub(u'七', '7', in_str)
        in_str = re.sub(u'八', '8', in_str)
        in_str = re.sub(u'九', '9', in_str)
        in_str = re.sub(ur'〇|零|○|Ｏ|O|О', '0', in_str)
    return in_str


def day_cs2num(in_str):
    if re.match(ur'^[一二三四五六七八九十]', in_str):
        in_str = re.sub(ur'^三十$', '30', in_str)
        in_str = re.sub(ur'^二十$', '20', in_str)
        in_str = re.sub(ur'^十$', '10', in_str)
        in_str = re.sub(u'二十', '2', in_str)
        in_str = re.sub(u'三十', '3', in_str)
        in_str = re.sub(u'一十', '1', in_str)
        in_str = re.sub(ur'一|十', '1', in_str)
        in_str = re.sub(u'二', '2', in_str)
        in_str = re.sub(u'三', '3', in_str)
        in_str = re.sub(u'四', '4', in_str)
        in_str = re.sub(u'五', '5', in_str)
        in_str = re.sub(u'六', '6', in_str)
        in_str = re.sub(u'七', '7', in_str)
        in_str = re.sub(u'八', '8', in_str)
        in_str = re.sub(u'九', '9', in_str)
        in_str = re.sub(ur'〇|零|○|O|Ｏ|О', '0', in_str)
    return in_str


cs_date_pattern = ur'[一二三四五六七八九0〇○Ｏ零十OО]+年[一二三四五六七八九〇十0○ＯOО]+月[一二三四五六七八九〇零○Ｏ0十OО]+日'
cs_date_pattern_recent = ur'[一二三四五六七八九0〇○Ｏ零十OО]{4}年[一二三四五六七八九〇十0○ＯOО]{1,2}月[一二三四五六七八九〇零○Ｏ0十OО]{1,3}日'
cs_date_pattern_recent_utf8 = r'[一二三四五六七八九0〇○Ｏ零十OО]{4}年[一二三四五六七八九〇十0○ＯOО]{1,2}月[一二三四五六七八九〇零○Ｏ0十OО]{1,3}日'


def date_cs2num(date):
    if re.match(ur'^[一二三四五六七八九0〇○Ｏ零十OО]+年[一二三四五六七八九〇十0○ＯOО]+月[一二三四五六七八九〇零○Ｏ0十OО]+日', date):
        ds = re.sub(ur'[年月日]', '-', date)
        v = ds.split('-', 3)
        if len(v) < 3:
            raise Exception('Invalid date string')
        return ym_cs2num(v[0]) + '-' + ym_cs2num(v[1]) + '-' + day_cs2num(v[2])
    return date


def remove_file(file):
    if os.path.exists(file) and os.path.isfile(file):
        os.remove(file)


def url_standardize(url):
    return re.sub(r'\?&', '?', re.sub('&$', '', url))


def redial_local_proxy():
    os.system("sshpass -p 'helloipin' ssh ipin@192.168.1.39 /home/ipin/bin/redial")


def extract_host(url):
    m = re.search('^\w+:\/\/([^\/]+)\/', url.strip())
    if m:
        return m.group(1)


def extract_path(url):
    m = re.search('^\w+:\/\/[^\/]+(\/.*)', url.strip())
    if m:
        return m.group(1)


def save_file(content, fname):
    with open(fname, 'wb') as f:
        f.writelines(content)


def count_unique_doc(coll, db, dbUrl):
    client = pymongo.MongoClient(dbUrl)
    if client is None:
        print 'Failed to connect to mongo'
        return 0
    dbs = client[db]
    if dbs is None:
        print 'Cannot find database', db
        return 0
    collection = dbs[coll]
    if collection is None:
        print 'No such collection', collection
        return 0
    ids = collection.find()
    indexUrls = []
    for url in ids:
        if url not in indexUrls:
            indexUrls.append(url)

    return len(indexUrls)


def isleapyear(year):
    return year % 400 == 0 or year % 400 != 0 and year % 4 == 0


class FileUtils():
    """utils handle files"""

    @staticmethod
    def read_all(fname):
        with open(fname, 'r') as f:
            return f.readlines()

    @staticmethod
    def save_all(fname, lines, mode='w'):
        with open(fname, mode) as f:
            for l in lines:
                f.write(l + '\n')


class ReaderWriterLock():
    def __init__(self):
        self._read_ready = threading.Condition()
        self._readers = 0

    def reader_acquire(self):
        self._read_ready.acquire()
        try:
            self._readers += 1
        finally:
            self._read_ready.release()

    def reader_release(self):
        self._read_ready.acquire()
        try:
            self._readers -= 1
            if not self._readers:
                self._read_ready.notifyAll()
        finally:
            self._read_ready.release()

    def writer_acquire(self):
        self._read_ready.acquire()
        while self._readers:
            self._read_ready.wait()

    def writer_release(self):
        self._read_ready.release()


class RWLock:
    """Synchronization object used in a solution of so-called second
    readers-writers problem. In this problem, many readers can simultaneously
    access a share, and a writer has an exclusive access to this share.
    Additionally, the following constraints should be met:
    1) no reader should be kept waiting if the share is currently opened for
        reading unless a writer is also waiting for the share,
    2) no writer should be kept waiting for the share longer than absolutely
        necessary.

    The implementation is based on [1, secs. 4.2.2, 4.2.6, 4.2.7]
    with a modification -- adding an additional lock (C{self.__readers_queue})
    -- in accordance with [2].

    Sources:
    [1] A.B. Downey: "The little book of semaphores", Version 2.1.5, 2008
    [2] P.J. Courtois, F. Heymans, D.L. Parnas:
        "Concurrent Control with 'Readers' and 'Writers'",
        Communications of the ACM, 1971 (via [3])
    [3] http://en.wikipedia.org/wiki/Readers-writers_problem
    """

    def __init__(self):
        self.__read_switch = _LightSwitch()
        self.__write_switch = _LightSwitch()
        self.__no_readers = threading.Lock()
        self.__no_writers = threading.Lock()
        self.__readers_queue = threading.Lock()
        """A lock giving an even higher priority to the writer in certain
        cases (see [2] for a discussion)"""

    def reader_acquire(self):
        self.__readers_queue.acquire()
        self.__no_readers.acquire()
        self.__read_switch.acquire(self.__no_writers)
        self.__no_readers.release()
        self.__readers_queue.release()

    def reader_release(self):
        self.__read_switch.release(self.__no_writers)

    def writer_acquire(self):
        self.__write_switch.acquire(self.__no_readers)
        self.__no_writers.acquire()

    def writer_release(self):
        self.__no_writers.release()
        self.__write_switch.release(self.__no_readers)


class _LightSwitch:
    """An auxiliary "light switch"-like object. The first thread turns on the
    "switch", the last one turns it off (see [1, sec. 4.2.2] for details)."""

    def __init__(self):
        self.__counter = 0
        self.__mutex = threading.Lock()

    def acquire(self, lock):
        self.__mutex.acquire()
        self.__counter += 1
        if self.__counter == 1:
            lock.acquire()
        self.__mutex.release()

    def release(self, lock):
        self.__mutex.acquire()
        self.__counter -= 1
        if self.__counter == 0:
            lock.release()
        self.__mutex.release()


class Main:
    def __init__(self):
        self.short_tag = ''
        self.tags = []

    def usage(self):
        print 'PyTest.py usage:'
        print '-h,--help: print help message.'
        print '-v, --version: print script version'
        print '-o, --output: input an output verb'
        print '--foo: Test option '
        print '--fre: another test option'

    def version(self):
        print 'PyTest.py 1.0.0.0.1'

    def output(self, args):
        print 'Hello, %s' % args

    @abc.abstractmethod
    def handle(self, opts):
        raise NotImplementedError('virtual function callled')

    def main(self, argv):
        try:
            opts, args = getopt.getopt(argv[1:], self.short_tag, self.tags)
        except getopt.GetoptError, err:
            print str(err)
            self.usage()
            sys.exit(2)
        self.handle(opts)


class Properties():
    def __init__(self, fn='setting.properties'):
        self._file_name = fn
        self._properties = {}

    def load(self):
        with open(self._file_name, 'r') as f:
            res = f.read()
            self._properties = eval(res.strip())

    def get(self, name, default=None):
        return self._properties.get(name, default)

    def set(self, name, value):
        self._properties[name] = value

    def save(self):
        with open(self._file_name, 'w') as f:
            f.write(json.dumps(self._properties, indent=4))


def date_split(start, end, date_format='%Y-%m-%d'):
    if start == end:
        return [[start, end]]
    st = datetime.datetime.strptime(start, date_format)
    et = datetime.datetime.strptime(end, date_format)
    delta = et - st
    if 2 < delta.days:
        days = delta.days / 2
        mt1 = st + datetime.timedelta(days=days)
        mt2 = st + datetime.timedelta(days=(days + 1))
        mid1 = mt1.strftime(date_format)
        mid2 = mt2.strftime(date_format)
        return [[start, mid1], [mid2, end]]
    elif 2 == delta.days:
        mt1 = st + datetime.timedelta(days=1)
        mid1 = mt1.strftime(date_format)
        return [[start, mid1], [end, end]]
    elif 1 == delta.days:
        return [[start, start], [end, end]]
    return [[start, end]]


class KuaidailiProxyManager():
    @staticmethod
    def load_proxy(count):
        req = BasicRequests()
        con = req.request_url(
            'http://dev.kuaidaili.com/api/getproxy/?orderid=925817981728018&num=%s' % count + \
            '&b_pcchrome=1&b_pcie=1&b_pcff=1&protocol=1&method=2&an_an=1&an_ha=1&sp1=1&quality=1&sort=1&format=json&sep=1')
        return eval(con.text)


def __extract_flws_ah_unicode(text):
    m = re.search(ur'(\(|〔|（)[\dXx]{4}(\)|）|〕).*?(刑|民|行|执|赔|财|商|移|调|协|司|认|保|外|送|请|清|破|知|仲|催|督).*?[\d\s×Xx-]+?号', text)
    if m:
        return m.group()


def __extract_flws_ah_str(text):
    m = re.search(
        r'(\(|(（)|(〔))[\dXx]{4}(\)|(）)|(〕)).*?((刑)|(民)|(行)|(执)|(赔)|(财)|(商)|(移)|(调)|(协)|(司)|(认)|(保)|(外)|(送)|(请)|(清)|(破)|(知)|(仲)|(催)|(督)).*?[\d\s×Xx-]+?号',
        text)
    if m:
        return m.group()


def extract_flws_ah(text):
    """法律文书案号解析器"""
    if isinstance(text, unicode):
        return __extract_flws_ah_unicode(text)
    elif isinstance(text, str):
        return __extract_flws_ah_str(text)


def save_to_word(content, docid, encode='GB2312'):
    f = codecs.open(docid + '.docx', 'wb', encode)
    f.write(content)
    f.close()


def save_to_word_2(content, docid):
    f = open(docid + '.docx', 'wb')
    f.write(content)
    f.close()


class Intervals():
    """
    不重合区间的整数区间组，而且组内区间已经无法再合并
    """

    def __init__(self):
        self.origin = []

    def add(self, interval):
        copy_interval = copy.deepcopy(interval)
        ml = len(self.origin)
        i = 0
        while i < ml and self.origin[i][1] < interval[0]:
            i += 1
        if i >= ml:
            self.origin.append(copy_interval)
            return
        j = ml - 1
        while j >= 0 and self.origin[j][0] > interval[1]:
            j -= 1
        if j < 0:
            self.origin.insert(0, copy_interval)
            return

        if self.origin[i][0] < interval[0]:
            copy_interval[0] = self.origin[i][0]
        if self.origin[j][1] > interval[1]:
            copy_interval[1] = self.origin[j][1]
        k = i
        while k <= j:
            self.origin.pop(i)
            k += 1
        self.origin.insert(i, copy_interval)

    def remove(self, interval):
        ln = len(self.origin)
        i = 0
        while i < ln and self.origin[i][1] < interval[0]:
            i += 1
        if i >= ln:
            return
        if self.origin[i][0] >= interval[0]:
            rmi = i
        else:
            rmi = i + 1
        j = i
        while j < ln and self.origin[j][1] < interval[1]:
            j += 1
        k = rmi
        while k < j:
            self.origin.pop(rmi)
            k += 1
        k = i + 1
        if i == j:
            if interval[0] > self.origin[i][0]:
                if self.origin[i][1] > interval[1]:
                    self.origin.insert(k, [interval[1] + 1, self.origin[i][1]])
                self.origin[i][1] = interval[0] - 1
            elif self.origin[i][0] < interval[1]:
                if self.origin[i][1] == self.origin[i][0] or self.origin[i][1] == interval[1]:
                    self.origin.pop(i)
                else:
                    self.origin[i][0] = interval[1] + 1
        else:
            if k < len(self.origin) and self.origin[k][0] <= interval[1]:
                self.origin[k][0] = interval[1] + 1
            if self.origin[i][0] <= interval[0]:
                if self.origin[i][0] == self.origin[i][1]:
                    self.origin.pop(i)
                else:
                    self.origin[i][0] = interval[0] - 1

    def check(self):
        its = []
        for iv in self.origin:
            if len(its) == 0:
                its.append(iv)
            else:
                if its[-1][1] + 1 == iv[0]:
                    its[-1][1] = iv[1]
                else:
                    its.append(iv)
        self.origin = its


if __name__ == '__main__':
    date_str = u'二〇一六年一月二十七日'
    print date_cs2num(date_str)
    print date_cs2num(u'二〇一六年十月二十日')
    print date_cs2num(u'二〇一六年一月十七日')
    print date_cs2num(u'二〇六年十一月二日')
    print date_cs2num(u'二〇〇年十二月三十一日')
    print re.match(ur'^[一二三四五六七八九十]', date_str).group()
    intervals = [[1, 5], [3, 4], [2, 9], [0, 3], [10, 11], [10, 19], [8, 13]]
    ivl = Intervals()
    for iv in intervals:
        ivl.add(iv)
        print iv, '==>', ivl.origin
    print 'removing:'
    for iv in intervals[4:]:
        ivl.remove(iv)
        print iv, '==>', ivl.origin
