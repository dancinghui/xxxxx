#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import re
import time

from court.sessionrequests import ATOSSessionRequests
from spider import spider
from spider.httpreq import BasicRequests
from wswsave import WenshuCourtStore, WenshuLinkDb
from wswspider import WenshuSpider

'''
查询格式:
http://host[:port]/List/List?sorttype=1&conditions=condition1&conditions=condition3&conditions=condition2
conditions格式:
conditions=caseType + caseValue + sign + pid + condition
例如:
http://wenshu.court.gov.cn/list/list/?sorttype=1&conditions=searchWord+001+AY++%E6%A1%88%E7%94%B1:%E5%88%91%E4%BA%8B%E6%A1%88%E7%94%B1
&conditions=searchWord+all+FYCJ++%E6%B3%95%E9%99%A2%E5%B1%82%E7%BA%A7:%E5%85%A8%E9%83%A8
&conditions=searchWord+1+AJLX++%E6%A1%88%E4%BB%B6%E7%B1%BB%E5%9E%8B:%E5%88%91%E4%BA%8B%E6%A1%88%E4%BB%B6
&conditions=searchWord+1_%E4%B8%80%E5%AE%A1+SPCX++%E5%AE%A1%E5%88%A4%E7%A8%8B%E5%BA%8F:%E4%B8%80%E5%AE%A1&conditions=searchWord+1+WSLX++%E6%96%87%E4%B9%A6%E7%B1%BB%E5%9E%8B:%E5%88%A4%E5%86%B3%E4%B9%A6

http://wenshu.court.gov.cn/list/list/?sorttype=1&conditions=searchWord+002002001003+AY++%E6%A1%88%E7%94%B1:%E7%A6%BB%E5%A9%9A%E5%90%8E%E8%B4%A2%E4%BA%A7%E7%BA%A0%E7%BA%B7
&conditions=searchWord+all+FYCJ++%E6%B3%95%E9%99%A2%E5%B1%82%E7%BA%A7:%E5%85%A8%E9%83%A8
&conditions=searchWord+1+AJLX++%E6%A1%88%E4%BB%B6%E7%B1%BB%E5%9E%8B:%E5%88%91%E4%BA%8B%E6%A1%88%E4%BB%B6
&conditions=searchWord+1+WSLX++%E6%96%87%E4%B9%A6%E7%B1%BB%E5%9E%8B:%E5%88%A4%E5%86%B3%E4%B9%A6

condition参数种类见
http://wenshu.court.gov.cn/Assets/js/Lawyee.CPWSW.ListLoad.js

获取列表内容接口:
url:http://wenshu.court.gov.cn/List/ListContent
方法:post
参数列表:
    {
        'Param': param,
        'Index': index,
        'Page': page,
        'Order': order,
        'Direction': direction
    }
返回格式:
json字符串(需要替换字符)：'[{\"Count\":1212,{},{}}]

'''


class WenshuCourtSpider(WenshuSpider):
    """
    文书网裁判文书爬虫
    为方便抓取按法院抓取文书
    种子格式:{'court':'北京市朝阳区人民法院','key':'法院代号','start':'起始日期','end':'终止日期','count':'文书数量'},
    任务格式：{'court':'北京市朝阳区人民法院','key':'法院代号','start':'起始日期','end':'终止日期','size':'每页文书数量','index':'第几页'},
    查询列表按审判日期排序,
    日期格式为:2015-01-15
    结果用PageStoreBase类保存
    """

    def __init__(self, thread_count, seeds=None, recover=False, name='WenshuCourtSpider'):
        WenshuSpider.__init__(self, thread_count, recover=recover, name=name, log='spider.log')
        self.seeds = seeds
        self.pagestore = WenshuCourtStore()
        self.linkdb = WenshuLinkDb()
        self.pagesize = 20

    def dispatch(self):
        seeds = []
        with open(self.seeds, 'r') as f:
            for l in f:
                seeds.append(eval(l.strip()))
        for seed in seeds:
            count = int(seed['count'])
            page_count = (count + self.pagesize / 2) / self.pagesize
            seed_id_title = '%s/%s/%s' % (seed['key'], seed['start'], seed['end'])
            for page in range(1, page_count + 1):
                seed_id = '%s/%s' % (seed_id_title, page)
                if not self.recover or not self.linkdb.has_any(self.linkdb.channel + '://' + seed_id):
                    job = copy.deepcopy(seed)
                    job['type'] = 'main'
                    job['index'] = page
                    job['page'] = self.pagesize
                    if not self.add_main_job(job):
                        self.add_job(job)

        time.sleep(3)
        self.wait_q()
        self.add_job(None, True)

    def request_page(self, param, jobid, refer):
        try:
            return self.request_results(param, page=jobid['page'], index=jobid['index'])
        except RuntimeError as e:
            if 'no proxy' in e.message:
                self.re_add_job(jobid)
                self.reload_proxy()
                return
            else:
                raise

    def run_job(self, jobid):
        param = self.seed2param(jobid)
        url = 'http://wenshu.court.gov.cn/list/list/?sorttype=0&conditions=searchWord+%s+SLFY++法院名称:%s&conditions=searchWord++CPRQ++裁判日期:%s TO %s' % (
            jobid['court'], jobid['court'], jobid['start'], jobid['end'],)

        con = self.request_page(param, jobid, url)
        if self.check_exception(con, jobid):
            return
        if self.check_js(con) and self.handle_js(con):
            curlckjar = getattr(self._curltls, 'cookies', None)
            print curlckjar
            con = self.request_page(param, jobid, url)
            if self.check_exception(con, jobid):
                return
        if '"remind"' == con.text:
            self.re_add_job(jobid)
            return
        try:
            data = eval(eval(con.text))
        except (NameError, SyntaxError):
            print con.text
            self.re_add_job(jobid)
            return
        if len(data) == 0:
            # print 'zero len data:', jobid['court']
            # print con.headers
            curlckjar = getattr(self._curltls, 'cookies', None)
            print '(%s,%s,%s)' % (jobid['court'], jobid['page'], jobid['index']), '==>', curlckjar
            print 'url(%s,%s):' % (jobid['page'], jobid['index']), url
            self.re_add_job(jobid)
            # self.proxy_error()
            return
        print 'add %d doc from %s' % (len(data) - 1, str(jobid))
        ids = ''
        for doc in data[1:]:
            ids += doc['文书ID'] + ','
            self.pagestore.save(int(time.time()), doc['文书ID'],
                                'http://wenshu.court.gov.cn/content/content?DocID=' + doc['文书ID'], str(doc))
        self.linkdb.save(url, self.to_list_seed_id(jobid), ids, int(time.time()))


def read_seeds(seed_file):
    seeds = []
    with open(seed_file, 'r') as f:
        for l in f:
            seeds.append(l.strip())
    return seeds


def test_fetch_paper(url, timeout=30):
    rq = WenshuCourtSpider(1)
    con = rq.request_url(url, timeout=timeout)
    print con.text


def test_get_count(url):
    rq = WenshuCourtSpider(1)
    param = WenshuCourtSpider.get_param(url)
    count = rq.get_count(param)
    print count, type(count)


def test_session_fetch(url):
    rq = WenshuCourtSpider(1)
    rq.test_mode = True
    con = rq.do_search(url)
    print con.text
    res = eval(con.text[1:-1].replace('\\"', '"'))
    for item in res:
        for k, v in item.items():
            print k, ':', v


def test_session_fetch_if_js(url):
    rq = ATOSSessionRequests()
    rq.test_mode = True
    con = rq.request_url(url)
    print con.text
    if '<html>' in con.text:
        print con.text
    else:
        res = eval(con.text[1:-1].replace('\\"', '"'))
        for item in res:
            for k, v in item.items():
                print k, ':', v


def runjs(url):
    rq = BasicRequests()
    con = rq.request_url(url, data={})
    if con:
        print con.text
        m = re.findall(r'<script[^>]*>(.+?)</script>', con.text, re.S)
        if m:
            for js in m:
                if js == '':
                    continue
                print js
                sc = "document = {set cookie(a){console.log(a);}}, window = {innerWidth: 1024, innerHeight: 768, screenX: 200, screenY: 100, screen: {width: 1024, height: 768}}\n"
                sc += js
                rv = spider.util.runjs(sc)
                print 'my results:'
                print rv


def _fetch_page():
    job = WenshuCourtSpider(1)
    job.select_user_agent(
        '=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36')
    job.load_proxy('proxy', 0)
    seed = {'count': '30444', 'start': '1900-01-01', 'end': '2016-05-29',
            'court': '\xe5\x8c\x97\xe4\xba\xac\xe5\xb8\x82\xe7\xac\xac\xe4\xb8\x89\xe4\xb8\xad\xe7\xba\xa7\xe4\xba\xba\xe6\xb0\x91\xe6\xb3\x95\xe9\x99\xa2',
            'key': '001001004000'}

    param = job.seed2param(seed)
    con = job.request_results(param, 25, 5)
    if con is None:
        print 'None type return'
    else:
        print con.text
        print con.headers


def _main():
    job = WenshuCourtSpider(1, 'seed.dat', recover=True)
    # job.set_proxy('192.168.1.39:3428:ipin:helloipin', 0)
    # job.load_proxy('proxy', 0)
    job.reload_proxy()
    job.select_user_agent(
        '=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.75 Safari/537.36')
    job.run()


if '__main__' == __name__:
    seeds = [
        'http://wenshu.court.gov.cn/list/list',
        'http://wenshu.court.gov.cn/list/list/?sorttype=1',
        'http://wenshu.court.gov.cn/list/list/?sorttype=0&conditions=searchWord+%E5%8C%97%E4%BA%AC%E5%B8%82%E6%9C%9D%E9%98%B3%E5%8C%BA%E4%BA%BA%E6%B0%91%E6%B3%95%E9%99%A2+SLFY++%E6%B3%95%E9%99%A2%E5%90%8D%E7%A7%B0:%E5%8C%97%E4%BA%AC%E5%B8%82%E6%9C%9D%E9%98%B3%E5%8C%BA%E4%BA%BA%E6%B0%91%E6%B3%95%E9%99%A2&conditions=searchWord++CPRQ++%E8%A3%81%E5%88%A4%E6%97%A5%E6%9C%9F:1949-05-01%20TO%202016-05-30',
        'http://wenshu.court.gov.cn/List/List?sorttype=1&conditions=searchWord+%E6%B5%B7%E5%8D%97%E7%9C%81%E4%B8%89%E6%B2%99%E5%B8%82%E4%B8%AD%E7%BA%A7%E4%BA%BA%E6%B0%91%E6%B3%95%E9%99%A2+++%E4%B8%AD%E7%BA%A7%E6%B3%95%E9%99%A2:%E6%B5%B7%E5%8D%97%E7%9C%81%E4%B8%89%E6%B2%99%E5%B8%82%E4%B8%AD%E7%BA%A7%E4%BA%BA%E6%B0%91%E6%B3%95%E9%99%A2',
        'http://wenshu.court.gov.cn/list/list/?sorttype=1&conditions=searchWord++CPRQ++%E8%A3%81%E5%88%A4%E6%97%A5%E6%9C%9F:2016-05-01%20TO%202016-05-02',
        'http://wenshu.court.gov.cn/List/List?sorttype=1&conditions=searchWord+%E6%B2%B3%E5%8D%97%E7%9C%81%E9%83%91%E5%B7%9E%E5%B8%82%E4%B8%AD%E7%BA%A7%E4%BA%BA%E6%B0%91%E6%B3%95%E9%99%A2+++%E4%B8%AD%E7%BA%A7%E6%B3%95%E9%99%A2:%E6%B2%B3%E5%8D%97%E7%9C%81%E9%83%91%E5%B7%9E%E5%B8%82%E4%B8%AD%E7%BA%A7%E4%BA%BA%E6%B0%91%E6%B3%95%E9%99%A2',
        'http://wenshu.court.gov.cn/list/list?sorttype=1&conditions=searchWord+001+AY++%E6%A1%88%E7%94%B1:%E5%88%91%E4%BA%8B%E6%A1%88%E7%94%B1&conditions=searchWord+all+FYCJ++%E6%B3%95%E9%99%A2%E5%B1%82%E7%BA%A7:%E5%85%A8%E9%83%A8&conditions=searchWord+1+AJLX++%E6%A1%88%E4%BB%B6%E7%B1%BB%E5%9E%8B:%E5%88%91%E4%BA%8B%E6%A1%88%E4%BB%B6&conditions=searchWord+1_%E4%B8%80%E5%AE%A1+SPCX++%E5%AE%A1%E5%88%A4%E7%A8%8B%E5%BA%8F:%E4%B8%80%E5%AE%A1&conditions=searchWord+1+WSLX++%E6%96%87%E4%B9%A6%E7%B1%BB%E5%9E%8B:%E5%88%A4%E5%86%B3%E4%B9%A6',
        'http://wenshu.court.gov.cn/List/List?sorttype=1&conditions=searchWord+001+AY++%E6%A1%88%E7%94%B1:%E5%88%91%E4%BA%8B%E6%A1%88%E7%94%B1&conditions=searchWord+all+FYCJ++%E6%B3%95%E9%99%A2%E5%B1%82%E7%BA%A7:%E5%85%A8%E9%83%A8&conditions=searchWord+1+AJLX++%E6%A1%88%E4%BB%B6%E7%B1%BB%E5%9E%8B:%E5%88%91%E4%BA%8B%E6%A1%88%E4%BB%B6&conditions=searchWord+1_%E4%B8%80%E5%AE%A1+SPCX++%E5%AE%A1%E5%88%A4%E7%A8%8B%E5%BA%8F:%E4%B8%80%E5%AE%A1&conditions=searchWord+1+WSLX++%E6%96%87%E4%B9%A6%E7%B1%BB%E5%9E%8B:%E5%88%A4%E5%86%B3%E4%B9%A6',
        'http://wenshu.court.gov.cn/list/list/?sorttype=1&conditions=searchWord+002002001003+AY++%E6%A1%88%E7%94%B1:%E7%A6%BB%E5%A9%9A%E5%90%8E%E8%B4%A2%E4%BA%A7%E7%BA%A0%E7%BA%B7',
    ]

    # job = WenshuCourtSpider(1, seeds)
    # job.load_proxy('proxy')
    # # job.run()
    # url = 'http://wenshu.court.gov.cn/List/ListContent'
    # data = {"Param": 'sorttype=1&conditions=searchWord+河南省郑州市中级人民法院+++中级法院:河南省郑州市中级人民法院', "Index": 1, "Page": 5,
    #         "Order": u'裁判日期', "Direction": 'asc'}
    # job.post_search(url, data)
    # con = job.request_url(seeds[0])
    # print con.text
    # job.post_search(seeds[0],{})
    # test_fetch_paper('http://wenshu.court.gov.cn/content/content?DocID=f97235b2-72e4-4f61-8e0b-00869f9f15ab')
    # runjs(seeds[0])
    # runjs(seeds[1])
    # test_session_fetch_if_js(seeds[0])
    # runjs(seeds[0])
    # seeds = read_seeds('seeds')
    _fetch_page()
