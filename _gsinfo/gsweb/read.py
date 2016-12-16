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
bloom = set()


def utf8str(obj):
    if isinstance(obj, unicode):
        return obj.encode('utf-8')
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict) or isinstance(obj, list):
        return utf8str(json.dumps(obj, ensure_ascii=False, sort_keys=True))
    return utf8str(str(obj))


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


def test_read1():
    filter = set()
    filter_name = set()
    with open("/home/windy/develop/getjd/_gsinfo/gsweb/guangdong/guangzhou/query_out_un_spider.txt", "r") as f:
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

def test__1():
    filter = set()
    save = FileSaver("guangdong_cname_tiqu.txt")
    ary = ["gsinfo_out_null.txt", "gsinfo_out_spidered_cname.txt", "gsinfo_out_spidered_cname1.txt", "guangdong_already_detail_cname.txt", "guangdong_cname_new.txt",
           "guangdong_success_spider_cname.txt", "guangdong_un_spider_cname.txt", "guangdong_un_spider_cname_15_14.txt"]
    i = 0
    j = 0
    for fil in ary:
        with open(fil, "r") as f:
            for line in f:
                r = line.strip()
                if r in filter:
                    j += 1
                    #print j, r, 'already exist!!!'
                else:
                    filter.add(r)
                    save.append(r)
                    i += 1
    print '重复条数:', j, "去重后条数:", i, "总条数:",(j+i)

def test_read2():
    filter = set()
    ary = ["./guangdong/gsinfo_guangdong_entityShow.txt", "./guangdong/gsinfo_guangdong_GSpublicityList.txt", "./guangdong/gsinfo_guangdong_QyxyDetail.txt", "./guangdong/gsinfo_guangdong_guangzhou.txt"]
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




def test_check():
    filter = set()
    old = 0
    with open("gsinfo_out.txt", "r") as f:
        for line in f:
            line = line.strip()
            name = eval(line)["name"]
            if name not in filter:
                filter.add(name)
                old += 1
    print "公司名加载条数:", old
    time.sleep(1)
    i = 0
    j = 0
    save = FileSaver("guangdong_cname_new.txt")
    with open("guangdong_cname.txt", "r") as f:
        for line in f:
            r = line.strip()
            if r in filter:
                j += 1
                print j, 'already exist!!!'
            else:
                i += 1
                print i, r, "not in "
                save.append(r)


    print "旧的公司名条数:", old, '已经查到的公司名条数:', j, "没有查到的公司名条数:", i, "总条数:",(j+i)


def test_check_url():
    old = 0
    new = 0
    save = FileSaver("gsinfo_guangdong_success_url1.txt")
    with open("gsinfo_guangdong_success_url.txt", "r") as f:
        for line in f:
            line = line.strip()
            oi = eval(line)
            url = oi["url"]
            if "gsxt.gzaic.gov.cn/aiccips/GSpublicity/GSpublicityList.html" in url:
                print "属于...跳过>..."
                new += 1
            else:
                save.append(line)
                old += 1
    print "跳过:", new, "已经爬过数据:", old

#查询 查到的entityshow但是还没有爬过的.
def read_entityShow():
    filter = set()
    with open("gsinfo_guangdong_success_url.txt", "r") as f:
        for line in f:
            line = line.strip()
            filter.add(line)

    i = 0
    cnt = 0
    with open("gsinfo_out.txt", "r") as f:
        for line in f:
            cnt += 1
            line = line.strip()
            if line in filter:
                continue
            oi = eval(line)
            url = oi["url"]
            if "gsxt.gzaic.gov.cn/search/search!entityShow" in url:
                i += 1
                print cnt, i, line

def guangzhou_daochu():
    old = 0
    new = 0
    filter = set()
    save = FileSaver("guangzhou_already_cname.txt")
    with open("ggsinfo_guangdong_guangzhou.txt", "r") as f:
        for line in f:
            line = line.strip()
            oi = eval(line)
            if "basicInfo" in oi:
                cname = oi["basicInfo"]["名称"]
                filter.add(cname)

    with open("ggsinfo_guangdong_guangzhou.txt", "r") as f:
        for line in f:
            line = line.strip()
            oi = eval(line)
            url = oi["url"]
            if "gsxt.gzaic.gov.cn/aiccips/GSpublicity/GSpublicityList.html" in url:
                pass
            else:
                save.append(line)
                old += 1
    print "跳过:", new, "已经爬过数据:", old

def check_guangzhou():
    # m = re.search(".*([\u4e00-\u9fa5]+).*", "abcdef阿瓦大实打实ghijk")
    # if m:
    #     print m.group(1)
    # temp = "abcdef阿瓦大实打实ghijk"
    # xx = u"([\u4e00-\u9fa5]+)"
    # pat = re.compile(xx)
    # result = pat.findall(temp.decode("utf8"))
    # for res in result:
    #     print res

    save = FileSaver("guangzhou4.txt")
    cnt = 0
    with open("guangzhou3.txt", "r") as f:
        for line in f:
            cnt += 1
            line = line.strip()
            xx = u"([\u4e00-\u9fa5]+)"
            pat = re.compile(xx)
            result = pat.findall(line.decode("utf8"))
            for res in result:
                if len(res) < 4 or res == u"有限公司" or res == u"贸易公司" or res == u"服装公司":
                    print "error: ", cnt, res
                    continue
                print cnt, len(res), res
                save.append(res.strip())
            # array = line.split("、")
            # for ary in array:
            #     m = re.search("广州-.*区(.*)", ary)
            #     if m:
            #         print m.group(1)
            #         save.append(m.group(1).strip())
            #     else:
            #         save.append(ary.strip())


def check_already_guangzhou():
    filter = set()
    x = 0
    with open("guangzhou4.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line not in filter:
                filter.add(line.strip())
                x += 1
            else:
                #print x, line
                pass
    print "加载完公司名:", x
    time.sleep(1)

    save1 = FileSaver("already_guangzhou_inc_name.txt")
    save2 = FileSaver("already_guangzhou_inc_detail.txt")

    ary = ["gsinfo_guangdong_entityShow.txt", "gsinfo_guangdong_GSpublicityList.txt", "gsinfo_guangdong_QyxyDetail.txt", "gsinfo_guangdong_guangzhou.txt"]
    i = 0
    cnt = 0
    #start = 0
    for fil in ary:
        with open(fil, "r") as f:
            for line in f:
                cnt += 1
                # if cnt < start:
                #     continue
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
                        #time.sleep(0.1)
                        continue

                    if cname in filter:
                        save1.append(cname)
                        save2.append(r)
                        i += 1
                        print "SUCCESS:", i, cname
                except Exception as e:
                    print cnt, e, "except异常--->r=", r
                    time.sleep(1)

def filter_self():
    filter = set()
    x = 0
    re = 0
    save = FileSaver("gsinfo_out.txt1")
    with open("gsinfo_out.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line not in filter:
                filter.add(line.strip())
                save.append(line)
                x += 1
            else:
                re += 1
                print "重复:", re, line
    print re, x


def check_guangdong_run():
    filter = set()
    ary = ["gsinfo_guangdong_entityShow.txt", "gsinfo_guangdong_GSpublicityList.txt", "gsinfo_guangdong_QyxyDetail.txt",
           "gsinfo_guangdong_guangzhou.txt"]
    cnt = 0
    # start = 0
    for fil in ary:
        with open(fil, "r") as f:
            for line in f:
                cnt += 1
                # if cnt < start:
                #     continue
                r = line.strip()
                try:
                    r = r.replace(': null,', ':"",')
                    oi = eval(r)
                    basic = None
                    if "basicInfo" in oi:
                        basic = oi["basicInfo"]
                    else:
                        #print "ERROR: basic is None -->oi=", oi
                        #time.sleep(0.1)
                        continue
                    cname = None
                    if "名称" in basic:
                        cname = basic["名称"]
                    elif "企业（机构）名称" in basic:
                        cname = basic["企业（机构）名称"]
                    # elif "\xe5\x90\x8d\xe7\xa7\xb0" in basic:
                    #     cname = basic["\xe5\x90\x8d\xe7\xa7\xb0"]
                    else:
                        #print "ERROR: name is None -->basic=", basic
                        #time.sleep(0.1)
                        continue

                    filter.add(cname)
                    # if cname not in filter:
                    #     i += 1
                    #     filter.add(cname)
                    # else:
                    #     print "RE:", i, cname

                except Exception as e:
                    print cnt, e, "except异常--->r=", r
                    time.sleep(1)

    save1 = FileSaver("guangdong_un_spider_cname.txt")
    save2 = FileSaver("guangdong_success_spider_cname.txt")
    i = 0
    j = 0
    cnt = 0
    with open("../_ct_inc_name/guangdong_cname.txt", "r") as f:
        for line in f:
            cnt += 1
            line = line.strip()
            if line in filter:
                i += 1
                print cnt, "~~~已经爬过:", i, line
                save2.append(line)
            else:
                j += 1
                print cnt, "---没有爬过:", j, line
                save1.append(line)


def test_beijing_req():
    url = "http://qyxy.baic.gov.cn/gjjbj/gjjQueryCreditAction!getBjQyList.dhtml"
    headers = {'Referer': "http://qyxy.baic.gov.cn/beijing",
               # "Origin": "http://qyxy.baic.gov.cn",
               # "Upgrade-Insecure-Requests": "1",
               "Content-Type": "application/x-www-form-urlencoded",
               "User-Agent":"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/49.0.2623.108 Chrome/49.0.2623.108 Safari/537.36"
               }

    data = {"credit_ticket": "46253C4383D0D22F1E234926E121704C", "currentTimeMillis": int(time.time()*1000), "keyword": "腾讯科技"}
    request = urllib2.Request(url, json.dumps(data))
    for k, v in headers.items():
        request.add_header("Content-Type","application/json")
    response = urllib2.urlopen(request)
    print response.read()

def split_beijing_cname():
    cnt = 0
    save = FileSaver("beijing_cname_backhalf.txt")
    with open("../_ct_inc_name/beijing_cname.txt", "r") as f:
        for line in f:
            cnt += 1
            if cnt < 900000:
                continue
            else:
                save.append(line.strip())
                print "--->", line.strip()

def tiqu_spidered_cname():
    filter = set()
    save = FileSaver("guangdong_already_detail_cname.txt")
    with open("gsinfo_guangdong_success_url.txt", "r") as f:
        i = 0
        j = 0
        for line in f:
            line = line.strip()
            r = None
            try:
                r = eval(line)
            except Exception as e:
                print "ERROR:", e, "--->", line
                time.sleep(2)
                continue
            name = r["name"]
            if name in filter:
                j += 1
                print j, name, 'already exist!!!'
            else:
                save.append(name)
                filter.add(name)
                i += 1
                #print "第", i, "行:", r #utf8str(r)   #1443977
    print '重复条数:', j, "去重后条数:", i, "总条数:",(j+i)

def a():
    filter = set()
    save = FileSaver("guangdong_un_spider_cname_15_14.txt")
    cnt = 0
    with open("guangdong_already_detail_cname.txt", "r") as f:#广东已经爬过详情的公司名
        for line in f:
            line = line.strip()
            cnt += 1
            filter.add(line)
        print "初始化完毕...", cnt
    with open("../_ct_inc_name/guangdong_cname.txt", "r") as f: #广东所有公司名
        i = 0
        j = 0
        for line in f:
            name = line.strip()
            if name in filter:
                i += 1
                #print i, name, "already spider !"
            else:
                j += 1
                save.append(name)
    print "已经爬过的:", i, "没有爬过的:", j



def check_already_guangdong():
    filter = set()

    ary = ["./guangdong/gsinfo_guangdong_entityShow.txt", "./guangdong/gsinfo_guangdong_GSpublicityList.txt", "./guangdong/gsinfo_guangdong_QyxyDetail.txt", "./guangdong/gsinfo_guangdong_guangzhou.txt"]
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
                    #print cnt, cname
                    filter.add(cname)
                except Exception as e:
                    print cnt, e, "except异常--->r=", r
                    #time.sleep(1)
    print "添加", cnt, "个公司名..."

    save1 = FileSaver("./guangdong/guangdong_geted_detail_cname.txt")
    save2 = FileSaver("./guangdong/guangdong_unget_detail_cname.txt")
    x = 0
    y = 0
    with open("./guangdong/guangdong_tiqu_all_cname.txt", "r") as f:
        for line in f:
            line = line.strip()
            if line in filter:
                x += 1
                #print "已经爬到过详情:", cnt, line
                save1.append(line)
            else:
                y += 1
                save2.append(line)
    print "爬过的:", x, "没有爬过的:", y


def qudiao_yinhao():
    save = FileSaver("already_guangzhou_inc_name2.txt")
    with open("/home/windy/develop/getjd/_gsinfo/gsweb/guangdong/guangzhou/已爬取广州所有公司0421unix.txt", "r") as f:
        i = 0
        j = 0
        for line in f:
            line = line.strip()[1:-1]
            print line
            save.append(line)


if __name__ == '__main__':
    #check_already_guangdong()
    #a()
    #tiqu_spidered_cname()
    #filter_proxy()
    #daochu1()
    #read_entityShow()
    #filter_corp_name()
    #test_check()
    test_read1()
    #test__1()
    #test_check_url()
    #check_guangzhou()
    #check_already_guangzhou()
    #filter_self()
    #check_guangdong_run()
    #split_beijing_cname()
    #qudiao_yinhao()
    #qudiao_yinhao()

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

