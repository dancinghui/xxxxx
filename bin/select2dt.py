#!/usr/bin/env python
# -*- coding:utf8 -*-

import json
import sys

from lxml import html


def main():
    ins = sys.stdin.read().decode('utf8')
    a = html.fromstring(ins)
    oa = []
    for i in list(a):
        if i.tag == 'option':
            value = i.attrib.get('value')
            if value is not None:
                it = i.text_content().strip()
                oa.append([value, it])
    print "\n\n"
    print json.dumps(oa, ensure_ascii=0).encode('utf8')

if __name__ == '__main__':
    main()
