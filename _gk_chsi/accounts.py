#!/usr/bin/env python
# -*- coding:utf8 -*-
import Queue
import copy
import re
import threading

import time

from chsispider import BaseGkChsiFsxSpider
from court.sessionrequests import ATOSSessionRequests

provinces = {'北京': 'bj',
             '天津': 'tj',
             '河北': 'hebei',
             '山西': 'sxty',
             '内蒙古': 'nm',
             '辽宁': 'ln',
             '吉林': 'jl',
             '黑龙江': 'hlj',
             '上海': 'sh',
             '江苏': 'js',
             '浙江': 'zj',
             '安徽': 'ah',
             '福建': 'fj',
             '江西': 'jx',
             '山东': 'sd',
             '河南': 'henan',
             '湖北': 'hb',
             '湖南': 'hunan',
             '广东': 'gd',
             '广西': 'gx',
             '海南': 'hainan',
             '重庆': 'cq',
             '四川': 'sc',
             '贵州': 'gz',
             '云南': 'yn',
             '西藏': 'xz',
             '陕西': 'sxxa',
             '甘肃': 'gs',
             '青海': 'qh',
             '宁夏': 'nx',
             '新疆': 'xj'}


def print_con(con):
    if con:
        print re.sub(r'\r|\n', '', con.text)
    else:
        print None


class ChsiSession(ATOSSessionRequests):
    def __init__(self, username, password):
        super(ChsiSession, self).__init__()
        self.username = username
        self.password = password
        self.is_logout = True
        self.remain_time = 0
        self.login_time = -1

    def login(self):
        data = {'j_username': self.username, 'j_password': self.password}
        con = super(ChsiSession, self).request_url('http://gk.chsi.com.cn/login.do', data=data)
        # todo: check return results
        print ('logging on')
        if con and con.text:
            m = re.search(ur'<td align="left">(\d+)分钟</td></tr>', con.text)
            if m:
                self.login_time = time.time()
                self.remain_time = int(m.group(1))
                if self.remain_time > 0:
                    print 'remaining time %d min ' % self.remain_time
                    self.is_logout = False
                    return True
                else:
                    print '已经没有剩余时间了:', m.group()
                    print 'there are no more time left'
                    return False
            else:
                print 'failed to find remain time'
            print re.sub(r'\r|\n', '', con.text)
        return False

    def logout(self):
        con = super(ChsiSession, self).request_url('http://gk.chsi.com.cn/user/logout.do', data={})
        print_con(con)
        self.is_logout = True

    def __del__(self):
        if not self.is_logout:
            self.logout()


def check_time(u, p, proxy=None):
    print u, p
    session = ChsiSession(u, p)
    if proxy:
        session.set_proxy(proxy)
    session.login()
    session.logout()
    return session.remain_time


class Accounts():
    def __init__(self, username, password, province, proxy=None, rt=0, ua='firefox'):
        self.username = username
        self.password = password
        self.province = province
        self.proxy = proxy
        self.user_agent = ua
        self.prefix = provinces[province]
        self.remain_time = rt

    def gen_run_param(self):
        return {'username': self.username, 'proxy': self.proxy, 'password': self.password, 'ua': self.user_agent,
                'name': self.province, 'prefix': self.prefix}
        pass

    def get_remain_time(self):
        ac = self.gen_run_param()
        self.remain_time = BaseGkChsiFsxSpider.get_remain_time(ac, ac['prefix'])

    def change_proxy(self, pm):
        count = 10
        proxy = None
        while count > 5 and not proxy:
            proxy = pm.get_good_proxy(count)
            count -= 1
        if proxy:
            self.proxy = proxy
            return True

    def save(self, ofile):
        ofile.write(self.toString() + '\n')

    def toString(self):
        return '%s,%s,%s,%s,%s,%s' % (
            self.username, self.password, self.province, self.prefix, self.remain_time, self.proxy)

    def pay(self, card):
        ac = self.gen_run_param()
        t = BaseGkChsiFsxSpider.pay_time(ac, ac['prefix'], card)
        self.remain_time = t[1]
        return t[0]


class AccountManager():
    def __init__(self, src='accounts.dat'):
        self.__accounts = {}
        self.__mutex = threading.RLock()
        self._load(src)

    def load(self, src='accounts.dat'):
        with open(src, 'r') as f:
            with self.__mutex:
                for l in f:
                    p = l.strip().split(',')
                    if len(p) >= 4:
                        if not eval(p[3]):
                            continue
                        if not self.__accounts.has_key(p[2]):
                            self.__accounts[p[2]] = []
                        self.__accounts[p[2]].append(Accounts(p[0], p[1], p[2]))

    def _load(self, src='accounts.dat'):
        with open(src, 'r') as f:
            with self.__mutex:
                for l in f:
                    p = l.strip().split(',')
                    if len(p) >= 6:
                        if not self.__accounts.has_key(p[2]):
                            self.__accounts[p[2]] = []
                        if p[5] != 'None':
                            self.__accounts[p[2]].append(Accounts(p[0], p[1], p[2], p[5], int(p[4])))
                        else:
                            self.__accounts[p[2]].append(Accounts(p[0], p[1], p[2], None, int(p[4])))

    def save(self, src='accounts.dat', mode='w'):
        with open(src, mode) as f:
            with self.__mutex:
                for p, a in self.__accounts.items():
                    for ac in a:
                        ac.save(f)

    def pay(self, prov, card):
        for ac in self.__accounts[prov]:
            if ac.remain_time <= 0:
                t = ac.pay(card)
                if int(t) > 0:
                    card['paydate'] = time.strftime('%Y-%m-%d', time.localtime())
                    card['account'] = ac.username
                print t, ac.username
                return int(t) > 0

    def ac_pay(self, username, prov, card):
        for ac in self.__accounts[prov]:
            if ac.username == username:
                t = ac.pay(card)
                if int(t) > 0:
                    card['paydate'] = time.strftime('%Y-%m-%d', time.localtime())
                    card['account'] = ac.username
                print t, ac.username
                return int(t) > 0

    def get(self, name, count):
        acs = []
        c = count
        for ac in self.__accounts[name]:
            if ac.remain_time > 0:
                c -= 1
                acs.append(ac)
                if c <= 0:
                    break
        return acs

    def get_all(self, name):
        return self.__accounts[name]


class CardManager():
    def __init__(self, srcfile='cards.dat', limit=40):
        self.__cards = {}
        self.__mutex = threading.RLock()
        self._load(srcfile)
        self.__limit = limit
        self.__used = 0

    def _load(self, src='cards.dat'):
        with open(src, 'r') as f:
            with self.__mutex:
                for l in f:
                    p = l.strip().split(',')
                    if len(p) == 4:
                        card = {'level': p[0], 'username': p[1], 'password': p[2], 'used': p[3],
                                'add_date': '2016-05-20',
                                'account': '', 'paydate': '2016-05-22'}
                    elif len(p) == 7:
                        card = {'level': p[0], 'username': p[1], 'password': p[2], 'used': p[3], 'add_date': p[4],
                                'account': p[5], 'paydate': p[6]}
                    else:
                        print 'invalid card', l.strip()
                        continue
                    if not self.__cards.has_key(p[0]):
                        self.__cards[card['level']] = []
                    self.__cards[card['level']].append(card)

    def save(self, src='cards.dat'):
        with open(src, 'w')as f:
            with self.__mutex:
                for k, v in self.__cards.items():
                    for card in v:
                        f.write('%s,%s,%s,%s,%s,%s,%s\n' % (
                            card['level'], card['username'], card['password'], card['used'], card['add_date'],
                            card['account'], card['paydate']))

    def get(self, level='510'):
        if not self.__cards.has_key(level):
            return
        with self.__mutex:
            if self.__used > self.__limit:
                return
            for c in self.__cards[level]:
                if c['used'] == '0':
                    c['used'] = '1'
                    self.__used += 1
                    return c

    def release(self, card):
        level = card['level']
        with self.__mutex:
            for c in self.__cards[level]:
                if c['used'] == '1' and c['username'] == card['username'] and c['password'] == card['password']:
                    c['used'] = '0'
                    self.__used -= 1
                    return True

    def invalid(self, card):
        level = card['level']
        with self.__mutex:
            for c in self.__cards[level]:
                if c['used'] == '1' and c['username'] == card['username'] and c['password'] == card['password']:
                    c['used'] = '2'
                    return True

    def getall(self, value='510'):
        return copy.deepcopy(self.__cards[value])


class ProxyManager():
    def __init__(self):
        self.__proxies = {}
        self.__mutex = threading.RLock()

    def load(self, src_file):
        with self.__mutex:
            with open(src_file, 'r') as f:
                for l in f:
                    p = l.strip().split(' ')
                    if len(p) >= 2:
                        self.__proxies[p[1]] = {'value': int(p[0])}
                    elif len(p) == 1:
                        self.__proxies[p[0]] = {'value': 10}

    def get_good_proxy(self, limit_value=10):
        with self.__mutex:
            for p, data in self.__proxies.items():
                if data['value'] >= limit_value:
                    used = data.get('used', False)
                    if not used:
                        data['used'] = True
                        return p

    def release(self, proxy):
        with self.__mutex:
            if self.__proxies.has_key(proxy):
                self.__proxies[proxy]['used'] = False

    def add_or_update(self, proxy, value=10):
        with self.__mutex:
            if not self.__proxies.has_key(proxy):
                self.__proxies[proxy] = {'value': value}
            else:
                self.__proxies[proxy]['value'] = value

    def save(self, ofile, mode='w'):
        with open(ofile, mode) as f:
            with self.__mutex:
                for p, data in self.__proxies:
                    f.write('%s %s\n' % (data['value'], p))


class ProxyQueue():
    def __init__(self):
        self.queue = Queue.Queue()

    def load(self, src_file):
        with open(src_file, 'r') as f:
            for l in f:
                p = l.strip().split(' ')
                if len(p) >= 2:
                    self.queue.put(p[1])

    def get_good_proxy(self, limit_value=10):
        return self.queue.get()

    def release(self, proxy):
        self.queue.put(proxy)


proxy_manager = ProxyManager()


def test_proxy_manager():
    pm = ProxyManager()
    pm.load('proxy_v')
    p = pm.get_good_proxy(5)
    print p
    p = pm.get_good_proxy(15)
    print p


def test_card():
    cm = CardManager()
    c1 = cm.get()
    c2 = cm.get('150')
    c3 = cm.get('310')
    cm.release(c1)
    cm.invalid(c2)
    print c1
    print c2
    print c3
    cm.save()


def ___test_user_proxy():
    pass


def __test_ac_m():
    am = AccountManager()
    am.save()


def pay_account(ac, card, name):
    return ac.pay(name, card)


def pay(ac, cm, card, name):
    r = ac.pay(name, card)
    if r:
        cm.invalid(card)
    else:
        cm.release(card)


def ac_pay(ac, cm, ct, username, prov):
    card = cm.get(ct)
    print card
    r = ac.ac_pay(username, prov, card)
    if r:
        cm.invalid(card)
    else:
        cm.release(card)


def pay_time(ct, name, ac, cm, count):
    c = count
    while c > 0:
        card = cm.get(ct)
        print card
        pay(ac, cm, card, name)
        c -= 1


def __pay():
    cm = CardManager()
    ac = AccountManager()
    # pay_time('510', '广东', ac, cm, 7)
    # pay_time('510', '河南', ac, cm, 8)
    # pay_time('510', '山东', ac, cm, 6)
    # pay_time('310', '山东', ac, cm, 1)
    # pay_time('510', '安徽', ac, cm, 6)
    # pay_time('150', '安徽', ac, cm, 1)
    # pay_time('150', '江苏', ac, cm, 1)
    # pay_time('310', '江苏', ac, cm, 1)
    # pay_time('510', '江苏', ac, cm, 4)
    # pay_time('510', '湖南', ac, cm, 4)
    # pay_time('310', '湖南', ac, cm, 1)
    # pay_time('150', '湖南', ac, cm, 1)
    # pay_time('510', '河北', ac, cm, 5)
    # pay_time('510', '江西', ac, cm, 4)
    pay_time('310', '江西', ac, cm, 1)
    cm.save()
    ac.save()
    pass


def __get_ac():
    ac = AccountManager()
    print  ac.get('广东', 2)
    print  ac.get('山东', 3)


def update_times():
    am = AccountManager()
    for name in provinces.keys():
        for ac in am.get_all(name):
            ac.remain_time = check_time(ac.username, ac.password)
    am.save()


def update_times_prov(name):
    am = AccountManager()
    for ac in am.get_all(name):
        ac.remain_time = check_time(ac.username, ac.password)
    am.save()


if __name__ == '__main__':
    # test_proxy_manager()
    # test_card()
    pass
    # __test_ac_m()
    update_times_prov('福建')
    # __get_ac()
