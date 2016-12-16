#!/usr/bin/env python
# -*- coding:utf8 -*-


from service.cv_contact_get.common import config
import pymongo


########################################
#   cv爬虫爬取页面 存储， 在hadoop2机器上  #
########################################

class CVPageStore(object):

    def __init__(self, channel):
        self.channel = channel
        self.mongo_url = config.SPIDER_CV_MONGODB_URLS.get(self.channel)
        self.db_name = config.SPIDER_DB_NAMES.get(self.channel)
        self.coll_name = config.SPIDER_COLL_NAMES.get(self.channel)
        self.pymongo_client = pymongo.MongoClient(self.mongo_url)

    def get_real_url(self, key):
        rs = self.pymongo_client[self.db_name][self.coll_name].find_one(key)
        if not rs:
            return None
        return rs.get('realUrl', '')