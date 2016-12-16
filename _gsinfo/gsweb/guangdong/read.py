#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
sys.path.append(sys.path[0]+"/..")
import urllib
import urllib2
import json
import threading
import time
import re
import json
import random
bloom = set()
from spider.savebin import FileSaver

def utf8str(obj):
    if isinstance(obj, unicode):
        return obj.encode('utf-8')
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict) or isinstance(obj, list):
        return utf8str(json.dumps(obj, ensure_ascii=False, sort_keys=True))
    return utf8str(str(obj))


def _read1():
    filter = set()
    filter_name = set()
    #save = FileSaver("已经拿到详情的公司名1.txt")
    debug = 0
    with open("gsinfo_guangdong_guangzhou.txt", "r") as f:
        i = 0
        j = 0
        for line in f:
            r = line.strip()
            if r in filter:
                j += 1
                #print j, 'already exist!!!'
            else:
                filter.add(r)
                i += 1
                if debug:
                    try:
                        js = json.loads(r)
                        if "changesInfo" not in js:
                            continue
                        changesInfo = js["changesInfo"]
                        if changesInfo is not None and len(changesInfo) != 0:
                            print "第", i, "行:", r
                    except Exception as e:
                        print "error..."
                else:
                    print "第", i, "行:", r #utf8str(r)
                    time.sleep(0.1)

    print '重复条数:', j, "去重后条数:", i, "总条数:",(j+i)


def _read2():
    filter = set()
    ary = ["gsinfo_guangdong_entityShow.txt", "gsinfo_guangdong_GSpublicityList.txt", "gsinfo_guangdong_QyxyDetail.txt", "gsinfo_guangdong_guangzhou.txt"]
    i = 0
    j = 0
    for fil in ary:
        with open(fil, "r") as f:
            for line in f:
                r = line.strip()
                if r in filter:
                    j += 1
                    #print j, 'already exist!!!'
                else:
                    filter.add(r)
                    #r = eval(r)
                    i += 1
                    #print "第", i, "行:", r #utf8str(r)

    print '重复条数:', j, "去重后条数:", i, "总条数:",(j+i)


def check_already_guangdong():
    filter = set()
    save = FileSaver("已经拿到详情的公司名.txt")
    ary = ["gsinfo_guangdong_entityShow.txt", "gsinfo_guangdong_GSpublicityList.txt", "gsinfo_guangdong_QyxyDetail.txt", "gsinfo_guangdong_guangzhou.txt"]
    cnt = 0
    for fil in ary:
        with open(fil, "r") as f:
            for line in f:
                cnt += 1
                r = line.strip()
                try:
                    r = r.replace(': null,', ':"",')
                    oi = eval(r)
                    basic = None
                    if "basicInfo" in oi:
                        basic = oi["basicInfo"]
                    else:
                        print "ERROR: basic is None -->oi=", oi
                        #time.sleep(0.1)
                        continue
                    cname = None
                    if "名称" in basic:
                        cname = basic["名称"]
                    elif "企业（机构）名称" in basic:
                        cname = basic["企业（机构）名称"]
                    elif "\xe5\x90\x8d\xe7\xa7\xb0" in basic:
                        cname = basic["\xe5\x90\x8d\xe7\xa7\xb0"]
                    else:
                        print "ERROR: name is None -->basic=", basic
                        #time.sleep(0.2)
                        continue
                    filter.add(cname)
                    save.append(cname)
                except Exception as e:
                    print cnt, e, "except异常--->r=", r
    print "拿到", cnt, "个公司名..."

    # save1 = FileSaver("./guangdong/guangdong_geted_detail_cname.txt")
    # save2 = FileSaver("./guangdong/guangdong_unget_detail_cname.txt")
    # x = 0
    # y = 0
    # with open("./guangdong/guangdong_tiqu_all_cname.txt", "r") as f:
    #     for line in f:
    #         line = line.strip()
    #         if line in filter:
    #             x += 1
    #             #print "已经爬到过详情:", cnt, line
    #             save1.append(line)
    #         else:
    #             y += 1
    #             save2.append(line)
    # print "爬过的:", x, "没有爬过的:", y



if __name__ == '__main__':
    _read1()
    #check_already_guangdong()