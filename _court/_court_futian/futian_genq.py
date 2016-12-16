#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import re

from spider.httpreq import BasicRequests


class FutianGenQueries(BasicRequests):
    def __init__(self):
        BasicRequests.__init__(self)
        self.url = 'http://www.ftcourt.gov.cn/cpwspt/writopenlist.aspx?cls=0'
        self.params = {}
        self.count = 0

    def run(self):
        self.get_form_values()
        self.show()

    def get_form_values(self):
        con = self.request_url(self.url)
        params = []
        if con:
            m = re.search(ur'<a[^>]*doPostBack\(\'anpWritList\',\'(\d+)\'\)"[^>]*>最后一页<\/a>', con.text)
            if m:
                self.count = int(m.group(1))
            form = re.search(r'<form[^>]*id="ctl00">.*?<\/form>', con.text, re.S)
            if form:
                form = form.group()
                # print form
                inputs = re.findall(r'<input[^>]*>', form, re.S)
                for p in inputs:
                    attrs = re.findall(r'((name|value)="([^"]*))', p)
                    if len(attrs) > 1:
                        param = {}
                        for a, k, v in attrs:
                            param[k] = v
                        params.append(param)
                    elif len(attrs) > 0:
                        for a, k, v in attrs:
                            if k == u'name':
                                params.append({k: v, u'value': ''})
        res = {}
        for p in params:
            res[p[u'name']] = p[u'value']
        res.pop('btnSearch')
        res.pop('btnChongz')
        self.params = copy.deepcopy(res)

    def show(self):
        print self.params
        print self.count
        print self.url


if __name__ == '__main__':
    job = FutianGenQueries()
    job.run()
