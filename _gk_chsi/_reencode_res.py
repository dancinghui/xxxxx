#!/usr/bin/env python
# -*- coding:utf8 -*-
import os

provinces = {'北京': 'beijing',
             '天津': 'tianjin',
             '河北': 'hebei',
             '山西': 'shanxity',
             '内蒙古': 'neimeng',
             '辽宁': 'liaoning',
             '吉林': 'jilin',
             '黑龙江': 'heilongjiang',
             '上海': 'shanghai',
             '江苏': 'jiangshu',
             '浙江': 'zhejiang',
             '安徽': 'anhui',
             '福建': 'fujian',
             '江西': 'jiangxi',
             '山东': 'shandong',
             '河南': 'henan',
             '湖北': 'hubei',
             '湖南': 'hunan',
             '广东': 'guangdong',
             '广西': 'guangxi',
             '海南': 'hainan',
             '重庆': 'chongqing',
             '四川': 'sichuan',
             '贵州': 'guizhou',
             '云南': 'yunnan',
             '西藏': 'xizang',
             '陕西': 'shanxixa',
             '甘肃': 'gansu',
             '青海': 'qinghai',
             '宁夏': 'ningxia',
             '新疆': 'xinjiang'}


def reencode(name, tag):
    for channel in ['school', 'spec', 'detail']:
        if os.path.exists('res_%s_%s.csv' % (channel, name)):
            os.system('iconv -f utf-8 -t gbk %s -o results/%s' % (
            'res_%s_%s.csv' % (channel, name), 'res_%s_%s.csv' % (channel, tag)))


def rename_all_results():
    for name, tag in provinces.items():
        reencode(name, tag)


if __name__ == '__main__':
    rename_all_results()
