#!/usr/bin/env python
# -*- coding:utf8 -*-


from spider.spider import Spider
import query
import re
import time
from page_store import COJobUIPageStore


class CoJobUI(Spider):
    def __init__(self, thread_cnt):
        Spider.__init__(self, thread_cnt)
        self.page_store = COJobUIPageStore("co_jobui")

    def dispatch(self):
        for i in range(0, 100000000):
            if i % 1000000 == 0:
                print "process %f%%" % (i/float(100000000))
            self.add_main_job({'co_id':i})

    def run_job(self, jobid):
        if not jobid:
            return

        co_id = str(jobid['co_id'])
        url = "http://www.jobui.com/company/%s/" % co_id
        con = self.request_url(url)

        if con.request.url != url:
            print "%s redirect to page : %s" % (url, con.request.url)
            url = con.request.url
            co_id = re.search(r'(\d+)', url).group(1)

        if isinstance(con.text, unicode):
            con.text = con.text.encode('utf-8')

        self.page_store.save(time.time(), co_id, url, con.text)


if __name__ == '__main__':
    s = CoJobUI(50)
    s.load_proxy("checked_proxy")
    s.run()