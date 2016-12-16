#!/usr/bin/env python
# -*- coding:utf8 -*-
import hashlib
import re
import threading

import time
import traceback

import datetime
import pymongo

from court.util import url_standardize
from spider import spider
from spider.ipin.savedb import PageStoreBase, MIN_TIME_MSEC, PageStoreDB
from spider.runtime import Log
from spider.savebin import FileSaver


class CourtStore(PageStoreBase):
    def __init__(self, channel, dburl="mongodb://root:helloipin@localhost/admin"):
        PageStoreBase.__init__(self, channel, dburl)

    def extract_content(self):
        title = self.parse_title()
        if not title:
            return None
        if isinstance(title, unicode):
            title = title.encode('utf-8')
        return title

    def page_time(self):
        time_str = self.parse_time()
        if time_str is not None:
            try:
                if re.match(r'\d+-\d+-\d+', time_str):
                    t = int(time.mktime(list(time.strptime(time_str, '%Y-%m-%d'))) * 1000)
                else:
                    t = int(time.mktime(list(time.strptime(time_str, '%b %d, %Y'))) * 1000)
            except Exception as e:
                print 'invalid time string', time_str
                Log.warning(e)
                traceback.print_exc()
                t = int(time.time() * 1000)
        else:
            t = int(time.time() * 1000)
        if t < MIN_TIME_MSEC:
            t = int(time.time() * 1000)
        return t

    def parse_title(self):
        return self.get_cur_doc().cur_content

    def parse_time(self):
        return None


class LinkSaver(FileSaver):
    def __init__(self, fn, mode='w', buffer_size=100):
        FileSaver.__init__(self, fn)
        self.fd = open(fn, mode)
        self.lock = threading.Lock()
        self.link_buffer = []
        self.buffer_size = buffer_size
        self.count = 0

    def add(self, link):
        with self.lock:
            self.count += 1
            self.link_buffer.append(link)
            if len(self.link_buffer) > self.buffer_size:
                for l in self.link_buffer:
                    self.fd.write(l + '\n')
                self.fd.flush()
                self.link_buffer = []

    def __del__(self):
        for l in self.link_buffer:
            self.fd.write(l + '\n')
        self.fd.close()

    def flush(self):
        with self.lock:
            for l in self.link_buffer:
                self.fd.write(l + '\n')
            self.link_buffer = []
            self.fd.flush()

    def close(self):
        self.fd.close()

    def readlines(self):
        if 'r' in self.fd.mode or '+' in self.fd.mode:
            pos = self.fd.tell()
            lines = self.fd.readlines()
            self.fd.seek(pos)
            return lines
        else:
            return []


class LinkStore(PageStoreDB):
    def __init__(self, channel, dbUrl="mongodb://localhost/link"):
        super(LinkStore, self).__init__(channel, dbUrl)
        self._hashchecker = spider.util.LocalHashChecker()
        self.save_count = 0

    def save(self, url, id, content, getime):
        if self._hashchecker.query(id) > 0:
            return True
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        url = url_standardize(url)
        sign = hashlib.md5(content).hexdigest()
        try:
            if self.find_item(id, sign):
                Log.warning("%s exists in db, skip" % id)
                self.update_time(id, sign, int(getime) * 1000, int(time.time()) * 1000)
                return True
            print 'saving', id
            ctime = int(time.time()) * 1000
            indexUrl = '%s://%s' % (self.channel, id)
            doc = {'contentSign': sign, 'indexUrl': indexUrl, 'realUrl': url,
                   'createTimeFlag': 1, 'owner': self.channel,
                   'createTimeTimeStamp': ctime,
                   'crawlerUpdateTime': int(getime) * 1000,
                   'updateTime': ctime,
                   'status': 0,
                   'isUpdated': 0,
                   'isExpired': 0,}

            if self.upsert_doc(id, doc):
                print id, 'saved'
                self.save_count += 1
                self._hashchecker.add(id)
        except Exception as e:
            print e
            traceback.print_exc()
            Log.error("failed to save %s %s" % (self.channel, id))
            time.sleep(5)
            return False


class LinkDb():
    def __init__(self, channel, db='link', dbUrl="mongodb://localhost/"):
        self.__client = pymongo.MongoClient(dbUrl)
        self.channel = channel
        self._hashchecker = spider.util.LocalHashChecker()
        self.__lock = threading.RLock()
        self.saved_count = 0

        if self.__client:
            self.__database = self.__client[db]
        else:
            raise Exception('Cannot connect to %s' % dbUrl)
        if self.__database:
            self.__collection = self.__database['link_' + self.channel]
        else:
            raise Exception('No such database %s' % db)
        if self.__client is None:
            raise Exception('No such channel %s in database %s' % (self.channel, db))

    def save(self, url, id, content, getime):
        if self._hashchecker.query(id) > 0:
            return True
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        url = url_standardize(url)
        sign = hashlib.md5(content).hexdigest()
        try:
            if self.has_any_with_sign(id, sign):
                Log.warning("%s exists in db, skip" % id)
                return True
            print 'saving', id
            ctime = int(time.time()) * 1000
            indexUrl = '%s://%s' % (self.channel, id)
            doc = {'sign': sign, 'indexUrl': indexUrl, 'realUrl': url,
                   'createTimeFlag': 1, 'owner': self.channel,
                   'createTimeTimeStamp': ctime,
                   'crawlerUpdateTime': int(getime) * 1000,
                   'updateTime': ctime,
                   'content': content,
                   'status': 0,
                   'isUpdated': 0,
                   'isExpired': 0,}

            if self.__collection.insert_one(doc):
                print id, 'saved'
                with self.__lock:
                    self.saved_count += 1
                self._hashchecker.add(id)
        except Exception as e:
            print e
            traceback.print_exc()
            Log.error("failed to save %s %s" % (self.channel, id))
            time.sleep(5)
            return False

    def has_any(self, id):
        cursor = self.__collection.find_one({'indexUrl': id})
        if cursor:
            return True
        return False

    def has_any_with_sign(self, id, sign):
        cursor = self.__collection.find_one({'indexUrl': id, 'sign': sign})
        if cursor:
            return True
        return False

    def find(self, *args, **kwargs):
        return self.__collection.find(*args, **kwargs)

    def export_seeds(self, handler=None):
        cursor = self.find()
        seeds = []
        if handler is None:
            for item in cursor:
                # print item
                seeds.append({'id': item['indexUrl'], 'content': item['content']})
        else:
            for item in cursor:
                seeds.append(handler(item))
        return seeds


class SpiderLinkStore(LinkStore):
    def __init__(self, channel, dbUrl="mongodb://localhost/link"):
        super(SpiderLinkStore, self).__init__(channel, dbUrl)

    def save_failed(self, url, subid, content):
        return self.save(url, 'failed/' + subid, content, int(time.time()))

    def save_seeds(self, url, subid, content):
        return self.save(url, 'seeds/' + subid, content, int(time.time()))

    def save_link(self, url, subid, content):
        return self.save(url, 'link/' + subid, content, int(time.time()))

    def save_list(self, url, subid, content):
        return self.save(url, 'list/' + subid, content, int(time.time()))


class FailedJobSaver():
    """失败作业保存类，用于恢复失败的作业"""

    def __init__(self, name):
        self.job_saver = open(name, 'a+')
        self.log_saver = open(name + '.log', 'a+')

    def save(self, line):
        self.job_saver.write(line + '\n')
        self.log_saver.write('%d\n' % self.job_saver.tell())

    def tag(self):
        self.log_saver.write(datetime.datetime.now().strftime('%Y-%m-%d %H:%M%:%S\n'))
