#!/usr/bin/env python
# -*- coding:utf8 -*-

import query
import requests
import re

def main():
    cnt = 0
    city_cnt = len(query.cities)
    for index, city in enumerate(query.cities):
        url = city[1]
        con = requests.get(url)
        find = re.search(r'为您找到 (\d+)条', con.text.encode('utf-8'))
        if not find:
            print "url %s, not find number" % url
            continue

        cnt += int(find.group(1))
        print "*** Current cnt: %d, process: %f" % (cnt, index/float(city_cnt))


    return cnt


if __name__ == '__main__':

    ## 315221
    cnt = main()
    print "=== All cnt: %s" % cnt
