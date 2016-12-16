#!/usr/bin/env python
# -*- coding:utf8 -*-
import copy
import logging
import random
import re
import uuid

import time

from court.sessionrequests import ATOSSessionRequests
from court.util import remove_file, save_file, Captcha

provinces = [
    {'code': '11', 'name': '北京', 'short': 'bj'},
    {'code': '12', 'name': '天津', 'short': 'tj'},
    {'code': '13', 'name': '河北', 'short': 'hebei'},
    {'code': '14', 'name': '山西', 'short': 'sxty'},
    {'code': '15', 'name': '内蒙古', 'short': 'nm'},
    {'code': '21', 'name': '辽宁', 'short': 'ln'},
    {'code': '22', 'name': '吉林', 'short': 'jl'},
    {'code': '23', 'name': '黑龙江', 'short': 'hlj'},
    {'code': '31', 'name': '上海', 'short': 'sh'},
    {'code': '32', 'name': '江苏', 'short': 'js'},
    {'code': '33', 'name': '浙江', 'short': 'zj'},
    {'code': '34', 'name': '安徽', 'short': 'ah'},
    {'code': '35', 'name': '福建', 'short': 'fj'},
    {'code': '36', 'name': '江西', 'short': 'jx'},
    {'code': '37', 'name': '山东', 'short': 'sd'},
    {'code': '41', 'name': '河南', 'short': 'henan'},
    {'code': '42', 'name': '湖北', 'short': 'hubei'},
    {'code': '43', 'name': '湖南', 'short': 'hunan'},
    {'code': '44', 'name': '广东', 'short': 'gd'},
    {'code': '45', 'name': '广西', 'short': 'gx'},
    {'code': '46', 'name': '海南', 'short': 'hainan'},
    {'code': '50', 'name': '重庆', 'short': 'cq'},
    {'code': '51', 'name': '四川', 'short': 'sc'},
    {'code': '52', 'name': '贵州', 'short': 'gz'},
    {'code': '53', 'name': '云南', 'short': 'yn'},
    {'code': '54', 'name': '西藏', 'short': 'xz'},
    {'code': '61', 'name': '陕西', 'short': 'sxxa'},
    {'code': '62', 'name': '甘肃', 'short': 'gs'},
    {'code': '63', 'name': '青海', 'short': 'qh'},
    {'code': '64', 'name': '宁夏', 'short': 'nx'},
    {'code': '65', 'name': '新疆', 'short': 'xj'}
]

pcodes = [
    {'北京': '11', '天津': '12', 'name': '天津', 'short': 'tj'},
    {'河北': '13', 'name': '河北', 'short': 'hebei'},
    {'山西': '14', 'name': '山西', 'short': 'sxty'},
    {'内蒙古': '15', 'name': '内蒙古', 'short': 'nm'},
    {'辽宁': '21', 'name': '辽宁', 'short': 'ln'},
    {'吉林': '22', 'name': '吉林', 'short': 'jl'},
    {'黑龙江': '23', 'name': '黑龙江', 'short': 'hlj'},
    {'上海': '31', 'name': '上海', 'short': 'sh'},
    {'江苏': '32', 'name': '江苏', 'short': 'js'},
    {'浙江': '33', 'name': '浙江', 'short': 'zj'},
    {'安徽': '34', 'name': '安徽', 'short': 'ah'},
    {'code': '35', 'name': '福建', 'short': 'fj'},
    {'code': '36', 'name': '江西', 'short': 'jx'},
    {'code': '37', 'name': '山东', 'short': 'sd'},
    {'code': '41', 'name': '河南', 'short': 'henan'},
    {'code': '42', 'name': '湖北', 'short': 'hubei'},
    {'code': '43', 'name': '湖南', 'short': 'hunan'},
    {'code': '44', 'name': '广东', 'short': 'gd'},
    {'code': '45', 'name': '广西', 'short': 'gx'},
    {'code': '46', 'name': '海南', 'short': 'hainan'},
    {'code': '50', 'name': '重庆', 'short': 'cq'},
    {'code': '51', 'name': '四川', 'short': 'sc'},
    {'code': '52', 'name': '贵州', 'short': 'gz'},
    {'code': '53', 'name': '云南', 'short': 'yn'},
    {'code': '54', 'name': '西藏', 'short': 'xz'},
    {'code': '61', 'name': '陕西', 'short': 'sxxa'},
    {'code': '62', 'name': '甘肃', 'short': 'gs'},
    {'code': '63', 'name': '青海', 'short': 'qh'},
    {'code': '64', 'name': '宁夏', 'short': 'nx'},
    {'code': '65', 'name': '新疆', 'short': 'xj'}
]


class Register(ATOSSessionRequests):
    def __init__(self, provinces, count):
        super(Register, self).__init__()
        self.provinces = provinces
        self.data = {
            'userName': '',
            'userTrueName': '',
            'userPassword': '',
            'repassword': '',
            'checkNum': '',
            'userGender': '1',
            'ssdm': '11',
            'userTel': '',
            'userMTel': '',
            'userEmail': '',
            'userAddress': '',
        }
        self.count = count

    def register(self, params):
        self.reset_session()
        self.set_proxy(params['proxy'], len(self.sp_proxies), False)
        data = copy.deepcopy(self.data)
        data['userName'] = params['username']
        data['userPassword'] = params['password']
        data['repassword'] = params['password']
        data['checkNum'] = self.resolve_captcha()
        data['ssdm'] = params['province']
        data['userEmail'] = params['email']
        con = self.request_url('http://gk.chsi.com.cn/user/newUser.do', data=data)
        if con:
            print con.text
        self.login(params['username'], params['password'])
        self.select_ssdm(params['province'])
        self.logout()

    def resolve_captcha(self):
        us = str(uuid.uuid4())
        rd = random.random() * 10000
        con = self.request_url('http://gk.chsi.com.cn/ValidatorIMG.JPG?ID=%s' % str(rd))
        if not con or not con.content:
            logging.info('failed to fetch captcha')
            return ''
        fname = '/tmp/' + us + '.jpg'
        save_file(con.content, fname)
        res = Captcha.resolve(fname, us)
        remove_file(fname)
        remove_file(us + '.txt')
        return res

    def login(self, username, password):
        data = {'j_username': username, 'j_password': password}
        con = self.request_url('http://gk.chsi.com.cn/login.do', data=data)
        # todo: check return results
        logging.info('logging on')
        if con and con.text:
            print re.findall(ur'<td align="right">[^<]剩余：<\/td>', con.text)
            return True
        return False

    def check_select(self, username, password):
        self.reset_session()
        data = {'j_username': username, 'j_password': password}
        con = self.request_url('http://gk.chsi.com.cn/login.do', data=data)
        # todo: check return results
        logging.info('logging on')
        if con and con.text:
            m = re.findall(ur'<td align="right">.*剩余：<\/td>', con.text)
            if m and len(m) > 0:
                print m[0]
                return True
            return False
        return False

    def select_ssdm(self, ssdm):
        data = {'ssdm': ssdm}
        con = self.request_url('http://gk.chsi.com.cn/user/setSsdm.do', data=data)
        if con:
            print re.findall(ur'您选择的省市名称为：', con.text)
        con = self.request_url('http://gk.chsi.com.cn/user/confirmSsdm.do', data=data)
        if con:
            print re.findall(ur'省市名称设置完毕', con.text)

    def run(self, start=0):
        accounts = []
        params = {
            'proxy': '106.75.134.192:18888:ipin:ipin1234',
            'username': 'shi10003c',
            'password': 'shi2026shi',
            'province': '11',
            'email': 'shi10003c@sina.com'
        }
        for prov in self.provinces:
            password = 'shi2026cxs'
            for ac in range(start, self.count + start):
                p = copy.deepcopy(params)
                p['username'] = prov['short'] + '2016e' + str(ac)
                p['password'] = password
                p['province'] = prov['code']
                p['prov'] = prov['name']
                p['email'] = p['username'] + '@sina.com'
                try:
                    self.register(p)
                except Exception as e:
                    print e.message
                    continue
                accounts.append(p)
                time.sleep(10)

        with open('accounts', 'w') as f:
            for ac in accounts:
                f.write(str(ac) + '\n')

    def logout(self):
        return self.request_url('http://gk.chsi.com.cn/user/logout.do', data={})

    def confirm_province(self, accounts):
        try:
            self.reset_session()
            self.login(accounts['username'], accounts['password'])
            self.select_ssdm(accounts['province'])
            self.logout()
        except Exception as e:
            print e.message

    def check_success(self, accounts, ofs):
        try:
            ok = self.check_select(accounts['username'], accounts['password'])
            self.logout()
            line = accounts['username'] + ',' + accounts['password'] + ',' + accounts['prov'] + ',' + str(ok)
            ofs.write(line + '\n')
            print line
        except Exception as e:
            print e.message


def register():
    reg = Register(provinces, 3)
    reg.run(5)


def select_province():
    accounts = []
    reg = Register(provinces, 5)
    with open('acs', 'r')as f:
        for l in f:
            accounts.append(eval(l))
    for a in accounts:
        reg.confirm_province(a)


def check_select():
    accounts = []
    reg = Register(provinces, 5)
    with open('acs', 'r')as f:
        for l in f:
            accounts.append(eval(l))
    ofs = open('accounts.success', 'a')
    for a in accounts:
        reg.check_success(a, ofs)


def register():
    acc = []
    with open('accounts.success', 'r') as f:
        for l in f:
            p = l.split(',')
            if not eval(p[3]):
                acc.append({
                    'proxy': '106.75.134.192:18888:ipin:ipin1234',
                    'username': p[0],
                    'password': p[1],
                    'province': '11',
                    'email': 'shi10003c@sina.com'
                })


if __name__ == '__main__':
    # register()
    check_select()
