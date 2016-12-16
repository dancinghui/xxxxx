#!/usr/bin/env python
# -*- coding:utf8 -*-
import datetime
import re

import pymongo

from __wlmq_parser import WLMQParser
from court.save import CourtStore
from court.util import save_to_word, save_to_word_2
from spider.savebin import BinReader


class WLMQDeleter(WLMQParser):
    def dojob(self):
        self.init()
        reader = None
        for item in self._docs:
            (ft, ofn, pos) = item['pageContentPath'].split('::')
            if reader is None or reader.fd.name != ofn:
                reader = BinReader(ofn)
            content = reader.readone_at(int(pos))
            if 'HTTP 错误 404.0' in content[1]:
                self.client[self.database][self.collection].delete_one(
                    {'indexUrl': item['indexUrl'], 'contentSign': item['contentSign']})


def delete_doc():
    p = WLMQDeleter()
    p.dojob()


if __name__ == '__main__':
    # delete_doc()
    url ='abstract://2005100739298'
    channel = re.search('^(.*):\/\/(.*)', url).group(1)
    print channel
    store = CourtStore(channel)
    res = store.find_new(url)
    print res
    dburl = 'mongodb://root:helloipin@localhost/'
    client = pymongo.MongoClient(dburl)
    c = client.zhuanli['page_store_' + channel]
    page = c.find({'indexUrl': url})
    count = 0
    for p in page:
        count += 1
        print p['pageContentPath']
        (ft, ofn, pos) = p['pageContentPath'].split('::')
        reader = BinReader(ofn)
        content = reader.readone_at(int(pos))
        print content[0]
        print content[1]
        print p['indexUrl']
        print p['realUrl']
        print datetime.datetime.fromtimestamp(long(p['crawlerUpdateTime']) / 1000)
        # text=eval(content[1].replace('null','None'))
        # doc=text['FileContent']
        # save_to_word_2(doc,url[11:])
    print 'count:', count
