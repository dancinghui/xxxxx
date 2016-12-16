#!/usr/bin/env python
# encoding:utf-8

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
from spider.httpreq import BasicRequests, SessionRequests
from spider.spider import Spider
import random
import time
import imghdr
import spider.util
from urllib import quote
import json
bloom = set()
from spider.savebin import FileSaver, BinSaver
import threading
import re
from spider import runtime

filter_kw = set()
urls = ["https://s.nacao.org.cn/specialResult.html?x=hdfzm10WvPvmv5sPN1lnjQ==&k=iicN9d+zPvBjAJxcWK1Byww=&s=BV/C5wtMpvrmJxLj5d1/4fD7b/2kDypt9bSz/KG9G3FDr9x/6d1sjp3nQ8Vg9hkhx4M=&y=RJZujsWSWqxq7UGusnHqSvP9IgyzrrdzdQ==",
        "https://s.nacao.org.cn/specialResult.html?x=IA0JgyayU7kWeluCRjeIEwn+kV8=&k=5UOfBXya6WGEzjJ7Z2JFmyI=&s=vVRpHdlliKNiPRi+JDc69VVsl4/t/alk+0NnVEjoRpFTz84mFNGlOL5HH8Co&y=Lq7RsQJwxDdwRHxoTlCyuXhxpmXGZw==",
        "https://s.nacao.org.cn/specialResult.html?x=3E56LUV49kFDX2cBQZL2RFx18Fc=&k=Svm7eKmCKoP9/T08V6GBQtA=&s=fPwJRwbHLQ4mHKteircizTTMnasSL9zjk2wvZqacBhixXAh/3yWTsNhrri4gyTxcelfK6A==&y=t+RxzvMYVTiWmBO/2MLrcC2Sv5HoHmlwazfEVg==",
        "https://s.nacao.org.cn/specialResult.html?x=FE42V8u13EbkVJC+lqv36XVIDMM=&k=DZNXJkZ+rw8tTjYQYuUz6rk=&s=MizttqE0ENEdYeKKdkqnf5mzLkBSpEyrgGAoqoDqzxHd6SKTYqhUJnUmFOrd&y=gsri4YDKaIo7jWxHv1CxeDaEvq5+Vw==",
        "https://s.nacao.org.cn/specialResult.html?x=9SJCJVpmpYM3oqiVyZ2BE8TKqs0=&k=raBO8bhBmkZsw8JLRk63xG0=&s=GIqTX3+2kOihc/xAkMb+nzYTxVl/JjB6XJxVHNk5y+GDvG4GF+KxPZm9DuOT&y=kd9JF6Y3s5MIBzqzpyR5aziKnNKHFQ=="
        ]
class Nacao(Spider):
    """遍历所有组织机构代码(现在仅限于数字)"""
    def __init__(self, thcnt):
        self.proxy_mode = 2
        # 代理模式如下:
        # 0:使用固定代理，代理数＝线程数
        # 1:使用单一ADSL切换 ,线程数自定义
        # 2:使用多个ADSL切换，线程数自定义
        # 3:通过API提取快代理，并将代理放入到队列,所有线程共享同一个代理，代理异常则切换并从队列中移除(目前没有做代理切换)
        if self.proxy_mode == 0:
            self.proxies_dict = [{'http': 'http://ipin:helloipin@106.75.134.189:18889', 'https': 'https://ipin:helloipin@106.75.134.189:18889'},
                                 {'http': 'http://ipin:helloipin@106.75.134.190:18889', 'https': 'https://ipin:helloipin@106.75.134.190:18889'},
                                 {'http': 'http://ipin:helloipin@106.75.134.191:18889', 'https': 'https://ipin:helloipin@106.75.134.191:18889'},
                                 {'http': 'http://ipin:helloipin@106.75.134.192:18889', 'https': 'https://ipin:helloipin@106.75.134.192:18889'},
                                 {'http': 'http://ipin:helloipin@106.75.134.193:18889', 'https': 'https://ipin:helloipin@106.75.134.193:18889'},
                                 ]
            Spider.__init__(self, 100)
        elif self.proxy_mode == 1:
            self.proxies = {'http': 'http://ipin:helloipin@121.40.186.237:50001', 'https': 'https://ipin:helloipin@121.40.186.237:50001'}
            #self.proxies = {'http': 'http://ipin:helloipin@183.56.160.174:50001', 'https': 'https://ipin:helloipin@183.56.160.174:50001'}
            #self.proxies = {'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'}
            #self.proxis = {'http': 'http://ipin:helloipin@106.75.134.189:18889', 'https': 'https://ipin:helloipin@106.75.134.189:18889'}
            Spider.__init__(self, 100)
        elif self.proxy_mode == 2:
            self.proxies_dict = [#{'http': 'http://ipin:helloipin@183.56.160.174:50001', 'https': 'https://ipin:helloipin@183.56.160.174:50001'},
                                {'http': 'http://ipin:helloipin@121.40.186.237:50001', 'https': 'https://ipin:helloipin@121.40.186.237:50001'},
                                 {'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'},
                                {'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'}]
            Spider.__init__(self, 200)
        elif self.proxy_mode == 3:
            self.proxies_dict = []
            self.proxies = {}
            self.get_kuaidaili()
        elif self.proxy_mode == 4:
            Spider.__init__(self, 1)
            self.proxies_dict = []

        self._curltls = threading.local()
        self.shoudong_img = False #手动输入验证码
        self.saver = FileSaver("nacao_traversal_info_l.txt")
        self.already = FileSaver("nacao_traversal_info_already_l.txt")
        self.queries0 = FileSaver("nacao_traversal_queies_0_l.txt")
        self.bin_saver = BinSaver("nacao_captcha_image.bin")
        self.init_already()
        self.time_record = time.time()
        self.scs_record = 0

    def get_adsl_proxies(self):
        proxies = {'http': 'http://ipin:helloipin@106.75.134.189:18888', 'https': 'https://ipin:helloipin@106.75.134.189:18888'}
        url = "http://localhost:9000/"
        while True:
            res = self.request_url(url, proxies=proxies)
            if res is not None and res.code == 200:
                if res.text == "" or res.text == "{}":
                    time.sleep(0.1)
                    continue
                results = json.loads(res.text)
                if results["code"] == 0:
                    continue
                result = results["result"]
                self.proxies_dict = []
                for k, v in result.items():
                    self._match_proxy(v)
                time.sleep(1)
                continue
            else:
                print "获取ADSL代理切换IP失败......重试......"
                time.sleep(0.1)
                continue

    def run(self, async=False, report=True):
        if self.proxy_mode == 4:
            self._interval = threading.Thread(target=self.get_adsl_proxies)
            self._interval.start()
            runtime.Runtime.set_thread_name(self._interval.ident, "%s.job.interval" % self._name)
        super(Nacao, self).run(async=async, report=report)

    def get_kuaidaili(self):
        url = "http://dev.kuaidaili.com/api/getproxy/?orderid=925817981728018&num=500&b_pcchrome=1&b_pcie=1&b_pcff=1&b_iphone=1&protocol=1&method=2&an_an=1&an_ha=1&sp1=1&sp2=1&quality=1&sort=2&format=json&sep=1"
        while True:
            res = self.request_url(url)
            if res is None or res.code != 200:
                time.sleep(0.5)
                continue
            else:
                text = res.text
                js = json.loads(text)
                lst = js["data"]["proxy_list"]
                self.proxies_dict = []
                for l in lst:
                    self._match_proxy(l)
                if len(self.proxies_dict) > 0:
                    return
                else:
                    time.sleep(0.5)
                    continue


    def init_already(self):
        cnt = 0
        with open("/home/chentao/ml.dat", "r") as f:
            for line in f:
                cnt += 1
                line = line.strip()
                code = self.compute_code(line)
                filter_kw.add(code)
        print "init oc_code finish ...", cnt
        with open("nacao_traversal_info_already_l.txt", "r") as f:
            for line in f:
                cnt += 1
                line = line.strip()
                filter_kw.add(line)
        print "init already finish ...", cnt


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


    # def buquan(self, code):
    #     code = str(code)
    #     if len(code) != 8:
    #         sub = 8 - len(code)
    #         while sub != 0:
    #             code = "0" + code
    #             sub -= 1
    #     return code

    def buquan(self, code):
        """只针对Ｌ开头的补全"""
        code = str(code)
        if len(code) != 7:
            sub = 7 - len(code)
            while sub != 0:
                code = "0" + code
                sub -= 1
        code = "L"+code
        return code

    def compute_code(self, code):
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


    def dispatch(self):
        for i in range(0, 10000000, 1):
                code = self.buquan(i)
                code = self.compute_code(code)
                if code in filter_kw:
                    print "oc_code [ %s ] already queried !" % code
                    continue
                job = {"code": code, "retry": 0}
                self.add_main_job(job)
        self.wait_q_breakable()
        self.add_job(None, True)

    def run_job(self, job):
        code = job.get("code")
        cnt = job.get("cnt")
        retry = job.get("retry")
        proxies = {}
        if self.proxy_mode == 4:
            num = random.randrange(0, len(self.proxies_dict), 1)
            proxies = self.proxies_dict[num]
        else:
            proxies = getattr(self._curltls, "proxies", {})
            if len(proxies) == 0:
                if self.proxy_mode == 0:
                    num = self.get_tid() % len(self.proxies_dict)
                    proxies = self.proxies_dict[num]
                elif self.proxy_mode == 1:
                    proxies = self.proxies
                elif self.proxy_mode == 2:
                    num = self.get_tid() % len(self.proxies_dict)
                    proxies = self.proxies_dict[num]
                elif self.proxy_mode == 3:
                    if len(self.proxies_dict) == 0:
                        self.get_kuaidaili()
                    else:
                        proxies = self.proxies_dict[len(self.proxies_dict) - 1]
                        #未完待续 -- 没有做代理切换
                setattr(self._curltls, "proxies", proxies)
        self.search(code, proxies=proxies, cnt=cnt, retry=retry)

    def init_req(self, proxies={}):
        req = getattr(self._curltls, "req", None)
        if req is None:
            req = SessionRequests()
            url = urls[random.randrange(0, len(urls))]
            while True:
                con_init = req.request_url(url, proxies=proxies)
                if con_init is None or con_init.code != 200:
                    print "...初始化失败..."
                else:
                    break
            setattr(self._curltls, "req", req)
            setattr(self._curltls, "init_url", url)
        return req

    def search(self, code, proxies={}, cnt=0, retry=0):
        req = self.init_req(proxies=proxies)
        #验证码校验的url
        captcha_check = "https://s.nacao.org.cn/servlet/CheckValidateCode "
        while True:
            # 获取验证码图片
            img_content = self.get_image(proxies=proxies)
            # 验证码识别
            imgcode = None
            expr = None
            if self.shoudong_img:
                imgcode = self.handler_imgcode(img_content)
            else:
                imgcode, expr = self.image_discern(img_content)
            if imgcode is None:
                continue

            headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8", "X-Requested-With": "XMLHttpRequest", "yzm": imgcode}
            res = req.request_url(captcha_check, data={"yzm": imgcode}, headers=headers, proxies=proxies)
            if res is not None and res.code == 200 and "true" in res.text:
                print cnt, code, "验证码校验成功..."
                self.bin_saver.append(expr, img_content)
                #self.save_file("/home/windy/codeimg/nacao/"+imgcode+".jpeg", img_content1)
                break
            else:
                print cnt, code, "验证码校验失败..."
                time.sleep(0.5)
                continue

        #获取数据
        init_url = getattr(self._curltls, "init_url", None)
        get_url = "https://s.nacao.org.cn/servlet/valication"
        headers1 = {"Content-Type": "application/x-www-form-urlencoded", "X-Requested-With": "XMLHttpRequest",
                   "Referer": init_url, "Accept": "application/json, text/javascript, */*",
                    "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
                    "Accept-Encoding": "gzip, deflate, br"}

        data = self.gen_post_data(code=code)
        res = None
        while True:
            res = req.request_url(get_url, data=data, headers=headers1, proxies=proxies)
            if res is None or res.code != 200:
                print "请求结果为空 ." if res is None else "请求结果 res.code = %d " % res.code
                time.sleep(0.5)
                continue
            else:
                break
        if u"请求无效或页面没找到" in res.text:
            self.already.append(code)
            print cnt, code, "请求无效或页面没找到......"
            return
        try:
            r = eval(res.text)
            result = r[1]
            print cnt, code, "查询到", len(result), "条数据...", spider.util.utf8str(result)
            self.speed_record(proxies=proxies)
            if len(result) == 0:
                #查询结果为空的关键字都写入到同一个文本
                self.queries0.append(code)
            else:
                for t in result:
                    self.saver.append(spider.util.utf8str(t))
            self.already.append(code)
        except Exception as e:
            print cnt, code, "数据查询结果转换出错,", e, "res.text:\n", res.text

    def speed_record(self, proxies={}):
        self.scs_record += 1
        interval = time.time() - self.time_record
        speed = self.scs_record / interval
        print "----------- 一条数据完整拉取速度：", speed, " 条/秒 ------------", proxies
        # if interval >= 60:
        #     self.time_record = time.time()
        #     self.scs_record = 1
        # else:
        #     self.scs_record += 1



    def handler_imgcode(self, img_content):
        #imgtype = imghdr.what(None, img_content)
            #if imgtype in ['gif', 'jpeg', 'jpg', 'png', 'bmp']:
                #spider.util.FS.dbg_save_file("captcha."+imgtype, con1.content)
        #spider.util.FS.dbg_save_file("captcha.jpeg", img_content)
        self.save_file("captcha.jpeg", img_content)
        imgcode = raw_input("请输入验证码(captcha.jpeg):")
        return imgcode

    def image_discern(self, img_content):
        #验证码识别
        captcha_discern = "http://192.168.1.94:3001/"
        response = self.request_url(captcha_discern, files={'file': img_content}, data={"province": "nacao"})
        if response is None or response.code != 200:
            return None, None
        result = response.text.strip()
        if '"valid":true' in result:
            try:
                result = json.loads(result)
                imgcode = result["answer"]
                if imgcode == None or imgcode == "":
                    print "验证码图片识别错误　imgcode==None或''"
                    return None, None
                else:
                    return imgcode, result["expr"]
            except Exception as err:
                print "验证码图片识别出现异常，重新校验...,result:", result, "错误原因:", err
                time.sleep(1)
                return None, None
        else:
            return None, None


    def get_image(self, proxies={}):
        captcha_retry = 0
        req = self.init_req(proxies=proxies)
        while True:
            captcha_url = "https://s.nacao.org.cn/servlet/ValidateCode?time=" + str(int(time.time() * 1000))
            con = req.request_url(captcha_url, proxies=proxies)
            if con is None or con.code != 200:
                captcha_retry += 1
                print captcha_retry, "获取验证码图片", " res is None " if con is None else " res.code = %d " % con.code
                time.sleep(0.5)
                continue
            return con.content


    def gen_post_data(self, code=None, kw=None):
        if code is None and kw is not None:
            # 根据公司名搜索
            kw = quote(kw)
            data = {"firststrfind": "%20jgmc='" + kw + "'%20%20not%20ZYBZ=('2')%20",
                     "strfind": "%20jgmc='" + kw + "'%20%20not%20ZYBZ=('2')%20",
                     "key": kw,
                     "kind": 2,
                     "tit1": kw,
                     "selecttags": "%E5%85%A8%E5%9B%BD",
                     "xzqhName": "alll",
                     "button": "",
                     "jgdm": "true",
                     "jgmc": "false",
                     "jgdz": "false",
                     "zch": "false",
                     "strJgmc": "",
                     "secondSelectFlag": ""
                     }
            return data
        elif code is not None and kw is None:
            # 根据组织机构代码搜索
            data = {"firststrfind": "%20jgdm='"+code+"'%20%20not%20ZYBZ=('2')%20",
                    "strfind": "%20jgdm='"+code+"'%20%20not%20ZYBZ=('2')%20",
                    "key": code,
                    "kind": 1,
                    "tit1": code,
                    "selecttags": "%E5%85%A8%E5%9B%BD",
                    "xzqhName": "alll",
                    "button": "",
                    "jgdm": "true",
                    "jgmc": "false",
                    "jgdz": "false",
                    "zch": "false",
                    "strJgmc": "",
                    "secondSelectFlag": ""
                    }
            return data
        else:
            print "生成Ｐｏｓｔ数据　请求参数错误．．．．．．"


    def _match_proxy(self, line):
        m = re.match('([0-9.]+):(\d+):([a-z0-9]+):([a-z0-9._-]+)$', line, re.I)
        m1 = re.match('([0-9.]+):(\d+):([a-z0-9]+)$', line, re.I)
        if m:
            prstr = '%s:%s@%s:%s' % (m.group(3), m.group(4), m.group(1), m.group(2))
            proxies = {'http': 'http://' + prstr, 'https': 'https://' + prstr}
        elif m1:
            prstr = '%s:%s' % (m1.group(1), m1.group(2))
            proxies = {'http': 'http://' + prstr, 'https': 'https://' + prstr}
        else:
            proxies = {'http': 'http://' + line, 'https': 'https://' + line}
        self.proxies_dict.append(proxies)


    def req_t(self, proxies={}):
        #proxies = {'http': 'http://ipin:helloipin@121.40.186.237:50001', 'https': 'https://ipin:helloipin@121.40.186.237:50001'}
        proxies={'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'}
        res = self.request_url("http://www.jobui.com/", proxies=proxies)
        if res is None or res.code != 200:
            print "－－－－－－－－－－－－－－－－－－－－－－","res is None" if res is None else "res.code = %d" % res.code
        else:
            print res.text


    def save_file(self, fname, content):
        with open(fname, 'wb') as f:
            f.writelines(content)


if __name__ == '__main__':
    n = Nacao(1)
    #n.search('大王大大哥')
    n.run()
    #print n.compute_code(9999999)
    #n.req_t()
