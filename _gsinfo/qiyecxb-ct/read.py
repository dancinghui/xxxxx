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
import random
bloom = set()



def check():
    filter = set()
    with open("to_get_full_info.txt","r") as f:
        for line in f:
            r = line.strip()
            filter.add(r)
    already = set()
    with open("t-already_cname.txt","r") as f:
        for line in f:
            i = line.strip()
            already.add(i)
    result = filter-already
    cnt = 0
    for i in result:
        cnt += 1
        print cnt,i


def test_read():
    filter = set()
    filter_name = set()
    with open("proxy_0229.txt","r") as f:
        i = 0
        j = 0
        s = 0
        x = 0
        for line in f:
            r = line.strip()
            if r in filter:
                j += 1
                print j, 'already exist!!!'
            else:
                i += 1
                filter.add(r)
                #print i, r
                cname = eval(r)['list'][0]["oc_name"]
                if cname in filter_name:
                    x += 1
                    print s, 're-------------------', cname
                else:
                    s += 1
                    filter_name.add(cname)
    print 'already:',j ,"new:", i
    print 'x:', x, "s:", s

def utf8str(obj):
    if isinstance(obj, unicode):
        return obj.encode('utf-8')
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict) or isinstance(obj, list):
        return utf8str(json.dumps(obj, ensure_ascii=False, sort_keys=True))
    return utf8str(str(obj))



def check_proxy():
    filter = set()
    a = 0
    with open("proxy_all.txt","r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                print "self in filter..."
                a += 1
            else:
                filter.add(line)
    time.sleep(1)
    all = 0
    re = 0
    b = 0
    filter1 = set()
    with open("proxy_022709.txt","r") as f:
        for line in f:
            line = line.strip()
            all += 1
            if line in filter1:
                b += 1
            else:
                filter1.add(line)

            if line in filter:
                re += 1
                print re, 'already exist!!!'
            else:
                filter.add(line)
    print "a=",a,"b=",b
    print "all=",all,"re=",re
    print "re percent:%.2f"%(re/all)

def check_re():
    filter = set()
    re = 0
    with open("proxy_022709.txt","r") as f:
        for line in f :
            line = line.strip()
            if line in filter:
                re += 1
                print re, " already exist --> ", line
            else:
                filter.add(line)
        print "re count = ", re


from spider.savebin import FileSaver
def filter_proxy():
    filter = set()
    save = FileSaver("proxy_all_filter.txt")
    with open("proxy_all.txt","r") as f:
        re = 0
        use = 0
        for line in f:
            line = line.strip()
            if line in filter:
                re += 1
                print line, 'is exist!!!'
            else:
                save.append(line)
                use += 1
                filter.add(line)
    print 'use:', use, "re:", re


def _read1():
    filter = set()
    filter_name = set()
    with open("beijing_query_detail.txt", "r") as f:
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
                #print r

    print '重复条数:', j, "去重后条数:", i


def hebin():
    filter = set()
    save = FileSaver("a_queried_company_list.txt")
    re = 0
    new = 0
    files = ["a_query_company_list.txt", "a_query_company_list1.txt", "a_query_company_list_re1.txt"]
    for file in files:
        with open(file, "r") as f:
            for line in f:
                line = line.strip()
                if line in filter:
                    re += 1
                    print re, 'already exist!!!'
                else:
                    new += 1
                    filter.add(line)
                    save.append(line)
                    print new, line
    print "new:", new, " re:", re


def tiaoxuan():
    filter = set()
    re = 0
    new = 0
    fali = 0
    save = FileSaver("a_already_company_names_success.txt")
    #查询失败的公司名
    with open("a_query_company_list_failure.txt", "r") as f:
        for line in f:
            filter.add(line.strip())
            fali += 1
        print "read old:",fali

    #所有的公司名
    with open("a_already_company_names.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                re += 1
                print re, 'already exist!!!'
            else:
                new += 1
                #save.append(line)
                print new, line


def daochu():
    filter = set()
    #save = FileSaver("company_code_number_1.txt")
    save = FileSaver("a_queried_company_list1.txt")
    re = 0
    new = 0
    with open("a_queried_company_list.txt", "r") as f:
        for line in f:
            lst = eval(line.strip())
            code = lst['oc_code']
            if code in filter:
                re += 1
                print re, 'already exist!!!'
            else:
                #s = lst['oc_code']+','+lst['oc_number']+','+lst['oc_name']
                s = line.strip()
                new += 1
                filter.add(code)
                save.append(s)
                print new, s
    print "new:", new,"re:", re

def daochu1():
    filter = set()
    save = FileSaver("un_spider_queries.txt")
    with open("b_query_detail.txt", "r") as f:
        for line in f:
            line = line.strip()
            #print line
            detail = eval(line)
            code = detail["list"][0]["oc_code"]
            filter.add(code)

    re = 0
    new = 0
    with open("a_queried_company_list1.txt", "r") as f:
        for line in f:
            lst = eval(line.strip())
            code = lst['oc_code']
            if code in filter:
                re += 1
                print re, 'already get details!'
            else:
                s = line.strip()
                new += 1
                filter.add(code)
                save.append(s)
                print new, s
    print "new:", new,"re:", re



def filter_corp_name():
    filter = set()
    save = FileSaver("hunan_cname.txt")
    with open("corp_name.txt", "r") as f:
        i = 0
        j = 0
        for line in f:
            line = line.strip()
            ary = line.split(" ")
            code = int(ary[1].strip())
            #地区代码
            if code < 430000 or code >= 440000:
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


def filter_corp_name_all():
    filter = set()
    save = FileSaver("all_cname.txt")
    cnt = 0
    with open("corp_name.txt", "r") as f:
        i = 0
        j = 0
        for line in f:
            cnt += 1
            line = line.strip()
            ary = line.split(" ")
            #code = int(ary[1].strip())
            #地区代码
            # if code < 110000 or code >= 120000:
            #     continue
            a = 0
            for name in ary:
                if a == 0 or a == 1:
                    a += 1
                    continue
                name = name.strip()
                if name in filter:
                    a += 1
                    j += 1
                    #print name, " already in filter..."
                    continue
                print cnt, name
                save.append(name)
                filter.add(name)
                a += 1
                i += 1
    print '重复条数:', j, "去重后条数:", i

def hebin1():
    filter = set()
    save = FileSaver("all_details.txt")
    re = 0
    new = 0
    files = ["b_query_detail.txt", "c_query_detail.txt"]
    for file in files:
        with open(file, "r") as f:
            for line in f:
                line = line.strip()
                if line in filter:
                    re += 1
                    print re, 'already exist!!!'
                else:
                    new += 1
                    filter.add(line)
                    save.append(line)
                    print new, line
    print "new:", new, " re:", re

def hebin2():
    filter = set()
    save = FileSaver("text.txt")
    re = 0
    new = 0
    files = ["b_query_detail.txt", "c_query_detail.txt"]
    for file in files:
        with open(file, "r") as f:
            for line in f:
                line = line.strip()
                if line in filter:
                    re += 1
                    print re, 'already exist!!!'
                else:
                    new += 1
                    filter.add(line)
                    save.append(line)
                    print new, line
    print "new:", new, " re:", re

def check_already_spider():
    filter = set()
    with open("guangzhou_company_list_already.txt", "r") as f:
        for line in f:
            line = line.strip()
            filter.add(line)

    un = 0
    al = 0
    with open("guangzhou_company_list.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                al += 1
                print al, 'already spiders!'
            else:
                un += 1
                filter.add(line)
                print un, "-------------------un spiders !"
    print "已经爬过的:", al, ",没有爬过的:", un


if __name__ == '__main__':
    #filter_proxy()
    #daochu1()
    _read1()
    #filter_corp_name()
    #hebin1()
    #filter_corp_name_all()
    #check_already_spider()

    # url = "http://appsvc.qiye.qianzhan.com/OrgCompany.svc/orgcompany/combine/search"
    # data = {"encryptedJson":"ZlWT15DsXFm0Y4QnYoK2ufXYi39Plo9\/yhwguqs9FWAHRqkKsKobDI+ai8+GR4NTJNeaHC7hDsivmsbOkOQ\/0lHsES3Wl5kF+pLW98YratGzlf4Tc5qnXiNDVUrc0WaqJD8obqeFhJLQsocfxB8REE6XpIbzthyB+CHX3TQpcJskJEZkJOyPxRdg9PTsCjTLPmgNHuWq3fSNyd3DpR6RIl\/AJNb+Ex70Uf0QDarg3koMErtDXwvcnEtxblp3kaMu2QmXxnDbkClaGASOP6ZsuKgVu6LXdW\/KOHk6cP+\/tEQ=","extJson":"Hoi6oX70l9whauZmjq8jVAmoe3UspXXhX9mPG+KAeqs1rKZVr\/uapICH92P\/CrrycI\/OjobbzuafHXthwGM38\/RMXUoOjROK+Psk7SCSv2\/vBYNK3RYrJk26Fgu1HxLDg9LWqdILYeoDE2G3IezMHPYyzrU1yEoFGenXS1U8gvc="}
    #
    # request = urllib2.Request(url,json.dumps(data))
    # request.add_header("Content-Type","application/json")
    # request.add_header("User-Agent","CCIQ/2.0.1 (iPhone; iOS 9.1; Scale/2.00)")
    # response = urllib2.urlopen(request)
    # print response.read()
    # i = 0
    # while i < 10:
    #     if i==5:
    #         bloom.add("haha--"+str(i-1))
    #         i+=1
    #         continue
    #     i+=1
    #     bloom.add("haha--"+str(i))
    # print bloom
    # inita()
    # print 'inita  finish---------'
    # testb()
    # with open("to_get_full_info.txt","r") as f:
    #     cnt = 0
    #     while True:
    #         line = f.readline().strip()
    #         cnt += 1
    #         if line is None:
    #             break
    #         ary = line.split(" ")
    #         print cnt,ary


    # url = "http://qyxy.baic.gov.cn/gjjbj/gjjQueryCreditAction!zyryBgxx.dhtml?old_reg_his_id=a1a1a1a031f9d49f0132054424f87ddb&new_reg_his_id=20e38b8b4ce3eebd014ce4036efd113c&clear=true&chr_id=null"
    # request = urllib2.Request(url)
    # response = urllib2.urlopen(request)
    # print response.read()