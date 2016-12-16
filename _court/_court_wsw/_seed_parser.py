#!/usr/bin/env python
# -*- coding:utf8 -*-
import time
import traceback

from  datetime import datetime

from court.save import LinkSaver
from spider.runtime import Log
from wswsave import WenshuLinkDb
from wswspider import WenshuSpider


class WenshuSeedDb(WenshuLinkDb):
    def export_seeds(self):
        cursor = self.find()
        seeds = []
        for item in cursor:
            # print item
            seeds.append({'indexUrl': item['indexUrl'], 'content': item['content']})
        return seeds


class SeedParser(WenshuSpider):
    date_format = '%Y%m%d'

    def __init__(self, thcnt=4, page=15):
        WenshuSpider.__init__(self, thcnt)
        self.source = WenshuSeedDb('ws_seed')
        self.link_saver = LinkSaver('seeds.dat', buffer_size=400)
        self.page = page

    def dispatch(self):
        seeds = self.source.export_seeds()

        print 'load %d seeds' % len(seeds)
        for seed in seeds:
            date = seed['indexUrl'].split('://')[1]
            eval_str = seed['content'][1:-1].replace('\\"', '"')
            res = eval(eval_str)
            try:

                if (isinstance(res, tuple) or isinstance(res, list)) and len(res) > 0:
                    self.add_main_job({'type': 'main', 'date': date.encode('utf-8'), 'count': int(res[0]['Count'])})
                else:
                    print 'invalid seed', seed
            except KeyError as e:
                Log.error('KeyError %s' % e.message)
                traceback.print_exc()
                print seed
                print eval_str
        time.sleep(2)
        self.wait_q()
        self.add_job(None)

    def run_job(self, jobid):
        pagecnt = (jobid['count'] + self.page / 2) / self.page
        for index in range(1, pagecnt + 1):
            self.link_saver.add(
                str({'date': jobid['date'], 'count': jobid['count'], 'index': index, 'page': self.page}))

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            self.link_saver.flush()


if __name__ == '__main__':
    gen = SeedParser()
    gen.run()
