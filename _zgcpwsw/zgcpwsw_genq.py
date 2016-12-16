#!/usr/bin/python
#-*- coding: utf-8 -*-

from __future__ import division
import sys
sys.path.append(sys.path[0]+"/../")
import datetime
import copy
import json
import threading
import math
import time
import re
import signal
import os
import Queue

from spider.spider import Spider
from spider.savebin import FileSaver
from spider.httpreq import CurlReq, SessionRequests
from spider.runtime import Runtime
import spider.util


class ZGcpwswData:

    upload_dates = {
        "upload_start_date": "2015-01-01",
        # do not search the end day
        "upload_end_date": "2016-02-29",
        "interval_date": 0
    }

    urls = {
        "referer_url": "http://wenshu.court.gov.cn/list/list",
        "list_url": "http://wenshu.court.gov.cn/List/ListContent",
        "content_url": "http://wenshu.court.gov.cn/content/content?DocID=",
    }

    yunsuo_cookie = "yunsuo_session_verify=7f8b8a092f63d339030b82bf84000d26;"

    post_data = {
        "Param": "search_params",
        "Index": "page_index",
        "Page": "5",
        "Order": "data_order",
        "Direction": "order_direction"
    }

    total_core_record = 500
    total_max_record = 1000

    page_max_index = 25
    page_max_count = 20

    search_params = {
        "search_upload_date": "上传日期:start_date TO end_date,",
        "search_court_level": "法院层级:court_level,",
        "search_higher_courts": "法院地域:higher,",
        "search_intermediate_courts": "中级法院:intermediate,",
        "search_primary_courts": "基层法院:primary,"
    }

    court_level = {
        "supreme": "最高法院",
        "higher": "高级法院",
        "intermediate": "中级法院",
        "primary": "基层法院"
    }

    data_order = {
        "court_level": "法院层级",
        "trial_date": "裁判日期",
        "trial_program": "审判程序"
    }

    order_direction = {
        "asc": "asc",
        "desc": "desc"
    }

    doc_id = u"文书ID"
    ##for record
    thread_lock = threading.RLock()
    supreme_count = 0
    higher_count = 0
    intermediate_count = 0
    primary_count = 0
    schedule = 0
    job_count = 0
    court_count = 0

    @staticmethod
    def set_count(jobid, count, file):
        print json.dumps(jobid.get("data"), ensure_ascii=False)
        if isinstance(jobid, dict) and isinstance(file, FileSaver):
            if count > ZGcpwswData.total_core_record:
                count = 0

            with ZGcpwswData.thread_lock:
                ZGcpwswData.schedule += 1
                ZGcpwswData.primary_count += count
            info = "%d : %d : %d : %f"%(ZGcpwswData.job_count, ZGcpwswData.primary_count, ZGcpwswData.schedule, time.time())
            file.append(info)
            """
            if "supreme" == type:
                ZGcpwswData.supreme_count += count
            elif "higher" == type:
                ZGcpwswData.higher_count += count
            elif "intermediate" == type:
                ZGcpwswData.intermediate_count += count
            elif "primary" == type:
                ZGcpwswData.primary_count += count
            """
    @staticmethod
    def set_doc_count(data, len, file):
        print json.dumps(data, ensure_ascii=False)
        if isinstance(data, dict) and isinstance(file, FileSaver):

            with ZGcpwswData.thread_lock:
                ZGcpwswData.schedule += 1
                ZGcpwswData.court_count += len
            info = "%d : %d : %f"%(ZGcpwswData.court_count, ZGcpwswData.schedule, time.time())
            file.append(info)
    ## for record

    @staticmethod
    # 返回时间列表，day_interval间隔时间
    def get_days_list_by_interval(start_date_str, end_date_str, day_interval=1):
        days_list = []

        if day_interval > 0:
            # if interval is given
            format = "%Y-%m-%d"
            start_date = datetime.datetime.strptime(start_date_str, format)
            start_date_temp = copy.deepcopy(start_date)
            end_date = datetime.datetime.strptime(end_date_str, format)
            end_date_temp = copy.deepcopy(end_date)
            days = datetime.timedelta(day_interval)

            day_counts = 0
            while start_date_temp < end_date_temp and start_date_temp != end_date_temp:
                end_date_temp = end_date_temp - days
                day_counts += 1

            for i in range(0, day_counts + 1):
                if start_date_temp < end_date:
                    days_list.append(str(start_date_temp)[0:10])
                else:
                    days_list.append(str(end_date)[0:10])
                start_date_temp = start_date_temp + days
        else:
            #if day_interval less than 0
            days_list.append(start_date_str[0:10])
            days_list.append(end_date_str[0:10])

        return days_list


    @staticmethod
    # 返回时间列表，list_count返回多少个时间
    def get_days_list_by_count(start_date_str, end_date_str, list_count=2):
        days_list = []

        if list_count >= 2:
            format = "%Y-%m-%d"
            start_date = datetime.datetime.strptime(start_date_str, format)
            end_date = datetime.datetime.strptime(end_date_str, format)

            # 2015-01-01 To 2015-01-02 interval is 1, but the count of day is 2
            interval_days = (end_date - start_date).days + 1
            if interval_days > list_count or (interval_days < list_count and interval_days > 2):
                # if interval is 4 but list count is 3 or if interval gt 2 and interval is 3 but list count is 4
                # use ceil() to deal the float
                interval_days = math.ceil(interval_days / (list_count - 1))
                return ZGcpwswData.get_days_list_by_interval(start_date_str, end_date_str, int(interval_days))

            elif interval_days == list_count:
                # if interval is 4 and list count is 4, use floor() to deal the float
                interval_days = math.floor(interval_days / (list_count - 1))
                return ZGcpwswData.get_days_list_by_interval(start_date_str, end_date_str, int(interval_days))

            else:
                pass
        else:
            # if list count lt 2
            days_list.append(start_date_str[0:10])
            days_list.append(end_date_str[0:10])

        return days_list


class ZGcpwswBasic(Spider):
    # 用于添加更新定时更新代理ip线程
    def __init__(self, thcnt, is_update_proxy=False):
        Spider.__init__(self, thcnt)
        # proxy thread
        self._proxy = None
        self.is_update_proxy = is_update_proxy

    def run(self, async=False):
        # add read proxy cfg thread
        if self.is_update_proxy:
            self._proxy = threading.Thread(target=self.update_proxy)
            self._proxy.start()
            Runtime.set_thread_name(self._proxy.ident, "%s.job.proxy" % self._name)
            # for finishing load proxy
            time.sleep(2)
        Spider.run(self, async)
        if self.is_update_proxy:
            self._proxy.join()

    def update_proxy(self):
        check_interval = 0
        while True:
            time.sleep(float(check_interval))
            try:
                with open("proxy_cfg", "r") as proxy_fs:
                    cfg = eval(proxy_fs.readline().strip())
                    if isinstance(cfg, dict):
                        check_interval = cfg.get("check")
                        url = cfg.get("proxy_url")

                        resp = self.request_url(url)
                        if isinstance(resp, CurlReq.Response) and resp and resp.content:
                            print "==== begin proxies loaded ===="
                            proxy_list = resp.content.split("|")
                            with self.locker:
                                self.sp_proxies.clear()
                                for proxy in proxy_list:
                                    self.sp_proxies[proxy] = 0
                                self._cur_proxy_index = -1
                                self._auto_change_proxy = True

                            print "==== %d proxies loaded ====" % len(self.sp_proxies.keys())
                            continue
            except Exception:
                pass

            check_interval = 0
            if self._end_mark:
                return


class ZGcpwswQueries(ZGcpwswBasic):

    def __init__(self, thcnt, need_srl=True):
        ZGcpwswBasic.__init__(self, thcnt)
        # for query save
        self.temp_fs = FileSaver("log")
        self.lc_fs = FileSaver("court_queries/large_count")
        self.mc_fs = FileSaver("court_queries/medium_count")
        self.sc_fs = FileSaver("court_queries/small_count")
        self.jl_fs = FileSaver("court_queries/job_list")
        self.ral_fs = FileSaver("court_queries/re_add_list")
        self.select_user_agent("firefox")
        #
        self.srl = {}
        self.need_srl = need_srl

        """
        copy_data = {
            "Param": "上传日期:2015-11-01 TO 2015-11-02,中级法院:黑龙江省齐齐哈尔市中级人民法院",
            "Index": "1",
            "Page": "5",
            "Order": "法院层级",
            "Direction": "asc"
        }
        """

    def dispatch(self):
        # read higher, intermediate, primary courts from file
        search_dates = ZGcpwswData.get_days_list_by_interval(ZGcpwswData.upload_dates["upload_start_date"], ZGcpwswData.upload_dates["upload_end_date"], ZGcpwswData.upload_dates["interval_date"])
        with open("courts_dict/gov_courts", "r") as courts_file:
            for line in courts_file:
                court = eval(line.strip())
                if isinstance(court, dict):
                    type = court.get("type")
                    name = court.get("name")

                    # construct post data
                    copy_headers = {"Referer": ZGcpwswData.urls["referer_url"]}
                    copy_data = {}
                    copy_data.update(ZGcpwswData.post_data)
                    copy_data["Order"] = ZGcpwswData.data_order["trial_date"]
                    copy_data["Direction"] = ZGcpwswData.order_direction["asc"]
                    copy_data["Index"] = 1
                    param = ZGcpwswData.search_params["search_upload_date"] + ZGcpwswData.search_params["search_court_level"]

                    if "supreme" == type:
                        # Param:上传日期:2016-01-27 TO 2016-01-28,法院层级:最高法院
                        param = param.replace("court_level", ZGcpwswData.court_level[type])

                    elif "higher" == type or "intermediate" == type or "primary" == type:
                        # Param:上传日期:2016-01-27 TO 2016-01-28,法院层级:高级法院,法院地域:北京市
                        # Param:上传日期:2016-01-27 TO 2016-01-28,法院层级:中级法院,中级法院:北京市第一中级人民法院
                        # Param:上传日期:2016-01-27 TO 2016-01-28,法院层级:基层法院,基层法院:北京市石景山区人民法院
                        param += ZGcpwswData.search_params[("search_" + type + "_courts")]
                        param = param.replace("court_level", ZGcpwswData.court_level[type])
                        param = param.replace(type, name)
                    else:
                        pass

                    # do not search the end day
                    for i in range(len(search_dates) - 1):
                        start_date = search_dates[i]
                        end_date = search_dates[i + 1]

                        copy_param = param.replace("start_date", start_date)
                        copy_param = copy_param.replace("end_date", end_date)
                        copy_data["Param"] = copy_param

                        flag_param = {"type": type, "start_date": start_date, "end_date": end_date}
                        jobid = {
                            "flag_param": flag_param,
                            "url": ZGcpwswData.urls["list_url"],
                            "data": copy_data,
                            "headers": copy_headers
                        }

                        self.jl_fs.append(json.dumps(jobid, ensure_ascii=False))
                        self.add_main_job(jobid)
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):
        if isinstance(jobid, dict):
            url = jobid.get("url")
            data = jobid.get("data")
            headers = jobid.get("headers")
            resp = None
            try:
                if self.need_srl:
                    nr = self.srl.get(getattr(self._tls, 'tid', 0))
                else:
                    nr = self.get_session_request()
                    self.set_cookie_passport(nr)
                # 由于文书网系统升级，所以每次请求前需要再请求两次，用于获取cookie passport
                resp = nr.request_url(url, data=data, headers=headers)
                if isinstance(resp, CurlReq.Response) and resp and resp.content:
                    result_list = json.loads(json.loads(resp.content))
                    if result_list:
                        for result in result_list:
                            if result.get("Count"):

                                count = int(result.get("Count"))
                                # for record
                                ZGcpwswData.set_count(jobid, count, self.temp_fs)
                                # for record

                                if 0 < count <= ZGcpwswData.total_core_record:
                                    self.split_post_data(jobid, count, self.sc_fs)
                                    return

                                elif ZGcpwswData.total_core_record < count <= ZGcpwswData.total_max_record:
                                    # for avoid queue2 too large
                                    time.sleep(1)
                                    self.split_post_data(jobid, count, self.mc_fs)
                                    return

                                elif count > ZGcpwswData.total_max_record:
                                    time.sleep(1)
                                    self.split_post_data(jobid, count, self.lc_fs)
                                    return
                                else:
                                    return
                            else:
                                pass
                    else:
                        pass
                else:
                    # owing to network, return None, add to job
                    pass
            except Exception, e:
                # print "%s-%s"%(resp.text, data)
                pass

            time.sleep(1)
            self.ral_fs.append(json.dumps(jobid, ensure_ascii=False))
            # self.re_add_job(jobid)

    # 细分参数，由于该网站一个法院一天只能查看500条数据
    def split_post_data(self, jobid, count, file=None):
        query = {"count": count, "jobid": jobid}
        if count > ZGcpwswData.total_core_record and isinstance(jobid, dict):
            start_date_str = jobid.get("flag_param").get("start_date")
            end_date_str = jobid.get("flag_param").get("end_date")
            # ceil(700/500) = 2，need to create 3 date value for 2 interval
            list_count = math.ceil(count / ZGcpwswData.total_core_record) + 1
            search_dates = ZGcpwswData.get_days_list_by_count(start_date_str, end_date_str, list_count)

            # 如果返回的时间列表为空或者小于2
            if not search_dates or len(search_dates) <= 2:
                if count <= ZGcpwswData.total_max_record:
                    self.mc_fs.append(json.dumps(query, ensure_ascii=False))
                else:
                    self.lc_fs.append(json.dumps(query, ensure_ascii=False))
                return

            # do not search the end day
            for i in range(len(search_dates) - 1):
                copy_jobid = copy.deepcopy(jobid)
                start_date = search_dates[i]
                end_date = search_dates[i + 1]

                param = copy_jobid.get("data").get("Param")
                param = param.replace(start_date_str, start_date)
                param = param.replace(end_date_str, end_date)
                copy_jobid["data"]["Param"] = param
                copy_jobid["flag_param"]["end_date"] = end_date
                copy_jobid["flag_param"]["start_date"] = start_date

                self.jl_fs.append(json.dumps(copy_jobid, ensure_ascii=False))
                self.add_job(copy_jobid)

        elif count < ZGcpwswData.total_core_record:
            self.sc_fs.append(json.dumps(query, ensure_ascii=False))

    def set_cookie_passport(self, nr):
        headers = {"Referer": ZGcpwswData.urls["referer_url"]}
        # 第一次请求，返回一段js代码，用于客户端生成cookie pair(wzwstemplate=;wzwschallenge=;wzwsconfirm=;)
        resp = nr.request_url(ZGcpwswData.urls["referer_url"], headers=headers)
        if resp and resp.content:
            mjs = re.search('<script type="text/javascript">(.*?)</script>', resp.content, re.S)
            if mjs:
                sc = "document = {set cookie(a){console.log(a);}}, window = {innerWidth: 1024, innerHeight: 768, screenX: 200, screenY: 100, screen: {width: 1024, height: 768}}\n"
                sc += mjs.group(1)
                #执行js代码
                rv = spider.util.runjs(sc)
                for ck in re.split('\n', rv):
                    ck = ck.strip()
                    if ck:
                        nr.add_cookie_line('wenshu.court.gov.cn', ck)
                nr.request_url(ZGcpwswData.urls["referer_url"], headers=headers, allow_redirects=0)
                return True
        return False

    # 获取SessionRqquests
    def get_session_request(self):
        sr = SessionRequests()
        with self.locker:
            if not isinstance(self.sp_proxies, dict) or len(self.sp_proxies.keys()) == 0:
                return sr
            if self._auto_change_proxy:
                prs = self.sp_proxies.keys()
                for i in range(0, len(prs)):
                    self._cur_proxy_index = (self._cur_proxy_index+1) % len(prs)
                    selproxy = prs[self._cur_proxy_index]
                    if self.sp_proxies.get(selproxy, 0) <= 10:
                        sr.set_proxy(selproxy, index=0, auto_change=False)
                        break
            elif self._cur_proxy_index < 0:
                pass
                # don't auto change proxy, and the index < 0, no proxy is used.
                # but don't report an error.
            else:
                prs = self.sp_proxies.keys()
                selproxy = prs[self._cur_proxy_index % len(prs)]
                self.set_proxy(selproxy, index=0, auto_change=False)
        return sr

    #　为每个线程绑定一个cookie
    def thread_init(self, tid):
        if self.need_srl:
            sr = self.get_session_request()
            try:
                pass
                self.set_cookie_passport(sr)
                self.srl[tid] = sr
            except Exception, e:
                print e
                time.sleep(5)
                self.thread_init(tid)
        else:
            pass

    # 处理几个系统信号量
    def register_signal(self):
        fun = lambda signo, frame: genq.signal_handler(signo)
        signal.signal(signal.SIGINT, fun)
        signal.signal(signal.SIGTSTP, fun)

    def signal_handler(self, signo):
        while True:
            try:
                jobid = self.job_queue.get_nowait()
                self.job_queue.task_done()
                self.ral_fs.append(json.dumps(jobid, ensure_ascii=False))
            except Queue.Empty:
                break

        while True:
            try:
                jobid = self.job_queue2.get_nowait()
                self.job_queue2.task_done()
                self.ral_fs.append(json.dumps(jobid, ensure_ascii=False))
            except Queue.Empty:
                break

        while True:
            try:
                jobid = self.job_queue3.get_nowait()
                self.job_queue3.task_done()
                self.ral_fs.append(json.dumps(jobid, ensure_ascii=False))
            except Queue.Empty:
                break
        os.kill(os.getpid(), signal.SIGKILL)


if __name__ == "__main__":

    spider.util.use_utf8()
    genq = ZGcpwswQueries(999)
    genq.load_proxy("proxy", True)
    # genq = ZGcpwswQueries(1)
    # genq.set_proxy(['106.75.134.189:18889:ipin:helloipin'], index=0, auto_change=False)
    genq.run()

