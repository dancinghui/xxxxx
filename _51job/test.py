#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
from spider.util import htmlfind, TimeHandler

with open('test.html', 'rb') as f:
      content = f.read()

      divs = htmlfind.findTag(content, 'div', 'class="jtag inbox">')
      if divs:
            spans = re.findall(r'<span[^<>]*>(.*?)</span>', divs[0], re.S)
            if spans:
                spans = spans[:-1] # 忽略更新时间
                for span in spans:
                    content += htmlfind.remove_tag(span, True) + "#"

      if isinstance(content, unicode):
            content = content.encode('utf-8')

      hf = htmlfind(content, '<div class="bmsg job_msg inbox">', 0)
      t2 = htmlfind.remove_tag(hf.get_node(), 1)

      find = re.search(r'tCompany_text">(.*?)</div>', content, re.S)
      # print htmlfind.remove_tag(find.group(1), 1)
      s = re.search(r'(\d*-?\d+-\d+发布)', content, re.S)
      print htmlfind.remove_tag(s.group(1),True)