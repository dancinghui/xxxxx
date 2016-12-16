#!/usr/bin/env python
# encoding:utf-8

from spider.httpreq import BasicRequests
import spider.util
import random
import time
import re


class BusinessCodeCheck(object):

    def __init__(self):
        self.baseCode = "0123456789ABCDEFGHJKLMNPQRTUWXY"
        self.codes = dict(zip(self.baseCode, range(28)))
        self.wi = (1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28)

    def isBusinessNo(self, businessCode):
        if not businessCode or re.search(r'\s+', businessCode) or \
                        len(businessCode) != 18:
            return False

        check = businessCode[17]

        if check not in self.baseCode:
            return False

        sum = 0

        for i in range(17):
            key = businessCode[i]
            if key not in self.baseCode:
                return False

            sum += (self.codes[key] * self.wi[i])

        value = 31 - sum % 31
        return value == self.codes[check]

    def generateLastParity(self, partBusinessCode):
        sum = 0
        for i in range(17):
            key = partBusinessCode[i]
            if key not in self.baseCode:
                return False

            sum += (self.codes[key] * self.wi[i])

        value = 31 - sum % 31
        return self.baseCode[value]


class Nacao(BasicRequests):
    def __init__(self):
        BasicRequests.__init__(self)
        self.select_user_agent('firefox')
        self.mainpage = "https://s.nacao.org.cn/"
        #self.proxies = {'http': 'http://ipin:helloipin@192.168.2.90:3428', 'https': 'https://ipin:helloipin@192.168.2.90:3428'}

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


    def search_code(self, code):
        post = """
callCount=1
c0-scriptName=ServiceForNum
c0-methodName=getData
c0-id={id}
c0-e1=string: jgdm='{code}'
c0-e2=string: jgdm='{code}'
c0-e3=string:{code}
c0-e4=string:1
c0-e5=string:{code}
c0-e6=string:全国
c0-e7=string:alll
c0-e8=string:
c0-e9=boolean:true
c0-e10=boolean:false
c0-e11=boolean:false
c0-e12=boolean:false
c0-e13=string:
c0-e14=string:
c0-e15=string:
c0-param0=Object:{{firststrfind:reference:c0-e1, strfind:reference:c0-e2, key:reference:c0-e3, kind:reference:c0-e4, tit1:reference:c0-e5, selecttags:reference:c0-e6, xzqhName:reference:c0-e7, button:reference:c0-e8, jgdm:reference:c0-e9, jgmc:reference:c0-e10, jgdz:reference:c0-e11, zch:reference:c0-e12, strJgmc:reference:c0-e13, :reference:c0-e14, secondSelectFlag:reference:c0-e15}}
xml=true
"""
        myid = "%d_%d" % (int(random.randint(1000, 9999)), int(time.time()*1000))
        post = post.format(id=myid, code=code).lstrip()
        con = self.request_url("https://s.nacao.org.cn/dwr/exec/ServiceForNum.getData.dwr", data=post,
                               headers={"Content-Type": "text/plain", "Referer":self.mainpage}) #, proxies=self.proxies)
        script = "DWREngine={_handleResponse : function(a,b){console.log(b[1][0])} }\n"
        script += con.text
        return spider.util.runjs(script)


if __name__ == '__main__':

    # # n = Nacao()
    # # print n.search_code('692944327')
    #
    # c = BusinessCodeCheck()
    # print c.generateLastParity('91440106076523297')

    n = Nacao()
    print n.compute_code('X3534943')
    #print n.compute_code('607384020')
    #print n.compute_code('692944327')

