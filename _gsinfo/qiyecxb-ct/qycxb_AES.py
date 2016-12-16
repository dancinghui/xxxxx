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

def utf8str(obj):
    if isinstance(obj, unicode):
        return obj.encode('utf-8')
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict) or isinstance(obj, list):
        return utf8str(json.dumps(obj, ensure_ascii=False, sort_keys=True))
    return utf8str(str(obj))

#抓包原版的请求字符串
# old_req ={"encryptedJson":"ZlWT15DsXFm0Y4QnYoK2ufXYi39Plo9\/yhwguqs9FWAHRqkKsKobDI+ai8+GR4NTJNeaHC7hDsivmsbOkOQ\/0lHsES3Wl5kF+pLW98YratGzlf4Tc5qnXiNDVUrc0WaqdACEGfMU\/P1+RrPDiH3ybXMKIP9Z6BAX\/7GroMy0pA3bmSD8q5nfPLXhU0B6SvgxddhPSIrQgCQTngVZWAo642fczbA7oPREkw1C6TwaI8aDOq2\/ALXTm3dvVOSODXsL9id8KB\/hbfUKUkEXe+myfQPZP5bGIvwB5MB5oB8lhGhtgHjVlVSZ7oURGsvganYX","extJson":"Hoi6oX70l9whauZmjq8jVAmoe3UspXXhX9mPG+KAeqs1rKZVr\/uapICH92P\/Crryt63u28aP4QP665AzcT\/jN5Go1o3bvwMvVIkuN9e60k6WI2pVFBrwZMvxwW6BnQukSzDSlyPvEhgpR5DIHQEV6C51hMgp4Zc3OkTSsyezAm4="}
# #通过原版解密原始格式加密出来的字符串
# req ={"encryptedJson": "cddSf6tJVUACGIdpU8mFR4mSZTct0LR1VS51Ro17\/V8dIFKd\/\/U4pVhAArBR8hpNnYQhkl7YFOrD59PLlYdr2\/nrrpt+ZtBkpRDq842VY3ssMJXrbMtXM7UrGSr8GEUoiyrnsDN0IY6o+A6lEr\/dlkSPthKq+TUmp1rOErYrI6cnSPS+CDIAL8lpkI1PkYw7MFZdlO\/c57oVXMmMFqFqfNE+rWdtKLXmSzt6\/rtX5oinWwBVszWApOHaM9onvawgiN9zltt7y8yx+IHz2W7R7A==", "extJson": "91kvxt0YIb+WInIsnkeky\/6ILdosT8urcbPoThaeBQ\/E9JibEbQ1UAeFPbay0DigxA6yybwuUzHKHsibZZntfJQ6NtfpjBgUpetjrgIALgC2A1LsWP+isw38lHRxO2gyfw\/MkO+m0LbK324avj7Yug=="}

#vv = {"c":"6u3wX+2kA6d3zgDt29gnvrRPs50goSUYwahsssPi4wUeZwPiphqoCaSpyQNw1+jMOQsUW7X9je1xRZAYinrpzQOVC/RJQfIPUKW69ySG9En5KQ8br4BJyY8u6H4JhM2hKM+lZpyJ5Qjif4by85M8qGkgE1ZqFvAO0uCIbxw+QGfc4L//fIWfJaAgZ2eauvyHFeEZakGoXVDWV0F6Rca+Gw3IC7k90USNmLhcCRBXU8p0/3NZdN5008OF3g8kFCMaqD/2gmvjCXswb9gxHx+3n5OsFpYBHAgIlxTwA0v6Kksl7/OmC18vYSVvC9NOqVeqfbkzfc+U0wd6FyOepYekVAvnRGamjRXa7eIGgo0EMht7uYKxPBYrw6oY+3t83QvKJX8cgHIEEXUAvm6gdwJiBrd/3ukm0R+DBlvmIv0nVq+gr5re3K8dKkf+O2c70/LuH8oVXAp3Ooozeh0XS7C/yvLJvKg1yxT05pOmAAFltt7HBgqUcklY1asT8bMG3uiHNBv2ZCdBK113UMeuxuztTlUJk4P+R42gO27f1z28VcHYE3/nd1BJ9UmNCqA9SWRiSJ3lIVJsQucV+NcCKLQxpoqzyH1L5zM+ksIgYLc4yS4=","v":"m2JSqrBtIXdQ4Vq6LTC1kw==","m":"BsRioKDdMi3oPdq2Klc/Bw=="}

#aa = {"f":"s6Wuhvfllbffl8U3ekqoeRygAECfl93fUCAwOG1rQ2V357ItCE2F87JCy/c5N30K","a":"ec96mWLLzjTkoRuQ6qOIRA==","i":"oXjwX1++ts9jKk5tY4tq1Q==","dbt":"1","uce":"1","iuce":"1","da":"s6SGN8suIqpknJiwMohkSyEvIDsNWGcB4RK3nXTnl79SSCryDPAvbNKwbDqCiqdXMzTU1C7j443yiqg5FHEtpOcrN0u2nsZGsxkLmgxs6Jg=","v":"K+bxWI5FFzN6UzB2rt+LUA==","m":"BsRioKDdMi3oPdq2Klc/Bw=="}


#req = {"extJson":"ctlCXDvoyaH2pCIArrgvXp7zrZTzpz2Q5rukh+aWvupEFABw6P2AvbmaN+HJ7IZgDJ\/kgBkJt\/rLppSGitYCPKGR2IGv6OXZsrJGgbRB3G3Ac4K8xpX3aMB5s8Ci2a\/YpTpioZxAvptqJsQUCoNn0tLCOVM4XxMJQWbrErkOcl4=","encryptedJson":"qelpntcS6pbFQdCD4jTENWsCKv88oVo0SiYpMatl\/Ur522lOV2PpLQQnLXSfkpK3\/02cg6E\/I\/ajPlSbpz5WmdQ5G12mCBacgpLQBkWafKQlzuPURKibVw1z\/7qO\/4nuLvYkuAeiHp3wqF4drUJOkQRCWFscq9McZm+mIEXk8eWxbjAaPBJEqXF9dFc2OspatHdigFE+RpdSe6Zv+119n8i6VOiuC\/TNYGUl9PDB2isOlVnRihYx6Wu1Kd30tao3ZALKDSH1yVRaV\/0R0kL2JpXFRcoREgJcvgD+VoP0WjaMmeiznWVuVp1zSAva9KI56VpbnxJeTK3Ue+gQphPJrA=="}
req = {"extJson":"ctlCXDvoyaH2pCIArrgvXp7zrZTzpz2Q5rukh+aWvupEFABw6P2AvbmaN+HJ7IZgDJ\/kgBkJt\/rLppSGitYCPKGR2IGv6OXZsrJGgbRB3G1U2wdOlL49\/aDwt3NZNp4TGa5iBFpYLm69F\/6PPFoXIR\/Aw5p48\/\/8OgZFpddDUwQ=","encryptedJson":"Tfd+Vc+oPKhLR1l6O2NBjViplapJ\/VoxBHx0e7P36uIgKOguZwqpIa8Bskt9TozJNX0CyJEkdnOEAmDF9XqWLqOhpkmLivxXVnu7T\/XR5FN3cFVONJg1FSTglm0QCB3AyqzuxlCggCmednjqxIwTo+dpv4GPtSFNohZFNAzxTmBBr5b2AAw4Qhag0opOeIcx4sPEGCxjC++qO\/I0e2UVeQ=="}

vv = {"c":"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","v":"K+bxWI5FFzN6UzB2rt+LUA==","m":"BsRioKDdMi3oPdq2Klc/Bw=="}



if __name__ == '__main__':
    # print '--------------解密请求数据------------原版--------'
    # for n, v in old_req.items():
    #     print n, "=", CCIQ_AES().decrypt(v)
    print '--------------解密请求数据--------------------'
    for n, v in req.items():
        print n, "=", CCIQ_AES().decrypt(v)
    print '--------------解密响应数据--------------------'
    for n in ["v", "m", "c"]:
        o = CCIQ_AES().decrypt(vv[n])
        print n, "=", len(o), o
    #o = CCIQ_AES("BB1856A312580D41256311147089E0CC").decrypt(vv['c'])
    o = CCIQ_AES("BF1856A312580D41256311147089E1CC").decrypt(vv['c'])
    print len(o), o
    # print "----------------------------------"
    # for x in ["f", "a","i","da","v","m"]: #, "c"
    #     o = CCIQ_AES().decrypt(vv[n])
    #     print x, "=", len(o), o
#     encryptedJson = {
#   "pagesize" : "20",
#   "page" : "1",
#   "od_orderBy" : "0",
#   "sh_searchType" : "一般搜索",
#   "sh_oc_areaName" : "",
#   "od_statusFilter" : "0",
#   "v1" : "QZOrgV005",
#   "oc_name" : "腾讯",
#   "sh_u_uid" : "",
#   "sh_u_name" : ""
# }

#     extJson = {
#   "cl_screenSize" : "640x960",
#   "cl_cookieId" : "B200BA9D-A3A0-4140-A293-9A1A671BA5CE",
#   "Org_iOS_Version" : "2.0.1"
# }
#     print utf8str(encryptedJson)
#     param = utf8str({"encryptedJson": CCIQ_AES().encrypt(utf8str(encryptedJson)), "extJson": CCIQ_AES().encrypt(utf8str(extJson))})
#     param = param.replace('/', "\/")
#     print "加密后参数:",param
#     old = 'ZlWT15DsXFm0Y4QnYoK2ufXYi39Plo9\/yhwguqs9FWAHRqkKsKobDI+ai8+GR4NTJNeaHC7hDsivmsbOkOQ\/0lHsES3Wl5kF+pLW98YratGzlf4Tc5qnXiNDVUrc0WaqdACEGfMU\/P1+RrPDiH3ybXMKIP9Z6BAX\/7GroMy0pA3bmSD8q5nfPLXhU0B6SvgxddhPSIrQgCQTngVZWAo642fczbA7oPREkw1C6TwaI8aDOq2\/ALXTm3dvVOSODXsL9id8KB\/hbfUKUkEXe+myfQPZP5bGIvwB5MB5oB8lhGhtgHjVlVSZ7oURGsvganYX'
#     new = CCIQ_AES().encrypt(utf8str(encryptedJson))
#     new = new.replace("/","\/")
#     if len(new) == len(old):
#         print "success!"
#     else:
#         print len(old)
#         print 'old:',old
#         print len(new)
#         print 'new:',new
#         print 'sub:',(len(old)-len(new))
#
#     test = CCIQ_AES().encrypt(utf8str(" "))
#     print len(test), test