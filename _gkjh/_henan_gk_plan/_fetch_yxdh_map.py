#!/usr/bin/env python
# -*- coding:utf8 -*-
import re

import time
from selenium import webdriver


class FetchYXDHMap():
    def __init__(self):
        self._name = 'yxdh.py'

    def run(self):
        count = 1
        total = -1
        driver = webdriver.Firefox()
        driver.get('http://www.heao.gov.cn/JHCX/PZ/enrollplan/SchoolList.aspx')
        code_map = []
        while True:
            res = re.findall(r'<a href="PCList.aspx\?YXDH=\d+">\[(\d+)\]([^<]*)<\/a>', driver.page_source)
            code_map += res
            next_btn = driver.find_element_by_id('PagesUpDown_btnNext')
            if not next_btn.is_enabled():
                print 'fetching finished at page', count
                break
            if count == 1:
                total = re.search(r'<span id="PagesUpDown_lblPageCount">\d+\/(\d+)<\/span>', driver.page_source).group(
                    1)
                total = int(total)
                print 'total page', total
            if count >= total >= 0:
                print 'fetching finished at page', count
                break
            count += 1
            time.sleep(1)
            next_btn.click()
            print 'fetch page', count
        driver.close()
        codes = {}
        for code, sch in code_map:
            codes[code] = sch
        self.save(codes)

    def save(self, code_map):
        f = open(self._name, 'w')
        f.writelines("#!/usr/bin/env python")
        f.writelines("# -*- coding:utf8 -*-")
        f.writelines("scho_map=" + str(code_map))
        f.writelines('')
        f.flush()
        f.close()
        print len(code_map), 'items save'


if __name__ == '__main__':
    job = FetchYXDHMap()
    job.run()
