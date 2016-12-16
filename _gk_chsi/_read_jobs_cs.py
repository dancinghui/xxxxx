#!/usr/bin/env python
# -*- coding:utf8 -*-

if __name__ == '__main__':
    accounts = []
    with open('accounts', 'r') as f:
        line =f.readline()
        ls=line.split('}')
        for ll in ls:
            accounts.append(ll.strip()+'}')
    with open('acs','w') as f:
        for a in accounts:
            f.write(a.strip()+'\n')