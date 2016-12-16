#!/usr/bin/env python
# -*- coding:utf8 -*-
import json
import random
import time
from urllib import quote

from court.sessionrequests import ETOSSessionRequests


class Nacao(ETOSSessionRequests):
    def __init__(self):
        super(Nacao, self).__init__()

    def init(self):
        con = self.request_url(
            "https://s.nacao.org.cn/specialResult.html?x=hdfzm10WvPvmv5sPN1lnjQ==&k=iicN9d+zPvBjAJxcWK1Byww=&s=BV/C5wtMpvrmJxLj5d1/4fD7b/2kDypt9bSz/KG9G3FDr9x/6d1sjp3nQ8Vg9hkhx4M=&y=RJZujsWSWqxq7UGusnHqSvP9IgyzrrdzdQ==")
        if not con or con.code < 200 or con.code >= 300:
            print con.headers
        else:
            print con.cookies
            print self.get_cookie('banggoo.nuva.cookie')
    def cookies(self):
        cookiejar=getattr(self.__curlshare)
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
            data = {"firststrfind": "%20jgdm='" + code + "'%20%20not%20ZYBZ=('2')%20",
                    "strfind": "%20jgdm='" + code + "'%20%20not%20ZYBZ=('2')%20",
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

    def do_job(self):
        img = self.request_url("https://s.nacao.org.cn/servlet/ValidateCode?time=" + str(int(random.random() * 1000)))
        print 'image length ==>', len(img.text)
        con = self.request_url("http://192.168.1.94:3001/", files={'file': img.content}, data={"province": "nacao"})
        if not con or con.code < 200 or con.code >= 300:
            print 'image:', con.headers
        else:
            print 'image:', con.cookies
            res = json.loads(con.text)
            print res

    def run(self):
        pass


if __name__ == '__main__':
    job = Nacao()
    job.init()
    job.do_job()
