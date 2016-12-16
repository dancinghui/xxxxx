#!/usr/bin/env python
# -*- coding:utf8 -*-


import bitstring

bit_model = [
    ('has_gender', 'uint:1'),
    ('has_industry', 'uint:1'),
    ('has_salary', 'uint:1'),
    ('has_birthday', 'uint:1'),
    ('has_update_ts', 'uint:1'),
    ('has_work_period', 'uint:1'),
    ('has_diploma', 'uint:1'),
    ('has_school_type', 'uint:1'),
    ('has_exp_industry', 'uint:1'),
    ('has_zhiji', 'uint:1'),
    ('has_exp_location', 'uint:1'),
    ('has_cur_location', 'uint:1'),
    ('has_qudao', 'uint:1'),
    ('has_reserved', 'uint:19'),
    ('gender', 'uint:2'),
    ('industry_0', 'uint:6'),
    ('industry_1', 'uint:6'),
    ('industry_2', 'uint:6'),
    ('industry_3', 'uint:6'),
    ('industry_4', 'uint:6'),

    ('exp_salary_min', 'uint:32'),
    ('exp_salary_max', 'uint:32'),

    ('birthday_min', 'uint:16'),
    ('birthday_max', 'uint:16'),
    ('cv_update_ts', 'uint:16'),

    ('work_period_min', 'uint:5'),
    ('work_period_max', 'uint:5'),

    ('edu', 'uint:4'),
    ('edu_type', 'uint:2'),

    ('exp_industry_0', 'uint:6'),
    ('exp_industry_1', 'uint:6'),
    ('exp_industry_2', 'uint:6'),
    ('exp_industry_3', 'uint:6'),
    ('exp_industry_4', 'uint:6'),

    ('zhiji', 'uint:2'),

    ('location_cur', 'uint:16'),
    ('qudao', 'uint:3'),
    ('reserved_0', 'uint:13'),
    ('exp_location_0', 'uint:16'),
    ('exp_location_1', 'uint:16'),
    ('exp_location_2', 'uint:16'),
    ('exp_location_3', 'uint:16'),

]

BIT_LENGTH = 80


def convert_bitarray(s, t='0x'):

    result = {}
    if len(s) != 80:
        return 0, "bit length error, need length: %d" % BIT_LENGTH

    bit_stream = bitstring.BitStream("%s%s" % (t, s))

    for l in bit_model:
        key, pattern = l
        value = bit_stream.read(pattern)
        result[key] = value

    return 1, result

