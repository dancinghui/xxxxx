#!/usr/bin/env python
# -*- coding:utf8 -*-

import tika
from tika import parser


class Doc2Txt:
    "extract text from doc or pdf with Apache Tika"

    @staticmethod
    def init():
        tika.initVM()

    @staticmethod
    def extract_from_file(urlOrPath):
        p = parser.from_file(urlOrPath)
        if p != {}:
            return p['content']
        else:
            return None

    @staticmethod
    def extract_from_buffer(string):
        p = parser.from_buffer(string, xmlContent=True)
        if p != {}:
            return p['content']
        else:
            return None


if '__main__' == __name__:
    Doc2Txt.init()
    # doc = '/tmp/288ae070-c91c-497c-839e-1bba712d2aa0.doc'
    # print Doc2Txt.extract_from_file(doc).strip()
    print Doc2Txt.extract_from_file('http://222.82.211.38:8002/ftproot/webinfo/data1/doc/wsz1_98669_4.pdf')
