#!/usr/bin/env python
# -*- coding:utf8 -*-
from court.util import count_unique_doc

if __name__ == '__main__':
    docs_len = count_unique_doc('page_store_sh_court', 'admin', "mongodb://root:helloipin@localhost/admin")
    print 'doc length', docs_len
