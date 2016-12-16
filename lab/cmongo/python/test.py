#!/usr/bin/env python
# -*- coding:utf8 -*-

import cpagestore
import sys

def test_on(a):
    print "has key?", a.has_key("jd_51job://71146739")
    print "has item?", a.has_item("jd_51job://71146739", "73a1425e218746fb0107750a1cf6b29b")
    print "has new ?", a.has_new("jd_51job://71146739")
    print "has new ?", a.has_new("jd_51job://67112653")
    ####                                                                     1449827311000
    print a.update_time("jd_51job://71146739", "73a1425e218746fb0107750a1cf6b29f", 1452144698235, 1449827311000)

a = cpagestore.PSObj('mongodb://root:helloipin@api.facelike.com/admin', 'page_store_jd_51job')
test_on(a)
sys.stdout.flush()
#a.dump()


b = cpagestore.RBFPSObj('test.bin', 'mongodb://root:helloipin@api.facelike.com/admin', 'page_store_jd_51job')
test_on(b)
