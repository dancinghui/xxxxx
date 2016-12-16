#!/usr/bin/env python
# -*- coding:utf8 -*-
import io
import tesseract_ocr
import pyocr
from PIL import Image

from court.util import Captcha

from spider.httpreq import BasicRequests

if __name__ == '__main__':

    rq = BasicRequests()
    rq.select_user_agent('firefox')
    rq.set_proxy('106.75.134.191:18888:ipin:ipin1234')
    # con = rq.request_url('http://ssfw.szcourt.gov.cn/yzm.jsp')
    con = rq.request_url('http://www.bjcourt.gov.cn/yzm.jpg')
    if not con:
        print 'failed to fetch image'
    else:
        t = tesseract_ocr.Tesseract()
        text = t.text_for_bytes(con.content)

        print text
        with open('a.jpeg', 'wb') as f:
            f.write(con.content)

        print Captcha.resolve('a.jpeg','1')
