#!/usr/bin/env python
# encoding:utf-8

import StringIO
from spider.httpreq import BasicRequests
import re
import time
import json

class OnlineOCR(object):
    def __init__(self, type_):
        self.server = 'http://www.haohaogame.com:8099/codeocr'
        self._type = type_

    def resolve(self, getimg, fc=None):
        while True:
            imgcon = getimg(dbgdata=fc)
            f = StringIO.StringIO()
            f.write(imgcon)
            f.seek(0)
            h = BasicRequests()
            imgcode = None
            if fc is not None and isinstance(fc, dict) and "type" in fc:
                response = h.request_url(self.server, files={'file': imgcon}, data={"province": self._type})
                result = response.text.strip()
                if '"valid":true' in result:
                    try:
                        result = json.loads(result)
                        imgcode = result["answer"]
                        if imgcode == None or imgcode == "":
                            print "验证码图片识别错误　imgcode==None或''"
                            continue
                    except Exception as err:
                        print "验证码图片识别错误，重新校验...,result:", result, "错误原因:", err
                        time.sleep(1)
                        continue
            else:
                url = "%s?type=%s" % (self.server, self._type)
                response = h.request_url(url, files={'file': f})
                imgcode = response.text.strip()
                if imgcode == '<fail>':
                    print "验证码图片识别错误　imgcode==<fail>"
                    continue
            if isinstance(fc, dict):
                fc['content'] = imgcon
                fc['code'] = imgcode
            return imgcode


if __name__ == '__main__':
    o = OnlineOCR('guangdong')
    o.server = 'http://127.0.0.1:8000/codeocr'
    imgc = open("0001.png").read()
    print o.resolve(lambda: imgc)
