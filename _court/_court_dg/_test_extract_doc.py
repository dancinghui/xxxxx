#!/usr/bin/env python
# -*- coding:utf8 -*-
from docx2txt import docx2txt
from textextraction.extractors import text_extractor

if '__main__' == __name__:
    # doc = u'/home/skiloop/Downloads/wsz1_100153_7.doc'
    doc = '/tmp/288ae070-c91c-497c-839e-1bba712d2aa0.doc'
    try:
        text = docx2txt.process(doc)
    except Exception as e:
        print e.message
        text = text_extractor(doc,True)
    print text
