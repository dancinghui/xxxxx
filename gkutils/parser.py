#!/usr/bin/env python
# -*- coding:utf8 -*-
import abc

import pymongo

from court.save import LinkSaver
from spider import spider
from spider.savebin import BinReader


class AbstractParser:
    """数据解析器，解析由PageStore保存的数据"""

    def __init__(self, channel, name, db='admin', url='mongodb://root:helloipin@localhost/'):
        self.client = pymongo.MongoClient(url)
        if isinstance(name, str):
            name = name.decode('utf-8')
        self.name = name
        self.collection = 'page_store_' + channel
        self.test_mode = False
        self.print_limit = -1
        self._print_count = 0
        self.channel = channel
        self.database = db

    def read_all(self):
        res = []
        c = self.client[self.database][self.collection]
        bin_reader = None
        for i in c.find():
            (ft, ofn, pos) = i['pageContentPath'].split('::')
            if bin_reader is None or bin_reader.fd.name != ofn:
                bin_reader = BinReader(ofn)
            i['content'] = bin_reader.readone_at(int(pos))
            res.append(i)
        return res

    def on_finish(self):
        pass

    def run(self):
        res = self.init()
        for item in self.iter_results(res):
            self.handle_item(item)
        self.on_finish()

    def init(self):
        pass

    def iter_results(self, res):
        return []

    def handle_item(self, item):
        pass


class CWPParser(AbstractParser):
    """Consuming while Producing Parser"""

    def __init__(self, channel, name, db='admin', url='mongodb://root:helloipin@localhost/'):
        AbstractParser.__init__(self, channel, name, db, url)
        self.bin_reader = None

    @abc.abstractmethod
    def parse_item(self, page):
        raise NotImplementedError('virtual function called')

    def init(self):
        return self.client[self.database][self.collection]

    def iter_results(self, res):
        return res.find()

    def handle_item(self, item):
        (ft, ofn, pos) = item['pageContentPath'].split('::')
        if self.bin_reader is None or self.bin_reader.fd.name != ofn:
            self.bin_reader = BinReader(ofn)
        item['content'] = self.bin_reader.readone_at(int(pos))
        items = self.parse_item(item)
        for ii in items:
            self.process_child_item(ii)

    @abc.abstractmethod
    def process_child_item(self, item):
        pass


class CAPParser(AbstractParser):
    """Consuming After Producing Parser"""

    def __init__(self, channel, name, db='admin', url='mongodb://root:helloipin@localhost/'):
        AbstractParser.__init__(self, channel, name, db, url)
        self.results = []

    def init(self):
        self.pre_save(None)
        self.results = []
        return self.read_all()

    def iter_results(self, res):
        return res

    def handle_item(self, item):
        self.results += self.parse(item)
        if self.test_mode and self._print_count > self.print_limit != -1:
            pass

    @abc.abstractmethod
    def parse(self, page):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def on_save(self, items):
        raise NotImplementedError('virtual function called')

    def on_finish(self):
        self.on_save(self.results)

    @abc.abstractmethod
    def pre_save(self, saver):
        pass


class FileAbstractParser(CAPParser):
    def __init__(self, channel, name, saver_name=None, db='admin', url='mongodb://root:helloipin@localhost/'):
        CAPParser.__init__(self, channel, name, db, url)
        if saver_name is None:
            self._save_name = 'out.csv'
        else:
            self._save_name = saver_name
        self.saver = None

    def init(self):
        self.saver = LinkSaver(self._save_name, 'w')
        self.pre_save(self.saver)
        return CAPParser.init(self)

    def parse(self, page):
        pass

    def pre_save(self, saver):
        pass

    def save(self, saver, page):
        pass

    def on_save(self, items):
        item_list = spider.util.unique_list(items)
        for item in item_list:
            self.save(self.saver, item)
        self.saver.flush()


class Parser(object):
    def __init__(self, channel, name, url='mongodb://root:helloipin@localhost/'):
        self.client = pymongo.MongoClient(url)
        self.name = name
        self.collection = 'page_store_' + channel
        self.test_mode = False
        self.print_limit = -1
        self._print_count = 0

    def read_all(self):
        res = []
        c = self.client.admin[self.collection]
        bin_reader = None
        for i in c.find():
            (ft, ofn, pos) = i['pageContentPath'].split('::')
            if bin_reader is None or bin_reader.fd.name != ofn:
                bin_reader = BinReader(ofn)
            i['content'] = bin_reader.readone_at(int(pos))
            res.append(i)
        return res

    @abc.abstractmethod
    def parse(self, detail):
        raise NotImplementedError('virtual function called')

    def save(self, f, page):
        if not isinstance(f, file):
            raise ValueError('f must be f')
        if not isinstance(page, dict):
            raise ValueError('page must be dict')
        f.write('\'' + page['year'] + '\',')
        f.write('\'' + page['yxdm'] + '\',')
        f.write('\'' + page['school'] + '\',')
        f.write('\'' + page['pici'] + '\',')
        f.write('\'' + page['kelei'] + '\',')
        f.write('\'' + page['zydh'] + '\',')
        f.write('\'' + page['zymc'] + '\',')
        f.write('\'' + page['jhxz'] + '\',')
        f.write('\'' + page['xz'] + '\',')
        f.write('\'' + page['num'] + '\',')
        f.write('\'' + page['xf'] + '\',')
        f.write('\'' + page['yz'] + '\',')
        f.write('\'' + page['beizhu'] + '\',')
        f.write('\'' + page['leipie'] + '\'')
        f.write('\n')

    def save_all(self, f, pages):
        for page in pages:
            self.save(f, page)
        print len(pages), 'saved in', f.name

    def on_finish(self):
        pass

    def run(self):
        pages = self.read_all()
        plan_list = []
        for page in pages:
            plan_list += self.parse(page)
            if self.test_mode and self._print_count > self.print_limit != -1:
                break
        output_file = open(('%s_plan.dat' % self.name), 'w')
        self.save_all(output_file, plan_list)
        output_file.flush()
        output_file.close()
        self.on_finish()
