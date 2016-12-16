#!/usr/bin/env python
# -*- coding:utf8 -*-

from cv_chinahr import ChinaHrCVGet
import json


class LatestCVGet(ChinaHrCVGet):
    def __init__(self, thread_cnt):
        ChinaHrCVGet.__init__(self, thread_cnt)

    def dispatch(self):
        with open('res.cv_chinahr.txt') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                line = line.split("||")[0]

                url = json.loads(line)
                url.update({"reFreshTime": 3}) # 最近一个月，
                self.add_main_job({"url": json.loads(line), "type": 'search', 'page': '1'})

        self.add_main_job(None)
        self.wait_q()


if __name__ == '__main__':
    t = LatestCVGet(4)
    t.run()