#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import logging
import os
import re
import time
from urllib import quote

import sys

from court.cspider import JobSpliter, CourtSpider
from court.save import CourtStore, LinkSaver
from court.util import date_cs2num, Properties, Main, date_split
from spider import spider
from spider.httpreq import BasicRequests


class HZSpliter(JobSpliter):
    def split_param(self, url):
        return [url]


class HZCourtStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'hz_court')

    def parse_time(self):
        if self.get_cur_doc().cur_content is None:
            return None
        if isinstance(self.get_cur_doc().cur_content, str):
            m = re.findall(ur'[一二三四五六七八九0〇○Ｏ零十OО]{4}年[一二三四五六七八九〇十0○ＯOО]{1,2}月[一二三四五六七八九〇零○Ｏ0十OО]{1,3}日',
                           self.get_cur_doc().cur_content.decode('utf-8'))
        else:
            m = re.findall(ur'[一二三四五六七八九0〇○Ｏ零十OО]{4}年[一二三四五六七八九〇十0○ＯOО]{1,2}月[一二三四五六七八九〇零○Ｏ0十OО]{1,3}日',
                           self.get_cur_doc().cur_content)
        if m and len(m) > 0:
            return date_cs2num(m[-1])
        else:
            return None


class HZCourtSpider(CourtSpider):
    """杭州市法院爬虫"""

    def get_page_store(self):
        return self.pagestore

    def __init__(self, threadcnt=10, seed_file=None, mode='links', list_file='links', recover=False, test=False):
        CourtSpider.__init__(self, threadcnt)
        self._name = 'HangzhouCourt'
        self.pagestore = HZCourtStore()
        self.job_spliter = HZSpliter()
        self._test_mode = test
        self.pagestore.testmode = test
        self.list_data = {
            'pageno': '1',
            'pagesize': '20',
            'ajlb': '',
            'cbfy': '1300',
            'ah': '',
            'jarq1': '19700101',
            'jarq2': time.strftime('%Y%m%d', time.localtime()),
            'key': ''
        }
        self.seed_file = seed_file
        self.page_size = 50
        self.mode = mode
        self.list_file = list_file
        self.recover = recover
        self.today = time.strftime('%Y%m%d', time.localtime())
        self.link_saver = LinkSaver(self.list_file)

    def run_job(self, jobid):
        jt = jobid['type']
        if 'paper' == jt:
            id = jobid['id']
            con = self.request_url('http://www.zjsfgkw.cn/document/JudgmentDetail/' + id)
            if con is None or con.text is None:
                logging.error('failed to request paper %s', str(id))
                raise Exception('Failed to request paper %s' % str(id))
            else:
                context = self.extract_content(con.text)
            m = None
            if context is not None:
                m = re.search(r'src="([^"]*)"', context)
            context2 = None
            if m is not None:
                con = self.request_url("http://www.zjsfgkw.cn" + quote(m.group(1).encode('utf-8')))
                if con:
                    context2 = con.text
                else:
                    logging.error('failed to request source paper %s', str(id))
                    raise Exception('Failed to request source paper %s' % str(id))
            else:
                logging.warn('failed to find source url %s', str(id))
            if context2 is not None:
                self.pagestore.save(int(time.time()), id, 'http://www.zjsfgkw.cn/document/JudgmentDetail/' + id,
                                    context2)
                print id, '=>', len(context2)
                logging.info('%s==>%d', str(id), len(context2))
            else:
                logging.info('fail to find content for %s', str(id))
                print 'fail to find content for:', id
            return

        if 'main' == jt:
            data = copy.deepcopy(self.list_data)
            data['cbfy'] = jobid['cbfy']
            data['pageno'] = jobid['page']
            data['pagesize'] = jobid['pagesize']
            con = self.request_url(jobid['url'], data=data)
            if con is None or con.text is None:
                logging.error('fail to request %s', jobid['url'])
                raise Exception('response is None %s' % jobid['url'])
        elif 'list' == jt:
            if jobid['pageno'] == 0:
                self.handle_count_and_split(jobid)
                return
            con = self.search(pagesize=self.page_size, pageno=jobid['pageno'], jarq1=jobid['jarq1'],
                              jarq2=jobid['jarq2'])
            if con is None or con.text is None:
                logging.error('fail to request %s', str(jobid))
                raise Exception('response is None %s' % str(jobid))
        else:
            print 'invalid job', jobid
            return
        docs = self.extract_paper_url(con.text)
        if len(docs) == 0:
            print 'no papers found on %s' % str(jobid)
            logging.warn('no papers found on %s', str(jobid))
            return
        docs = spider.util.unique_list(docs)
        logging.info('add %d links from %s', len(docs), str(jobid))
        for doc in docs:
            self.link_saver.add(doc)
            self.add_job({'type': 'paper', 'id': doc})

    def search(self, **kwargs):
        pageno = kwargs.get('pageno', 1)
        pagesize = kwargs.get('pagesize', 10)
        ajlb = kwargs.get('ajlb', '')
        cbfy = kwargs.get('cbfy', '')
        ah = kwargs.get('ah', '')
        jarq1 = kwargs.get('jarq1', '')
        jarq2 = kwargs.get('jarq2', self.today)
        key = kwargs.get('key', '')
        # url = 'http://www.zjsfgkw.cn/document/JudgmentSearch?ajlb=%s&cbfy=%s&ah=%s&key=%s&jarq1=%s&jarq2=%s&pageno=%s&pagesize=%s' % (
        #     ajlb, cbfy, ah, key, jarq1, jarq2, pageno, pagesize)
        # return self.request_url(url)

        return self.request_url('http://www.zjsfgkw.cn/document/JudgmentSearch', data={
            'pageno': pageno,
            'pagesize': pagesize,
            'ajlb': ajlb,
            'cbfy': cbfy,
            'ah': ah,
            'jarq1': jarq1,
            'jarq2': jarq2,
            'key': key
        })

    def dispatch(self):
        if 'links' == self.mode and self.seed_file:
            with open(self.seed_file, 'r') as f:
                for l in f:
                    j = eval(l)
                    pagecnt = int(j['count']) / self.page_size + 1
                    for page in range(1, pagecnt + 1):
                        self.add_main_job({'type': 'main', 'url': 'http://www.zjsfgkw.cn/document/JudgmentSearch',
                                           'page': page, 'pagesize': self.page_size, 'cbfy': j['id']})
        elif 'papers' == self.mode:
            with open(self.seed_file, 'r') as f:
                ids = []
                for l in f:
                    ids.append(l.strip())
                if self.recover:
                    tmp = ids
                    ids = []
                    for i in tmp:
                        if not self.pagestore.find_any(self.pagestore.channel + '://' + i):
                            ids.append(i)
                for i in ids:
                    self.add_main_job({'type': 'paper', 'id': i})
                logging.info('add %d paper links', len(ids))
        elif 'update' == self.mode:
            config = Properties(self.seed_file)
            config.load()
            self.add_main_job(
                {'type': 'list', 'jarq1': config.get('jarq1'), 'jarq2': config.get('jarq2', self.today), 'pageno': 0,
                 'level': 0})

        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def need_split(self, context, url):
        return False

    def extract_content(self, context):
        m = re.search(r'<div class="books_detail_header">.*</IFRAME>', context, re.S)
        if m:
            return m.group(0)
        return None

    def extract_paper_id(self, url):
        m = re.findall(r'http://www.zjsfgkw.cn/document/JudgmentDetail/(\d+)', url)
        if m is not None:
            return m[0]
        return None

    def extract_paper_url(self, content):
        return re.findall(r'DocumentId":(\d+)', content)

    def add_list_job(self, url, con):
        pass

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "Court Spider:%s\n" % self._name
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass

    def get_court_by_id(self, id):
        data = {
            'courtId': id
        }

        con = self.request_url('http://www.zjsfgkw.cn/Judges/GetCountByCountId', data=data)
        print con.text

    def get_court_paper_count(self, court_id, start_date, end_date):
        con = self.search(pageno=1, pagesize=1, cbfy=court_id, jarq1=start_date, jarq2=end_date)
        if con and con.text:
            res = re.search(r'"total":(\d+)', con.text)
            if res:
                print court_id, res.group(1)
                return int(res.group(1))
            else:
                return -1
        return -1

    def handle_count_and_split(self, jobid):
        cnt = self.get_court_paper_count(jobid.get('court', ''), jobid['jarq1'], jobid['jarq2'])
        pagecnt = (cnt + self.page_size / 2) / self.page_size
        if pagecnt > 100:
            splits = date_split(jobid['jarq1'], jobid['jarq2'], '%Y%m%d')
            if len(splits) == 1:
                print 'cannot split any more:', jobid
                return
            print '[%s,%s],[%s]->%s,%s' % (
                jobid['jarq1'], jobid['jarq2'], jobid['level'], str(splits[0]), str(splits[1]))
            for t in splits:
                job = copy.deepcopy(jobid)
                job['jarq1'] = t[0]
                job['jarq2'] = t[1]
                job['_failcnt_'] = 0
                job['level'] += 1
                self.add_job(job)
            return
        print '[%s,%s][%d]=>%d,%d' % (jobid['jarq1'], jobid['jarq2'], jobid['level'], cnt, pagecnt)
        for page in range(1, pagecnt + 1):
            job = copy.deepcopy(jobid)
            job['pageno'] = page
            self.add_job(job)


def find_and_print_page(driver):
    content = driver.page_source
    m = re.findall(r'<a href="javascript:toPage\(\d+,\'getlist\'\);">&gt;</a>', content)
    print m


def test_extract_inner_paper_url():
    rq = BasicRequests()
    con = rq.request_url('http://www.zjsfgkw.cn/document/JudgmentDetail/4177773')
    content = re.search(r'<div class="books_detail_header">.*</IFRAME>', con.text, re.S)
    m = re.search(r'src="([^"]+)"', content.group())
    if m:
        print m.group(1)
    else:
        print content


def test_parse_time():
    request = BasicRequests()
    con = request.request_url(
        'http://www.zjsfgkw.cn/attachment/documentbook/2016-04-05/0225-0229/html/671a34a7-b068-4025-af13-d9fe4c28ce6a.html')
    m = re.search(ur'[一二三四五六七八九〇零○十]{4}年[一二三四五六七八九〇十○]{1,2}月[一二三四五六七八九〇零○十]{1,3}日', con.text)
    if m:
        print date_cs2num(m.group())


class CMain(Main):
    def __init__(self):
        Main.__init__(self)
        self.short_tag = 'm:t:s'
        self.tags = ['threads=', 'mode=', 'output=', 'test=']
        self.thread_count = 3
        self.mode = None
        self.seed = None
        self.test = False

    def usage(self):
        print '%s usage:' % __file__
        print '-h, --help: print help message.'
        print '-v, --version: print script version'
        print '-o, --output: input an output verb'
        print '-t, --threads: thread count '
        print '-m, --mode: links with fetch all list to parse paper id;papers which crawl papers only and update for update mode'

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
            elif o == '--test':
                self.test = ('1' == a or 'true' == a or 'True' == a)

        if self.check():
            self.run()
        else:
            print 'not all arguments are right'

    def check(self):
        if self.thread_count <= 0:
            self.thread_count = 1
        if self.mode != 'links' and self.mode != 'papers':
            self.mode = 'update'
        if self.seed is None:
            self.seed = 'setting.properties'
        if not os.path.exists(self.seed):
            print 'seed file %s not exists' % self.seed
            return False
        return True

    def run(self):
        print 'seed:', self.seed
        print 'mode:', self.mode
        print 'threads:', self.thread_count
        job = HZCourtSpider(mode=self.mode, seed_file=self.seed, threadcnt=self.thread_count, test=self.test)
        job.load_proxy('proxy')
        job.run()


if __name__ == '__main__':
    main = CMain()
    main.main(sys.argv)
