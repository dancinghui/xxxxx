#!/usr/bin/env python
# -*- coding:utf8 -*-
import abc
import re
import time
from datetime import datetime, timedelta

import sys

from court.cspider import JobSpliter, CourtSpider
from court.save import CourtStore
from court.util import Properties, Main
from spider import spider


class CCSpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class CCCourtStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'cc_court')


class CCCourtSpider(CourtSpider):
    """长春市各法院裁判文书爬虫"""

    def get_page_store(self):
        return self.pagestore

    def __init__(self, endFbrq='', startFbrq='', thread_cnt=5):
        CourtSpider.__init__(self, thread_cnt)
        self._name = 'ChangchunCourt'
        self.pagestore = CCCourtStore()
        self.job_spliter = CCSpliter()
        self.startFbrq = startFbrq
        self.endFbrq = endFbrq

    def dispatch(self):
        self.add_main_job({'type': 'main', 'url':
            'http://www.jlsfy.gov.cn:8080/susong51/fymh/751/cpws.htm?' +
            'ajlb=&st=1&wszl=&jbfy=&ay=&ah=&startCprq=&endCprq=&q=' +
            '&startFbrq=%s&endFbrq=%s' % (self.startFbrq, self.endFbrq)})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def need_split(self, context, url):
        return False

    def extract_content(self, context):
        con = re.findall(r'unescape\("(.*)"\)\);', context)
        return con[0].encode("utf-8").decode('unicode_escape')

    def extract_paper_id(self, url):
        m = re.findall(r'id=([\w\d]{32})', url)
        if m is not None:
            return m[0]
        return None

    def extract_paper_url(self, content):
        m = re.findall(r'cpwsDetail\(\'([\w\d]{32})\'\)', content)
        if m is not None:
            urls = []
            for u in m:
                urls.append(('http://www.jlsfy.gov.cn:8080/susong51/cpws/paperView.htm?id=%s&fy=751' % u))
            return urls
        return None

    def add_list_job(self, url, con):
        divs = re.findall(r'<em>(\d+)</em>', con)
        if divs:
            pagecnt = (int(divs[0]) + 19) / 20
            for page in range(2, pagecnt + 1):
                self.add_job(
                    {'type': 'list', 'url': ('http://www.jlsfy.gov.cn:8080/susong51/fymh/751/cpws.htm?page=%d' % page)})
        else:
            print url, 'has no more page'

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass


class CCCourtTest():
    @staticmethod
    def test_extract_paper_id(url):
        job = CCCourtSpider(thread_cnt=1)
        print  job.extract_paper_id(url)


def test():
    t = CCCourtTest()
    t.test_extract_paper_id('http://www.susong51.com/cpws/paperView.htm?id=157f9fcffad9b33c61d35d0b09d5925f&fy=753')


class CMain(Main):
    def __init__(self):
        Main.__init__(self)
        self.short_tag = 'm:t:l:c:e'
        self.tags = ['threads=', 'mode=', 'output=', 'last=', 'config=', 'end=']
        self.thread_count = 3
        self.mode = None
        self.config = False
        self.last_crawl = None
        self.end_crawl = None
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    def usage(self):
        print '%s usage:' % __file__
        print '-h, --help: print help message.'
        print '-v, --version: print script version'
        print '-o, --output: input an output verb'
        print '-t, --threads: thread count '
        print '-e, --end: endFbrq in date like 2016-01-15'
        print '-l, --last: last crawl date, like 2015-10-01'
        print '-m, --mode: mode, if not full-crawl then will be update-crawl mode'
        print '\tfull for full crawl and update for update crawl'
        print '-c, --config: config file,this option will overwrite other like -t -l -m'

    def version(self):
        print '%s 1.0.0.0.1' % __file__

    def handle(self, opts):
        for o, a in opts:
            if o in ('-h', '--help'):
                self.usage()
                sys.exit(1)
            elif o in ('-v', '--version'):
                self.version()
                sys.exit(0)
            elif o in ('-o', '--output'):
                self.output(a)
                sys.exit(0)
            elif o in ('-t', '--threads'):
                self.thread_count = int(a)
            elif o in ('-m', '--mode'):
                self.mode = a
            elif o in ('-l', '--last'):
                self.last_crawl = a
            elif o in ('-e', '--end'):
                self.end_crawl = a
            elif o in ('-c', '--config'):
                self.config = a
        if self.check():
            self.run()
        else:
            print 'not all arguments are right'

    def check(self):
        if self.config is None:
            if self.mode != 'full':
                self.mode = 'update'
                config = Properties()
                config.load()
                self.last_crawl = config.get('last_crawled', '')
                self.end_crawl = self.yesterday
            else:
                self.last_crawl = ''
                self.end_crawl = ''
            if self.thread_count <= 0:
                self.thread_count = 1
        else:
            config = Properties()
            config.load()
            self.mode = config.get('mode', 'update')
            self.last_crawl = config.get('startFbrq', '')
            if self.last_crawl == '':
                self.last_crawl = config.get('last_crawled', '')
            self.end_crawl = config.get('endFbrq', self.yesterday)
            self.thread_count = config.get('threads', 4)
        return True

    def run(self):
        print 'startFbrq:',self.last_crawl
        print 'endFbrq:',self.end_crawl
        print 'mode:',self.mode
        print 'threads:',self.thread_count
        job = CCCourtSpider(startFbrq=self.last_crawl, endFbrq=self.end_crawl, thread_cnt=self.thread_count)
        job.load_proxy('proxy')
        job.run()
        con = Properties()
        con.load()
        con.set('last_crawled', datetime.now().strftime('%Y-%m-%d'))
        con.save()


if __name__ == '__main__':
    main = CMain()
    main.main(sys.argv)
