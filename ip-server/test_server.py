#!/usr/bin/env python
# -*- coding:utf8 -*-
import unittest
from  flask import url_for

from spider.httpreq import BasicRequests, SessionRequests


class ServerTestCase():
    main_url = 'http://192.168.1.251:9000/'

    def test_login(self):
        req = BasicRequests()
        con = req.request_url(self.main_url + 'login', date={'username': 'ipin', 'password': 'ipin1234'})
        print con.headers
        print con.text

    def test_post(self):
        req = SessionRequests()
        res = req.request_url(self.main_url + 'update',
                data={'encrypt': 'LuJAxGaUMqnDOARGzY9zIe0Rd41opkL7', 'key': 'mumas', 'value': '192.168.1.251'})

        print res.headers
        print res.text
        res = req.request_url(self.main_url + 'update',
                data={'encrypt': 'LuJAxGaUMqnDOARGzY9zIe0Rd41opkL7', 'key': 'mumaas', 'value': '192.168.1.251'})

        print res.headers
        print res.text

    def test_find(self):
        req = BasicRequests()
        con = req.request_url(self.main_url + '?key=' + 'mumas')
        print con.text
        con = req.request_url(self.main_url + '?key=' + 'skiloop')
        print con.text

if __name__=='__main__':
    case=ServerTestCase()
    case.test_find()
    case.test_post()
