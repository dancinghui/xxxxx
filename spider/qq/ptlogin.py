#!/usr/bin/env python
# -*- coding:utf8 -*-
import sys
import random
import re
import threading

import spider.util
import urllib
import json
import os
import base64
import time

from spider.runtime import Log
from spider.ipinemail import BaseEmail
from spider.spider import MultiRequestsWithLogin
from spider.captcha.lianzhong import LianzhongCaptcha
from Crypto.Cipher import AES

r"""
have image case:

>>https://ssl.ptlogin2.qq.com/check?regmaster=&pt_tea=1&pt_vcode=1&uin=283016336&appid=716027609&js_ver=10141&js_type=1&login_sig=LcCzQtNm7I6DcqJ1yHa8sd4smiUHu5JiLilBNrsJh0TF4xjwZCpvYDwi8rxgYNIV&u1=https%3A%2F%2Fgraph.qq.com%2Foauth%2Flogin_jump&r=0.5651564613141064
ptui_checkVC('1','exNin2YftTnqXZ6_PBVBxofuOxwbqmiSThss5xmXbuICHSQ2rSTxqg**','\x00\x00\x00\x00\x10\xde\x7c\x90','','0');

>>https://ssl.captcha.qq.com/cap_union_show?clientype=2&uin=283016336&aid=716027609&cap_cd=exNin2YftTnqXZ6_PBVBxofuOxwbqmiSThss5xmXbuICHSQ2rSTxqg**&pt_style=33&0.6849819258547322
ignore

>>https://ssl.captcha.qq.com/cap_union_getsig_new?clientype=2&uin=283016336&aid=716027609&cap_cd=exNin2YftTnqXZ6_PBVBxofuOxwbqmiSThss5xmXbuICHSQ2rSTxqg**&pt_style=33&0.6849819258547322&rand=0.10228582964677402
{"vsig":"gd9Qow8bPKnb4FvjEX5I_TM77L4ouzxyE-tjA-mly3ZCNYl0obVh5Avqh4y42ZknmDFAHqdUeQWthNPT8s-JvgTgzkGHiYmQeYI2y7XbYDGy4LOrQGg1Agw**","ques":""}

>>https://ssl.captcha.qq.com/getimgbysig?clientype=2&uin=283016336&aid=716027609&cap_cd=exNin2YftTnqXZ6_PBVBxofuOxwbqmiSThss5xmXbuICHSQ2rSTxqg**&pt_style=33&0.6849819258547322&rand=0.5879723208800172&sig=gd9Qow8bPKnb4FvjEX5I_TM77L4ouzxyE-tjA-mly3ZCNYl0obVh5Avqh4y42ZknmDFAHqdUeQWthNPT8s-JvgTgzkGHiYmQeYI2y7XbYDGy4LOrQGg1Agw**
<image>


>> https://ssl.captcha.qq.com/cap_union_verify_new?clientype=2&uin=283016336&aid=716027609&cap_cd=exNin2YftTnqXZ6_PBVBxofuOxwbqmiSThss5xmXbuICHSQ2rSTxqg**&pt_style=33&0.6849819258547322&rand=0.280420319677154&capclass=0&sig=gu4caxW62_eHLMHKMakcJMH0SNYA2OZON5U3wHDAT0iLV5R9h47flpzVt5DrOfJ9guMz9rJlwYEs2fnpMMTmz2ofCJiHtNtG3E4a3T6gp6BovRVzZmiNG2Q**&ans=%E7%BC%BA%E8%BE%83%E7%A7%A7%E6%A1%82&collect=iXIOnvRdio3BO7OeMS910FF4hUGTuxiqgNb_psvEgTJOttoC2d_2bj6KtuisWNtGjt9tD4U1rfbKS67pBfpdspx28Dc5jr2k04OSIxQPRPd7k5f4gveCtrAspp1_k_vEN5crjoyychg06XGhEdrDaA0G-aEkMxo1Gy-B5peb82ABMthMCGi-kERl0Y78zhy-gICAZaZp7qL-TzNJeU_6aKRSn_EiARHLlgUadRzm7nGSFMNZtWTmMjDm0JyQ5qgxrvgfeEZLeFpvquqBTau_9LVFZuAHLSzm2LQBd0TmUm-R9cw2hvur3lbvx_M6qJthOwyMqbciatSKu_igA5bawDP7P8qTrMcacgTibVWToXgDq_euSPET8GBl1YHlVAvXyFKu_2nziui6my9yUhOr57xu17IoCf9nuuk4tkp2wuqlEH89UOxMg8Z6Nhk_943nO79io7iGG5hwjRVzglAoBknLPGhCtT9jBO6IqhJPluFNlYgf9EI_DTLz4PiYnslCOvGVOGP5r55uq6SXYbNUidE6FCCSaL2Z2GX8ihVlNpm-cYweIiO9zToRkXEwuPOo
{"errorCode":"0" ,
"randstr" : "@HZ4" ,
"ticket" : "t02mIAz-_bzMHsJ5aRQekKpSsJbVeDI_n16kxhKF728oPeSarvOa9Im2a4NZnMfyKQiI4bj5JdtCp7QFotjSHv6XWfGxHNzSj5Q"
 , "errMessage":"验证失败，请重试。"}

>> https://ssl.ptlogin2.qq.com/login?u=283016336&verifycode=@HZ4&pt_vcode_v1=1&pt_verifysession_v1=t02mIAz-_bzMHsJ5aRQekKpSsJbVeDI_n16kxhKF728oPeSarvOa9Im2a4NZnMfyKQiI4bj5JdtCp7QFotjSHv6XWfGxHNzSj5Q&p=X7iUYgWGqIMQWdXI3oBp6zfab3LOspwS8xbBmVYgMT2K*8ilcTUZjhC2TVUqRNMmiHmkLmtkZB0A8RZXz99PL5YaM-l52WLyvrMRqwSx5CZrB2KuM*JVMhvsUdKf-BVzWvsm8zTlEnF6LN3lXE-UTtV-DsZ7FDbwjeQEgg3Xytr6JtBEC0C9dg-s3S4IRaBKb0bTiy3d6XVr6L2sYHmLRg__&pt_randsalt=0&u1=https%3A%2F%2Fgraph.qq.com%2Foauth%2Flogin_jump&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=4-13-1449134416269&js_ver=10141&js_type=1&login_sig=LcCzQtNm7I6DcqJ1yHa8sd4smiUHu5JiLilBNrsJh0TF4xjwZCpvYDwi8rxgYNIV&pt_uistyle=33&aid=716027609&daid=383&pt_3rd_aid=101188807&


"""


class QQPtLogin(MultiRequestsWithLogin):
    def __init__(self, ac, starturl):
        MultiRequestsWithLogin.__init__(self, ac)
        self.qqno = ac['qqno']
        self.qqpwd = ac['qqpwd']
        self.starturl = starturl
        self.isvalid = True
        self.lianzhongcheck = False

    def values(self, *v):
        return v
    def bin2string(self, bin):
        v = 0
        for c in bin:
            v = v*256 + ord(c)
        return v

    def get_param(self, url, arg, decode=False):
        url = re.sub(r'^.*?\?|#.*$', '', url)
        a = re.split('&', url)
        for i in a:
            nv = re.split('=', i, 1)
            if nv[0] == arg:
                if decode:
                    return urllib.unquote(nv[1])
                else:
                    return nv[1]
        return ''

    def get_token(self, skey):
        hash = 5381
        for i in range(0, len(skey)):
            hash += (hash << 5) + ord(skey[i])
        return hash & 2147483647

    def build_trace_data(self, img_start_time):
        img_end_time = int(time.time())
        if img_end_time - img_start_time < 3:
            time.sleep(3)
            img_end_time = int(time.time())

        TRDATA = {
            "keyboards":[9,72,8,8,224,79,78,89,66],
            "mousemove":[],
            "mouseclick":[],
            "opertimestamp":[img_start_time, img_end_time],
            "trycnt":1,
            "user_agent": self._user_agent,
            "plugins":["Default Browser Helper","Google Earth Plug-in","Java Applet Plug-in","Shockwave Flash"],
            "resolution":[1440,900],
            "timestamp":img_end_time - img_start_time
        }
        #.......................................
        trdata_enc = json.dumps(TRDATA)
        for i in range(0, 15-len(trdata_enc)%16):
            trdata_enc += ' '
        #print trdata_enc
        es = AES.new('0123456789abcdef', AES.MODE_CBC, '0123456789abcdef')
        trdata_enc = base64.encodestring(es.encrypt(trdata_enc + '\x01'))
        trdata_enc = re.sub(r'\+', '-', trdata_enc)
        trdata_enc = re.sub(r'/', '_', trdata_enc)
        trdata_enc = re.sub(r'=', '*', trdata_enc)
        return trdata_enc

    def resolve_image(self, rv, imgcode, uin, appid):
        u1p = {
            "aid" : appid,
            "uin" : uin,
            "clientype" : "2",
            "pt_style" : "33",
            "cap_cd" : imgcode,
            "rand": str(random.random())
        }
        con1 = self.request_url("https://ssl.captcha.qq.com/cap_union_show", params=u1p)
        vsig = spider.util.chained_regex(con1.text, r'var\s+g_vsig\s*=\s*"(.*?)"') [0]
        #con2 = self.request_url("https://ssl.captcha.qq.com/cap_union_getsig_new", params=u1p)
        #con2j = json.loads(con2.text)
        #vsig = con2j['vsig']
        u3p = {
            "uin" : uin,
            "rand" : str(random.random()),
            "cap_cd" : imgcode,
            "clientype" : "2",
            "aid" : appid,
            "sig" : vsig,
            "pt_style" : "33"
        }
        con3 = self.request_url("https://ssl.captcha.qq.com/getimgbysig", params=u3p)
        img_start_time = int(time.time())
        lc = LianzhongCaptcha()
        if hasattr(self, 'lianzhongcheck') is False:
            self.lianzhongcheck = False
        if  self.lianzhongcheck is False:
            with open('xx.jpg', 'wb') as fi:
                fi.write(con3.content)
            sys.stderr.write("input image code: ")
            uimgcode = sys.stdin.readline().strip()
        else:
            pc = lc.point_check()
            print '========begin lianzhong img input with points:', pc
            if pc > 0:
                uimgcode = lc.resolve(con3.content)
                print "image codde is:", uimgcode
            else:
                sys.stderr.write("cant resolve image by lianzhong.\n")
                time.sleep(3)
                return False
        chks = {
            "uin" : uin,
            "rand" : str(random.random()),
            str(random.random()):"",
            "capclass" : "0",
            "cap_cd" : imgcode,
            "sig" : vsig,
            "clientype" : "2",
            "aid" : appid,
            "ans" : uimgcode,
            "collect" : self.build_trace_data(img_start_time),
            "pt_style" : "33"
        }
        con4 = self.request_url("https://ssl.captcha.qq.com/cap_union_verify_new", params=chks)
        sys.stderr.write("verify imgcode %s : %s\n" % (uimgcode, con4.text))
        j4 = json.loads(con4.text)
        if int(j4.get('errorCode', '-1')) == 0:
            rv.update(j4)
            return True
        else:
            if lc:
                sys.stderr.write("verify imagecode %s : mark lianzhong error!\n" % uimgcode)
                lc.mark_last_error()
            return False

    def do_pt_login(self, objarr):
        con1 = self.request_url(self.starturl)
        while con1 is None:
            print "req failed wait 5s"
            time.sleep(5)
            con1 = self.request_url(self.starturl)
        appids_ = spider.util.chained_regex(con1.text, r"appid=(\d+)")
        if appids_ is None or len(appids_) == 0:
            Log.error("ptlogin 1st step failed, maybe blocked.")
            time.sleep(5)
            return False
        appid = appids_[0]
        apphost = spider.util.chained_regex(self.starturl, r"://(.*?)/") [0]
        pt_3rd_aid = self.get_param(con1.request.url, 'client_id')

        url2 = spider.util.chained_regex(con1.text, r"""(https://xui.ptlogin2.qq.com.*?)['"]""")[0]
        url2 += "https%3A%2F%2Fgraph.qq.com%2Foauth%2Flogin_jump&"
        url2 += "pt_3rd_aid=" + pt_3rd_aid + "&"
        url2 += "pt_feedback_link=http%3A%2F%2Fsupport.qq.com%2Fwrite.shtml%3Ffid%3D780%26SSTAG%3D"+apphost+".appid"+appid
        con2 = self.request_url(url2)

        url3_params = {
            "appid" : appid,
            "uin" : self.qqno,
            "r" : str(random.random()),
            "pt_tea" : "1",
            "js_ver" : "10141",
            "login_sig" : self.get_cookie('pt_login_sig'),
            "pt_vcode" : "1",
            "u1" : "https://graph.qq.com/oauth/login_jump",
            "regmaster" : "",
            "js_type" : "1"
        }
        con3 = self.request_url("https://ssl.ptlogin2.qq.com/check", params=url3_params)
        code = re.sub('ptui_checkVC', 'self.values', con3.text)
        code = re.sub(';', '', code)
        (type, imgcode, binuin, pt_verifysession, isRandSalt) = tuple(eval(code))
        uin = self.bin2string(binuin)
        pt_vcode_v1 = '0'
        #print type, imgcode, uin, pt_verifysession, isRandSalt
        if int(type) == 1:
            rv = {}
            if self.resolve_image(rv, imgcode, uin, appid):
                imgcode = rv['randstr']
                pt_verifysession = rv['ticket']
                pt_vcode_v1 = '1'
            else:
                print 'failed to resolve image.'
                time.sleep(5)
                return False

        b64salt = re.sub(r'\s+', r'', base64.encodestring(binuin), 0, re.S)
        postpwd = os.popen("getqqpwd \"%s\" \"%s\" \"%s\"" % (self.qqpwd, b64salt, imgcode)).read().strip()

        url4_params = {
        "pt_uistyle" : "33",
        "from_ui" : "1",
        "login_sig" : self.get_cookie('pt_login_sig'),
        "pt_vcode_v1" : pt_vcode_v1,
        "pt_3rd_aid" : pt_3rd_aid,
        "aid" : appid,
        "h" : "1",
        "pt_verifysession_v1" : pt_verifysession,
        "daid" : "383",
        "g" : "1",
        "t" : "1",
        "ptlang" : "2052",
        "js_ver" : "10141",
        "u1" : "https://graph.qq.com/oauth/login_jump",
        "pt_randsalt" : "0",
        "p" : postpwd,
        "action" : "2-17-1449122627807",
        "ptredirect" : "0",
        "verifycode" : imgcode,
        "u" : uin,
        "js_type" : "1"
        }
        con4 = self.request_url("https://ssl.ptlogin2.qq.com/login", params=url4_params)
        code = re.sub('ptuiCB', 'self.values', con4.text)
        code = re.sub(';', '', code)
        kkkk = eval(code)
        sys.stderr.write("ptlogin: %s\n" % json.dumps(kkkk, indent=None, ensure_ascii=0).encode('utf-8'))

        if int(kkkk[0]) == 0:
            con5 = self.request_url(kkkk[2])
            url6_params = {
                "response_type" : self.get_param(con1.request.url, 'response_type'),
                "src" : "1",
                "g_tk" : self.get_token(self.get_cookie('skey')),
                "openapi" : "80901010",  #获得性别昵称头像
                "client_id" : pt_3rd_aid,
                "state" : self.get_param(con1.request.url, 'state'),
                "auth_time" : int(time.time()*1000),
                "ui" : "A79902F0-2179-41A7-ABE9-2E685201E2B6",
                "redirect_uri" : self.get_param(con1.request.url, 'redirect_uri', True),
                "scope" : self.get_param(con1.request.url, 'scope', True),
                "update_auth" : "1"
            }
            con6 = self.request_url('https://graph.qq.com/oauth2.0/authorize', data=url6_params)
            objarr.append(con6)
            return True
        else:
            if u'您输入的帐号或密码不正确' in kkkk[4]:
                self.isvalid = False
            if u'您的账号暂时无法登录' in kkkk[4]:
                self.isvalid = False
            return False

    def is_valid(self):
        return self.isvalid
