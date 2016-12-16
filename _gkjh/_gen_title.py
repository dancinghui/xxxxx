#!/usr/bin/env python
# -*- coding:utf8 -*-
from gkutils import parser

if __name__ == '__main__':
    f = open('header.dat', 'w')
    header = {}
    header['year'] = u'年份'.encode('utf-8')
    header['yxdm'] = u'院校代码'.encode('utf-8')
    header['school'] = u'高校名称'.encode('utf-8')
    header['pici'] = u'招生批次'.encode('utf-8')
    header['kelei'] = u'科类'.encode('utf-8')
    header['zydh'] = u'专业代号'.encode('utf-8')
    header['zymc'] = u'专业名称'.encode('utf-8')
    header['jhxz'] = u'计划性质'.encode('utf-8')
    header['xz'] = u'学制'.encode('utf-8')
    header['num'] = u'招生人数'.encode('utf-8')
    header['yz'] = u'语种'.encode('utf-8')
    header['xf'] = u'学费'.encode('utf-8')
    header['beizhu'] = u'备注'.encode('utf-8')
    header['leipie'] = u'类别'.encode('utf-8')
    parser = parser.Parser('header', header)
    parser.save(f, header)
