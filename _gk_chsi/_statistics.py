#!/usr/bin/env python
# -*- coding:utf8 -*-
import os

import pymongo

from accounts import provinces, AccountManager, check_time


class MongoStatistis():
    def __init__(self, db='admin', url='mongodb://root:helloipin@localhost/'):
        self.client = pymongo.MongoClient(url)
        self.database = self.client.get_database(db)

    def get_distinct_item_count(self, collection):
        if not self.database:
            return 0
        if self.database[collection]:
            return len(self.database[collection].distinct('indexUrl'))
        else:
            return 0

    def get_size(self, channel):
        return self.get_distinct_item_count('page_store_' + channel)

    def get_sch_size(self, name):
        return self.get_size('yggk_sch_%s' % name)

    def get_spec_size(self, name):
        return self.get_size('yggk_spec_%s' % name)

    def get_detail_size(self, name):
        return self.get_size('yggk_detail_%s' % name)

    def get_remain_time(self, name, am):
        t = 0
        for ac in am.get_all(name):
            t += check_time(ac.username, ac.password)
        return t

    def run_status(self, out='status.csv'):
        rs = []

        am = AccountManager()
        for name, short in provinces.items():
            r = [name, str(self.get_sch_size(short)), str(self.get_spec_size(short)), str(self.get_detail_size(short)),
                 '0', '0',
                 str(self.get_remain_time(name, am))]
            rs.append('-'.join(r))
        with open(out, 'w') as f:
            for r in rs:
                f.write(r + '\n')


if __name__ == '__main__':
    statistis = MongoStatistis()
    statistis.run_status()
