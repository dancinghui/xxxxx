#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.spider import Spider
import query
import re
import time
from page_store import COZLPageStore


class COZLSpider(Spider):

    def __init__(self, thread_cnt):
        Spider.__init__(self, thread_cnt)
        self.page_store = COZLPageStore('co_zhilian')

    def dispatch(self):
        for city in query.cities:
            for ind in query.inds:
                self.add_main_job({"url":"%s/%s" % (city[1], ind[1]), 'type':'search'})
        self.add_main_job(None)

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return

        if jobid['type'] == 'search':
            self.run_search_job(jobid)

        elif jobid['type'] == 'page':
            self.run_page_job(jobid)

        else:
            raise Exception("unknown type")

    def run_search_job(self, jobid):
        url = jobid['url']
        con = self.request_url(url)
        if not con:
            print " request url fail :", url
            return

        if isinstance(con.text, unicode):
            con.text = con.text.encode('utf-8')

        if 'pageNo' not in jobid:
            find = re.search(r'为您找到 (\d+)条', con.text)
            if find:
                print "query: %s, has totally %s companies" % (url, find.group(1))
                total_cnt = int(find.group(1))
                total_pages = min([100, (total_cnt-1+35)/35])
                for i in range(1,total_pages+1):
                    self.add_job({'url': url, 'type':'search', 'pageNo': i})

        else:
            real_url = '%s/p%d' % (url, jobid['pageNo'])
            search_con = self.request_url(real_url)
            if isinstance(search_con.text, unicode):
                search_con.text = search_con.text.encode('utf-8')

            items = re.findall(r'(http://company.zhaopin.com/\w+\.htm)', search_con.text)
            for item in items:

                self.add_job({'url': item, 'type': 'page'})

    def run_page_job(self, jobid):
        url = jobid['url']
        con = self.request_url(url)

        find = re.search(r'http://company.zhaopin.com.*?[/_](\w+)\.htm', url)
        if not find:
            print "can not find co_id, url：%s" % url

        co_id = find.group(1)

        self.page_store.save(time.time(), co_id, url, con.text)


if __name__ == '__main__':
    s = COZLSpider(50)
    s.load_proxy('checked_proxy')
    s.run()

