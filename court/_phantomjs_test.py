#!/usr/bin/env python
# -*- coding:utf8 -*-

from selenium import webdriver

from spider.httpreq import BasicRequests


def test_sw(url):
    driver = webdriver.PhantomJS()
    driver.get(url)

    page1 = driver.page_source
    print page1
    driver.find_element_by_id('btnNext').click()
    page2 = driver.page_source
    print page2


def load_url(url):
    br = BasicRequests()
    con = br.request_url(url)
    print con.text


if __name__ == '__main__':
    url = 'http://www.smgqcourt.org:8002/publiclist.aspx?fymc=&ajlb=9715918889E6905BB9AD59B88AA07AC2&type=4F813CCBFE6A7793'
    test_sw(url)
