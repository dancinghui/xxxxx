#!/usr/bin/env python
# -*- coding:utf8 -*-
import sys


def char_value(char):
    if char[0].isdigit():
        return int(char[0])
    elif char[0].isupper():
        return ord(char[0]) - 55
    raise ValueError('invalid code: %s' % char[0])


def code2list8(code):
    v = []
    for c in code[:8]:
        v.append(char_value(c))
    return v


def code2list(code):
    v = code2list8(code)
    v.append(int(code[8]) if code[8].isdigit() else 0)
    return v


def verify_code(code):
    if not isinstance(code, str) and not isinstance(code, unicode):
        raise ValueError('invalid type')
    if isinstance(code, unicode):
        code = code.encode('utf-8')
    c_code = code2list8(code)
    weight = [3, 7, 9, 10, 5, 8, 4, 2]
    s = 0
    for i in range(8):
        s += c_code[i] * weight[i]
    result_code = 11 - s % 11
    return '0123456789X'[result_code % 11]


def verify(fn):
    count = 0
    success = 0
    failed = 0
    invalid = 0
    ivf = open('invalid.txt', 'w')
    ff = open('failed.txt', 'w')
    sf = open('success.txt', 'w')
    with open(fn, 'r') as f:
        for l in f:
            code = l.strip()
            count += 1
            if len(code) != 9:
                invalid += 1
                print code
                ivf.write(l)
                continue
            try:
                code = code.replace('-', '')
                vc = verify_code(code)
                if vc == code[8]:
                    success += 1
                    sf.write(l)
                else:
                    failed += 1
                    ff.write(l)
            except (ValueError, IndexError):
                invalid += 1
                print code
                ivf.write(l)
    print 'count: %d\nsuccess: %d\nfailed: %d\ninvalid: %d\n' % (count, success, failed, invalid)


def test_verify(code):
    vcode = verify_code(code)
    if len(code) > 8:
        print vcode == code[8]
        print 'verify code:', vcode
    else:
        print '%s%s' % (code, vcode)


def int2code(c):
    if c >= 10000000:
        return '%d' % c
    elif c >= 1000000:
        return '0%d' % c
    elif c >= 100000:
        return '00%d' % c
    elif c >= 10000:
        return '000%d' % c
    elif c >= 1000:
        return '0000%d' % c
    elif c >= 100:
        return '00000%d' % c
    elif c >= 10:
        return '000000%d' % c
    else:
        return '0000000%d' % c


def find_numeric(found, not_found):
    fr = []
    with open(found, 'r') as f:
        for l in f:
            fr.append(int(l.strip()))

    fr.append(100000000)
    i = 0
    l = len(fr)
    nf = open(not_found, 'w')
    while i < l - 1:
        for c in range(fr[i] + 1, fr[i + 1]):
            nc = int2code(c)
            print nc
            nf.write(nc + '\n')


def export_all(src, dst):
    s = open(src, 'r')
    d = open(dst, 'a')
    for l in s:
        r = eval(l.strip())
        print r
        d.write('%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (
            r['jgdm'].strip(), r['jgdz'].strip(), r['jgmc'].strip(), r['bzjgmcs'].strip(), r['jglx'].strip(),
            r['bzrq'].strip(), r['zcrq'].strip(), r['zfrq'].strip(), r['zch'].strip()))
    d.flush()


if __name__ == '__main__':
    # verify('oucode.txt')
    for argv in sys.argv[1:]:
        test_verify(argv)

    # find_numeric('numeric.txt', 'remain.txt')
    # export_all('nacao_queries_info.txt', 'res.csv')
    # export_all('nacao_queries_info_local.txt', 'res.local.csv')
