#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.spider import MultiRequestsWithLogin, SessionRequests
from spider.captcha.lianzhong import LianzhongCaptcha
import StringIO
import json
import spider.util
from lxml import html


class HrConfig(object):
    LOGIN_REFER = 'http://qy.chinahr.com/buser/login?'
    LOGIN_URL = 'http://qy.chinahr.com/buser/subLogin'

    ac = [
        {'u': 'hqxx001', 'p': 'hq1234'},
        {'u': 'ipin_xxoo1', 'p': '123456'},
        {'u': 'ipin_xxoo2', 'p': '123456'},
        {'u': 'ipin_xxoo3', 'p': '123456'},

    ]


class HrImager(object):
    def __init__(self):
        self.lianzhongC = LianzhongCaptcha()

    def get_code(self, osr, codeurl):
        headers={'Referer': HrConfig.LOGIN_REFER}
        con = osr.request_url(codeurl, headers=headers)
        f = StringIO.StringIO()
        f.write(con.content)
        f.seek(0)
        self.code = self.lianzhongC.resolve(f)
        return self.code


class HrLogin(MultiRequestsWithLogin):
    def __init__(self, ac):
        MultiRequestsWithLogin.__init__(self, ac)
        assert isinstance(ac, dict)
        self.hrimger = HrImager()

        self.ac = ac

    def need_login(self, url, con, hint):
        if r'/buser/login' in con.request.url:
           return True

        return False

    def _real_do_login(self):
        print "============ logining ============="
        self.reset_session()
        headers = {'Referer': HrConfig.LOGIN_REFER, }
        con = self.request_url(HrConfig.LOGIN_REFER)
        data = self.extract_login_data(con.text)


        res = self.request_url(HrConfig.LOGIN_URL, data=data, headers=headers)
        jsonresp = json.loads(res.text)
        if jsonresp.get('code') == 1:
            self.isvalid = True
            print "============ login succuss ==========="
            return 1
        else:
            print "login Fail"

        return 0

    def extract_login_data(self, content):
        doc = html.fromstring(content)
        hiddens = doc.xpath('//input[@type="hidden"]')
        codeurl = doc.xpath('//img[@id="comPicValidateCode"]/@src')[0]

        code = self.hrimger.get_code(self, codeurl)

        data = {'name': self.ac['u'], 'code': code}

        for hidden in hiddens:
            id_ = hidden.attrib.get('id', '')
            value_ = hidden.attrib.get('value', '')
            if id_ == 'login_sign':
                data.update({'invokeSign': value_})

            if id_ == 'login_user_sensFlag':
                data.update({'precode': value_})

            if id_ == 'lt':
                data.update({'lt': value_})

            if id_ == 'rem_txt':
                data.update({'remeberme': value_})

            if id_ == 'modulus':
                modulus = value_

        pw = self._get_pw(modulus, self.ac['p']).strip()
        data.update({'pw': pw})

        return data

    def _get_pw(self, modulus, p):
        sc = ''
        with open('login_data.js') as f:
            sc = f.read()

        sc += '\nconsole.log(encrypted("%s", "%s"));' % (modulus, p)
        return spider.util.runjs(sc)


if __name__ == '__main__':
    s = HrLogin(HrConfig.ac)
    s.do_login()
    s.load_proxy('proxy')

    # s.get_code("http://qy.chinahr.com/buser/gpic?ltk=l_e29a20c9ca122c8db185424ff183b51d37911149762&temp=123ilruy732")
