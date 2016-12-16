#!/usr/bin/env python
# -*- coding:utf8 -*-
from accounts import provinces
from runner import Counter

if __name__ == '__main__':
    for name, code in provinces.items():
        for channel in ['sch', 'spec', 'detail']:
            counter = Counter('yggk_%s_%s' % (channel, code))
            counter.run('account.%s.%s.log' % (code, channel))
