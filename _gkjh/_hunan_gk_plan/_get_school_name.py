#!/usr/bin/env python
# -*- coding:utf8 -*-
import re

from spider import spider
from spider.httpreq import BasicRequests


class GetSchoolName(BasicRequests):
    def __init__(self):
        BasicRequests.__init__(self)
        self._url_format = 'http://gaokao.chsi.com.cn/zyk/pub/myd/schAppraisalTop.action?start=%d'
        self._url_format2 = 'http://gaokao.chsi.com.cn/zsgs/zhangcheng/listVerifedZszc--method-index,lb-1,start-%d.dhtml'
        self._schools = []

    @staticmethod
    def parse_page_count(context, page_reg):
        m = re.findall(page_reg, context)
        # m = re.findall(r'<a[^>]*start=\d+[^>]*>(\d+)<', context)
        cnt = 0
        for i in m:
            n = int(i)
            if n > cnt:
                cnt = n
        return cnt

    @staticmethod
    def fetch_schools(request, url_format, pagesize, url_reg, page_reg):
        schools = []
        start = 0
        pagecnt = -1
        count = 1
        while True:
            url = url_format % start
            con = request.request_url(url)
            if con is None:
                print 'Cannot fetch', url
                break
            if pagecnt == -1:
                pagecnt = GetSchoolName.parse_page_count(con.text, page_reg)
                print 'Page Count', pagecnt
            sch = re.findall(url_reg, con.text)
            # sch = re.findall(ur'<a href="#" onclick="doDialog\(\'\d+\',\'([^\']+)\'\);', con.text)
            schools += sch
            count += 1
            start += pagesize
            if count > pagecnt != -1 or len(sch) == 0:
                print 'count:', count
                print 'sch size:', len(sch)
                break
        schools = spider.util.unique_list(schools)
        print 'school list size', len(schools)
        return schools

    @staticmethod
    def save(schools):
        f = open('school.py', 'w')
        # f = open('_hunan_gk_plan/school.py', 'w')
        f.writelines('# !/usr/bin/env python')
        f.writelines('# -*- coding:utf8 -*-')
        f.writelines("\n")
        f.write('schools=' + str(schools))
        f.flush()
        f.close()
        print 'school list saved,', len(schools)


if __name__ == '__main__':
    sites = [{
        'format': 'http://gaokao.chsi.com.cn/zyk/pub/myd/schAppraisalTop.action?start=%d',
        'url_reg': '<a href="#" onclick="doDialog\(\'\d+\',\'([^\']+)\'\);',
        'page_reg': r'<a[^>]*start=\d+[^>]*>(\d+)<',
        'pagesize': 20
    }, {
        'format': 'http://gaokao.chsi.com.cn/zsgs/zhangcheng/listVerifedZszc--method-index,lb-1,start-%d.dhtml',
        'url_reg': r'<a href="\/zsgs\/zhangcheng\/listZszc\-\-schId\-\d+\.dhtml".*>([^<]*)<\/a>',
        'page_reg': r'<a[^>]*start\-\d+[^>]*>(\d+)<',
        'pagesize': 100
    }]
    url_format = ['http://gaokao.chsi.com.cn/zyk/pub/myd/schAppraisalTop.action?start=%d',
                  'http://gaokao.chsi.com.cn/zsgs/zhangcheng/listVerifedZszc--method-index,lb-1,start-%d.dhtml']
    url_pattern = [r'<a href="#" onclick="doDialog\(\'\d+\',\'([^\']+)\'\);',
                   r'<a href="\/zsgs\/zhangcheng\/listZszc\-\-schId\-\d+\.dhtml".*>([^<]*)<\/a>']
    page_pattern = [r'<a[^>]*start=\d+[^>]*>(\d+)<', r'<a[^>]*start\-\d+[^>]*>(\d+)<']
    request = BasicRequests()
    schools = []
    for site in sites:
        schools += GetSchoolName.fetch_schools(request, site['format'], site['pagesize'], site['url_reg'],
                                               site['page_reg'])
    ss = []
    for c in schools:
        if c not in ss:
            ss.append(c)
    GetSchoolName.save(schools)
