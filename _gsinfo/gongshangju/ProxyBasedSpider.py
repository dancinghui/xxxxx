#! /usr/bin/env python
# encoding:utf-8
import os
import json
from spider.spider import Spider, AccountErrors
from spider.httpreq import BasicRequests
from spider.savebin import BinSaver
from spider.runtime import Log
import spider.util
import spider.runtime
import time
import hashlib
import Queue

'''
工商总局基于代理的爬虫,代理数量决定线程数量
ProxyBasedSpider:
    prepare_proxy(self,*proxyfile):准备代理,参数是数量可变的文件路径,返回加载好的代理数量
    preproc_key(self, key):预处理搜索关键字,这里只是去掉英文字母,留下括号符
    thread_check(self):线程检查,连续出错超过三次的线程会被杀死
    thread_init(self, tid):线程开跑前的初始化工作,给每个线程初始化一个只有一个代理的BasicRequests
    get_autoname(self, job):输入联想接口,会返回公司名称list
    get_summary(self, job):搜索接口,返回相关公司信息,会有注册号和公司ID
    get_detail(self, job):公司详细信息
    get_cookie(slef):每个线程的cookie隔一段时间要换一次
    save_info(self,job,jsonobj):根据job的不同存信息
    save_fail_info(self,job):防止有些job被重加了50次以上然后丢失,重入失败的任务会被存下
    proxy_error_inc(self):代理出错数加1
    proxy_error_init(self):代理成功返回正确信息时会调用它来将代理出错数归0

ps:
总局的QueryAutoName接口出错有返回空或者返回{"ERRCODE":"0","RESULT":{}}这种空列表
总局的QuerySummary接口出错有三种情况:返回总是空(或如上的空结果列表),返回随机的一条北京地区公司的信息(信息是正确的,却不是你想查的,返回的总是那几百个北京公司),返回公司名为天津港的东东(信息随机组合)
以上情况更换Cookie和IP就好.
'''

class ProxyBasedSpider(Spider):
    def __init__(self, *proxyfile):
        threadcnt = self.prepare_proxy(*proxyfile)
        Spider.__init__(self, threadcnt)
        if not os.path.exists("data1"):
            os.makedirs("data1")
        self.namefile = open("data1/corpname." + str(time.time()).split(".")[0] + ".txt", "w+b")
        self.failfile = open("data1/fail." + str(time.time()).split(".")[0] + ".txt", "w+b")
        self.binsaver = BinSaver("data1/gsinfo"+ str(time.time()).split(".")[0] + ".bin")

    def prepare_proxy(self, *proxyfile):
        self.proxyq=Queue.Queue()
        cnt = 0;
        for file in proxyfile:
            f = open(file, "rb")
            lines = f.readlines()
            for line in lines:
                if line.strip()!="":
                    self.proxyq.put(line.strip(), False)
                    cnt+=1
        Log.info("total %d proxies." % cnt)
        return cnt

    def preproc_key(self, key):
        key = key.decode("utf-8")
        all = []
        for i in key:
            if i == "(" or i == ")":
                all.append(i)
            else:
                if ord(i) > 0x400:
                    all.append(i)
        return "".join(all)

    def dispatch(self):
        currline = 0
        skip = 310000
        endline = 400000
        f = open(os.environ['HOME'] + "/r1.txt", "r+b")
        # f = open("regNo.txt", "r+b")
        line = ""
        while currline < skip:
            line = f.readline()
            currline += 1
        while currline < endline:
            line = f.readline().strip()
            if line == "":
                break
            if line.isdigit():
                regNo = line
                areacode = regNo[0:2] + "0000"
                job = {"AreaCode": areacode, "Q": regNo, "type": "t1", "line": line, "lineno": currline}
                self.add_main_job(job)
            else:
                areacode = line.strip().split(" ")[1].strip()
                q = line.strip().split(" ")[2].strip()
                job = {"AreaCode": areacode, "Q": self.preproc_key(q),
                       "type": "QueryAutoName",
                       # "type": "QuerySummary",
                       "line": line,
                       "lineno": currline}
                self.add_main_job(job)
            currline += 1
        self.wait_q()
        self.add_main_job(None)

    def run_job(self, job):
        Log.info("Running job:" + spider.util.utf8str(job))
        # thread_check
        if self.thread_check() == False:
            # raise NoAccountError to set end_this_thread true, spider will readd the job. See Spider._job_runner
            raise AccountErrors.NoAccountError()

        if job["type"] == "QuerySummary":
            self.get_summary(job)
        elif job["type"] == "QueryDetail":
            self.get_detail(job)
        elif job["type"] == "QueryAutoName":
            self.get_autoname(job)

    def thread_check(self):
        # 3次连续错误,杀死线程
        basicreq = getattr(self._tls, "req")
        proxy_error_cnt = getattr(basicreq._curltls, "proxy_error_cnt", 0)
        if proxy_error_cnt > 3:
            Log.error("Proxy %s and its thread is going down." % (basicreq.sp_proxies.items()[0][0]))
            return False
        return True

    def thread_init(self, tid):
        # self.proxyq is threading-safe
        proxy = self.proxyq.get(True)
        basicreq = BasicRequests()
        basicreq.sp_proxies[proxy] = 0
        basicreq._cur_proxy_index = 0
        basicreq._auto_change_proxy = False
        setattr(self._tls, "req", basicreq)
        with self.locker:
            Log.info("Thread%d's request prepared..Proxy:%s" % (tid, proxy))

    def get_autoname(self, job):
        con = self.realQueryAutoName(job)
        if con is None or con.text == "" or con.code != 200:
            spider.runtime.Log.error("QueryAutoName empty back.")
            self.proxy_error_inc()
            time.sleep(10)
            if not self.re_add_job(job):
                self.save_fail_info(job)
            return
        # init proxy_error_cnt
        self.proxy_error_init()
        jsonobj = json.loads(con.text)
        self.save_info(job, jsonobj)

    def get_summary(self, job):
        spider.runtime.Log.info("line %d:%s searching...." % (job["lineno"], job["Q"]))
        con = self.realQuerySummary(job)
        if con is None or con.text.strip() == "{}":
            spider.runtime.Log.error("QuerySummary Nothing Back!!!" + spider.util.utf8str(job))
            self.proxy_error_inc()
            time.sleep(10)
            if not self.re_add_job(job):
                self.save_fail_info(job)
            return
        jsonObj = json.loads(con.text, "utf-8")
        errorcode = jsonObj.get("ERRCODE", None)
        resultObj = jsonObj.get("RESULT", None)
        if errorcode != "0" and errorcode != 0:
            spider.runtime.Log.error("QuerySummary Error!!!Error code:" + str(errorcode) + ",job:" + spider.util.utf8str(job))
            self.proxy_error_inc()
            if not self.re_add_job(job):
                self.save_fail_info(job)
            return
        if resultObj is None or len(resultObj) == 0 or resultObj.__str__().strip() == "":
            spider.runtime.Log.error("QuerySummary empty result back!!!" + spider.util.utf8str(job))
            self.proxy_error_inc()
            time.sleep(10)
            if not self.re_add_job(job):
                self.save_fail_info(job)
            return
        if ur"天津港" in con.text:
            spider.runtime.Log.error("天津港出现了!")
            self.proxy_error_inc()
            if not self.re_add_job(job):
                self.save_fail_info(job)
            return

        entId = resultObj[0].get("ID", None)
        if entId is None or entId.strip() == "":
            spider.runtime.Log.error("QuerySummary empty entId back!!!" + spider.util.utf8str(job))
            self.proxy_error_inc()
            if not self.re_add_job(job):
                self.save_fail_info(job)
            return

        self.proxy_error_init()
        for j in resultObj:
            self.save_info(job, j)
        # q = resultObj[0].get("REGNO", None)
        #     job2 = {"AreaCode": job["AreaCode"], "EntId": entId, "Q": q, "EntName":entname,"type": "t2",
        #             "line":job["line"], "lineno":job["lineno"]}
        #     self.add_job(job2)
        return

    def get_detail(self, job):
        con = self.readQueryGSInfo(job)
        if con is None or con.text.strip() == "{}":
            spider.runtime.Log.error("QueryGSInfo Nothing Back!!!" + spider.util.utf8str(job))
            self.proxy_error_inc()
            if not self.re_add_job(job):
                self.save_fail_info(job)
            return
        jsonObj = json.loads(con.text, "utf-8")
        errorcode = jsonObj.get("ERRCODE", None)
        resultObj = jsonObj.get("RESULT", None)
        if errorcode != "0" and errorcode != 0:
            spider.runtime.Log.error("QuerySummary Error!!!Error code:" + errorcode + ",job:" + spider.util.utf8str(job))
            self.proxy_error_inc()
            if not self.re_add_job(job):
                self.save_fail_info(job)
            return
        if resultObj is None or resultObj.__str__().strip() == "":
            spider.runtime.Log.error("QuerySummary empty result back!!!" + spider.util.utf8str(job))
            self.proxy_error_inc()
            if not self.re_add_job(job):
                self.save_fail_info(job)
            return
        self.proxy_error_init()
        self.binsaver.append(job["Q"] + ":" + job["EntName"], json.dumps(resultObj))
        spider.runtime.Log.info("%s:%s=========>saved." % (job["Q"], job["EntName"]))
        print spider.util.utf8str(resultObj)
        return

    def realQueryAutoName(self, job):
        cookie = self.get_cookie()
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone;8.4;iPhone;iPhone);Version/2.1.7;ISN_GSXT',
                   "Host": "gzhd.saic.gov.cn",
                   "Cookie": cookie,
                   'Connection': 'keep-alive',
                   'Accept-Language': "zh-Hans;q=1"}
        data = {"AreaCode": job["AreaCode"], "Size": 20, "Q": job["Q"]}
        before = time.time()
        basicreq = getattr(self._tls, "req")
        con = basicreq.request_url('https://120.52.121.75:8443/QueryAutoName', headers=headers, data=data)
        wait_time = 2 - (time.time() - before)
        if wait_time > 0: time.sleep(wait_time)
        return con

    def realQuerySummary(self, job):
        cookie = self.get_cookie()

        headers = {'User-Agent': 'Mozilla/5.0 (iPhone;8.4;iPhone;iPhone);Version/2.1.7;ISN_GSXT',
                   "Host": "gzhd.saic.gov.cn",
                   "Cookie": cookie,
                   'Connection': 'keep-alive',
                   'Accept-Language': "zh-Hans;q=1"}
        data = {"AreaCode": job["AreaCode"], "Limit": 50, "Page": 1, "Q": job["Q"]}
        before = time.time()
        basicreq = getattr(self._tls, "req")
        con = basicreq.request_url('https://120.52.121.75:8443/QuerySummary', headers=headers, data=data)
        wait_time = 3 - (time.time() - before)
        if wait_time > 0: time.sleep(wait_time)
        return con

    def realQueryGSInfo(self, job):
        cookie = self.get_cookie()
        data = {'AreaCode': job["AreaCode"], "EntId": job["EntId"], "EntNo": job["Q"],
                "Info": "All", 'Limit': 50, 'Page': 1, 'Q': job["Q"]}
        headers = {'User-Agent': 'Mozilla/5.0 (iPhone;8.4;iPhone;iPhone);Version/2.1.7;ISN_GSXT',
                   "Cookie": cookie,
                   'Host': 'gzhd.saic.gov.cn', 'Connection': 'keep-alive',
                   'Accept-Language': "zh-Hans;q=1"}
        before = time.time()
        basicreq = getattr(self._tls, "req")
        con = basicreq.request_url('https://120.52.121.75:8443/QueryGSInfo', headers=headers, data=data)
        wait_time = 3 - (time.time() - before)
        if wait_time > 0: time.sleep(wait_time)
        return con

    def get_cookie(self):
        cookiepair = getattr(self._tls, "cookie", None)
        # cookie 隔一段时间换一次
        if cookiepair == None:
            cookiestr = hashlib.md5(str(time.time())).hexdigest().upper()
            cookiepair = [cookiestr[:8] + '-' + cookiestr[8:12] + '-' + cookiestr[12:16]
                          + '-' + cookiestr[16:20] + '-' + cookiestr[20:],
                          time.time()]
            setattr(self._tls, "cookie", cookiepair)
        else:
            cookietime = cookiepair[1]
            if (time.time() - cookietime) > 60 * 10:
                cookiestr = hashlib.md5(str(time.time())).hexdigest().upper()
                cookiepair = [cookiestr[:8] + '-' + cookiestr[8:12] + '-' + cookiestr[12:16]
                              + '-' + cookiestr[16:20] + '-' + cookiestr[20:],
                              time.time()]
                setattr(self._tls, "cookie", cookiepair)
                Log.info("Cookie changed, sleep 10s")
                time.sleep(10)
        return cookiepair[0]

    def save_info(self, job, jsonobj):
        with self.locker:
            if job["type"] == "QuerySummary":
                name = jsonobj.get("ENTNAME", "-")
                regNo = jsonobj.get("REGNO", "-")
                id = jsonobj.get("ID", "-")
                self.namefile.write(
                        job["line"] + " " + name.encode("utf-8") + " " + regNo.encode("utf-8") + " " + id.encode(
                                "utf-8") + "\n")
                self.namefile.flush()
                self.binsaver.append(name.encode("utf-8") + "_" + regNo.encode("utf-8"), json.dumps(jsonobj))
                spider.runtime.Log.info("%s:%s=========>saved." % (job["Q"], name))
            elif job["type"] == "QueryAutoName":
                if "ERRCODE" in jsonobj:
                    if not self.re_add_job(job):
                        self.save_fail_info(job)
                    Log.error("ErrCode, proxy down.")
                    raise AccountErrors.NoAccountError()
                for name in jsonobj:
                    self.namefile.write(job["line"] + " " + name.encode("utf-8") + "\n")
                    self.namefile.flush()
                    spider.runtime.Log.info("%s:%s=========>saved." % (job["Q"], name))

    def save_fail_info(self, job):
        with self.locker:
            self.failfile.write(spider.util.utf8str(job) + " failed.\n")
            self.failfile.flush()
            spider.runtime.Log.info(spider.util.utf8str(job) + " failed.\n")

    def proxy_error_inc(self):
        # proxy_error_cnt ++
        basicreq = getattr(self._tls, "req")
        proxy_error_cnt = getattr(basicreq._curltls, "proxy_error_cnt", 0)
        setattr(basicreq._curltls, "proxy_error_cnt", proxy_error_cnt + 1)

    def proxy_error_init(self):
        basicreq = getattr(self._tls, "req")
        setattr(basicreq._curltls, "proxy_error_cnt", 0)

    def report(self):
        while True:
            time.sleep(1)  ##sleep for next report.
            if int(time.time()) % 60 == 0:
                Log.errinfo(time.strftime('%Y-%m-%d %H:%M:%S'))
                Log.errinfo("Total %d, running %d" % (self.thread_count, self._running_count))
            prog = "mj:%d/%s,aj:%d/(%d,%d,%d)" % (self._mjob_count, self._mjob_all, self._job_count,
                                                  self.job_queue.qsize(), self.job_queue2.qsize(),
                                                  self.job_queue3.qsize())

            if self._end_mark:
                message = "[pid=%d] DONE\n" % (os.getpid())
                Log.info("%s%s" % (message, prog))
                return


if __name__ == "__main__":
    spider.util.use_utf8()
    # sp = ProxyBasedSpider("ipinproxy.txt")
    sp = ProxyBasedSpider("proxy_all_uniq","ipinproxy.txt")
    sp.run()
