#!/usr/bin/env python
# -*- coding:utf8 -*-
import HTMLParser
import copy
import logging
import re

import time

from chsispider import GkChsiDetailPaperStore, BaseGkChsiFsxSpider
from court.save import LinkSaver
from spider import spider


class BaseChsiSpider(BaseGkChsiFsxSpider):
    def __init__(self, threadcnt, account, tag, proxy=None, sleep=0.0, captcha_limit=50000000, seeds='detail_seeds',
                 recover=False, sleep_max=5, ua='firefox', year='15', bkccs=None, kldms=None, job_tag=''):
        super(BaseChsiSpider, self).__init__(threadcnt, account, tag, proxy, sleep, captcha_limit, sleep_max,
                                             ua)
        if kldms is None:
            kldms = ['5', '1']
        if bkccs is None:
            bkccs = ['1', '2']
        self.pagestore = GkChsiDetailPaperStore('yggk_detail_' + tag)
        self.full_tag = tag
        self.seeds = seeds
        if proxy:
            self.set_proxy(proxy)
        self.kldms = kldms
        self.bkccs = bkccs
        self.recover = recover
        self.parser = HTMLParser.HTMLParser()
        self.info_saver = LinkSaver(tag + '_detail_data')
        self.failed_saver = LinkSaver('detail.failed.seeds.' + tag + job_tag)
        self.year = year
        self.detail_url_format = 'http://gk.chsi.com.cn/recruit/listWeiciBySpec.do?year=%s&yxdm=%s&zydm=%s&start=%s'
        self.failed_list = []
        self.last_request_time = time.time()


    def dispatch(self):
        # read all seeds
        seeds = []
        with open(self.seeds, 'r') as f:
            for l in f:
                if l[0] == '{':
                    data = eval(l.strip())
                else:
                    param = l.strip().split(',')
                    if len(param) != 8:
                        logging.warn('invalid seeds %s', l)
                        continue
                    data = {'wclx': 1, 'yxdm': param[6], 'kldm': param[2], 'bkcc': param[4], 'start': 0,
                            'years': param[5], 'zydm': param[7], 'zymc': param[8].encode('utf-8')}
                if self.year == data['years'] and not self.pagestore.find_any(
                                        self.pagestore.channel + '://' + self.get_jobid(data)):
                    seeds.append(data)
        print 'load ', len(seeds), 'jobs'
        count = 10
        while len(seeds) > 0 and count > 0:
            count += 1
            logging.info('remain tries %d', count)
            for kldm in self.kldms:
                for bkcc in self.bkccs:
                    seeds = self.request_list(seeds, kldm, bkcc)
                    logging.info('seeds %d,failed %d,kldm=%s,bkcc=%s', len(seeds), len(self.failed_list), kldm, bkcc)
                    seeds += self.failed_list
                    self.failed_list = []
        time.sleep(2)
        self.wait_q()
        self.add_job(None)
        print 'remain seeds', len(seeds)
        for seed in seeds:
            self.failed_saver.add(seed)
        self.failed_saver.flush()
        self.failed_list = seeds

    def handle_job(self, jobid):
        pass


    def request_list(self, seeds, kldm, bkcc):
        self.post_kldm_bkcc_for_session(kldm, bkcc)
        remains = []
        for seed in seeds:
            if seed['kldm'] == kldm and bkcc == seed['bkcc']:
                self.add_main_job(seed)
            else:
                remains.append(seed)
        return remains

    def run_job(self, jobid):
        if not jobid.has_key('content'):
            if jobid not in self.failed_list:
                self.failed_list.append(jobid)
            return
        detail_content = jobid['content']
        jtitle = '%s/%s/%s/%s/%s/%s' % (
            jobid['yxdm'], jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['wclx'],
            jobid['start'])
        self.pagestore.save(int(time.time()), '%s/%s/%s' % (jtitle, jobid['zydm'], int(jobid['start']) / 10),
                            jobid['url'], detail_content.text)

    def add_job(self, jobid, mainjob=False):
        if jobid is None:
            super(BaseChsiSpider, self).add_job(jobid)
            return
        logging.info('fetching special %s,%s', jobid['zymc'], jobid['zydm'])
        detail_url = self.detail_url_format % (jobid['years'], jobid['yxdm'], jobid['zydm'], jobid['start'])
        content = self.fetch_content(jobid, detail_url)
        if content is None:
            # exception is handle
            return
        jobid['content'] = content
        jobid['url'] = detail_url
        super(BaseChsiSpider, self).add_job(jobid, True)
        if 0 == jobid['start']:
            m = re.search(ur'共 (\d+) 页', content.text)
            if not m:
                logging.warn('failed to find page count %s,%s,%s', jobid['kldm'], jobid['bkcc'], detail_url)
                return
            page_cnt = int(m.group(1))
            if page_cnt <= 1:
                return
            for p in range(1, page_cnt):
                job = copy.deepcopy(jobid)
                job['start'] = p * 10
                self.add_main_job(job)

    def get_jobid(self, jobid):
        return '%s/%s/%s/%s/%s/%s/%s/%s' % (
            jobid['yxdm'], jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['wclx'],
            jobid['start'], jobid['zydm'], int(jobid['start']) / 10)

    def fetch_content(self, jobid, detail_url):
        detail_content = self.request_url(detail_url, allow_redirects=20)
        if detail_content is None:
            self.failed_list.append(jobid)
            return
        try:
            if not self._check_result(detail_content.text, jobid, detail_url):
                self.failed_list.append(jobid)
            else:
                return detail_content
        except Exception as e:
            logging.info(e.message)
            self.failed_list.append(jobid)

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += 'seeds: %s\n' % self.seeds
            msg += "saved: %d\n" % self.pagestore.saved_count
            msg += 'captcha times: %s' % self._captcha_times
            msg += 'remain seeds: %d\n' % len(self.failed_list)
            spider.util.sendmail(['shibaofeng@ipin.com'], '%s DONE' % self._name, msg)
        elif evt == 'STARTED':
            # spider.misc.stacktracer.trace_start('res.trace.html')
            pass
