#!/usr/bin/env python
# -*- coding:utf8 -*-

import re

with open('test.html', 'rb') as f:
      content = f.read()

      s = re.search(r'职位描述：.*?"content content-word">(.*?)</div>', content, re.S)

      print s