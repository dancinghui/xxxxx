#!/usr/bin/env python
# -*- coding:utf8 -*-
import Image
import uuid

import cv2
import numpy as np
import pyocr
import os

from court.util import remove_file
from spider.captcha.lianzhong import LianzhongCaptcha


class Captcha:
    @staticmethod
    def resolve(filename, tag):
        img = cv2.imread(filename, 0)
        blur = cv2.GaussianBlur(img, (1, 1), 0)
        ret, thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)
        binary = thresh[3:-3, 2:-2]
        us = str(uuid.uuid4())
        outfile = '/tmp/' + us + '.png'
        result = ''
        for i in range(4):
            single = binary[0:14, 14 * i:14 * i + 14]
            cv2.imwrite(outfile, single)
            command = 'tesseract --tessdata-dir /usr/share/tesseract-ocr/tessdata/ %s %s -psm 10 digits 2> /dev/null && cat %s.txt' % (
                outfile, tag, tag)
            output = os.popen(command)
            result = result + output.read().strip()
        remove_file(outfile)
        return result

    @staticmethod
    def resolve_gk_chsi(image):
        arr = np.asarray(bytearray(image), dtype=np.uint8)
        img = cv2.imdecode(arr, -1)
        blur = cv2.GaussianBlur(img, (1, 1), 0)
        ret, thresh = cv2.threshold(blur, 100, 255, cv2.THRESH_BINARY)
        binary = thresh[3:-3, 2:-2]
        txt = ''
        for i in range(4):
            single = binary[0:14, 14 * i:14 * i + 14]
            simgb = single.tobytes()
            simg = Image.open(Image.io.BytesIO(simgb))
            txt += pyocr.tesseract.image_to_string(simg, builder=pyocr.tesseract.DigitBuilder())
        return txt

    @staticmethod
    def resolve_with_pyocr(img):
        tools = pyocr.get_available_tools()

        # img1=Image.frombytes('RGB',(60,20),con.content)
        img2 = Image.open(Image.io.BytesIO(img))
        if tools:
            tool = tools[0]
            txt = tool.image_to_string(img2, builder=pyocr.tesseract.DigitBuilder())
            return txt

    @staticmethod
    def resolve_with_lianzhong(img, test=False):
        server = LianzhongCaptcha()
        points = server.point_check()
        if points <= 0:
            print 'there are no more points'
            return
        if test:
            print 'There are %d points remaining' % points
        captcha = server.resolve(img)
        return captcha

    @staticmethod
    def resolve_my_self(img, test=False):
        ofs = open('yzm.jpg', 'w')
        ofs.write(img)
        ofs.flush()
        ofs.close()
        image = Image.open('yzm.jpg')
        image.show()
        code = raw_input()
        if test:
            print 'your captcha is', code
        return code
