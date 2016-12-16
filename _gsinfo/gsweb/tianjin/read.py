#!/usr/bin/env python
# -*- coding:utf8 -*-

from lxml import html
import spider.util

def _parse():
    doc = None
    with open("index.html", 'rb') as f:
        text = f.read().decode("gbk").encode("utf-8")
        doc = html.fromstring(text)


    tables = doc.xpath("//table[@class='detailsList']")
    trs = tables[0].xpath("tr")

def _read1():
    filter = set()
    with open("gsinfo_tianjin.txt", "r") as f:
        i = 0
        j = 0
        for line in f:
            r = line.strip()
            if r in filter:
                j += 1
                print j, 'already exist!!!'
            else:
                filter.add(r)
                #save.append(r)
                #r = eval(r)
                i += 1
                print "第", i, "行:", r #utf8str(r)

    print '重复条数:', j, "去重后条数:", i, "总条数:",(j+i)


if __name__ == '__main__':
    spider.util.use_utf8()
    #_parse()
    _read1()