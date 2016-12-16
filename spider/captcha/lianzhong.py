#!/usr/bin/env python
# encoding: utf-8

import json
import time
import threading
import re
import traceback
from spider.spider import SessionRequests


class LianzhongCaptcha(SessionRequests):
    PROCESS_URL = 'http://bbb4.hyslt.com/api.php?mod=php&act=upload'
    ERROR_URL = 'http://bbb4.hyslt.com/api.php?mod=php&act=error'
    LIANZHONG_SOFT_KEY = 'fpTof8NxP4FTFOTp6Tfi3ik6TxtfEOkE68nE3foK'
    ACCOUNTS = [{'u': 'brantbzhang', 'p': '15004622415', 'softkey': ''}]

    def __init__(self, ac=None):
        SessionRequests.__init__(self)
        if not ac:
            ac = self.ACCOUNTS[0]
        self._username = ac['u']
        self._pwd = ac['p']
        self._soft_key = ac.get('softkey', '') or self.LIANZHONG_SOFT_KEY
        self._timeout = 60
        self._img_type = '3040'
        self.lastid = None

    def point_check(self):
        #{'-1': '参数错误，用户名为空或密码为空', '-2': '用户不存在', '-3': '密码错误', '-4': ' 账户被锁定', '-5': ' 非法登录',
        #'-6': ' 用户点数不足，请及时充值', '-8': ' 系统维护中', '-9': ' 其他'}
        url = "http://bbb4.hyslt.com/api.php?mod=php&act=point"
        params = {'user_name': self._username, 'user_pw': self._pwd, }
        response = self.request_url(url, data=params)
        if u'密码错误' in response.text or 'name or pw error' in response.text:
            return 0
        j = json.loads(response.text)
        if j.get('result', None):
            return j.get('data')
        else:
            print response.text
            return 0

    def resolve(self, img, minlen=4, maxlen=20):
        data = {
            'user_name': self._username,
            'user_pw': self._pwd,
            'yzm_maxlen': maxlen,
            'yzm_minlen': minlen,
            'yzmtype_mark': 0,
            'zztool_token': self._soft_key,
        }
        files = {'upload': ('a.jpg', img)}

        time.sleep(3)
        con = self.request_url(self.PROCESS_URL, data=data, files=files, timeout=self._timeout)
        if con is None:
            return False
        print '====>lianzhong.result:', con.text
        j = json.loads(con.text)
        if j.get('result', False):
            self.lastid = j['data']['id']
            return j['data']['val']
        elif "已经损坏或者不是正确的图像格式" in j.get("Error", ""):
            return False
        else:
            print con.text
            # raise Exception(u"联众服务返回异常数据[%s]" % con.text)
            return False

    def mark_last_error(self):
        if not self.lastid:
            return False
        data = {'user_name':self._username, 'user_pw':self._pwd, 'yzm_id':self.lastid}
        self.request_url(self.ERROR_URL, data=data)


if __name__ == '__main__':
    a = LianzhongCaptcha()
    print "points:", a.point_check()
