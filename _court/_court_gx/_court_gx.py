#!/usr/bin/env python
# -*- coding:utf8 -*-
import datetime
import json
import os
import re
import time

import sys

from court.save import CourtStore
from court.util import remove_file
from spider.savebin import FileSaver
from spider.spider import Spider


class CData():
    @staticmethod
    def split_param(url):
        if not re.search(r'\?', url):
            url += '?'
        url = re.sub(r'page=[0-9]+', 'page=1', url)
        urls = []
        if not re.search(r'jbfyId=[0-9]+', url):
            for fy in [1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 29, 30]:
                urls.append(url + ('&jbfyId=%d' % fy))
        elif not re.search(r'ajlb=[0-9]+', url):
            for ajlb in range(1, 6):
                urls.append(url + ('&ajlb=%d' % ajlb))
        elif not re.search(r'sxnflx=[0-9]+', url):
            urls.append(url + '&sxnflx=1')
            urls.append(url + '&sxnflx=2')
        elif not re.search(r'startCprq=([0-9-]+)', url) and not re.search(r'endCprq=([0-9-]+)', url):
            return CData.split_time(url)
        else:
            print 'Cannot spilt url any more:' + url
            return None
        return urls

    @staticmethod
    def split_time(url):
        ft = re.search(r'startCprq=([0-9-]+)', url)
        tt = re.search(r'endCprq=([0-9-]+)', url)
        if ft or tt:
            print 'Cannot split any more:', url
            return None
        url = re.sub(r'startCprq=[0-9-]*', '', url)
        url = re.sub(r'endCprq=[0-9-]*', '', url)
        oldtime = time.strptime('2012-01-01', "%Y-%m-%d")
        time2012 = datetime.datetime(*oldtime[:3])
        oldtime = time.strptime('2015-10-01', "%Y-%m-%d")
        time2015 = datetime.datetime(*oldtime[:3])
        today = datetime.datetime.today()
        timearr = ['']
        arr = CData.gen_date_arr(time2012, time2015, datetime.timedelta(days=30))
        for t in arr:
            timearr.append(t.strftime('%Y-%m-%d'))
        arr = CData.gen_date_arr(time2015, today, datetime.timedelta(days=10))
        for t in arr:
            timearr.append(t.strftime('%Y-%m-%d'))
        timearr.append('')
        l = len(timearr) - 1
        i = 0
        urls = []
        while i < l:
            urls.append(url + ('&startCprq=%s&endCprq=%s' % (timearr[i], timearr[i + 1])))
            i += 1
        return urls

    @staticmethod
    def gen_date_arr(f, t, delta):
        if not isinstance(f, datetime.datetime) or not isinstance(t, datetime.datetime):
            return []
        else:
            tt = f
            arr = []
            while tt < t:
                arr.append(tt)
                tt += delta
            arr.append(t)
        return arr


class GXCourtStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'gx_court')

    def page_time(self):
        js = json.loads(self.get_cur_doc().cur_content)
        time_str = js['AddTime']
        return int(time.mktime(list(time.strptime(time_str[:10], '%Y-%m-%d'))) * 1000)


class GXCourtSpider(Spider):
    "Spider which crawl legal instrument from http://www.bjcourt.gov.cn"

    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        self._name = "GuangxiCourtSpider"
        self.test_mode = False
        self.enable_mainjob_timedlock = False
        self.prlist = []
        self.pagestore = GXCourtStore()
        self._paper_url_format = 'http://ws.gxcourt.gov.cn:23001/WDocManage.asmx/GetDocFileInfo?param={"Param":"{\'DocID\':\'%s\'}"}'
        self.case_types = [
            {'key': '案件种类', 'value': 1, 'info': '案.案件种类', 'count': 67381},
            {'key': '案件种类', 'value': 2, 'info': '案.案件种类', 'count': 178674},
            {'key': '案件种类', 'value': 3, 'info': '案.案件种类', 'count': 6839},
            {'key': '案件种类', 'value': 4, 'info': '案.案件种类', 'count': 46387},
            {'key': '案件涉及', 'value': 12, 'info': '案.J案件特征.J民事案件特征.J案件涉及.案件涉及', 'count': 1618},
            {'key': '案件类型', 'value': 16, 'info': '案.CLS', 'count': 40}
        ]
        self.pagesize = 20
        self.job_file = 'queries'
        self.param_format = "{'Param':{'Dic':[{'@Key':'%s','@Value':'%d','@SearchType':'eq'},{'@Key':'searchType','@Value':'高级检索'}]}}"

    def dispatch(self):
        if not os.path.exists(self.job_file):
            self.update_paper_count()
            self.gen_queries()
        with open(self.job_file, 'r') as f:
            for l in f:
                p = l.split('|', 4)
                if len(p) < 4:
                    sys.stderr.write('invalid line:' + l)
                    continue
                self.add_main_job(
                    {'type': 'main', 'param': self.param_format % (p[0], int(p[1])), 'page': p[2], 'pagesize': p[3]})
        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def update_paper_count(self):
        print 'updating page count'
        param_format = "{'Param':\"{'%s':'%d'}\",'TableName':'CaseInfo'}"
        for ct in self.case_types:
            url = 'http://ws.gxcourt.gov.cn:23001/WDocManage.asmx/GetDataCountByParam?param=' + (
                param_format % (ct['info'], ct['value']))
            con = self.request_url(url)
            if con and con.text:
                res = eval(con.text)
                msg = eval(res['msg'])
                ct['count'] = int(msg['count'])
        for ct in self.case_types:
            print ct['value'], '==>', ct['count']

    def gen_queries(self):
        remove_file(self.job_file)
        fs = FileSaver(self.job_file)
        for ct in self.case_types:
            pcnt = ct['count'] / self.pagesize + 1
            for page in range(1, pcnt + 1):
                fs.append(ct['key'] + '|' + str(ct['value']) + '|' + str(page) + '|' + str(self.pagesize))

    def run_job(self, jobid):
        if not isinstance(jobid, dict):
            return
        jt = jobid['type']
        if 'main' == jt:
            self.do_main_job(jobid)
        else:
            url = self._paper_url_format % jobid['id']
            content = self.post_for_case(url)
            if content:
                self.pagestore.save(int(time.time()), jobid['id'], url, content)
                print jobid['id'], '==>', len(content)
            else:
                print 'Cannot find document', jobid['id']

    def do_main_job(self, jid):
        data = {
            "param": jid['param'],
            "sort": "案.J流程.标准裁判日期",
            "direction": "1",
            "pageNo": jid['page'],
            "pageSize": jid['pagesize'],
            "searchType": "高级检索"
        }
        cs = self.post_for_list('http://ws.gxcourt.gov.cn:22001/Service/SearchDocument.asmx/SearchDocumentJson',
                                data)
        if len(cs) == 0:
            return
        for c in cs:
            self.add_job(
                {'type': 'paper', 'id': c['CaseID']})

    def split_url(self, url):
        return False

    def post_for_list(self, url, data):
        con = self.request_url(url, data=data)
        if con:
            jstr = re.findall(r'>(\{[^<]*)<', con.text)
            js = json.loads(jstr[0])
            return js['rows']

    def post_for_case(self, url):
        print url
        con = self.request_url(url)
        if con:
            js = json.loads(con.text[1:-1])
            if js['stuts'] == 'true':
                return js['msg']
            else:
                return None


if '__main__' == __name__:
    job = GXCourtSpider(1)
    job.load_proxy('proxy')
    job.run()
    # param = '%7B%27Param%27:%7B%27Dic%27:[%7B%27@Key%27:%27案件种类%27,%27@Value%27:%272%27,%27@SearchType%27:%27eq%27%7D,%7B%27@Key%27:%27searchType%27,%27@Value%27:%27高级检索%27%7D]%7D%7D'
    # print unquote(param)
    # sort = "案.J流程.标准裁判日期"
    # data = {
    #     "param": unquote(param),
    #     "sort": sort,
    #     "direction": "1",
    #     "pageNo": 100000,
    #     "pageSize": 20 + 1,
    #     "searchType": "高级检索"
    # }
    #
    # cases = job.post_for_list('http://ws.gxcourt.gov.cn:22001/Service/SearchDocument.asmx/SearchDocumentJson', data)
    # for case in cases:
    #     print '{'
    #     for k, v in case.items():
    #         print k, ':', v
    #     print '}'

    # url2 = 'http://ws.gxcourt.gov.cn:23001/WDocManage.asmx/GetDocFileInfo?' + 'param={"Param":"{\'DocID\':\'9db7a0e8-27e7-471d-8c04-dec200caccd4\'}"}'
    # content = job.post_for_case(url2)
    # print content
