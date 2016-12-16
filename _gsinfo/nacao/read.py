#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
sys.path.append(sys.path[0]+"/..")
reload(sys)
sys.setdefaultencoding('utf-8')
import urllib
import urllib2
import json
import threading
import time
import re
import random
from spider.savebin import FileSaver, BinReader
import imghdr
import spider.spider
bloom = set()

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
    with open("nacao_queries_info.txt", "r") as f:
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


def _read2():
    filter_code = set()
    files = ["nacao_queries_info_local.txt", "nacao_queries_info.txt"]
    i = 0
    x = 0
    y = 0
    for fs in files:
        with open(fs, "r") as f:
            for line in f:
                i += 1
                r = line.strip()
                #print r
                jn = json.loads(r)
                zch = jn["zch"]
                if zch in filter_code:
                    x += 1
                else:
                    filter_code.add(zch)
                    #print zch
                    y += 1
    print "总条数:", i, "重复注册号:", x, "不重注册号:", y


def check_code2():
    fail = 0
    ary = [{"max":1009393, "all":1009393, "min":1009393, "count":1}]
    with open("sort_code_beijing.txt", "r") as f:
        for line in f:
            line = line.strip()
            code8 = line[0:8]
            try:
                code8 = int(code8)
                flag = True
                for ay in ary:
                    all = ay["all"]
                    count = ay["count"]
                    avg_temp = abs(all/count - code8)
                    if avg_temp < 10000:
                        all += code8
                        count += 1
                        max = ay["max"]
                        min = ay["min"]
                        if code8 < min:
                            ay["min"] = code8
                        elif code8 > max:
                            ay["max"] = code8
                        ay["all"] = all
                        ay["count"] = count
                        flag = False
                        break
                    elif avg_temp > 1000000:
                        ay = {"max":code8, "all":code8, "min":code8, "count":1}
                        ary.append(ay)
                        flag = False
                        break
                if flag:
                    fail += 1
                    print code8, "被剔除掉...", fail
            except Exception as e:
                continue
    cnt = 0
    for ay in ary:
        cnt += 1
        print "区间段：[ %d , %d ] , 记录条数 : %d" % (ay["min"], ay["max"], ay["count"])
    print "被剔除掉的数量：", fail, "区间段的数量：", cnt

def check_code():
    temp = 0
    result = 0
    #save = FileSaver("need_query_code_50.txt")
    with open("oc_code.txt", "r") as f:
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
                if 1 < sub < 10:
                    for i in range(temp, code, 1):
                        if i == temp or i == code:
                            continue
                        c = compute_code(i)
                        #print "最后的oc_code:", c
                        #save.append(c)
                        result += 1
                    #result += (sub - 1)
                    print "code - temp = sub --> %d - %d = %d , result = %d, test=%s" % (code, temp, sub, result, compute_code(code-1))
                temp = code
            except Exception as e:
                #print "转换错误,可能含有字母，跳过...", code
                continue
    print "最后有 %d 个需要迭代..." % result



def tiaoxuan(code1, code2):
    temp = code1+1
    while temp < code2:
        buquan(temp)
        temp += 1


def buquan(code):
    code = str(code)
    if len(code) != 8:
        sub = 8 - len(code)
        while sub != 0:
            code = "0" + code
            sub -= 1
    return code

def compute_code(code):
    code = buquan(code)
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

def hebing():
    ary = ["sort_code_beijing.txt", "sort_code_guangzhou.txt"]
    lst = []
    filter = set()
    re_num = 0
    for ay in ary:
        with open(ay, "r") as f:
            for line in f:
                line = line.strip()
                if line in filter:
                    re_num += 1
                    print "重复...", re_num
                    continue
                lst.append(line)
                filter.add(line)
    if len(lst) != 0:
        lst.sort()
    save = FileSaver("sort_code.txt")
    cnt = 0
    for ls in lst:
        save.append(ls)
        cnt += 1
    print "重新获取 ", cnt


# def tiqu_cname_r1():
#     filter_name = set()
#     save = FileSaver("r1_fenci1.txt")
#     cat = [u"公司", u"有限公司", u"分公司", u"子公司", u"责任公司", u"集团"]#"委员会", "商行", "合作社", "经营部", "工作室", "维修部", "影楼", "生活馆", "网吧", "经销处", "服饰店", "营业厅",
#            #"西餐厅", "商店", "票务部", "经销处", "五金厂", "超市", "咖啡店", "咨询中心", "茶餐厅", "酒吧", "针织厂", "塑料厂", "服务部", "酒店", "宾馆", "旅馆"]
#     with open("/home/windy/r1.txt", "r") as f:
#         cnt = 0
#         i = 0
#         for line in f:
#             cnt += 1
#             line = line.strip()
#             ary = line.split(" ")
#             x = -1
#             for ay in ary:
#                 x += 1
#                 if x == 0 or x == 1:
#                     continue
#                 result = _jieba_(ay.strip())
#                 for r in result:
#                     r = r.strip()
#                     if len(r) <= 1 or r in filter_name or r in cat:
#                         continue
#                     else:
#                         i += 1
#                         print "文件第 %d 行 , 获得第 %d 个分词:" % (cnt, i), ay, " : ",r
#                         filter_name.add(r)
#                         save.append(str(cnt) + " " + ay + " " + r)
#         print "文件 %d 行 , 获得 %d 个分词:" % (cnt, i)

def guolv():
    filter1 = set()
    filter2 = set()
    save = FileSaver("r1_fenci_local_filter.txt")
    with open("r1_fenci.txt", "r") as f:
        for line in f:
            line = line.strip()
            filter1.add(line)

    cat = [u"公司", u"有限公司", u"分公司", u"子公司", u"责任公司", u"集团", u"委员会", u"商行", u"合作社", u"经营部", u"工作室", u"维修部", u"影楼", u"生活馆", u"网吧", u"经销处", u"服饰店", u"营业厅",
           u"西餐厅", u"商店", u"票务部", u"经销处", u"五金厂", u"超市", u"咖啡店", u"咨询中心", u"茶餐厅", u"酒吧", u"针织厂", u"塑料厂", u"服务部", u"酒店", u"宾馆", u"旅馆"]
    with open("r1_fenci_local.txt", "r") as f:
        cnt = 0
        i = 0
        for line in f:
            line = line.strip()
            if line in filter2:
                print line, "...... 自身重复 ......"
                continue
            else:
                filter2.add(line)

            if line in filter1:
                i += 1
                print i, line, "...... 重复 ......"
            else:
                if line in cat:
                    print cnt, line, "...... 要去掉 ......"
                    continue
                cnt += 1
                save.append(line)
        print "重复 %d 行 , 获得 %d 个分词:" % (i, cnt)

#
# import jieba
# def _jieba_(line):
#     # seg_list = jieba.cut("繁德信息技术服务(北京)有限公司", cut_all=True)
#     # print "Full Mode:", "/ ".join(seg_list)  # 全模式
#     # seg_list = jieba.cut("fis繁德信息技术服务(北京)有限公司", cut_all=False)
#     # print "Default Mode:", "/ ".join(seg_list)  # 精确模式
#     # seg_list = jieba.cut("fis繁德信息技术服务(北京)有限公司")  # 默认是精确模式
#     # print ", ".join(seg_list)
#     seg_list = jieba.cut_for_search(line)  # 搜索引擎模式
#     result = "#".join(seg_list)
#     #print result
#     return result.split("#")
#     # for r in result.split("#"):
#     #     r = r.strip()
#     #     if len(r) > 1:
#     #         print r
#     #     else:
#     #         print "ｉｇｎｏｒｅ...", r


def save_file(fname, content):
    with open(fname, 'wb') as f:
        f.writelines(content)

def read_bin_file():
    t = BinReader('nacao_captcha_image.bin')
    count = 0
    while True:
        (a, b) = t.readone()
        if a is None or b is None:
            break
        count += 1
        save_file("/home/windy/codeimg/nacao/"+ a +".jpeg", b)
        print count, a


def tiqu_oc_code():
    filter_code = set()
    save = FileSaver("oc_code.txt")
    files = ["nacao_queries_info_local.txt", "nacao_queries_info.txt"]
    s = []
    i = 0
    x = 0
    y = 0
    for fs in files:
        with open(fs, "r") as f:
            for line in f:
                i += 1
                r = line.strip()
                jn = json.loads(r)
                oc = jn["jgdm"]
                if oc in filter_code:
                    x += 1
                else:
                    filter_code.add(oc)
                    s.append(oc)
                    y += 1
    print "总条数:", i, "重复注册号:", x, "不重注册号:", y
    z = 0
    if len(s) != 0:
        s.sort()
        for c in s:
            z += 1
            save.append(c)
    print "结束，写入", z, "条数据..."


def tiqu_oc_code_cname():
    save = FileSaver("oc_code_cname.txt")
    files = ["nacao_queries_info_local.txt", "nacao_queries_info.txt"]
    s2 = {}
    i = 0
    x = 0
    y = 0
    for fs in files:
        with open(fs, "r") as f:
            for line in f:
                i += 1
                r = line.strip()
                jn = json.loads(r)
                oc = jn["jgdm"]
                cname = jn["bzjgmcs"]
                try:
                    s2[oc.strip()] = cname.strip()
                    print i, oc
                except Exception as e:
                    print "出错......", e, r
                    continue
    print "总条数:", i, "重复注册号:", x, "不重注册号:", y, "字典内元素个数:",len(s2)
    z = 0
    if len(s2) != 0:
        items = s2.items()
        print "排序开始...", time.time()
        items.sort()
        print "排序完毕...", time.time()
        for k, v in items:
            z += 1
            save.append(k + " " + v)
    print "结束，写入", z, "条数据...", time.time()


all = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
       "A": 10, "B": 11, "C": 12, "D": 13, "E": 14, "F": 15, "G": 16, "H": 17, #"I":18,
       "J": 18, "K": 19,"L": 20, "M": 21, "N": 22, #"O":24,
       "P": 23, "Q": 24, "R": 25, "S": 26, "T": 27, "U": 28, "V": 29,
       "W": 30, "X": 31, "Y": 32}  #"Z":35

# all = {"0": 0, "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
#        "A": 10, "B": 11, "C": 12, "D": 13, "E": 14, "F": 15, "G": 16, "H": 17, "I":18,
#        "J": 19, "K": 20,"L": 21, "M": 22, "N": 23, "O": 24,
#        "P": 25, "Q": 26, "R": 27, "S": 28, "T": 29, "U": 30, "V": 31,
#        "W": 32, "X": 33, "Y": 34, "Z": 35}

def jinzhi(code):
    #code = "SDF4435" #621457925
    result = 0
    x = len(code) - 1
    for i in code:
        # temp = 1
        # a = 0
        # while a < x:
        #     temp = temp * 36
        #     a += 1
        temp = 36 ** x
        result += all[i] * temp
        x -= 1
    #print "结果1:", result
    #print "结果2:", int(code, 36)
    return result

# def jian():
#     code1 = "MA1MH7DC"
#     code2 = "MA1MH7DF"
#     lth = 8
#     a = 0
#     result = 0
#     while a < 8:
#         b1 = code1[a:a+1]
#         b2 = code2[a:a+1]
#         c = all[b2] - all[b1]
#         result += c * (36 ** (lth-a))
#         a += 1

def read_MA():
    """针对M开头组织机构　转成34进制计算差值　统计这个差值有多少个数值需要遍历"""
    with open("/home/chentao/m.dat", "r") as f:
        cnt = 0
        temp = 0
        tempstr = ""
        result = 0
        for line in f:
            cnt += 1
            r = line.strip()
            codestr = r[1:8]
            code = jinzhi(codestr)
            sub = code - temp
            if sub < 50:
                result += (sub - 1)
                print "新码 - 旧码 = %s - %s = %d , result = %d" % (r, tempstr, sub, result)
            temp = code
            tempstr = r
        print "最后结果：", result


if __name__ == '__main__':
    _read2()
    #tiqu_oc_code_cname()
    #tiqu_oc_code()
    #check_code()
    #write_file(1)
    #tiaoxuan(99880556, 99880583)
    #check_code()
    #hebing()
    #_jieba_("")
    #tiqu_cname_r1()
    #guolv()
    #read_bin_file()
    #print compute_code("MA005APC")
    #jinzhi()
    #read_MA()