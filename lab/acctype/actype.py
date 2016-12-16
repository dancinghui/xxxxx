#!/usr/bin/env python
# -*- coding:utf8 -*-
import json
import spider.util
import cutil
import re
import sys
import gc

class AccChecker(object):
    def __init__(self):
        self.acs = []
        pass

    def add_from_json(self, filename, name):
        jd = json.JSONDecoder(encoding='utf-8')
        rv = []
        with open(filename) as f:
            idx = 0
            while True:
                n = f.readline()
                if n is None or n=='':
                    break
                n = n.strip()
                if n == '':
                    continue
                j,_ = jd.raw_decode(n)
                if j.has_key('crawlerName') and j.has_key('account') and j.has_key('password'):
                    if j['crawlerName'] == name:
                        idx += 1
                        ac = {'u':j['account'], 'p':j['password']}
                        rv.append(ac)
                elif j.has_key('u') and j.has_key('p'):
                    idx += 1
                    ac = {'u':j['u'], 'p':j['p']}
                    rv.append(ac)
        self.add(rv)

    def add_from_tab_file(self, name):
        acs = []
        with open(name) as f:
            while True:
                l = f.readline()
                if not l:
                    break
                try:
                    u,p = re.split(r'\t', l.strip())
                    acs.append({'u':u.strip(), 'p':p.strip()})
                except:
                    print "ERROR", l.strip()
                    raise
        self.add(acs)

    def add(self, acs):
        for ac in acs:
            if ac not in self.acs:
                self.acs.append(ac)

    def pop_to(self, acname):
        found = False
        acs2=[]
        for ac in self.acs:
            if found:
                acs2.append(ac)
            if ac['u'] == acname:
                found = True
        self.acs = acs2

    def docheck(self, cls):
        proxy_index = -1
        fo = open('check_result', 'a+b')
        for ac in self.acs:
            proxy_index += 1
            z = cls(ac)
            z.load_proxy("curproxy1", int(proxy_index/50), False)
            z.do_login()
            z.dump_result([fo, sys.stderr])
            z = None
            fo.flush()
            gc.collect()


def check_51job():
    c = AccChecker()
    cv51 = cutil.import_module("../../cv_51job/cv51.py")
    #c.add_from_json('accounts', '51job')
    #c.add_from_tab_file('51job')
    c.add_from_json('a', '')
    c.docheck(cv51.Job51Login)


def check_zhilian():
    c = AccChecker()
    cvzl = cutil.import_module("../../cv_zhilian/zl_login.py")
    #c.add_from_json('accounts', 'zhilian')
    #c.add_from_tab_file('zhilian')
    #c.add([{"p": "zhilian123", "u": "hgwe5267"}])
    c.add_from_json('a', '')
    c.docheck(cvzl.ZLLogin)


def check_(what):
    if what == '51job':
        return check_51job()
    if what == 'zhilian':
        return check_zhilian()
    print "usage:"
    print " %s 51job|zhilian" % sys.argv[0]


if __name__ == '__main__':
    spider.util.use_utf8()
    if len(sys.argv)>1:
        check_(sys.argv[1])
    else:
        check_('?')
