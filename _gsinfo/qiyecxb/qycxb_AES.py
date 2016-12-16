#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
sys.path.append(sys.path[0]+"/..")
from spider.spider import Spider
from spider.httpreq import SessionRequests, CurlReq
import spider.util
import pycurl
import cutil
import json
import abc
from spider.runtime import Log
import time
import base64
from Crypto.Cipher import AES

class CCIQ_AES:
    def __init__( self, key = None ):
        self.key = key
        if self.key is None:
            self.key = "9BF70E91907CA25135B36B5328AF36C4"
        BS = 16
        self.pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
        self.unpad = lambda s : s[:-ord(s[len(s)-1:])]

    def encrypt(self, raw):
        iv = "\0" * 16
        raw = self.pad(raw)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(raw))

    def decrypt( self, enc ):
        iv = "\0" * 16
        enc = base64.b64decode(enc)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.unpad(cipher.decrypt(enc))


req ={"encryptedJson":"g5w1RrRgZK4VZLGyS4on8GPnQrLiRK\/vBKB5Li7mSEeRPQd6MeZ5kv6u9PeWN\/hhTrVMQ73ujhomGtjVDxiABT2GMR4hrVgqYZsOnkly55jc9Wy3snYgIo6BDlzRNzBggbt20WAaENvPwtKU48fnnzL+a5xsRuDhun1I7Mm2zFM=","extJson":"Hoi6oX70l9whauZmjq8jVAmoe3UspXXhX9mPG+KAeqs1rKZVr\/uapICH92P\/CrrycI\/OjobbzuafHXthwGM38\/RMXUoOjROK+Psk7SCSv2\/vBYNK3RYrJk26Fgu1HxLDg9LWqdILYeoDE2G3IezMHPYyzrU1yEoFGenXS1U8gvc="}

vv = {"c":"6u3wX+2kA6d3zgDt29gnvrRPs50goSUYwahsssPi4wUeZwPiphqoCaSpyQNw1+jMOQsUW7X9je1xRZAYinrpzQOVC/RJQfIPUKW69ySG9En5KQ8br4BJyY8u6H4JhM2hKM+lZpyJ5Qjif4by85M8qGkgE1ZqFvAO0uCIbxw+QGfc4L//fIWfJaAgZ2eauvyHFeEZakGoXVDWV0F6Rca+Gw3IC7k90USNmLhcCRBXU8p0/3NZdN5008OF3g8kFCMaqD/2gmvjCXswb9gxHx+3n5OsFpYBHAgIlxTwA0v6Kksl7/OmC18vYSVvC9NOqVeqfbkzfc+U0wd6FyOepYekVAvnRGamjRXa7eIGgo0EMht7uYKxPBYrw6oY+3t83QvKJX8cgHIEEXUAvm6gdwJiBrd/3ukm0R+DBlvmIv0nVq+gr5re3K8dKkf+O2c70/LuH8oVXAp3Ooozeh0XS7C/yvLJvKg1yxT05pOmAAFltt7HBgqUcklY1asT8bMG3uiHNBv2ZCdBK113UMeuxuztTlUJk4P+R42gO27f1z28VcHYE3/nd1BJ9UmNCqA9SWRiSJ3lIVJsQucV+NcCKLQxpoqzyH1L5zM+ksIgYLc4yS4=","v":"m2JSqrBtIXdQ4Vq6LTC1kw==","m":"BsRioKDdMi3oPdq2Klc/Bw=="}

if __name__ == '__main__':
    for n, v in req.items():
        print n, "=", CCIQ_AES().decrypt(v)
    print '----------------------------------'
    for n in ["v", "m"]: #, "c"
        o = CCIQ_AES().decrypt(vv[n])
        print n, "=", len(o), o
    print '----------------------------------'
    o = CCIQ_AES("BB1856A312580D41256311147089E0CC").decrypt(vv['c'])
    print len(o), o

    # encryptedJson = {
    #     "pagesize" : "20",
    #     "page" : "1",
    #     "od_orderBy" : "0",
    #     "sh_searchType" : "一般搜索",
    #     "od_statusFilter" : "0",
    #      "v1" : "QZOrgV004",
    #     "oc_name" : "腾讯",
    #     "sh_u_uid" : "",
    #     "sh_u_name" : ""
    # }
    # extJson = {
    #     "cl_screenSize" : "640x960",
    #     "cl_cookieId" : "16923697-D73E-485A-BDCF-68FAD456AC02",
    #     "Org_iOS_Version" : "2.0.1"
    # }
    # param = {"encryptedJson": CCIQ_AES().encrypt(encryptedJson.__str__()), "extJson": CCIQ_AES().encrypt(extJson.__str__())}
    # print param