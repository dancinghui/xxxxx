#!/usr/bin/env python
# encoding: utf-8

import time
import os
import datetime
import hashlib
from spider.savebin import BinReader, BinSaver
import pprint
import traceback
import json
import spider.util
import abc
import cpagestore
import threading
import cutil
from spider.runtime import Log

assert cutil.version() >= 102
MIN_TIME_MSEC = 502889763578

##mongo_db_url = "mongodb://page_store:page_store@db4,hadoop3,hadoop4/page_store"
mongo_db_url = os.getenv('PAGESTORE_DB', "mongodb://localhost/jd_crawler")
saved_count = 0


class PageStoreDB(object):
    def __init__(self, channel, dburl, mode='mongo'):
        global mongo_db_url
        self.channel = channel
        if mode == 'mongo':
            self.dbimpl = cpagestore.PSObj(dburl or mongo_db_url, "page_store_" + channel)
        elif mode == 'fdb':
            self.dbimpl = cpagestore.RBFPSObj(channel+".fdb.bin", dburl or '', "page_store_" + channel)
        else:
            raise RuntimeError("unsupported mode")
        assert self.dbimpl.version() >= 105

    def find_item(self, indexUrl, contentSign):
        return self.dbimpl.has_item(indexUrl, contentSign)

    def find_new(self, indexUrl):
        return self.dbimpl.has_new(indexUrl)

    def find_any(self, indexUrl):
        return self.dbimpl.has_key(indexUrl)

    def get_page_time(self, indexUrl):
        return self.dbimpl.get_page_time(indexUrl, "")

    def update_time(self, indexUrl, contentSign, getime, webtime):
        if getime < MIN_TIME_MSEC:
            raise RuntimeError("update time must be ms.")
        return self.dbimpl.update_time(indexUrl, contentSign, getime, webtime)

    def upsert_doc(self, key, doc):
        js = json.dumps(doc, ensure_ascii=False)
        if isinstance(js, unicode):
            js = js.encode('utf-8')
        return self.dbimpl.upsert_doc(key, js)


class PageStoreBase(PageStoreDB):
    class CurDoc(object):
        def __init__(self, content, getime, jdid, real_url):
            self.cur_content = content
            self.cur_getime = getime
            self.cur_jdid = jdid
            self.cur_url = real_url

    def __init__(self, channel, dburl=None):
        super(PageStoreBase, self).__init__(channel, dburl)
        self.testmode = False
        opath = self.getopath()
        t = time.localtime()
        folder = "%s/%s/%d" % (opath, self.channel, t.tm_year)
        fnbase = "%s_%d%02d" % (self.channel, t.tm_year, t.tm_mon)
        os.system("mkdir -m 777 -p " + folder)
        self._ofn = "%s/%s.bin" % (folder, fnbase)
        self._ofnlog = "%s/%s_update.log" % (folder, fnbase)
        self.fssaver = BinSaver(self._ofn)
        self._hashcheck = spider.util.LocalHashChecker()
        self._docobjtls = threading.local()
        self.saved_count = 0

    def getopath(self):
        dirs = ['/data/crawler/_files3_', '/opt/_test_store_']
        for di in dirs:
            if os.path.isdir(di) and os.access(di, os.W_OK):
                return di
        raise RuntimeError("no dir to write files.")

    def get_cur_doc(self):
        return getattr(self._docobjtls, 'doc', None)

    def set_cur_doc(self,  content, getime, jdid, real_url):
        doc = PageStoreBase.CurDoc(content, getime, jdid, real_url)
        setattr(self._docobjtls, 'doc', doc)

    @staticmethod
    def mktime(year=2015, m=1, d=1, hour=0, minute=0, second=0):
        arr = [year, m, d, hour, minute, second, 0, 0, 0]
        for i in range(0, len(arr)):
            arr[i] = int(arr[i])
        return time.mktime(arr)

    def extract_content(self):
        raise NotImplementedError('virtual function called')

    def page_time(self):
        raise NotImplementedError('virtual function called')

    def check_should_fetch(self, jdid):
        indexUrl = "%s://%s" % (self.channel, jdid)
        return not self.find_new(indexUrl)

    def save_time_log(self, indexUrl, cur_tm):
        oldtime = self.get_page_time(indexUrl)
        if oldtime == cur_tm:
            return
        logstr = "%s %ld => %ld\n" % (indexUrl, oldtime, cur_tm)
        cutil.mp_append_log(self._ofnlog, logstr)

    def save(self, getime, jdid, real_url, content, fnpath=None, offset=None):
        global MIN_TIME_MSEC
        if getime > MIN_TIME_MSEC:
            raise RuntimeError("get time muse be in seconds.")
        if self._hashcheck.query(jdid) > 0:
            return True
        self.set_cur_doc(content, getime, jdid, real_url)

        try:
            pageDesc = self.extract_content()
            if not pageDesc:
                print "jdid: %s, pageDesc empty" % self.get_cur_doc().cur_jdid
                return False
            elif self.testmode:
                print pageDesc
            pageTime = self.page_time()
            if pageTime is None or pageTime < MIN_TIME_MSEC:
                raise RuntimeError("page time must be in msec")
            if isinstance(pageTime, float):
                pageTime = int(pageTime)
            if isinstance(pageDesc, unicode):
                pageDesc = pageDesc.encode('utf-8')
            contentSign = hashlib.md5(pageDesc).hexdigest()
            indexUrl = "%s://%s" % (self.channel, jdid)

            self.save_time_log(indexUrl, pageTime)
            # if there is an entry with this contentSign, update it with no need to save webpage in binfile.
            # otherwise update by indexUrl.
            if self.find_item(indexUrl, contentSign):
                Log.warning("%s exists in db, skip" % jdid)
                self.update_time(indexUrl, contentSign, int(getime) * 1000, pageTime)
                return True
            print "saving", indexUrl
            odoc = {'contentSign': contentSign, 'indexUrl': indexUrl, 'realUrl': real_url,
                    'createTimeFlag': 1, 'owner': self.channel,
                    'createTimeTimeStamp': pageTime,
                    'crawlerUpdateTime': int(getime) * 1000,
                    'updateTime': pageTime,
                    'status':0,
                    'isUpdated':0,
                    'isExpired':0,}
            if self.testmode:
                pprint.pprint(odoc)
                return True
            else:
                if self.do_save(odoc, content, fnpath, offset):
                    print indexUrl, "saved"
                    self.saved_count += 1
                    self._hashcheck.add(jdid)
                    return True
                return False
        except Exception as e:
            print e
            traceback.print_exc()
            Log.error("failed to save %s %s" % (self.channel, jdid))
            time.sleep(5)
            return False

    def do_save(self, odoc, content, fnpath=None, offset=None):
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        filepos = self.fssaver.append("%s.%s.%d" % (self.channel, self.get_cur_doc().cur_jdid, self.get_cur_doc().cur_getime), content)
        odoc.update({'pageContentPath': "binf::%s::%d" % (self._ofn, filepos)})
        return self.upsert_doc(odoc['indexUrl'], odoc)


class Bin2DB(object):
    def skipto(self, r, xn):
        while True:
            (n, v) = r.readone()
            print n
            if n is None or xn in n:
                return

    @abc.abstractmethod
    def parse_name(self, name):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_pagestore(self):
        raise NotImplementedError()

    @abc.abstractmethod
    def get_url(self, jdid):
        raise NotImplementedError()

    def save(self, fn):
        start = datetime.datetime.now()
        r = BinReader(fn)
        # self.skipto(r, 'zhilian_144361202250012_1446732064')
        while True:
            fnpath = r.fn  #todo
            offset = r.fd.tell()
            print "fn: %s, offset: %d" % (fnpath, offset)
            (n, v) = r.readone()
            if n is None:
                break
            print fn, n
            (getime, jdid) = self.parse_name(n)
            if getime is None or jdid is None:
                continue
            getime = int(getime)
            pp = self.get_pagestore()

            if pp.save(getime, jdid, self.get_url(jdid), v, fnpath, offset):
                global saved_count
                saved_count += 1
                timeused = str(datetime.datetime.now() - start)
                if saved_count % 1000 == 1:
                    print "====== saved:%d [%.2f%%][%s] =====" % (saved_count, r.progress() * 100, timeused)


if __name__ == "__main__":
    pass
    #sb = ZLBin2DB()
    #sb.save("../../zhilian/zhilian_1111.bin")
