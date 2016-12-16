#!/usr/bin/env python
# encoding:utf-8

from spider.httpreq import BasicRequests, CurlReq
import time

class PhoneCode(BasicRequests):
    def __init__(self):
        BasicRequests.__init__(self)
        #self.info = "Developer=en1f6%2fhZ%2bU83YaiOGnLlpw%3d%3d"
        self.baseurl = "http://xapi.83r.com"
        self.token = ''
        self.balance = 0

    def _req(self, url, **kwargs):
        con = self.request_url(self.baseurl+url, **kwargs)
        con.encoding = 'gbk'
        con.text = con.content.decode('gb18030', 'replace')
        return con

    def login(self):
        params = {'Developer':'en1f6/hZ+U83YaiOGnLlpw==', 'uName':'swigger', 'pWord':'123@456'}
        url = self.baseurl + "/User/login"
        con = self.request_url(url, params=params)
        #token&账户余额&最大登录客户端个数&最多获取号码数&单个客户端最多获取号码数&折扣
        tpl = con.text.split('&')
        self.token = tpl[0]
        self.balance = tpl[1]
        self.get_message()
        #print balance, maxcli, maxnos, snos, discount, other

    def dump_projs(self):
        con = self._req('/User/getItems', params={'token':self.token, 'tp':'ut'})
        print con.text

    def logout(self):
        if self.token:
            r = CurlReq(None)
            try:
                r.doreq("http://xapi.83r.com/User/exit?token=" + self.token)
            except:
                pass
            self.token = ''

    def get_phones(self, count=1, itemid=181):
        ##181&QQ号|QQ注册|注册QQ&0.08&1
        params={'ItemId':itemid, 'token':self.token, 'PhoneType':0, 'Count':count }
        con = self._req('/User/getPhone', params=params)
        print con.text
        return con.text

    def get_message(self, phoneno=None):
        params={'token':self.token}
        if phoneno:
            params['Phone'] = phoneno
        con = self._req('/User/getMessage', params=params)
        print con.text
        return con.text

    def __del__(self):
        self.logout()

if __name__ == '__main__':
    a = PhoneCode()
    a.login()
    a.get_phones(10)
    a.get_phones(10)
    a.get_phones(10)
    for i in range(0, 100):
        time.sleep(6)
        a.get_message()
