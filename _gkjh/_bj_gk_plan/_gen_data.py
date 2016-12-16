#!/usr/bin/env python
# -*- coding:utf8 -*-
import re

from selenium import webdriver
from selenium.webdriver.support.select import Select

from spider.httpreq import BasicRequests


class GenQueryData(BasicRequests):
    def gen(self):
        url = 'http://query.bjeea.cn/queryService/rest/plan/115'
        count = 0
        option = 1
        driver = webdriver.PhantomJS()
        driver.get(url)
        code_list = []
        val = None
        while True:
            if count <= 0:
                if option == 1:
                    val = u'文科'
                elif option == 2:
                    val = u'理科'
                elif option == 3:
                    val = u'单考'
                else:
                    break
                selector = driver.find_element_by_xpath('//select[@name="subject"]')
                if selector is None:
                    break
                Select(selector).select_by_value(val)
                driver.find_element_by_id('query_btn').click()
                option += 1
            else:
                try:
                    next_button = driver.find_element_by_css_selector('div.pagination>ul[style]>li:nth-child(3)>a')
                except Exception:
                    count = 0
                    print 'Paring list finished,page count:', count
                    continue
                if next_button is None or next_button.text != u'下一页':
                    count = 0
                    continue
                try:
                    next_button.click()
                except Exception as e:
                    print e.message
                    count = 0
                    continue
            count += 1
            print 'subject:', val, '\tpage count:', count
            con = driver.page_source
            if con is None:
                continue
            urls = re.findall(r'return goschool\(\'(\d+)\'[^\)]*\)">([^<]*)<', con)
            if urls is None:
                continue
            for u in urls:
                if u not in code_list:
                    code_list.append(u)
        driver.close()
        schlist = {}
        for c, s in code_list:
            schlist[s] = c
        f = open('_bj_jh/qdata.py', 'w')
        f.writelines('# !/usr/bin/env python')
        f.writelines('# -*- coding:utf8 -*-')
        f.writelines("\n")
        f.write('schools=' + str(schlist))
        f.flush()
        f.close()
        print 'dist len:', len(schlist)


if __name__ == '__main__':
    gen = GenQueryData()
    gen.gen()
