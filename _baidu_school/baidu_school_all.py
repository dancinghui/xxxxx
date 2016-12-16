#!/usr/bin/env python
# -*- coding: utf-8 -*-

from spider.spider import Spider
from spider.httpreq import SpeedControlRequests
import json
import time
from lxml import html
import re
import openpyxl


class BaiduSchoolSpider(Spider):

    def __init__(self, threadcnt):
        super(BaiduSchoolSpider, self).__init__(threadcnt)
        self.speed_control_requests = SpeedControlRequests()
        self.wb = openpyxl.Workbook()
        self.ws = self.wb.active
        self.sheet_list = [u'高校', u'院校分类', u'办学性质', '211', '985', u'研究生院', u'院校隶属', u'办学类型', u'学历层次', u'标签']
        self.ws.append(self.sheet_list)

    def get_ids(self):
        url = 'http://baike.baidu.com/wikitag/api/getlemmas'
        form_data = {'limit': 30,
                     'timeout': 3000,
                     'filterTags': [0, 0, 0, 0, 0, 0, 0],
                     'tagId': 60829,
                     'fromLemma': 'false',
                     'contentLength': 40, 'page': 0}
        total_page = 81
        while form_data['page'] <= total_page:
            res = self.request_url(url, data=form_data)
            form_data['page'] += 1
            json_resp = json.loads(res.text)
            for item in json_resp['lemmaList']:
                lis = item['lemmaUrl'].split('/')
                # 6 means url format is http://baike.baidu.com/subview/d1/d2.htm
                if len(lis) == 6:
                    id_lis = [str(lis[4]), str(lis[5].split('.')[0])]
                    yield {'id': id_lis}
                else:
                    yield {'id': str(lis[4].split('.')[0])}

    def dispatch(self):
        for jobid in self.get_ids():
            self.add_main_job(jobid)
        self.wait_q()
        self.add_main_job(None)

    def get_info(self, content):
        raw_info = {u'高校': u'不确定',
                    u'院校分类': u'不确定',
                    u'办学性质': u'不确定',
                    '211': u'否',
                    '985': u'否',
                    u'研究生院': u'否',
                    u'院校隶属': u'不确定',
                    u'办学类型': u'不确定',
                    u'学历层次': u'不确定',
                    u'标签': u'不确定'}
        doc = html.fromstring(content)
        tag_list = doc.xpath('//*[@id="open-tag-item"]/span/a/text()|//*[@id="open-tag-item"]/span/text()')
        tag_list = [i.strip() for i in tag_list]
        tag = ' ' + ' '.join(tag_list) + ' '
        raw_info[u'标签'] = tag
        if u'211高校' in tag:
            raw_info['211'] = u'是'
        if u'985高校' in tag:
            raw_info['985'] = u'是'
        if u'研究生院高校' in tag:
            raw_info[u'研究生院'] = u'是'

        gaoxiao = doc.xpath('//h1/text()')
        if gaoxiao:
            raw_info[u'高校'] = gaoxiao[0]

        fenlei = re.findall(ur'\s([\u4e00-\u9fa5]*?类)高校\s', tag)
        if fenlei:
            raw_info[u'院校分类'] = fenlei[0]
        xingzhi = re.findall(ur'\s([\u4e00-\u9fa5]*?办)高校\s', tag)
        if xingzhi:
            raw_info[u'办学性质'] = xingzhi[0]

        lishu = re.findall(ur'\s([\u4e00-\u9fa5]*?)隶属高校\s', tag)
        if lishu:
            raw_info[u'院校隶属'] = lishu[0]
        elif u'地方所属高校' in tag:
            raw_info[u'院校隶属'] = u'地方所属'

        if u'本科' in tag:
            raw_info[u'学历层次'] = u'本科'
        else:
            raw_info[u'学历层次'] = u'专科'

        if u' 大学 ' in tag:
            raw_info[u'办学类型'] = u'大学'
        elif u' 学院 ' in tag:
            raw_info[u'办学类型'] = u'学院'
        elif u'高等专科院校' in tag:
            raw_info[u'办学类型'] = u'高等专科院校'
        elif u'高等职业技术院校' in tag:
            raw_info[u'办学类型'] = u'高等职业技术院校'
        elif u'独立学院' in tag:
            raw_info[u'办学类型'] = u'独立学院'
        elif u'成人高等院校' in tag:
            raw_info[u'办学类型'] = u'成人高等院校'
        elif u'短期职业大学' in tag:
            raw_info[u'办学类型'] = u'短期职业大学'
        elif u'管理干部学院' in tag:
            raw_info[u'办学类型'] = u'管理干部学院'
        elif u'教育学院' in tag:
            raw_info[u'办学类型'] = u'教育学院'
        elif u'高等学校分校' in tag:
            raw_info[u'办学类型'] = u'高等学校分校'
        else:
            raw_info[u'办学类型'] = u'其他'

        new_list = [raw_info[i] for i in self.sheet_list]
        self.ws.append(new_list)

    def run_job(self, jobid):
        if isinstance(jobid['id'], list):
            url = 'http://baike.baidu.com/subview/{}/{}.htm'.format(jobid['id'][0], jobid['id'][1])
            res = self.speed_control_requests.with_sleep_requests(url, 0.1)
            jobid_str = '&'.join(jobid['id'])
            if res is not None:
                print "saving %s ..." % jobid_str
                self.get_info(res.text)
                # self.page_store.save(int(time.time), jobid_str, url, res.text)
            else:
                print "%d failed, sleeping 10 secs." % jobid_str
                time.sleep(2)
                self.add_job(jobid)
        elif isinstance(jobid['id'], str):
            url = 'http://baike.baidu.com/view/{}.htm'.format(jobid['id'])
            res = self.speed_control_requests.with_sleep_requests(url, 0.1)
            if res is not None:
                print "saving %s ..." % jobid['id']
                self.get_info(res.text)
                # self.page_store.save(int(time.time), jobid, url, res.text)
            else:
                print "%d failed, sleeping 10 secs." % jobid['id']
                time.sleep(2)
                self.add_job(jobid)

if __name__ == "__main__":
    s = BaiduSchoolSpider(10)
    s.load_proxy('proxy')
    s.run()
    s.wb.save('school_result.xlsx')





