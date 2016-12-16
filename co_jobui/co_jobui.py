#!/usr/bin/env python
# -*- coding:utf8 -*-


from spider.spider import Spider
import query
import re
import time
from page_store import COJobUIPageStore

class MProxySpider(Spider):
    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        self.prlist = []

    def useproxy(self, fn):
        fd = open(fn, 'r')
        assert fd is not None
        for i in fd.readlines():
            self.prlist.append(i.strip())
        fd.close()
        #self.thread_count = len(self.prlist)

    def prequest_url(self, kw, url, **kwargs):
        pr = self.prlist[self.get_tid() % len(self.prlist)]
        self._set_proxy(kwargs, pr)
        con = self.request_url(url, **kwargs)
        if con is not None and con.code != 200:
            return None
        if kw not in con.text:
            return None
        return con


class CoJobUISpider(MProxySpider):
    def __init__(self, thread_cnt):
        MProxySpider.__init__(self, thread_cnt)
        self.page_store = COJobUIPageStore("co_jobui")


    def dispatch(self):
        for city in query.cities:
            for ind in query.inds:
                for co_type in query.co_types:
                    for co_scale in query.co_scale:
                        url = self.genUrl({'area':city, 'industry': ind, 'type':co_type, 'worker':co_scale})

                        self.add_main_job({'url':url, 'type':'search'})

    def genUrl(self, data):
        URL_TEMPLATE = "http://www.jobui.com/cmp?%s"
        assert isinstance(data, dict)

        q = ''
        for k, v in data.items():
            q += '%s=%s&' % (k, v)

        return URL_TEMPLATE % q[:-1]


    def run_job(self, jobid):

        _type = jobid.get('type')
        if _type == 'search':
            self.run_search_job(jobid)
        elif _type == 'page':
            self.run_page_job(jobid)

        elif _type == 'search_more':
            self.run_search_more_job(jobid)
        else:
            raise Exception("unknown url type")

    def run_search_job(self, jobid):

        url = jobid.get('url','')
        if not url:
            print "run_search_job url is null"
            return
        if 'pageNo' not in jobid:
            con = self.request_url(url)

            if isinstance(con.text, unicode):
                con.text = con.text.encode('utf-8')

            find = re.search(r'找到.*(\d+).*?条结果',con.text)
            if not find:
                raise Exception('can not find total number under url: %s' % url)

            total_no = int(find.group(1))
            print "url : %r, find %d items" % (url, total_no)
            if total_no < 1000:
                # 直接翻页
                total_page = (total_no-1+20)/20

                for pageNo in range(1, total_page+1):
                    self.add_job({'url':url, 'pageNo':pageNo, 'type':'search'})

            else:
                self.do_more_split(jobid)

        else:
            con = self.request_url(url)
            if isinstance(con.text, unicode):
                con.text = con.text.encode('utf-8')

            items = re.findall(r'/company/(\d+)/', con.text)
            for item in items:
                item_url = "http://www.jobui.com/company/%s/" % item
                self.add_job({'url': item_url, 'type':'page', 'co_id': item})

    def do_more_split(self, jobid):

        print "split more jobid: %r", jobid

        url = jobid['url']
        find = re.search(r'area=(\w+)[&$]', url)
        area = find.group(1)

        areas = query.areaCodes[area]
        for area in areas:
            areaCode = area[1]
            url += "&areaCode=%s" % areaCode
            self.add_job({'url': url, 'type':'search_more'})

    def run_search_more_job(self, jobid):
        if 'type' not in jobid:
            return

        if jobid['type'] != 'search_more':
            print "jobid :%r, is not search_more job" % jobid
            return

        url = jobid.get('url','')
        if not url:
            print "jobid :%r, has not url" % jobid
            return

        con = self.request_url(url)
        if isinstance(con.text, unicode):
            con.text = con.text.encode('utf-8')

        find = re.search(r'找到.*(\d+).*?条结果',con.text)
        if not find:
            raise Exception('can not find total number under url: ' % url)

        total_no = int(find.group(1))
        total_page = min([50, (total_no-1+20)/20])
        for pageNo in range(1, total_page+1):
            self.add_job({'url':url, 'pageNo':pageNo, 'type':'search'})


    def run_page_job(self, jobid):
        if 'url' not in jobid:
            return

        url = jobid['url']
        con = self.request_url(url)

        if isinstance(con.text, unicode):
            con.text = con.text.encode('utf-8')

        self.extract_more_page(con.text)

        self.page_store.save(time.time(), jobid['co_id'], url, con.text)

    def extract_more_page(self, content):
        items = re.findall(r'/company/(\d+)/', content)
        for item in items:
            if item == '109916':
                continue
            item_url = "http://www.jobui.com/company/%s/" % item
            self.add_job({'url': item_url, 'type':'page', 'co_id': item})


if __name__ == '__main__':

    s = CoJobUISpider(50)
    s.load_proxy('checked_proxy')
    # s.set_proxy(['ipin:helloipin@192.168.1.39:3428'])
    s.run()


