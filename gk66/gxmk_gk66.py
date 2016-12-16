#!/bin/usr/env python
#-*- coding: utf-8 -*-
import os
import sys
import traceback
import urllib
import urllib2
import cookielib
import mongoengine

from bs4 import BeautifulSoup

from ipin.gaokao.score.model.score_gxmk import Score_gxmk


#ACCOUNTS = {"江苏":["38225005", "436728"]}
ACCOUNTS = {
    "jilin":["38193610", "115689"],
    "guangdong":["07125593", "825304"],
}
current_loc=""
data_file=None
have_get_url_file=None

FILE_NAME_1 = ""
FILE_NAME=""

have_get_url=set()

class NoRedirection(urllib2.HTTPErrorProcessor):
    def http_response(self, request, response):
        return response
    https_response = http_response

def _do_get(opener, url):
    req = urllib2.Request(url)
    req.add_header("User-Agent", "Mozilla/4.0 (compatible; MSIE 7.0;"
         " Windows NT 5.1; Trident/4.0; "
         ".NET CLR 2.0.50727; .N ET4.0C; .NET4.0E)")
    resp = opener.open(req)
    return resp.read()


def _do_post(opener, url, data):
    req = urllib2.Request(url, data)
    req.add_header("User-Agent", "Mozilla/4.0 (compatible; MSIE 7.0;"
         " Windows NT 5.1; Trident/4.0; "
         ".NET CLR 2.0.50727; .N ET4.0C; .NET4.0E)")
    resp = opener.open(req)
    return resp.read()

def login(opener, username, password):
    # 验证码
    global FILE_NAME
    captcha_url = "http://14wj.gk66.cn/ashx/code.ashx"
    captcha = func_retry(_do_get,opener=opener, url=captcha_url)
    captcha_file = open(FILE_NAME, "wb")
    captcha_file.truncate(0)
    captcha_file.write(captcha)
    captcha_file.close()

    print "please input the captcha code"
    line = sys.stdin.readline()
    print line
    if line:
        rand = line[ : -1]
    else:
        raise RuntimeError()

    login_url = "http://14wj.gk66.cn/ashx/login.ashx"
    data = {"username": username,
            "password": password,
            "rand":     rand,
            "rempass":  "off"}
    func_retry(_do_post,opener=opener, url=login_url, data=urllib.urlencode(data))

def logout(opener):
    logout_url = "http://www.gk66.cn/loginout.aspx"
    func_retry(_do_get,opener=opener, url=logout_url)
    print "logout"

def prepare_param(opener):
    # search_url = "http://14wj.gk66.cn/wj/fs.aspx"
    search_url = "http://14wj.gk66.cn/zd/gxmk.aspx"
    fs_page=func_retry(_do_get,opener=opener, url=search_url)
    soup = BeautifulSoup(fs_page, 'html5lib')
    view_state  = soup.find(attrs={'id':"__VIEWSTATE"}).get("value")
    event_valid = soup.find(attrs={'id':"__EVENTVALIDATION"}).get("value")
    print view_state, event_valid
    return view_state, event_valid

def prepare_rand(opener):
    global FILE_NAME_1
    captcha_url_2 = "http://14wj.gk66.cn/ashx/codewj.ashx"
    captcha_2=func_retry(_do_get,opener=opener,url=captcha_url_2)
    captcha_file = open(FILE_NAME_1, "wb")
    captcha_file.truncate(0)
    captcha_file.write(captcha_2)
    captcha_file.close()

    print "please input the captcha2 code"
    line = sys.stdin.readline()
    print line
    if line:
        rand = line[ : -1]
    return rand

def get_sch_ids(opener,nf,wl,bz,pro_id):
    url="http://14wj.gk66.cn/ashx/zdajax.ashx"
    data={"nf":nf,"wl":wl,"bz":bz,"t":"gxlist","id":pro_id,"pro":current_loc}
    content=func_retry(_do_post,opener=opener, url=url, data=urllib.urlencode(data))
    pro_list=eval(content)
    for item in pro_list:
        id=item["id"]
        # name=item["name"].decode("gb2312")
        yield id

def get_prolist(opener,nf,wl,bz):
    url="http://14wj.gk66.cn/ashx/zdajax.ashx"
    data={"nf":nf,"wl":wl,"bz":bz,"t":"prolist","id":1,"pro":current_loc}
    content=func_retry(_do_post,opener=opener, url=url, data=urllib.urlencode(data))
    pro_list=eval(content)
    for item in pro_list:
        id=item["id"]
        # name=item["name"].decode("gb2312")
        yield id


def yield_param():
    nf_list = ["12","13","14"]     # 年份
    wl_list = ["w", "l"] # 文科 理科
    bz_list = ["b", "z"] # 本科 专科
    for nf in nf_list:
        for wl in wl_list:
            for bz in bz_list:
                yield nf,wl,bz

def build_post_data(view_state, event_valid, rand,opener):
    for nf,wl,bz in yield_param():
        for pro_id in get_prolist(opener,nf,wl,bz):
            for sch_id in get_sch_ids(opener,nf,wl,bz,pro_id):
                data = {"__VIEWSTATE": view_state,
                    "__EVENTVALIDATION": event_valid,
                    "nf": nf,
                    "wl": wl,
                    "bz": bz,
                    "gxdb_pro":pro_id,
                    "gxmc":sch_id,
                    "pc": "",
                    "rand": rand,
                    "ImageButton1.x": 98,
                    "ImageButton1.y": 13}
                yield data

def build_search_url(opener, data):
    search_url = "http://14wj.gk66.cn/zd/gxmk.aspx"
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

def get_score_data(opener, data_url):
    # try:
    page_content =func_retry(_do_get,opener=opener, url=data_url)
    soup = BeautifulSoup(page_content, 'html5lib')
    rows = soup.findAll("tr")
    if rows is not None and len(rows) >1:
        for row in rows[1:]:
            cols = row.findAll("td")
            if cols is not None and len(cols) == 14:
                data = {}
                data["school"]              = cols[0].getText()
                data["batch"]              = cols[3].getText()
                data["pro_score"]              = cols[4].getText()
                data["sch_score"]              = cols[7].getText()
                yield data
    else:
        yield None
    if len(rows)<4:#如果一页只有3行数据，说明下一页没有了，不用在查了
        yield None
    # except:
    #     traceback.print_exc()


def func_retry(func,**kwargs):
    retry=5
    while retry>=0:
        try:
            return func(**kwargs)
        except:
            traceback.print_exc()
            retry-=1
    raise RuntimeError("重复3次超时")

def store_score(value):
    obj=Score_gxmk.objects(location=value["location"],year=value["year"],wl=value["wl"],bz=value["bz"],school=value['school'],batch=value["batch"]).no_cache().timeout(False).first()
    if not obj:
        obj=Score_gxmk(location=value["location"],year=value["year"],wl=value["wl"],bz=value["bz"],school=value['school'],batch=value["batch"])
        obj.pro_score=float(value["pro_score"])
        obj.sch_score=float(value["sch_score"])
        obj.save()
    else:
        print u"数据已存在"

def loop_exec(opener, data, loc):
    try:
        url = build_search_url(opener, data)
    except:
        return
    page_break = False
    last_v = {}
    if url in have_get_url:
        print "已经爬去，pass"
        return
    for page in range(1, 1000):
        if page_break:
            break
        exec_url = url + "&s=0&page=" + str(page)
        print exec_url
        for v in get_score_data(opener, exec_url):
            if v is None:
                page_break = True
                break
            v["location"] = loc
            v["year"]     = data["nf"]
            v["wl"]       = 1 if data["wl"]=='w' else 2 if data["wl"]=='l' else 0
            v["bz"]       = 1 if data["bz"]=='b' else 2 if data["bz"]=='z' else 0
            if (str(last_v) == str(v)):
                page_break = True
                break
            last_v = v
            print v
            data_file.write(str(v)+"\n")
            # func_retry(store_score,value=v)
    have_get_url_file.write(url+"\n")

def crawler(loc, opener):
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
    global ACCOUNTS
    try:
        login(opener, ACCOUNTS[loc][0], ACCOUNTS[loc][1])
        view_state, event_valid = prepare_param(opener)
        rand = prepare_rand(opener)
        for data in build_post_data(view_state, event_valid, rand,opener):
            loop_exec(opener, data, loc)
        logout(opener)
    except Exception as e:
        import traceback
        traceback.print_exc()
        logout(opener)

def main(loc_list):
    global FILE_NAME, FILE_NAME_1
    cookieJar = cookielib.CookieJar()
    dir=os.path.dirname(__file__)
    handlerCookie = urllib2.HTTPCookieProcessor(cookieJar)
    handlerDebug = urllib2.HTTPHandler(debuglevel=0)
    opener = urllib2.build_opener(NoRedirection, handlerCookie, handlerDebug)
    global current_loc
    for loc in loc_list:
        current_loc=loc
        FILE_NAME = loc + ".jpg"
        FILE_NAME_1 = loc + "_1.jpg"
        if os.path.exists(os.path.join(dir,"%s_get_url.txt"%loc)):
            with open(os.path.join(dir,"%s_get_url.txt"%loc)) as f:
                while True:
                    line=f.readline()
                    if not line:break
                    have_get_url.add(line.split("&s=0&page=")[0])
        global data_file,have_get_url_file
        have_get_url_file=open(os.path.join(dir,"%s_get_url.txt"%loc),"a")
        data_file=open(os.path.join(dir,"%s_data.txt"%loc),"a")
        crawler(loc, opener)
        have_get_url_file.close()
        data_file.close()

if __name__ == "__main__":
    if len(sys.argv)>=2:
        loc_list=sys.argv[1:]
    else:
        loc_list=ACCOUNTS.keys()
    main(loc_list)
    # pdb.run(main())
