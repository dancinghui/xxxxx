#!/usr/bin/env python
# -*- coding:utf8 -*-
import abc
import copy

import pymongo

from court.save import LinkSaver
from spider import spider
from spider.savebin import BinReader


class AbstractCourtParser:
    def __init__(self, collection, name, saver_name=None, database='admin', url='mongodb://root:helloipin@localhost/'):
        self.client = pymongo.MongoClient(url)
        if isinstance(name, str):
            name = name.decode('utf-8')
        self.name = name
        self.collection = collection
        self.test_mode = False
        self.print_limit = -1
        self._print_count = 0
        self.database = database
        if saver_name is None:
            self._save_name = 'out.csv'
        else:
            self._save_name = saver_name
        self.channel = collection
        self.__current = 0
        self._docs = None

    def init(self):
        if self._docs is None:
            self._docs = []
            c = self.client[self.database][self.collection]
            for i in c.find():
                self._docs.append(i)

    def parse(self, page):
        doc = {'url': page['realUrl'], 'title': self.parse_title(page['content'][1]).strip(),
               'date': self.parse_date(page['content'][1]).strip(),
               'code': self.parse_code(page['content'][1]).strip(),
               'content': self.parse_content(page['content'][1])}
        if self.test_mode:
            if doc['title'] == '':
                print 'empty title', page['indexUrl']
            if doc['code'] == '':
                print 'empty title', page['indexUrl']
        return doc

    def read_all(self):
        res = []
        if len(self._docs) > 0:
            bin_reader = None
            for i in self._docs:
                doc = copy.deepcopy(i)
                (ft, ofn, pos) = doc['pageContentPath'].split('::')
                if bin_reader is None or bin_reader.fd.name != ofn:
                    bin_reader = BinReader(ofn)
                doc['content'] = bin_reader.readone_at(int(pos))
                res.append(doc)
        return res

    def read_next(self, count=1000):
        res = []
        if len(self._docs) > 0:
            bin_reader = None
            end = self.__current + count
            if end > len(self._docs):
                end = len(self._docs)
            for i in self._docs[self.__current:end]:
                doc = copy.deepcopy(i)
                (ft, ofn, pos) = doc['pageContentPath'].split('::')
                if bin_reader is None or bin_reader.fd.name != ofn:
                    bin_reader = BinReader(ofn)
                doc['content'] = bin_reader.readone_at(int(pos))
                res.append(doc)
            self.__current = end
        return res

    def reset(self, pos=0):
        if pos < len(self._docs):
            self.__current = pos

    def save(self, saver, page):
        saver.write('url:' + page['url'] + '\n')
        saver.write('title:' + page['title'] + '\n')
        saver.write('code:' + page['code'] + '\n')
        saver.write('date:' + page['date'] + '\n')
        saver.write('\n')
        saver.write(page['content'] + '\n')
        saver.write('\n')

    @abc.abstractmethod
    def pre_save(self, saver):
        pass

    def save_all(self, f, pages):
        for page in pages:
            self.save(f, page)
        print len(pages), 'saved in', f.name

    def on_finish(self):
        pass

    def run(self, increase=1000):
        outfile = open(self._save_name, 'w')
        self.init()
        self.pre_save(outfile)
        while True:
            pages = self.read_next(increase)
            if len(pages) <= 0:
                break
            item_list = []
            for page in pages:
                item_list.append(self.parse(page))
                if self.test_mode and self._print_count > self.print_limit != -1:
                    pass
            item_list = spider.util.unique_list(item_list)
            self.save_all(outfile, item_list)
        outfile.flush()
        self.on_finish()

    @abc.abstractmethod
    def parse_title(self, content):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_code(self, content):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_content(self, content):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_date(self, content):
        raise NotImplementedError('virtual function called')
