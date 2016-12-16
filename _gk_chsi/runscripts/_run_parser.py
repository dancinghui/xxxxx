#!/usr/bin/env python
# -*- coding:utf8 -*-
from _detail_parser import GkChsiDetailParser
from _gk_spec_parser import GkChsiSpecParser
from accounts import provinces
from _gk_school_parser import GkChsiSchoolParser


def run_school_parser(name):
    job = GkChsiSchoolParser(name, 'yggk_sch_%s' % provinces[name], save_title=False,
                             save_name='spec.seeds.%s' % provinces[name])
    job.run()

def run_detail_parser(name):
    job = GkChsiDetailParser(name, 'yggk_detail_%s' % provinces[name], save_title=True)
    job.run()


def run_spec_parser(name):
    job = GkChsiSpecParser(name, 'yggk_spec_%s' % provinces[name], save_title=True)
    job.run()


def run_parser(name):
    run_school_parser(name)
    run_spec_parser(name)
    run_detail_parser(name)


if __name__ == '__main__':
    names = [
        # '广东',
        # '江西',
        # '山东',
        # '青海',
        '湖南',
        '江苏',
        '陕西',
        '安徽',
        '黑龙江',
        '山西',
        '吉林',
        '宁夏',
        '辽宁',
    ]
    for name, short in provinces.items():
        print name, short
        # run_parser(name)
        run_school_parser(name)