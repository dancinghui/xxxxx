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
import random
from spider.savebin import FileSaver, BinReader
import imghdr
import spider.util

def temp():
    save = FileSaver("浙江_2014_gk66.txt")
    with open("/home/windy/develop/getjd/_gsinfo/gsweb/guangdong/guangzhou/zhejiang_2014.csv", "r") as f:
        i = 0
        j = 0
        for line in f:
            i += 1
            line = line.strip()
            if i == 1:
                save.append(line)
                continue
            arys = line.split(",")
            #ObjectId(554dcb3f77476421628828b8),4,z,四川,镇江市高等专科学校,420,工业环保与安全技术,l,14,416,173038,1,169413,412,420,2,165653,165653
            if len(arys) != 0 and arys[3] == "浙江" and arys[8] == "14":
                j += 1
                print j, line
                save.append(line)
    print "总共", i, "拿到：", j


def _read1():
    filter = set()
    filter_name = set()
    with open("/home/windy/develop/getjd/_gsinfo/gsweb/guangdong/guangzhou/already_guangzhou_inc_name3.txt", "r") as f:
        i = 0
        j = 0
        for line in f:
            r = line.strip()
            if r in filter:
                j += 1
                print j, 'already exist!!!'
            else:
                filter.add(r)
                #r = eval(r)
                i += 1
                print "第", i, "行:", r #utf8str(r)

    print '重复条数:', j, "去重后条数:", i, "总条数:",(j+i)


def qudiao_yinhao():
    save = FileSaver("already_guangzhou_inc_name2.txt")
    with open("/home/windy/develop/getjd/_gsinfo/gsweb/guangdong/guangzhou/已爬取广州所有公司0421unix.txt", "r") as f:
        i = 0
        j = 0
        for line in f:
            line = line.strip()[1:-1]
            print line
            save.append(line)

def check_already_spider():
    filter = set()
    with open("guangzhou.txt") as f:
        for line in f:
            line = line.strip()
            filter.add(line)

    # re = 0
    # new = 0
    # filter_self = set()
    # with open("already_guangzhou_inc_name1.txt") as f:
    #     for line in f:
    #         line = line.strip()
    #         if line in filter_self:
    #             continue
    #         else:
    #             if line in filter:
    #                 re += 1
    #                 #print re, " spider~~~"
    #             else:
    #                 new += 1
    #             filter_self.add(line)
    # print "爬过的名字:", re, "未爬名字:", new

    re = 0
    new = 0
    filter_self = set()
    with open("gsinfo_guangdong_guangzhou_gz1.txt") as f:
        for line in f:
            line = line.strip()
            if line in filter_self:
                continue
            else:
                try:
                    r = eval(line)
                    cname = r["basicInfo"]["名称"]
                    if cname in filter:
                        re += 1
                    else:
                        new += 1
                    filter_self.add(line)
                except Exception as e:
                    print "ERROR:", e, line
    print "爬过的名字:", re, "未爬名字:", new


def tiqu_already_spider_cname():
    re = 0
    new = 0
    filter_self = set()
    filter_cname = set()
    save = FileSaver("already_guangzhou_query_inc_name2.txt")
    with open("gsinfo_guangdong_guangzhou_gz1.txt") as f:
        for line in f:
            line = line.strip()
            if line in filter_self:
                re += 1
                continue
            else:
                try:
                    r = eval(line)
                    cname = r["basicInfo"]["名称"]
                    if cname in filter_cname:
                        re += 1
                        continue
                    else:
                        save.append(cname)
                        new += 1
                except Exception as e:
                    print "ERROR:", e, line
    print "重复:", re, "新:", new

def check_2_file_re():
    filter_re = set()
    re = 0
    new = 0
    with open("already_guangzhou_inc_name2.txt") as f:
        for line in f:
            line = line.strip()
            filter_re.add(line)

    with open("already_guangzhou_query_inc_name2.txt") as f:
        for line in f:
            line = line.strip()
            if line in filter_re:
                re += 1
                print re, "重复...", line
            else:
                new += 1
    print "重复条数:",re , "新数据:", new


def check_match_inc_name():
    #filter = set()
    ft = []
    ary = ["gsinfo_guangdong_guangzhou_gz3.txt", "gsinfo_guangdong_GSpublicityList_gz3.txt"]
    cnt = 0
    for fil in ary:
        with open(fil, "r") as f:
            for line in f:
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
                    #print cnt, cname
                    if cname.decode("utf-8") in ft:
                        continue
                    ft.append(cname.decode("utf-8"))
                    cnt += 1
                    #filter.add(cname.decode("utf-8"))
                except Exception as e:
                    print cnt, e, "except异常--->r=", r
                    #time.sleep(1)
    print "添加", cnt, "个公司名..."

    x = 0
    y = 0
    rule = [u"广州", u"广州白云区", u"广州天河区", u"广州工程", u"广州市", u"旅行社", u"贸易", u"广州有限公", u"湛江", u"县", u"广州一", u"上海", u"中国", u"广州市白云区", u"管理咨询", u"广州市黄埔区", u"广州市黄埔区", u"广州番禺"]
    with open("仍缺公司去掉有限字样.txt", "r") as f:
        for line in f:
            line = line.strip().decode("utf-8")
            if line in rule or line == "":
                continue
            for n in ft:
                if line in n:
                    x += 1
                    print x, "kw=", line, "queried:", n
    print "爬过的:", x, "没有爬过的:", y



def guangzhou_geted_detail_cname():
    filter = set()
    save = FileSaver("已经拿到详情的公司名.txt")
    ary = ["gsinfo_guangdong_GSpublicityList_gz.txt", "gsinfo_guangdong_GSpublicityList_gz1.txt", "gsinfo_guangdong_GSpublicityList_gz3.txt", "gsinfo_guangdong_guangzhou_gz1.txt", "gsinfo_guangdong_guangzhou_gz2.txt", "gsinfo_guangdong_guangzhou_gz3.txt", "gsinfo_guangdong_QyxyDetail_gz1.txt"]
    cnt = 0
    use = 0
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
                        print cnt, "ERROR: basic is None -->oi=", oi
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
                        print cnt, "ERROR: name is None -->basic=", basic
                        #time.sleep(0.2)
                        continue
                    if cname in filter:
                        print cnt, cname, "重复......"
                        continue
                    use += 1
                    filter.add(cname)
                    save.append(cname)
                except Exception as e:
                    print cnt, e, "except异常--->r=", r
    print "总共", cnt, "个公司名, 拿到爬过的：", use


def _read2():
    filter = set()
    ary = ["gsinfo_guangdong_GSpublicityList_gz.txt", "gsinfo_guangdong_GSpublicityList_gz1.txt",
           "gsinfo_guangdong_GSpublicityList_gz3.txt", "gsinfo_guangdong_guangzhou_gz1.txt",
           "gsinfo_guangdong_guangzhou_gz2.txt", "gsinfo_guangdong_guangzhou_gz3.txt",
           "gsinfo_guangdong_QyxyDetail_gz1.txt"]
    i = 0
    j = 0
    for fil in ary:
        with open(fil, "r") as f:
            for line in f:
                r = line.strip()
                if r in filter:
                    j += 1
                    print j, 'already exist!!!'
                else:
                    filter.add(r)
                    #r = eval(r)
                    i += 1
                    print "第", i, "行:", r #utf8str(r)

    print '重复条数:', j, "去重后条数:", i, "总条数:",(j+i)



def read_bin_file():
    t = BinReader('gsinfo_Guangdong_pic.bin')
    count = 0
    while True:
        (a, b) = t.readone()
        if a is None or b is None:
            break
        count += 1
        imgtype = imghdr.what(None, b)
        if imgtype in ['gif', 'jpeg', 'jpg', 'png', 'bmp']:
            spider.util.FS.dbg_save_file("./captcha/"+spider.util.utf8str(a) + "." + imgtype, b)
            #print a, "save suceess..."
        else:
            print a, "验证码格式无效，可能内容已经损坏..."
            continue

if __name__ == '__main__':
    _read1()
    #check_already_spider()
    #tiqu_already_spider_cname()
    #check_2_file_re()
    #check_match_inc_name()
    #guangzhou_geted_detail_cname()
    #read_bin_file()