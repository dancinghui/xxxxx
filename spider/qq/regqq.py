#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.spider import SessionRequests
from spider.captcha.askimg import GetImageCode
import spider.util
import random
import re
import urllib
import json
import sys


class RegQQ(SessionRequests):
    def __init__(self):
        SessionRequests.__init__(self)
        self.select_user_agent('firefox')
        self.password = '91a679d6cc25af1a7e303dd77c2bc8cb1fe781eee66ad6573c4e998cbe9be44e1d2837011b25619be280a174f0fddc570d2719d1543ae9e4c7b62b16526eaef16d23489fb435aa60f5aeb5a6ab693c13a19afb92d2605e1bcad857b10896f38d7282371db1f7f4f2db7e22e35e7fc0247c405d661b4fe1c4636a00ad0cca1f95'
        self.baseurl = 'http://zc.qq.com/chs/index.html'
        self.telphone = '13143436016'
        self.telphone = '0012421533440'

    def _getiamge(self):
        url = 'http://captcha.qq.com/getimage?aid=1007901&r=%s' % str(random.random())
        con = self.request_url(url, headers={'Referer':self.baseurl})
        return con.content

    def get_aqobj(self):
        url = 'http://zc.qq.com/chs/m.js?v=' + str(random.random())
        con = self.request_url(url)
        robj = {}
        for i in  con.text.split(';'):
            m = re.search(ur"A\('(.*)','(.*)'\)", i)
            if m:
                robj[m.group(1)] = m.group(2)
        return robj

    def doreg(self):
        headers={'Referer':self.baseurl}
        self.request_url(self.baseurl)
        self.request_url('http://zc.qq.com/cgi-bin/chs/numreg/init?r=%s&cookieCode=0' % random.random(), headers=headers)
        aq = self.get_aqobj()
        pobj = {
            'elevel':'1',

            "year": random.randint(1978,1994),
            "month": random.randint(1,12),
            "day": random.randint(1,28),
            "sex": random.randint(1,2),
            'nick':'天天向上',

            'country':'1',
            'province':'44',
            'city':'3',

            'csloginstatus':'0',
            'email':'false',
            'isnongli':'0',
            'isrunyue':'0',
            'jumpfrom':'58030',
            'other_email':'false',
            'password':self.password,
            'qzdate':'',
            'telphone':'',
            'verifycode': 'aaaa',
        }
        pobj.update(aq)

        while True:
            pobj['verifycode'] = GetImageCode().resolve(self._getiamge)
            scurl = 'http://zc.qq.com/cgi-bin/chs/common/safe_check?r=' + str(random.random())
            con = self.request_url(scurl, data=pobj, headers=headers)
            # {"VerifyCodeResult":"2","ec":0,"elevel":"4","safeverifyResult":"4"}
            print con.text
            j = json.loads(con.text)
            VerifyCodeResult = int(j['VerifyCodeResult'])
            if VerifyCodeResult == 2 or VerifyCodeResult == 0:
                pobj['elevel'] = j['elevel']
                break
            elif VerifyCodeResult == 1:
                print "验证码错误"
        pobj['telphone'] = self.telphone
        ckurl = "http://zc.qq.com/cgi-bin/common/check_phone?telphone=%s&r=%s" % (pobj['telphone'], random.random())
        con = self.request_url(ckurl, headers=headers)
        j = json.loads(con.text)
        if int(j['ec']) != 0:
            print "手机号已经不能用", j
            return

        smsvc = ''
        elevel = int(pobj['elevel'])
        if elevel == 4:
            print "发送短信 1 到  1069 0700 511 ，发送后稍等，按回车继续"
            sys.stdin.readline()
        elif elevel==1 or elevel==3:
            getsmsurl = 'http://zc.qq.com/cgi-bin/chs/common/sms_send_safe?r=%s' % random.random()
            data={'telphone': pobj['telphone'], 'elevel':elevel, 'regType':1, 'nick':pobj['nick']}
            con = self.request_url(getsmsurl, data=data, headers=headers)
            print con.text
            print "请输入短信验证码: "
            smsvc = sys.stdin.readline()
            smsvc = smsvc.strip()
        else:
            raise RuntimeError('不明elevel %d 待处理 ' % int(pobj['elevel']))

        ckurl = "http://zc.qq.com/cgi-bin/chs/numreg/get_acc_safe?r=%s" % random.random()
        pobj.update({'qzone_flag':1, 'smsvc':smsvc})
        con = self.request_url(ckurl, data=pobj, headers=headers)
        print con.text
        j = json.loads(con.text)
        #{"ec":17,"em":"sms_up&nbsp;check&nbsp;error"}
        # {"VerifyCodeResult":"2","bind_result":"2","ec":0,"mibao_result":"0","olduin":"264*****",
        # "phone_result":"1","safeverifyResult":"0","telphone":"13826537792","type":"0","uin":"2164760843"}
        if int(j['ec']) == 0:
            print "注册成功\n新号码： %s\n老号码： %s" % (j['uin'], j.get('olduin', ''))

if __name__ == '__main__':
    spider.util.use_utf8()
    r = RegQQ()
    if len(sys.argv) > 1:
        r.telphone = sys.argv[1]
    r.load_proxy('aproxy')
    r.doreg()
