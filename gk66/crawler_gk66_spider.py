#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
#sys.path.append(sys.path[0]+"/..")
print sys.path
import time
from spider.spider import Spider, AccountErrors
import re
from spider.savebin import BinSaver,FileSaver
import spider.util
import mongoengine
import sys
from spider.httpreq import SessionRequests
from score_gk66 import Score_gk66
import os
import time
import string
import urllib
import pymongo
import cookielib
import traceback
import collections
import spider.util
from bs4 import BeautifulSoup
from code_process_spider import get_code

have_get_url = set()

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

filename = None
mongoengine.connect(None, alias="gk66", host="mongodb://crawler:crawler@192.168.1.81,192.168.1.82,192.168.1.83/gaokao_crawler", socketKeepAlive=True, wtimeout=100000)

class GK66(Spider):
    """这是使用自己的多线程框架重构的gk66网站爬取代码，没有针对所有省份进行处理，只能针对特定省份的账号密码进行爬取，验证码也是手动的，未进行处理"""
    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        self.request = SessionRequests()
        self.view_state = None
        self.event_valid = None
        self.rand = None
        self.loc = "浙江"
        self.data_file = FileSaver("浙江_data.txt")
        self.have_get_url_file = FileSaver("浙江_get_url.txt")
        self.init_already()
        self.login("38037395", "773950")

    def init_already(self):
        cnt = 0
        with open("浙江_get_url.txt") as f:
            for line in f:
                line = line.strip()
                have_get_url.add(line)
                cnt += 1
        print "初始化已经爬过的链接 ", cnt

    def login(self, username, password):
        # 验证码
        captcha_url = "http://14wj.gk66.cn/ashx/code.ashx"
        rand = None
        while True:
            res = self.request.request_url(captcha_url)
            if res is not None and res.code == 200:
                spider.util.FS.dbg_save_file("captcha.jpeg", res.content)
                rand = raw_input("login －－－＞　请输入验证码：") #get_code(res.text) #
                if rand == "retry":
                    continue
                #break

                login_url = "http://14wj.gk66.cn/ashx/login.ashx"
                data = {"username": username,
                        "password": password,
                        "rand": rand,
                        "rempass": "off"}
                while True:
                    con = self.request.request_url(login_url, data=data)
                    if con is None or con.code != 200:
                        continue
                    content = con.content
                    r_type = eval(content)[0]["type"]
                    if r_type == "2":
                        print "登陆失败：", spider.util.utf8str(content)
                        if u"验证码错误".encode("gb2312") in content:
                            break
                        continue
                    else:
                        self.view_state, self.event_valid = self.prepare_param()
                        self.rand = self.prepare_rand()
                        if self.view_state is None or self.event_valid is None or self.rand is None:
                            print "－－－未获取到view_state　event_valid　rand　－－－"
                            continue
                        print "登陆成功..."
                        return
                continue
            else:
                print "login　获取验证码图片失败,", "res is None" if res is None else "res.code = %d" % res.code

        # login_url = "http://14wj.gk66.cn/ashx/login.ashx"
        # data = {"username": username,
        #         "password": password,
        #         "rand": rand,
        #         "rempass": "off"}
        # while True:
        #     con = self.request.request_url(login_url, data=data)
        #     if con is None or con.code != 200:
        #         continue
        #     content = con.content
        #     r_type = eval(content)[0]["type"]
        #     if r_type == "2":
        #         print "登陆失败：", spider.util.utf8str(content)
        #         continue
        #     else:
        #         self.view_state, self.event_valid = self.prepare_param()
        #         self.rand = self.prepare_rand()
        #         if self.view_state is None or self.event_valid is None or self.rand is None:
        #             print "－－－未获取到view_state　event_valid　rand　－－－"
        #             continue
        #         print "登陆成功..."
        #         break

    def prepare_param(self):
        search_url = "http://14wj.gk66.cn/wj/fs.aspx"
        res = self.request.request_url(search_url)
        if res is not None and res.code == 200:
            fs_page = res.content
            soup = BeautifulSoup(fs_page, 'html5lib')
            view_state = soup.find(attrs={'id':"__VIEWSTATE"}).get("value")
            event_valid = soup.find(attrs={'id':"__EVENTVALIDATION"}).get("value")
            print "view_state=", view_state, "event_valid=", event_valid
            return view_state, event_valid
        return None, None

    def prepare_rand(self):
        global FILE_NAME_1
        captcha_url_2 = "http://14wj.gk66.cn/ashx/codewj.ashx"
        while True:
            con = self.request.request_url(captcha_url_2)
            if con is None or con.code != 200:
                print "prepare_rand 请求错误...","结果为空" if con is None else "http code = %d" % con.code
                continue
            spider.util.FS.dbg_save_file("captcha2.jpeg", con.content)
            rand = raw_input("prepare_rand　－－－＞　请输入验证码：") #get_code(con.content)
            if rand == "retry":
                continue
            return rand

    def logout(self):
        logout_url = "http://www.gk66.cn/loginout.aspx"
        self.request.request_url(logout_url)

    def wait_q_breakable(self):
        lt = 0
        while True:
            if not self.job_queue.empty() or not self.job_queue2.empty() or not self.job_queue3.empty():
                time.sleep(5)
            if time.time() < lt + 1 and self._running_count == 0:
                return True
            time.sleep(2)
            lt = time.time()
            if self._worker_count == 0:
                return False

    def dispatch(self):
        nf_list = ["14"]#["06" , "07", "08", "09", "10", "11"]     # 年份
        wl_list = ["w", "l"] # 文科 理科
        bz_list = ["b", "z"] # 本科 专科
        for fs in range(732, 810):
            print "分数：", fs
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
                        #print "合成请求数据：", data
                        job = {"data": data}
                        self.add_main_job(job)
                        time.sleep(0.1)
        self.wait_q_breakable()
        self.add_job(None, True)



    def run_job(self, job):
        data = job["data"]
        data["__VIEWSTATE"] = self.view_state
        data["__EVENTVALIDATION"] = self.event_valid
        data["rand"] = self.rand
        retry = 3
        while retry >= 0:
            try:
                self.loop_exec(data)
                break
            except:
                traceback.print_exc()
                print "出错,sleep 1s"
                time.sleep(1)
                retry-=1
                try:
                    self.logout()
                except:
                    pass
                self.login("38037395", "773950")

    def loop_exec(self, data):
        try:
            while True:
                url = self.build_search_url(data)
                if url != None:
                    break
                else:
                    self.login("38037395", "773950")
        except Exception as e:
            print "build_search_url　failure ...", e
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
            datas = self.get_score_data(exec_url, page_break=page_break)
            if len(datas) < 20:
                page_break = True
            for v in datas:
                if v is None:
                    page_break = True
                    break
                v["location"] = self.loc
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
                self.data_file.append(spider.util.utf8str(v))
                #store_score(k, v)
        self.recorde_spided(url)

    def recorde_spided(self, url):
        self.have_get_url_file.append(url)
        have_get_url.add(url)


    def get_score_data(self, data_url, page_break=False):
        try:
            page_content = None
            while True:
                res = self.request.request_url(data_url)
                if res is not None and res.code == 200:
                    page_content = res.content
                    if u"对不起,请先登录".encode("gb2312") in page_content:
                        self.logout()
                        self.login("38037395", "773950")
                        continue
                    break
                else:
                    print "获取页面出错＞．．", "res is None" if res is None else "res.code == %d " % res.code
                    continue
            datas = []
            if string.find(page_content, u"相近分数".encode("gb2312")) > 0:
                print "该页面没有数据"
                return datas
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
                        datas.append(data)
                return datas
            else:
                print "页面无内容：", page_content
        except Exception as e:
            print "get_score_data　发生异常", e
            return None


    def build_search_url(self, data):
        search_url = "http://14wj.gk66.cn/wj/fs.aspx"
        headers = {"User-Agent": "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .N ET4.0C; .NET4.0E)"}
        resp = self.request.request_url(search_url, data=data, headers=headers)
        headers = resp.headers
        m = re.search("Location:(.*)\r\n", headers)
        if m:
            location = m.group(1).strip()
            return "http://14wj.gk66.cn" + location
        else:
            return None
        #location = resp.headers["Location"]


    def store_score(self, value):
        print filename+' being write-->', value
        obj=Score_gk66.objects(location=value["location"],year=value["year"],bz=value["bz"],wl=value["wl"],school=value['school'],spec=value['spec'],rank=value['rank'],score=value['score'],batch=value["batch"],score_number=value['score_number'],spec_number=value['spec_number'],high_score=value['high_score'],high_score_rank=value['high_score_rank'],low_score=value['low_score'],low_score_rank=value['low_score_rank'],average_score=value['average_score'],average_score_rank=value['average_score_rank']).no_cache().timeout(False).first()
        if not obj:
            obj=Score_gk66(location=value["location"],year=value["year"],bz=value["bz"],wl=value["wl"],school=value['school'],spec=value['spec'],rank=value['rank'],score=value['score'],batch=value["batch"],score_number=value['score_number'],spec_number=value['spec_number'],high_score=value['high_score'],high_score_rank=value['high_score_rank'],low_score=value['low_score'],low_score_rank=value['low_score_rank'],average_score=value['average_score'],average_score_rank=value['average_score_rank'])
            obj.save()
            self.num_count+=1
            print "保存成功：", value
        else:
            print u"数据已存在"


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)

if __name__ == "__main__":
    start = time.time()
    s = GK66(10)
    s.run()
    end = time.time()
