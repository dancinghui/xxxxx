#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(sys.path[0]+"/../")
import copy
import json
import time
import re
import os


from spider.httpreq import CurlReq, SessionRequests
import spider.util
from spider.spider2 import Spider2
from spider.savebin import FileSaver
from spider.savebin import BinSaver
from zgcpwsw_genq import ZGcpwswData

class ZGcpwswSpider2(Spider2):

    def __init__(self, thcnt, need_srl=True, qf_name=None):
        Spider2.__init__(self, thcnt)
        #
        self.ce_fs = FileSaver("court_queries/check_error")
        self.docbin_fs = BinSaver("ws_data/ws.%d.bin"% os.getpid())
        self.log_fs = FileSaver("log")
        #
        self.qf_name = qf_name
        self._name = "%s"% self.qf_name.split("/")[1]
        self.srl = {}
        self.need_srl = need_srl
        pass

    def init_jobs(self):
        with open(self.qf_name) as fs:
            for line in fs:
                job = eval(line.strip())
                count = job.get("count")
                if count > ZGcpwswData.total_max_record:
                    for i in ZGcpwswData.data_order:
                        for j in ZGcpwswData.order_direction:
                            for k in range(ZGcpwswData.page_max_index):
                                copy_job = copy.deepcopy(job)
                                copy_job["jobid"]["data"]["Index"] = k + 1
                                copy_job["jobid"]["data"]["Page"] = ZGcpwswData.page_max_count
                                copy_job["jobid"]["data"]["Direction"] = ZGcpwswData.order_direction[j]
                                copy_job["jobid"]["data"]["Order"] = ZGcpwswData.data_order[i]
                                self.add_job(copy_job)

                elif ZGcpwswData.total_core_record < count <= ZGcpwswData.total_max_record:
                    for j in ZGcpwswData.order_direction:
                        for k in range(ZGcpwswData.page_max_index):
                            copy_job = copy.deepcopy(job)
                            copy_job["jobid"]["data"]["Index"] = k + 1
                            copy_job["jobid"]["data"]["Page"] = ZGcpwswData.page_max_count
                            copy_job["jobid"]["data"]["Direction"] = ZGcpwswData.order_direction[j]
                            self.add_job(copy_job)

                elif 0 < count <= ZGcpwswData.total_core_record:
                    for k in range(ZGcpwswData.page_max_index):
                        copy_job = copy.deepcopy(job)
                        copy_job["jobid"]["data"]["Index"] = k + 1
                        copy_job["jobid"]["data"]["Page"] = ZGcpwswData.page_max_count
                        self.add_job(copy_job)

        print "=======finish loading job======"

    def run_job(self, jobid):
        time.sleep(0.1)
        if isinstance(jobid, dict):
            url = jobid.get("jobid").get("url")
            data = jobid.get("jobid").get("data")
            headers = jobid.get("jobid").get("headers")
            reg_count = int(jobid.get("count"))
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
                        # for record
                        ZGcpwswData.set_doc_count(data, len(result_list) - 1, self.log_fs)
                        # for record
                        for result in result_list:
                            if result.get("Count"):
                                new_count = int(result.get("Count"))
                                if new_count > reg_count:
                                    jobid["check_count"] = new_count
                                    self.ce_fs.append(json.dumps(jobid, ensure_ascii=False))
                            else:
                                name = '%s.%d' % (result.get(ZGcpwswData.doc_id), int(time.time()) )
                                self.docbin_fs.append(name, json.dumps(result, ensure_ascii=False))
                    else:
                        pass
                else:
                    # owing to network, return None, add to job
                    pass
            except Exception, e:
                # print "%s-%s"%(resp.text, data)
                pass

            time.sleep(1)
            self.re_add_job(jobid)

    def load_proxy(self, fn, index=-1, auto_change=False):
         self.networker.load_proxy(fn, index, auto_change)

    def event_handler(self, evt, msg, **kwargs):
        if "DONE" == evt:
            msg += "crawling %d links and save %d legal papers"%ZGcpwswData.schedule, ZGcpwswData.court_count
            spider.util.sendmail(["<lixungeng@ipin.com>"], "裁判文书网爬取完成", msg)
            return


    """
    以下代码与zgcpwsw_genq.py中的代码重复，可重新设计类的结构，采用多重继承方式
    """
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

    def get_session_request(self):
        sr = SessionRequests()
        with self.locker:
            if not isinstance(self.networker.sp_proxies, dict) or len(self.networker.sp_proxies.keys()) == 0:
                return sr
            if self.networker._auto_change_proxy:
                prs = self.networker.sp_proxies.keys()
                for i in range(0, len(prs)):
                    self.networker._cur_proxy_index = (self.networker._cur_proxy_index+1) % len(prs)
                    selproxy = prs[self.networker._cur_proxy_index]
                    if self.networker.sp_proxies.get(selproxy, 0) <= 10:
                        sr.set_proxy(selproxy, index=0, auto_change=False)
                        break
            elif self.networker._cur_proxy_index < 0:
                pass
                # don't auto change proxy, and the index < 0, no proxy is used.
                # but don't report an error.
            else:
                prs = self.networker.sp_proxies.keys()
                selproxy = prs[self.networker._cur_proxy_index % len(prs)]
                self.networker.set_proxy(selproxy, index=0, auto_change=False)
        return sr


if __name__ == "__main__":
    spider.util.use_utf8()
    s = ZGcpwswSpider2(9, False, "court_queries/large_count")
    s.load_proxy("proxy", False)
    s.run()