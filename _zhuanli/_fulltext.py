#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import sys
import time

from court.save import LinkSaver
from court.util import Captcha, FileUtils, save_file, remove_file
from gkutils.parser import CWPParser
from spider import spider
from zlspider import ZhuanliBaseSpider, ZhuanliBaseStore, PatentMain


class PatentFullTextStore(ZhuanliBaseStore):
    def __init__(self, channel='fulltext'):
        ZhuanliBaseStore.__init__(self, channel)

    def extract_content(self):
        return self.get_cur_doc().cur_content

    def page_time(self):
        return int(time.time()) * 1000


class FullTextSeedGen(CWPParser):
    def __init__(self, channel, save='fulltext.seed.txt', db='zhuanli', dburl='mongodb://localhost/zhuanli'):
        CWPParser.__init__(self, channel, channel, db, dburl)
        self.seed_saver = LinkSaver(save)

    def process_child_item(self, item):
        print item
        self.seed_saver.add(item)

    def parse_item(self, page):
        apc = page['indexUrl'].split('://')[1]
        m = re.search(r"d.strWhere.value = \"pnm='([\w\d]+)'\";", page['content'][1])
        if m:
            pnm = m.group(1)
        else:
            print 'cannot find patent number:', page['indexUrl']
            return []
        s = re.search(r'd\.strSources\.value = "(\w+)";', page['content'][1])
        if s:
            pt = s.group(1)
        else:
            print 'cannot find patent type:', page['indexUrl']
            return []
        return ['%s-%s-%s' % (pnm, pt, apc)]

    def on_finish(self):
        print '%d link saved' % self.seed_saver.count


class PatentFullTextSpider(ZhuanliBaseSpider):
    """专利全文爬虫"""

    def __init__(self, thcnt, recover=False, seeds='seed.dat'):
        ZhuanliBaseSpider.__init__(self, thcnt, recover)
        self.seeds = seeds
        self.pagestore = PatentFullTextStore()
        self.failed_saver = LinkSaver('failed.fulltext.txt')

    def dispatch(self):
        seeds = []
        with open(self.seeds, 'r') as f:
            for s in f:
                v = s.rstrip().split('-')
                if len(v) < 3:
                    print 'invalid seed:', s
                if not self.recover or not self.pagestore.find_any(self.pagestore.channel + '://%s-%s' % (v[0], v[2])):
                    seeds.append({'type': v[1], 'pnm': v[0], 'apply': v[2]})
        # seeds = spider.util.unique_list(seeds)
        print 'load %s seeds' % len(seeds)
        for seed in seeds:
            self.add_main_job(seed)
        time.sleep(2)
        self.wait_q()
        self.add_job(None)

    @staticmethod
    def extract_seed_id(pnm, apply_code):
        return '%s-%s' % (pnm, apply_code)

    def run_job(self, jobid):
        url = self.form_download_url(jobid['pnm'], jobid['type'])
        con = self.request_url(url, timeout=self.timeout)
        if self.check_exception(con, jobid):
            return
        if u'<input type="text" name="vct" />' in con.text:
            # 输入验证码下载
            m = re.search(r'\?path=([^&\s]*)', con.headers)
            if m:
                path = m.group(1)
            else:
                l_p = re.search('Location:http://egaz.sipo.gov.cn/FileWeb/.*', con.headers)
                if l_p:
                    location = l_p.group()
                else:
                    l_p = re.search('Location:.*', con.headers)
                    location = 'None' if not l_p else l_p.group()
                print 'wrong redirect page:', url, 'location:', location
                if not self.re_add_job(jobid):
                    self.failed_saver.add('1,%s-%s-%s' % (jobid['pnm'], jobid['type'], jobid['apply']))
                return
            img = self.request_url('http://egaz.sipo.gov.cn/FileWeb/vci.jpg')
            fn = jobid['pnm'] + '.jpg'
            save_file(img.content, fn)
            vci = Captcha.resolve(fn, jobid['pnm'])
            con = self.request_url('http://egaz.sipo.gov.cn/FileWeb/pfs?path=%s&vct=%s' % (path, vci))
            remove_file(fn)
            if self.check_exception(con, jobid):
                return
            if u'您要下载的文件不存在' in con.text:
                self.failed_saver.add('2,%s-%s-%s' % (jobid['pnm'], jobid['type'], jobid['apply']))
                return
            if u'<input type="text" name="vct" />' in con.text:
                if not self.re_add_job(jobid):
                    self.failed_saver.add('3,%s-%s-%s' % (jobid['pnm'], jobid['type'], jobid['apply']))
                return
        self.pagestore.save(int(time.time()), self.extract_seed_id(jobid['pnm'], jobid['apply']), url, con.text)


class MainProgram(PatentMain):
    def __init__(self):
        PatentMain.__init__(self)

    def gen_seed(self):
        p = FullTextSeedGen('abstract', self.seeds)
        p.run()

    def crawl(self):
        job = PatentFullTextSpider(self.thread_count, self.recover, self.seeds)
        job.run()

    def check(self):
        if self.thread_count <= 0:
            self.thread_count = 1
        return True

    def run(self):
        if self.mode == 'seeds':
            self.gen_seed()
        elif self.mode == 'crawl':
            self.crawl()
        else:
            self.gen_seed()
            self.crawl()

    def on_other_opt(self, opt, arg):
        pass


if '__main__' == __name__:
    main = MainProgram()
    main.main(sys.argv)
