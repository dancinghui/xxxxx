#!/usr/bin/env python
# -*- coding:utf8 -*-
import time
import random

from court.cspider import RestorableSpider


class RSpiderTest(RestorableSpider):
    def dispatch(self):
        for id in range(1, 21):
            self.add_job({'id': id, 'name': 'test'})
        for id in range(21, 41):
            self.add_job({'id': id, 'name': 'main'})
        time.sleep(3)

        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):
        RestorableSpider.run_job(self, jobid)
        print jobid
        if jobid['id'] % 2 == 0:
            time.sleep(2)
        else:
            time.sleep(4)
        if 99 == random.randint(1, 100):
            raise Exception('Test Exception')


if __name__ == "__main__":
    j = RSpiderTest(1)
    j.run()
