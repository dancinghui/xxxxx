#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import uuid
import re

from util import remove_file


def swf2text(swf):
    if re.search('\||\&|>', swf):
        raise ValueError('Invalid swf file name')
    tmp = '/tmp/' + str(uuid.uuid4()) + '.txt'
    os.system('swfstrings %s >%s' % (swf, tmp))
    text = ''
    with open(tmp) as f:
        for l in f:
            text += l
    remove_file(tmp)
    return text


if '__main__' == __name__:
    text = swf2text('~/PycharmProjects/getjd/_court_yantian/a.swf')
    print text
