#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.spider import MultiRequestsWithLogin, SessionRequests
from spider.captcha.lianzhong import LianzhongCaptcha
from spider.util import sendmail
import StringIO
import hashlib
import json
import random
import time
import spider.util
from lxml import html
import sys


class Config(object):
    LOGIN_URL = 'https://passport.liepin.com/e/account/'
    HOST = 'passport.liepin.com'
    ORIGIN = 'https://passport.liepin.com'
    RASID = '7B760F91-20140904-142400-b2a3cc-81404d'
    RAVer = '3.0.7'
    LOGIN_PAGE = 'https://passport.liepin.com/e/login.json'


class LPImager(object):
    def __init__(self):
        self.lianzhongC = LianzhongCaptcha()

    def get_code(self, osr):
        headers={'Referer': Config.LOGIN_URL}
        con = osr.request_url('https://passport.liepin.com/captcha/randomcode/?' + str(random.random()), headers=headers)
        f = StringIO.StringIO()
        f.write(con.content)
        f.seek(0)
        self.code = self.lianzhongC.resolve(f)
        return self.code

    ##type=1, 企业账号情况
    ## type=2, 猎头账号情况
    def get_user_valid_code(self, osr, url, type):

        headers = {

            'Upgrade-Insecure-Requests':'1'

        }
        con = osr.request_url('https://www.liepin.com/image/randomcode4ValidationUser/?time=%d' % int(time.time()*1000), headers=headers)
        f = StringIO.StringIO()
        f.write(con.content)
        f.seek(0)
        self.code = self.lianzhongC.resolve(f)
        return self.code

    def find_codeurl(self, content):
        doc = html.fromstring(content)
        img = doc.xpath('//img')
        if img:
            return "http://www.liepin.com" + img[0]

        return None

class GlobalData(object):
    lpImager = LPImager()


class LPQYLogin(MultiRequestsWithLogin):
    def __init__(self, ac):
        MultiRequestsWithLogin.__init__(self, ac)
        self.ac = ac
        assert isinstance(ac, dict)
        self.cansearch = 0
        self.isvalid = True

        self.main_page = 'https://passport.liepin.com/e/account/'
        self.login_page = 'https://passport.liepin.com/e/login.json'

        self._retry_max_times = 6

    def _real_do_login(self):
        print "=========== login... ========="
        self.reset_session()
        headers = {'Referer':self.main_page,
                   'Origin': Config.ORIGIN,
                   'RA-Sid': Config.RASID,
                   'RA-Ver': Config.RAVer,
                   'X-Requested-With': 'XMLHttpRequest',
                   }

        con = self.request_url(self.main_page)
        imgcode = GlobalData.lpImager.get_code(self)
        data = {'verifycode':imgcode, 'user_kind': 1, 'user_login':self.account['u'],
                'user_pwd': hashlib.md5(self.account['p']).hexdigest(), 'url':'', }

        con = self.request_url(self.login_page, data=data, headers=headers)
        print con.text
        try:
            jo = json.loads(con.text)
            if '帐号己被冻结' in jo.get('msg', ''):
                self.isvalid = False
            if jo.get('flag') == 1:
                return 1
        except:
            pass
        return 0

    def is_valid(self):
        return self.isvalid

    def need_login(self, url, con, hint):
        if r'/e/account/' in con.request.url:
           return True
        # if u'登录猎聘通' in con.text:
        #     return True

        if u'系统检测到异常浏览行为，建议您立即进行验证，否则可能被封禁账号。' in con.text \
                or u'警告:由于您浏览过于频繁,请验证后重试！' in con.text or '/validation/captcha?object_type=1' in con.request.url:
            retry_time = 0

            # 暂时 人工验证
            if 'secret.liepin.com' in con.request.url:
                sendmail(['jianghao@ipin.com'], "liepin 验证", "\n\naccout: %r 需要验证" % self.ac)
                exit(1)

            while not self.validate_user(con.request.url) and retry_time < self._retry_max_times:
                retry_time += 1
                print "retry validate user, time: %d" % retry_time
                time.sleep(5)
                continue

            if retry_time >= self._retry_max_times:
                print "validation more than %d times fail..." % self._retry_max_times
                sys.exit(1)

            return True

        if u'您的操作过于频繁，为确保账号安全，请稍后再试' in con.text:
            print u'您的操作过于频繁，为确保账号安全，请稍后再试'
            sys.exit(1)

        return False

    def validate_user(self, url):

        code = GlobalData.lpImager.get_user_valid_code(self, url, 1)

        if not code:
            print "validate code is empty"
            return False

        postdata = {'object_type': 1, 'rand_validationuser':code}

        postdata = "rand_validationuser=%s&object_type=1" % code

        headers = {'X-Requested-With':'XMLHttpRequest',
                   'Origin':'https://www.liepin.com',
                   'Content-Type':'application/x-www-form-urlencoded',
                   'Host':'www.liepin.com',
                   'Refer':url,
                   'Accept-Encoding':'gzip, deflate, sdch',
                   'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.103 Safari/537.36'}
        con = self.request_url('https://www.liepin.com/validation/verifyillegaluser.json', data=postdata, headers=headers)
        if con is not None:
            j = json.loads(con.text)
            if int(j.get('flag')) == 0:
                print j.get('msg').encode('utf-8')
            else:
                return True
        return False


class LPLTLogin(MultiRequestsWithLogin):
    def __init__(self, ac):
        MultiRequestsWithLogin.__init__(self, ac)
        assert isinstance(ac, dict)
        self.cansearch = 0
        self.isvalid = True

        self.main_page = 'https://passport.liepin.com/h/account/'
        self.login_page = 'https://passport.liepin.com/h/login.json'

        self._retry_max_times = 6

    def _real_do_login(self):
        print "=========== login... ========="
        self.reset_session()
        headers = {'Referer':self.main_page,
                   'Origin': Config.ORIGIN,
                   'RA-Sid': Config.RASID,
                   'RA-Ver': Config.RAVer,
                   'X-Requested-With': 'XMLHttpRequest',
                   }

        con = self.request_url(self.main_page)
        imgcode = GlobalData.lpImager.get_code(self)
        data = {'verifycode':imgcode, 'isMd5':1, 'user_kind': 2, 'user_login':self.account['u'],
                'user_pwd': hashlib.md5(self.account['p']).hexdigest(), 'url':'', }

        con = self.request_url(self.login_page, data=data, headers=headers)
        print con.text
        try:
            jo = json.loads(con.text)
            if '帐号己被冻结' in jo.get('msg', ''):
                self.isvalid = False
            if jo.get('flag') == 1:
                return 1
        except Exception as e:
            print e.message
        return 0

    def is_valid(self):
        return self.isvalid

    def need_login(self, url, con, hint):
        if '/h/account' in con.request.url:
           return True
        if u'登录猎聘通' in con.text:
            return True
        if u'猎头顾问注册_猎聘网：' in con.text:
            return True

        if u'系统检测到异常浏览简历行为，建议您立即进行验证，否则可能被封禁账号。' in con.text:
            retry_time = 0
            while not self.validate_user(con.request.url) and retry_time < self._retry_max_times:
                retry_time += 1
                print "retry validate user, time: %d" % retry_time
                time.sleep(5)
                continue

            if retry_time >= self._retry_max_times:
                print "validation more than %d times fail..." % self._retry_max_times
                sys
                time.sleep(3600 * 24)

            return True

        if u'您的操作过于频繁，为确保账号安全，请稍后再试' in con.text:
            time.sleep(3600 * 24)
            return True

        return False

    def validate_user(self, url):
        code = GlobalData.lpImager.get_user_valid_code(self, url, 2)
        if not code:
            print "validate code is empty"
            return False

        postdata = {'object_type': 2, 'rand_validationuser':code}
        headers = {'X-Requested-With':'XMLHttpRequest', 'Referer': 'http://www.liepin.com/validation/captcha?url={}&object_type=2'.format(url)}
        con = self.request_url('http://www.liepin.com/validation/verifyillegaluser.json', data=postdata, headers=headers)
        if con is not None:
            j = json.loads(con.text)
            if int(j.get('flag')) == 0:
                print j.get('msg').encode('utf-8')
            else:
                return True
        return False


if __name__ == '__main__':
    spider.util.use_utf8()
    # osr = SessionRequests()
    # img = LPImager()
    # print img.get_code(osr)
    # lg = LPQYLogin({'u':'上海富卿商贸有限公司', 'p':'zhaopin123'})
    lg = LPQYLogin({'u':'qwer040506', 'p':'zhaopin123', 'type': 1})
    lg.load_proxy('proxy')
    lg.do_login()
