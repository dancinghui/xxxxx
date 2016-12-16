#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider, AccountErrors
import re
from spider.savebin import BinSaver
import random
import threading
import traceback
import spider.util
from spider.savebin import FileSaver
import urllib2
import json

def tiqu_zuzhijigou_code():
    save = FileSaver("sort_code_guangzhou.txt")
    code_ary = []
    filter = set()
    cnt = 0
    sus = 0
    fail = 0
    filtet_code = set()
    with open("guangzhou_company_list.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                continue
            cnt += 1
            try:
                r = eval(line)
                old_code = r["oc_code"]
                if old_code is not None and old_code != "":
                    code = old_code[0:-1]
                    new_code = compute_code(code)
                    if old_code == new_code:
                        if new_code in filtet_code:
                            continue
                        code_ary.append(new_code)
                        sus += 1
                        print sus, "校验成功：",new_code
                        filtet_code.add(new_code)
                    else:
                        fail += 1
                        print fail, "失败:", old_code, new_code
                filter.add(line)
            except Exception as e:
                print "错误：", cnt, e, line
    print "总共", cnt, "成功的：", sus, "失败的:", fail
    time.sleep(1)
    if len(code_ary) != 0:
        i = 0
        code_ary.sort()
        for code in code_ary:
            i += 1
            save.append(code)
    print "获得", i, "个组织机构代码！"


def compute_code(code):
    code = code.strip()
    assert len(code) == 8
    vs = [3, 7, 9, 10, 5, 8, 4, 2]
    v = 0
    for i in range(0, 8):
        if '0' <= code[i] <= '9':
            v += (ord(code[i]) - ord('0')) * vs[i]
        elif 'A' <= code[i] <= 'Z':
            v += (ord(code[i]) - ord('A') + 10) * vs[i]
        elif 'a' <= code[i] <= 'z':
            v += (ord(code[i]) - ord('a') + 10) * vs[i]
        else:
            raise RuntimeError("invalid code")
    v = (11 - v % 11) % 11
    return code + '0123456789X'[v]

def read1():
    filter = set()
    filter_name = set()
    with open("成功拿到的详情900.txt", "r") as f:
        i = 0
        j = 0
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
                #print r

    print '重复条数:', j, "去重后条数:", i

def try_http_get():
    url = "http://gsxt.gzaic.gov.cn/aiccips/GSpublicity/GSpublicityList.html?service=entInfo_PGcPo7E76u4khJQyh/Jeeb9Y3aP8pyvHI/OTcd2/xk8=-9Sdep34ycmGGcR7OsMoWBQ=="

    headers = {"Referer": url, "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0"}
    request = urllib2.Request(url, headers)
    #request.add_header("Referer", url)
    #request.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0")
    response = urllib2.urlopen(request)
    print response.read()


def check_two_file():
    filter = set()
    with open("all_company_list.txt", "r") as f:
        for line in f:
            line = line.strip()
            try:
                r = eval(line)
                cname = r["oc_name"]
                filter.add(cname)
            except Exception as e:
                print "ERROR：", e, line
                continue
    re = 0
    new = 0
    with open("all_company_list_already.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                re += 1
                print re, "爬过．．．", line
            else:
                new += 1
    print "爬过：", re, "未爬过：", new

def filter_occode():
    filter = set()
    lst = []
    re_num = 0
    with open("all_company_list.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                re_num += 1
                print "重复数：", re_num
                continue
            else:
                try:
                    r = eval(line)
                    code = r["oc_code"]
                    lst.append(code)
                except Exception as e:
                    print "ERROR:", e
                filter.add(line)
    print "lst = ", len(lst)
    lst.sort()
    save = FileSaver("已经存在.txt")
    for l in lst:
       save.append(l)

def tiqu_cname_by_corp_name():
    filter = set()
    filter_name = set()
    i = 0
    j = 0
    save = FileSaver("corp_name_tiqu.txt")
    with open("corp_name.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                i += 1
                continue
            ary = line.split(" ")
            x = 0
            for ay in ary:
                x += 1
                if x == 1 or x == 2:
                    continue
                cname = ay.strip()
                if cname in filter_name:
                    continue
                save.append(cname)
                filter_name.add(cname)
                j += 1
            filter.add(line)
    print "重复数：", i, "拿到公司名：", j


def filter_corp_name():
    filter = set()
    save = FileSaver("../gsweb/gansu/Gansu_cname.txt")
    with open("corp_name.txt", "r") as f:
        i = 0
        j = 0
        for line in f:
            line = line.strip()
            ary = line.split(" ")
            code = int(ary[1].strip())
            #地区代码
            if code < 620000 or code >= 630000:
                continue
            a = 0
            for name in ary:
                if a == 0 or a == 1:
                    a += 1
                    continue
                if name in filter:
                    a += 1
                    j += 1
                    #print name, " already in filter..."
                    continue
                print code, name
                save.append(name)
                filter.add(name)
                a += 1
                i += 1
    print '重复条数:', j, "去重后条数:", i

def filter_already_occode():
    filter = set()
    lst = []
    re_num = 0
    with open("all_company_list.txt", "r") as f:
        for line in f:
            line = line.strip()
            try:
                r = eval(line)
                code = r["oc_code"]
                if code in filter:
                    re_num += 1
                    continue
                lst.append(code)
                filter.add(code)
            except Exception as e:
                print "ERROR:", e
    print "lst = ", len(lst)
    lst.sort()
    save = FileSaver("已经拿到注册码的机构代码test.txt")
    for l in lst:
       save.append(l)

def filter_already_occode1():
    filter = set()
    lst = []
    re_num = 0
    with open("测试-成功拿到的详情.txt", "r") as f:
        for line in f:
            line = line.strip()
            try:
                r = eval(line)
                code = r["list"][0]["oc_code"]
                if code in filter:
                    re_num += 1
                    continue
                lst.append(code)
                filter.add(code)
            except Exception as e:
                print "ERROR:", e
                #time.sleep(0.2)
    print "lst = ", len(lst)
    lst.sort()
    save = FileSaver("已经拿到注册码的机构代码test1.txt")
    for l in lst:
       save.append(l)

def hebing_filter():
    filter = set()
    save = FileSaver("已经拿到注册码的机构代码.txt")
    lst = []
    fs = ["已经拿到注册码的机构代码test.txt", "已经拿到注册码的机构代码test1.txt"]
    for fl in fs:
        with open(fl, "r") as f:
            for line in f:
                code = line.strip()
                if code in filter:
                    continue
                lst.append(code)
                filter.add(code)
    print "lst = ", len(lst)
    if len(lst) != 0:
        lst.sort()
        for l in lst:
            save.append(l)


def generate_code(code):
    code = str(code)
    if len(code) != 8:
        sub = 8 - len(code)
        while sub != 0:
            code = "0" + code
            sub -= 1
    code = compute_code(code)
    print "最后生成组织机构代码：", code
    return code

def compute_code(code):
    code = code.strip()
    assert len(code) == 8
    vs = [3, 7, 9, 10, 5, 8, 4, 2]
    v = 0
    for i in range(0, 8):
        if '0' <= code[i] <= '9':
            v += (ord(code[i]) - ord('0')) * vs[i]
        elif 'A' <= code[i] <= 'Z':
            v += (ord(code[i]) - ord('A') + 10) * vs[i]
        elif 'a' <= code[i] <= 'z':
            v += (ord(code[i]) - ord('a') + 10) * vs[i]
        else:
            raise RuntimeError("invalid code")
    v = (11 - v % 11) % 11
    return code + '0123456789X'[v]

def check_code():
    filter_code = set()
    with open("测试-获取失败的机构代码和原因.txt") as f:
        for line in f:
            line = line.strip()
            code = line.split(",")[0][0:8]
            filter_code.add(code)

    temp = 0
    result = 0
    save = FileSaver("推测组织机构代码.txt")
    with open("已经拿到注册码的机构代码.txt", "r") as f:
        flag = True
        for line in f:
            line = line.strip()
            code = line[0:8]
            try:
                code = int(code)
                if flag:
                    temp = code
                    flag = False
                    continue
                sub = code - temp
                if 1 < sub < 100:
                    for i in range(temp, code, 1):
                        if i == temp or i == code or str(i) in filter_code:
                            continue
                        c = generate_code(i)
                        save.append(c)
                    result += (sub - 1)
                    print "code - temp = sub --> %d - %d = %d , result = %d" % (code, temp, sub, result)
                temp = code
            except Exception as e:
                #print "转换错误,可能含有字母，跳过...", code
                continue
    print "最后有 %d 个需要迭代..." % result

if __name__ == "__main__":
    #filter_already_occode1()
    #hebing_filter()
    read1()
    #check_code()
    #try_http_get()
    #check_two_file()
    #filter_occode()
    #tiqu_zuzhijigou_code()
    #tiqu_cname_by_corp_name()
    #filter_corp_name()
