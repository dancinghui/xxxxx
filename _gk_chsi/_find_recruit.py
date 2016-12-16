#!/usr/bin/env python
# -*- coding:utf8 -*-
import re

from spider.httpreq import BasicRequests


def find_recuit(url, sfile):
    req = BasicRequests()
    con = req.request_url(url)
    if not con:
        print 'None type response'
        return
    m = re.findall(r'<tr.*?<\/tr>', con.text, re.S)
    if not m:
        print 'cannot find any rows'
        return
    rows = []
    for r in m:
        rows.append(re.sub('<[^>]*>|&nbsp;', '', re.sub(r'\s', '',
                                                        re.sub(r'<\/td>', ',', r))))
    with open(sfile, 'w') as f:
        for row in rows:
            f.write(row.encode('utf-8') + '\n')
    print 'write ', len(rows)
    return rows


def cal():
    res = []
    bl = 60.63
    with open('j.txt') as f:
        for l in f:
            s = l.strip().split(' ')
            p = s[0]
            print s
            if len(s) > 1:
                m = re.search(r'\d+', s[1])
                if m:
                    r = int(m.group())
                else:
                    r = 0
            else:
                r = 0
            if len(s) > 2:
                c = float(s[2])
            else:
                c = 0
            if r != 0:
                t = r * c * bl/100.0
            else:
                t = c * bl
            res.append((p, str(r), str(c), str(t)))

    print 'size', len(res)
    with open('r.txt', 'w') as f:
        for r in res:
            f.write(','.join(r) + '\n')


if __name__ == '__main__':
    # res = find_recuit('http://www.gxeduw.com/news/2015/116383.html', 'recruit.txt')
    # res2 = find_recuit('http://www.tesoon.com/a_new/htm/26/126479.htm', 'recruit2.txt')
    cal()
