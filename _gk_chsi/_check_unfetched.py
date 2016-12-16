#!/usr/bin/env python
# -*- coding:utf8 -*-
import os

from _gk_chsi import GkChsiFsxStore
from accounts import provinces


def check_spec(seed, store):
    if seed[0] == '{':
        jobid = eval(seed.strip())
    else:
        param = seed.strip().split(',')
        jobid = {'wclx': 1, 'yxdm': param[6], 'kldm': param[2], 'bkcc': param[4], 'start': 0,
                 'years': param[5],
                 'yxmc': param[7].decode('utf-8')}
    jtitle = '%s/%s/%s/%s/%s/%s' % (
        jobid['yxdm'], jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['wclx'],
        jobid['start'])
    return store.find_any(store.channel + '://' + jtitle)


def check_detail(seed, store):
    if seed[0] == '{':
        jobid = eval(seed)
    else:
        param = seed.strip().split(',')
        jobid = {'wclx': 1, 'yxdm': param[6], 'kldm': param[2], 'bkcc': param[4], 'start': 0,
                 'years': param[5], 'zydm': param[7], 'zymc': param[8].encode('utf-8')}
    jtitle = '%s/%s/%s/%s/%s/%s/%s/%s' % (
        jobid['yxdm'], jobid['years'], jobid['kldm'], jobid['bkcc'], jobid['wclx'],
        jobid['start'], jobid['zydm'], int(jobid['start']) / 10)
    return store.find_any(store.channel + '://' + jtitle)


def check_unfetched(seeds, channel, spec=False):
    store = GkChsiFsxStore(channel)
    lines = []
    with open(seeds, 'r') as f:
        for l in f:
            lines.append(l.strip())
    seeds = []
    print 'seed size', len(lines)
    if spec:
        for seed in lines:
            if not check_spec(seed, store):
                seeds.append(seed)
    else:
        for seed in lines:
            if not check_detail(seed, store):
                seeds.append(seed)
    print 'unfetched seeds ', len(seeds)
    return [len(lines), len(seeds)]
    # c = 3
    # for seed in seeds:
    #     print seed
    #     c -= 1
    #     if c <= 0:
    #         break


def check_and_save_unfetched(seedfile, channel, spec=False):
    store = GkChsiFsxStore(channel)
    lines = []
    with open(seedfile, 'r') as f:
        for l in f:
            lines.append(l.strip())
    seeds = []
    print 'seed size', len(lines)
    if spec:
        for seed in lines:
            if not check_spec(seed, store):
                seeds.append(seed)
    else:
        for seed in lines:
            if not check_detail(seed, store):
                seeds.append(seed)
    print 'unfetched seeds ', len(seeds)

    with open('%s.unfetched' % seedfile, 'w') as f:
        for l in seeds:
            f.write(str(l) + '\n')
    return [len(lines), len(seeds)]


def check_all(channel):
    res = []
    for name, short in provinces.items():
        print 'check', channel, name
        seeds = '%s.seeds.%s' % (channel, short)
        if os.path.exists(seeds):
            data = check_unfetched(seeds, 'yggk_%s_%s' % (channel, short), channel == 'spec')
            res.append('%s,%s,%s' % (name, data[0], data[1]))
    with open('status.dat', 'w') as f:
        for r in res:
            f.write(r + '\n')


if __name__ == '__main__':
    # print 'spec chongqing'
    # check_unfetched('spec.seeds.fj', 'yggk_spec_fj', True)
    check_unfetched('detail.seeds.fj', 'yggk_detail_fj', False)
    # check_all('spec')
