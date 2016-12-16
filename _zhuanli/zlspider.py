#!/usr/bin/env python
# -*- coding:utf8 -*-

'''
中国专利发布公告
http://epub.sipo.gov.cn/
查询接口:
url:http://epub.sipo.gov.cn/patentoutline.action
method:post
data:{
    'showType': 展示模式,0列表模式,1公布模式,2附图模式
    'strWord':  查询语句,例如:公开（公告）号='CN2015%' or 申请日,公开（公告）日,进入国家日期+='2015' or 申请号,本国优先权,分案原申请号+='2015%' or 申请（专利权）人,发明（设计）人,代理人,优先权,本国优先权,分案原申请号,生物保藏,国际申请,国际公布+='%2015%' or 地址,名称,专利代理机构,摘要+='2015'
    'numSortMethod': 排序方法,1申请日期升序,2申请日期降序,3发布公告日升序,4发布公告日降序
    'strLicenceCode': ''
    'selected': 查询的内容,fmgb--发明公布,fmsq--发明授权,xxsq--新型实用,wqsq--外观授权
    'numFMGB':  发明公布数量
    'numFMSQ':  发明授权数量
    'numSYXX':  实用新型数量
    'numWGSQ':  外观设计数量
    'pageSize': 页面大小，即每页返回专利条数
    'pageNow':  当前页
    }

专利信息下载接口:
url:http://epub.sipo.gov.cn/dxbdl.action
method:post
data:{
    'strSources': 'fmmost'
    'strWhere':  "pnm='专利号'"
    'recordCursor': 0
    'strLicenceCode': ''
    'action': 'dxbdln'
    }
'''
import abc
import pycurl
import re
import sys
import time
from urllib import quote

from court.cspider import EShutdownableSpider
from court.util import Main
from spider.ipin.savedb import PageStoreBase


class Patent():
    download_url_format = 'http://epub.sipo.gov.cn/dxbdl.action?strSources=%s&strWhere=%s&recordCursor=%s&strLicenseCode=&action=dxbdln'

    def __init__(self):
        self.name = ''
        self.patent_type = ''
        self.apply_code = ''
        self.apply_date = ''
        self.patent_number = ''
        self.apply_pub_date = ''
        self.petitioner = ''
        self.inventor = ''
        self.inventor_address = ''
        self.classify_code = ''
        self.abstract = ''
        self.fulltext = ''

    def parse(self, con):
        self.parse_name(con)
        self.parse_type(con)
        self.parse_apply_code(con)
        self.parse_apply_date(con)
        self.parse_pub_code(con)
        self.parse_pub_date(con)
        self.parse_petitioner(con)
        self.parse_inventor(con)
        self.parse_inventer_address(con)
        self.parse_classify_code(con)
        self.parse_abstract(con)

    @abc.abstractmethod
    def parse_name(self, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_type(self, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_apply_date(self, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_apply_code(self, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_pub_date(self, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_pub_code(self, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_petitioner(self, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_inventor(self, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_inventer_address(self, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_classify_code(self, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_abstract(self, con):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def parse_fulltext(self, con):
        raise NotImplementedError('virtual function called')

    @staticmethod
    def form_download_url(pub_code, type, code):
        return Patent.download_url_format % (type, quote('pnm\'%s\'' % pub_code), code)


class ZhuanliBaseSpider(EShutdownableSpider):
    class QueryError(Exception):
        pass

    def __init__(self, thcnt=2, recover=False, sleep=0, timeout=60):
        super(ZhuanliBaseSpider, self).__init__(thcnt)
        self.recover = recover
        self.test_mode = False
        self.origin_sleep = sleep
        self.origin_timeout = timeout
        self.sleep = self.origin_sleep
        self.timeout = self.origin_timeout

    def on_other_http_exception(self, exception):
        if isinstance(exception, pycurl.error):
            if len(exception.args) > 0 and (28 == exception.args[0] or 52 == exception.args[0]):
                with self.locker:
                    print 'pycurl exception: ', exception.args[1], exception.message
                    if self.sleep <= self.origin_sleep + 10:
                        self.sleep += 1
                        self.timeout += 1
                    return True
        return False

    def reset_state(self):
        with self.locker:
            self.timeout = self.origin_timeout
            self.sleep = self.origin_sleep

    def check_state(self):
        if self.origin_sleep < self.sleep:
            self.reset_state()

    def query(self, strword, showtype=1, sort=1, selected='', licence_code='', nfmgb=0, nfmsq=0, nsyxx=0, nwgsq=0,
              size=3, page=1):
        """查询专利"""
        if self.test_mode:
            print 'query word:', strword
        return self.request_url('http://epub.sipo.gov.cn/patentoutline.action', data={
            'showType': showtype, 'strWord': strword, 'numSortMethod': sort, 'strLicenceCode': licence_code,
            'selected': selected, 'numFMGB': nfmgb, 'numFMSQ': nfmsq, 'numSYXX': nsyxx, 'numWGSQ': nwgsq,
            'pageSize': size, 'pageNow': page
        }, timeout=self.timeout)

    def query_get(self, strword, showtype=1, sort=1, selected='', licence_code='', nfmgb=0, nfmsq=0, nsyxx=0, nwgsq=0,
                  size=3, page=1):
        """查询专利"""
        if self.test_mode:
            print 'query word:', strword, quote(strword)
        return self.request_url(
            self.form_query_url(strword, showtype, sort, selected, licence_code, nfmgb, nfmsq, nsyxx, nwgsq, size,
                                page))

    def query_with_apply_date(self, start, end=None):
        if start is None or not re.match('\d{4}\.\d{2}\.\d{2}', start):
            raise self.QueryError('Invalid date string %s' % start)
        if end is not None and not re.match('\d{4}\.\d{2}\.\d{2}', end):
            raise self.QueryError('Invalid date string %s' % end)
        if end is None:
            strword = '申请日=' + start
        else:
            strword = '申请日=BETWEEN[\'' + start + '\',\'' + end + '\']'
        return self.query_get(strword)

    def query_with_apply_pub_date(self, start, end=None, page=1, size=3):
        """通过申请公布日查询"""
        if start is None or not re.match('\d{4}\.\d{2}\.\d{2}', start):
            raise self.QueryError('Invalid date string %s' % start)
        if end is not None and not re.match('\d{4}\.\d{2}\.\d{2}', end):
            raise self.QueryError('Invalid date string %s' % end)
        if end is None:
            strword = '公开（公告）日=' + start
        else:
            strword = '公开（公告）日=BETWEEN[\'' + start + '\',\'' + end + '\']'
        return self.query_get(strword, page=page, size=size)

    def download_patent(self, where, source='fmmost', recordCursor=0, licence_code=''):
        """下载专利全文"""
        return self.request_url('http://epub.sipo.gov.cn/dxbdl.action', data={
            'strSources': source, 'strWhere': where, 'recordCursor': recordCursor, 'strLicenceCode': licence_code,
            'action': 'dxbdln'
        }, timeout=self.timeout)

    @staticmethod
    def form_download_url(pnm, source, recordCursor=0, licence_code=''):
        return 'http://epub.sipo.gov.cn/dxbdl.action?strSources=%s&strWhere=%s&recordCursor=%s&strLicenceCode=%s&action=dxbdln' % (
            source, quote("pnm='%s'" % pnm), recordCursor, licence_code
        )

    @staticmethod
    def form_query_url(strword, showtype=1, sort=1, selected='', licence_code='', nfmgb=0, nfmsq=0, nsyxx=0,
                       nwgsq=0,
                       size=3, page=1):
        return 'http://epub.sipo.gov.cn/patentoutline.action?showType=' + str(showtype) + '&strWord=' + str(
            quote(strword)) + '&numSortMethod=' + str(sort) + '&strLicenceCode=' + str(
            licence_code) + '&selected=' + str(selected) + '&numFMGB=' + str(nfmgb) + '&numFMSQ=' + str(
            nfmsq) + '&numSYXX=' + str(
            nsyxx) + '&numWGSQ=' + str(nwgsq) + '&pageSize=' + str(size) + '&pageNow=' + str(page)

    def fetch_captcha(self):
        return self.request_url('http://egaz.sipo.gov.cn/FileWeb/vci.jpg', timeout=self.timeout)

    def validate_download(self, path, code):
        return self.request_url('http://egaz.sipo.gov.cn/FileWeb/pfs', data={
            'path': path, 'vct': code
        }, timeout=self.timeout)

    def fetch_shiwushuju(self, apply_code):
        """事务数据查询"""
        return self.request_url('http://egaz.sipo.gov.cn/fullTran.action', data={'an': apply_code},
                                timeout=self.timeout)

    @staticmethod
    def normalize_query(keyword):
        pass


class ZhuanliBaseStore(PageStoreBase):
    def __init__(self, channel, dburl='mongodb://localhost/zhuanli'):
        super(ZhuanliBaseStore, self).__init__(channel, dburl)

    def page_time(self):
        int(time.time() * 1000)

    def extract_content(self):
        return self.get_cur_doc().cur_content


class PatentStore(ZhuanliBaseStore):
    def page_time(self):
        m = re.search(ur'<li class="wl228">申请日：(\d{4}\.\d{2}\.\d{2})</li>', self.get_cur_doc().cur_content)
        if m:
            return int(time.mktime(list(time.strptime(m.group(1), '%Y.%m.%d'))) * 1000)
        return int(time.time() * 1000)

    def extract_content(self):
        m = re.search(r'<div class="cp_img">.*?width="74" height="74" /></a>', self.get_cur_doc().cur_content, re.S)
        if m:
            return m.group()
        return self.get_cur_doc().cur_content


class PatentMain(Main):
    def __init__(self):
        Main.__init__(self)
        self.short_tag = 'm:t:s:r:'
        self.tags = ['recover=', 'threads=', 'mode=', 'seeds=', 'output=']
        self.thread_count = 3
        self.mode = None
        self.recover = False
        self.seeds = None

    def usage(self):
        print '%s usage:' % __file__
        print '-h, --help: print help message.'
        print '-v, --version: print script version'
        print '-o, --output: input an output verb'
        print '-t, --threads: thread count '
        print '-m, --mode: mode,if not id then will be abstract mode'
        print '-r, --recover: recover,1 or True for recover mode'
        print '-s, --seeds: seeds file'

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
            elif o in ('-s', '--seeds'):
                self.seeds = a
            elif o in ('-r', '--recover'):
                self.recover = True if (a == '1' or a == 'True') else False
            else:
                self.on_other_opt(o, a)
        if self.check():
            self.run()
        else:
            print 'not all arguments are right'

    def check(self):
        return True

    @abc.abstractmethod
    def on_other_opt(self, opt, arg):
        raise NotImplementedError('virtual function called')

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError('virtual function called')


def __test_query_pub_date():
    job = ZhuanliBaseSpider()
    job.load_proxy('proxy', 0)
    job.test_mode = True
    con = job.query_with_apply_pub_date('2010.01.12', '2010.01.16')
    if con:
        print con.headers
        print con.cookies
        print con.text


def __test_query_apply_date():
    job = ZhuanliBaseSpider()
    job.load_proxy('proxy', 0)
    job.test_mode = True
    con = job.query_with_apply_date('2010.01.12', '2010.01.16')
    if con:
        print con.headers
        print con.cookies
        print con.text


def __test_query():
    job = ZhuanliBaseSpider()
    job.load_proxy('proxy', 0)
    job.test_mode = True
    con = job.query("公开（公告）日=BETWEEN['2010.01.12','2010.01.16']", sort=3, size=1)
    if con:
        print con.headers
        print con.cookies
        print con.text


def __test_query_get():
    job = ZhuanliBaseSpider()
    job.load_proxy('proxy', 0)
    job.test_mode = True
    con = job.query_get("公开（公告）日=BETWEEN['2010.01.12','2010.01.16']", sort=3, size=1)
    if con:
        print con.headers
        print con.cookies
        print con.text


def __test_invalid_query():
    job = ZhuanliBaseSpider()
    job.load_proxy('proxy', 0)
    job.test_mode = True
    con = job.query("公布（公告）日=BETWEEN['2010.01.12','2010.01.16']")
    if con:
        print con.headers
        print con.cookies
        print con.text


if __name__ == '__main__':
    # __test_query_pub_date()
    # __test_query_apply_date()
    # __test_invalid_query()
    # __test_query()
    __test_query_get()

    pass
