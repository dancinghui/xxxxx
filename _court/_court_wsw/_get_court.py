#!/usr/bin/env python
# -*- coding:utf8 -*-
import time

from spider.httpreq import BasicRequests


class CourtFetcher():
    def __init__(self, proxy=None):
        self.provinces = [{'name': '北京', 'value': 0},
                          {'name': '天津', 'value': 4},
                          {'name': '上海', 'value': 0},
                          {'name': '重庆', 'value': 0},
                          {'name': '河北', 'value': 3},
                          {'name': '河南', 'value': 3},
                          {'name': '云南', 'value': 3},
                          {'name': '辽宁', 'value': 0},
                          {'name': '黑龙江', 'value': 0},
                          {'name': '湖南', 'value': 2},
                          {'name': '安徽', 'value': 0},
                          {'name': '山东', 'value': 4},
                          {'name': '新疆', 'value': 3},
                          {'name': '新疆兵团', 'value': 3},
                          {'name': '江苏', 'value': 3},
                          {'name': '浙江', 'value': 4},
                          {'name': '江西', 'value': 2},
                          {'name': '湖北', 'value': 4},
                          {'name': '广西', 'value': 1},
                          {'name': '甘肃', 'value': 0},
                          {'name': '山西', 'value': 4},
                          {'name': '内蒙古', 'value': 3},
                          {'name': '陕西', 'value': 3},
                          {'name': '吉林', 'value': 4},
                          {'name': '福建', 'value': 3},
                          {'name': '贵州', 'value': 4},
                          {'name': '广东', 'value': 0},
                          {'name': '青海', 'value': 4},
                          {'name': '西藏', 'value': 0},
                          {'name': '四川', 'value': 2},
                          {'name': '宁夏', 'value': 4},
                          {'name': '海南', 'value': 3},
                          {'name': '台湾', 'value': 3},
                          {'name': '香港', 'value': 0},
                          {'name': '澳门', 'value': 0}]
        self.courts = []
        self.child_courts = []
        self.save_name = 'court.txt'
        self.proxy = proxy

    def get_court(self):
        req = BasicRequests()
        req.set_proxy(self.proxy)
        for p in self.provinces:
            time.sleep(1)
            print 'fetch province', p['name']
            con = req.request_url('http://wenshu.court.gov.cn/Index/GetCourt', data={'province': p['name']})
            if '<' in con.text:
                print 'invalid response'
                continue
            court = self.parse_results(con)
            for c in court:
                self.courts.append(c)

    def get_child_court(self, court):
        req = BasicRequests()
        req.set_proxy(self.proxy)
        time.sleep(1)
        print 'fetching child court', court['key']
        con = req.request_url('http://wenshu.court.gov.cn/Index/GetChildAllCourt',
                              data={'keyCodeArrayStr': court['key']})
        if '<' in con.text:
            return
        court = self.parse_results(con)
        for c in court:
            self.child_courts.append(c)

    def parse_results(self, con):
        res = con.text.replace('\\u0027', '\'')
        res = res.replace('parentkey', '\'parent\'')
        for tag in ['region', 'leval', 'key', 'court', 'province']:
            res = res.replace(tag, '\'%s\'' % tag)
        if res[0] == '\'' or res[0] == '"':
            court = eval(res[1:-1])
        else:
            court = eval(res)
        return court

    def save(self):
        with open(self.save_name, 'w') as f:
            for c in self.courts:
                f.write(str(c) + '\n')
            for c in self.child_courts:
                f.write(str(c) + '\n')

    def run(self):
        self.get_court()
        for c in self.courts:
            self.get_child_court(c)
        self.save()

    @staticmethod
    def json2csv(infile='court.txt', outfile='court.csv'):
        inf = open(infile, 'r')
        out = open(outfile, 'w')
        title = '法院,省份,层级,地区,代号,上级代号'
        out.write(title + '\n')
        for l in inf:
            d = eval(l.strip())
            parent = d.get('parent', '')
            out.write('%s,%s,%s,%s,%s,%s\n' % (d['court'], d['province'], d['leval'], d['region'], d['key'], parent))


if __name__ == '__main__':
    job = CourtFetcher('112.124.113.155:80')
    job.run()
    CourtFetcher.json2csv()
