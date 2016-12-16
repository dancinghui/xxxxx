#!/usr/bin/env python
# -*- coding:utf8 -*-
import datetime
import re
import time
import pymongo

from _gk_special2 import GkChsiSpecialPaperStore
from spider.savebin import BinReader

if __name__ == '__main__':
    url = "yggk_detail_fj://13469/15/5/1/1/10/070102/1"
    channel = re.search('^(.*):\/\/(.*)', url).group(1)
    print channel
    store = GkChsiSpecialPaperStore(channel)
    res = store.find_new(url)
    print res
    dburl = 'mongodb://root:helloipin@localhost/'
    client = pymongo.MongoClient(dburl)
    c = client.admin['page_store_' + channel]
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
        print datetime.datetime.fromtimestamp(long(p['crawlerUpdateTime']) / 1000)
    print 'count:', count
