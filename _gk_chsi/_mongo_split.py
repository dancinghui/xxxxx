#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import re

import pymongo
import time

from chsispider import GkChsiFsxStore
from spider.savebin import BinReader


class Spliter():
    def __init__(self, source, targets):
        self.mongo = pymongo.MongoClient('mongodb://root:helloipin@localhost/')
        self.source = 'page_store_' + source
        self.targets = {}
        for t in targets:
            s = copy.deepcopy(t)
            s['store'] = GkChsiFsxStore(t['channel'])
            self.targets[s['tag']] = s

    def run(self):
        res = self.read_all()
        for page in res:
            for tag, data in self.targets.items():
                if re.search(tag, page['content'][1]):
                    data['store'].save(int(time.time()), re.sub('^.*:\/\/', '', page['indexUrl']),
                                       page['realUrl'], page['content'][1])
                    print tag
            pass

    def read_all(self):
        res = []
        c = self.mongo.admin[self.source]
        bin_reader = None
        for i in c.find():
            (ft, ofn, pos) = i['pageContentPath'].split('::')
            if bin_reader is None or bin_reader.fd.name != ofn:
                bin_reader = BinReader(ofn)
            i['content'] = bin_reader.readone_at(int(pos))
            res.append(i)
        return res


if __name__ == '__main__':
    spliter = Spliter('yggk_sch_sh',
                      [{'channel': 'yggk_sch_ln_', 'tag': '辽宁 剩余：'}, {'channel': 'yggk_sch_sh_', 'tag': '上海 剩余：'}])
    spliter.run()

    spliter = Spliter('yggk_spec_sh',
                      [{'channel': 'yggk_spec_ln_', 'tag': '辽宁 剩余：'}, {'channel': 'yggk_spec_sh_', 'tag': '上海 剩余：'}])

    spliter.run()

    spliter = Spliter('yggk_detail_sh',
                      [{'channel': 'yggk_detail_ln_', 'tag': '辽宁 剩余：'},
                       {'channel': 'yggk_detail_sh_', 'tag': '上海 剩余：'}])

    spliter.run()
    spliter = Spliter('yggk_sch_ln',
                      [{'channel': 'yggk_sch_ln_', 'tag': '辽宁 剩余：'}, {'channel': 'yggk_sch_sh_', 'tag': '上海 剩余：'}])
    spliter.run()

    spliter = Spliter('yggk_spec_ln',
                      [{'channel': 'yggk_spec_ln_', 'tag': '辽宁 剩余：'}, {'channel': 'yggk_spec_sh_', 'tag': '上海 剩余：'}])

    spliter.run()

    spliter = Spliter('yggk_detail_ln',
                      [{'channel': 'yggk_detail_ln_', 'tag': '辽宁 剩余：'},
                       {'channel': 'yggk_detail_sh_', 'tag': '上海 剩余：'}])

    spliter.run()
