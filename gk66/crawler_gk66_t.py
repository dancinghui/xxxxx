#!/bin/usr/env python
#-*- coding: utf-8 -*-
import os

import time
import string
import urllib
import urllib2
import pymongo
import cookielib
import traceback
import collections
import spider.util
from bs4 import BeautifulSoup
from code_process import get_code

# ACCOUNTS = {"安徽":["38209827", "245159"]}
acc = collections.OrderedDict()
#acc["北京"]=["38217744", "540227"]
# acc["天津"]= ["38157304", "641474"]
# acc["河北"]= ["38057560", "427718"]
# acc["山西"]= ["38222253", "131356"]
# acc["内蒙古"]= ["38208375", "818381"]
# acc["辽宁"]=["38197440", "631816"]
# acc["吉林"]= ["38193610", "115689"]
# acc["黑龙江"]= ["38175767", "805178"]
acc["浙江"]= ["38037395", "773950"]
# acc["安徽"]= ["38209827", "245159"]
# acc["福建"]= ["38230839", "012006"]
# acc["江西"]= ["38139963", "044143"]
# acc["山东"]= ["38044642", "463353"]
# acc["河南"]= ["38065897", "894586"]
# acc["湖北"]= ["38067435", "730998"]
# acc["湖南"]= ["38115296", "049631"]
# acc["广东"]= ["07125593", "825304"]
# acc["重庆"]= ["38481118", "946106"]
# acc["四川"]=  ["38484796", "935158"]
# acc["贵州"]=   ["38496482", "331626"]
# acc["云南"]=  ["38506015", "399980"]
# acc["西藏"]=  ["38542875", "353275"]
# acc["陕西"]= ["38558805", "105871"]
#acc["甘肃"]=  ["38558945", "740773"]
#acc["青海"]=  ["38562829", "716859"]
#acc["宁夏"]= ["38566547", "956459"]
#acc["新疆"]=  ["38601271", "129483"]
# acc["江苏"]= ["38225005", "436728"] #1-480
# acc["海南"]=  ["38479419", "921847"] #1-900
# acc["广西"]=  ["32712146", "797688"] #fail

FILE_NAME_1 = ""

have_get_url_file = None
have_get_url = set()
proxy = 'http://ipin:helloipin@192.168.1.39:3428'

class NoRedirection(urllib2.HTTPErrorProcessor):
    def http_response(self, request, response):
        return response
    https_response = http_response

def do_get(opener, url):
    req = urllib2.Request(url)
    # op = urllib2.build_opener(urllib2.ProxyHandler({"http":proxy}))
    # urllib2.install_opener(op)
    req.add_header("User-Agent", "Mozilla/4.0 (compatible; MSIE 7.0;"
         " Windows NT 5.1; Trident/4.0; "
         ".NET CLR 2.0.50727; .N ET4.0C; .NET4.0E)")
    resp = opener.open(req)
    return resp.read()


def do_post(opener, url, data):
    req = urllib2.Request(url, data)
    req.add_header("User-Agent", "Mozilla/4.0 (compatible; MSIE 7.0;"
         " Windows NT 5.1; Trident/4.0; "
         ".NET CLR 2.0.50727; .N ET4.0C; .NET4.0E)")
    resp = opener.open(req)
    return resp.read()

def _do_get(opener,url):
    return func_retry(do_get, opener=opener,url=url)

def _do_post(opener,url,data):
    return func_retry(do_post,opener=opener,url=url,data=data)

def func_retry(func,**kwargs):
    retry=10
    while retry>=0:
        try:
            return func(**kwargs)
        except:
            import traceback
            traceback.print_exc()
            retry-=1
            time.sleep(10-retry)
    raise RuntimeError("重复3次超时")

def login(opener, username, password):
    # 验证码
    global FILE_NAME
    captcha_url = "http://14wj.gk66.cn/ashx/code.ashx"
    captcha = _do_get(opener, captcha_url)
    # captcha_file = open(FILE_NAME, "wb")
    # captcha_file.truncate(0)
    # captcha_file.write(captcha)
    # captcha_file.close()
    rand=get_code(captcha)
    # print "please input the captcha code"
    # line = sys.stdin.readline()
    # print line
    # if line:
    #     rand = line[ : -1]

    login_url = "http://14wj.gk66.cn/ashx/login.ashx"
    data = {"username": username,
            "password": password,
            "rand":     rand,
            "rempass":  "off"}
    content = _do_post(opener, login_url, urllib.urlencode(data))
    r_type = eval(content)[0]["type"]
    print "登陆结果：", spider.util.utf8str(content)
    if r_type == "2":
        logout(opener)
        login(opener, username, password)
    else:
        print "登陆成功..."

def logout(opener):
    logout_url = "http://www.gk66.cn/loginout.aspx"
    _do_get(opener, logout_url)

def prepare_param(opener):
    search_url = "http://14wj.gk66.cn/wj/fs.aspx"
    fs_page = _do_get(opener, search_url)
    soup = BeautifulSoup(fs_page, 'html5lib')
    view_state = soup.find(attrs={'id':"__VIEWSTATE"}).get("value")
    event_valid = soup.find(attrs={'id':"__EVENTVALIDATION"}).get("value")
    print view_state, event_valid
    return view_state, event_valid

def prepare_rand(opener):
    global FILE_NAME_1
    captcha_url_2 = "http://14wj.gk66.cn/ashx/codewj.ashx"
    captcha_2 = _do_get(opener, captcha_url_2)
    rand=get_code(captcha_2)
    # captcha_file = open(FILE_NAME_1, "wb")
    # captcha_file.truncate(0)
    # captcha_file.write(captcha_2)
    # captcha_file.close()

    # print "please input the captcha2 code"
    # line = sys.stdin.readline()
    # print line
    # if line:
    #     rand = line[ : -1]
    return rand

def build_post_data():
    nf_list = ["14"]#["06" , "07", "08", "09", "10", "11"]     # 年份
    wl_list = ["w", "l"] # 文科 理科
    bz_list = ["b", "z"] # 本科 专科
    #wl_list = ["l"] # 文科 理科
    #bz_list = ["z"] # 本科 专科
    for fs in range(0, 810):
        print fs
        for nf in nf_list:
            for wl in wl_list:
                for bz in bz_list:
                    data = {
                            "fs": fs,
                            "nf": nf,
                            "wl": wl,
                            "bz": bz,
                            "pc": "",
                            "ImageButton1.x": 98,
                            "ImageButton1.y": 13}
                    print data
                    yield data

def build_search_url(opener, data):
    search_url = "http://14wj.gk66.cn/wj/fs.aspx"
    req = urllib2.Request(search_url, urllib.urlencode(data))
    req.add_header("User-Agent", "Mozilla/4.0 (compatible; MSIE 7.0;"
         " Windows NT 5.1; Trident/4.0; "
         ".NET CLR 2.0.50727; .N ET4.0C; .NET4.0E)")
    resp = opener.open(req)
    location = resp.headers["Location"]
    return "http://14wj.gk66.cn" + location
    #for page in range(1, 10000):
    #    url = result_url + "&s=0&page=" + str(page)
    #    yield url
    #print _do_get(opener, result_url)

def get_score_data(opener, data_url, page_break=False):
    try:
        page_content = _do_get(opener, data_url)
        if string.find(page_content, u"相近分数".encode("gb2312")) > 0:
            print "该页面没有数据"
            yield None
        soup = BeautifulSoup(page_content, 'html5lib')
        rows = soup.findAll("tr")
        if rows is not None and len(rows) > 0:
            if len(rows) != 20:
                page_break = True
            for row in rows:
                cols = row.findAll("td")
                if cols is not None and len(cols) == 13:
                    data = {}
                    data["school"]              = cols[0].getText()
                    data["spec"]                = cols[1].getText()
                    data["rank"]                = cols[2].getText()
                    data["score"]               = cols[3].getText()
                    data["batch"]               = cols[4].getText()
                    data["score_number"]        = cols[5].getText()
                    data["spec_number"]         = cols[6].getText()
                    data["high_score"]          = cols[7].getText()
                    data["high_score_rank"]     = cols[8].getText()
                    data["low_score"]           = cols[9].getText()
                    data["low_score_rank"]      = cols[10].getText()
                    data["average_score"]       = cols[11].getText()
                    data["average_score_rank"]  = cols[12].getText()
                    yield data
        else:
            print "页面内容：", page_content
            raise Exception("no data found")
    except Exception, e:
        import traceback
        traceback.print_exc()
        raise Exception("unkown exception")

def store_score(key, value):
    conn = pymongo.Connection("192.168.1.83", 27017)
    db = conn.gaokao_crawler #连接库
    db.authenticate("crawler", "crawler")
    db.gk66_score_2.update(key, {"$set": value}, upsert=True)
    conn.close()

def loop_exec(opener, data, loc):
    try:
        url = build_search_url(opener, data)
    except:
        return
    page_break = False
    last_v = {}
    if url in have_get_url:
        print "已经爬取，pass"
        return
    if "http://14wj.gk66.cn/login.aspx?" in url:
        raise RuntimeError()
    for page in range(1, 1000):
        if page_break:
            break
        exec_url = url + "&s=0&page=" + str(page)
        print "执行链接：", exec_url
        for v in get_score_data(opener, exec_url, page_break=page_break):
            if v is None:
                page_break = True
                break
            v["location"] = loc
            v["year"]     = data["nf"]
            v["wl"]       = data["wl"]
            v["bz"]       = data["bz"]
            if (str(last_v) == str(v)):
                page_break = True
                break
            last_v = v
            k = {
                    "location": v["location"],
                    "school": v["school"],
                    "spec": v["spec"],
                    "batch": v["batch"], # 批次
                    "score": v["score"],
                    "year": v["year"],
                    "wl": v["wl"],
                    "bz": v["bz"]
                }
            print v
            data_file.write(spider.util.utf8str(v) + "\n")
            #data_file.write(str(v)+"\n")
            #store_score(k, v)
    have_get_url_file.write(url+"\n")

def crawler(loc):
    """
    crawler process steps
    step 1: login
    step 2: captcha 1
    step 3: captcha 2
    step 4: build post data
    step 5: get data page and parse
    step 6: store data into mongodb
    step 7: logout
    """
    global acc
    try:
        opener, view_state, event_valid, rand = init_opener(loc)
        for data in build_post_data():
            data["__VIEWSTATE"] = view_state
            data["__EVENTVALIDATION"] = event_valid
            data["rand"] = rand
            retry = 3
            while retry >= 0:
                try:
                    loop_exec(opener, data, loc)
                    break
                except:
                    traceback.print_exc()
                    print "出错,sleep 1s"
                    time.sleep(1)
                    retry-=1
                    try:
                        logout(opener)
                    except:
                        pass
                    opener, view_state, event_valid, rand = init_opener(loc)
        logout(opener)
    except Exception as e:
        traceback.print_exc()
        print e
        # logout(opener)
        raise RuntimeError()

def init_opener(loc):
    retry=3
    while retry>=0:
        try:
            cookieJar = cookielib.CookieJar()
            handlerCookie = urllib2.HTTPCookieProcessor(cookieJar)
            handlerDebug = urllib2.HTTPHandler(debuglevel=0)
            proxyHandler = urllib2.ProxyHandler({"http": proxy})
            opener = urllib2.build_opener(NoRedirection, handlerCookie, handlerDebug, proxyHandler)
            login(opener, acc[loc][0], acc[loc][1])
            view_state, event_valid = prepare_param(opener)
            rand = prepare_rand(opener)
            return opener,view_state,event_valid,rand
        except:
            retry-=1

def main():
    global FILE_NAME, FILE_NAME_1
    dir=os.path.dirname(__file__)

    for loc in acc:
        FILE_NAME = loc + ".jpg"
        FILE_NAME_1 = loc + "_1.jpg"
        if os.path.exists(os.path.join(dir, "%s_get_url.txt" % loc)):
            with open(os.path.join(dir, "%s_get_url.txt" % loc)) as f:
                while True:
                    line = f.readline()
                    if not line: break
                    have_get_url.add(line.strip().split("&s=0&page=")[0])
        global data_file,have_get_url_file
        have_get_url_file = open(os.path.join(dir, "%s_get_url.txt"%loc), "a")
        data_file = open(os.path.join(dir, "%s_data.txt"%loc), "a")
        crawler(loc)
        have_get_url_file.close()
        data_file.close()

if __name__ == "__main__":
    main()
