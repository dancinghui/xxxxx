#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import threading
import sys
import spider
from spider.qq.ptlogin import QQPtLogin
from spider.spider import LoginErrors, MRLManager
import time
import spider.util
from spider.runtime import Log

'''
=================================================
qichacha QQ login
=================================================
'''
class QccData:
    def __init__(self, acc_file):
        self.acc_file = acc_file

    def get_accounts(self):
        Log.warning("read account from %s" % self.acc_file)
        f = open(self.acc_file)
        rs = []
        for line in f:
            if line.strip() is "":
                break
            print line
            qqno, qqpsw, noop = re.split("\s+", line)
            rs.append({"qqno": qqno, "qqpwd": qqpsw})

        return rs


class QccLogin(QQPtLogin):
    def __init__(self, acc):
        QQPtLogin.__init__(self, acc, 'http://qichacha.com/user_qqlogin')
        self.lianzhongcheck = True
        self.search_times_limit = 9999 # 99 times per account
        self.search_time_gap = 3000 #search gap 3000 ms
        self.can_search = False
        self.recur_depth = 0

    def _real_do_login(self):
        self.reset_session()
        rv = self.do_pt_login([])
        if rv:
            con = self.request_url("http://qichacha.com/global_user_qqcallback")
            if ur"登录成功" in con.text:
                self.request_url("http://qichacha.com/")
                self.can_search = True
            else:
                self.set_nologin()
                return False
        return rv

    def need_login(self, url, response, hint):
        if 'gongsi_getList' in url:
            if response.text.strip() == "":
                return True
            return False
        if u'亲，您的账户存在异常，请重新激活账户！' in response.text or r'user_relive' in url:
            Log.error("帐号%s暂时不能继续搜索" % self.account["qqno"] )
            self.isvalid = False
            raise LoginErrors.AccountHoldError('too much op')
        if u'家符合条件的企业' in response.text:
            return False
        if u'小查还没找到数据' in response.text:
            return False
        return True

    def request_url(self, url, **kwargs):
        if not self.islogin:
            print self.account["qqno"], "logging............"
            self.can_search = False
        if self.can_search:
            print self.account["qqno"]+" searching"
            if not hasattr(self, "search_count"):
                self.search_count = 0

            #search count limit
            if self.search_count >= self.search_times_limit:
                print "account:%s has use %d times" % (self.account["qqno"], self.search_times_limit)
                # self.isvalid = False
                self.search_count = 0
                raise LoginErrors.AccountHoldError()
            self.search_count += 1

        rv = QQPtLogin.request_url(self, url, **kwargs)
        return rv



# class QccMRLManager(MRLManager):
#     def __init__(self, accounts, req_class, shared=False):
#         MRLManager.__init__(self, accounts, req_class, shared)
#

    # def ensure_login_do(self, caller, checker):
    #     #all threads use one account
    #     if self.singlemode:
    #         # net = getattr(self._nettls, 'net', None)
    #         net = self.curracc
    #         if self.curracc is None:
    #             with self.locker:
    #                 net = self.curracc
    #                 while net is None:
    #                     print "----------------------", str(threading.current_thread().ident),"enter!!!!!!!!!!!!!!!"
    #                     net1 = self.net_list.get(lambda v:v.is_valid())
    #                     net1.do_login()
    #                     if net1.is_valid():
    #                         # setattr(self._nettls, 'net', net1)
    #                         self.curracc = net1
    #                         net = net1
    #
    #         net._inc_call()
    #         try:
    #             con = caller(net)
    #             if checker is not None:
    #                 checker(net, con)
    #             net._dec_call()
    #             return con
    #         except LoginErrors.RetryError:
    #             net._dec_call()
    #             return self.ensure_login_do(caller, checker)
    #         except LoginErrors.AccountHoldError:
    #             net.set_nologin()
    #             net._dec_call()
    #             # setattr(self._nettls, 'net', None)
    #             self.curracc = None
    #             self.net_list.unlock(net)
    #             return self.ensure_login_do(caller, checker)
    #         except LoginErrors.NeedLoginError:
    #             net.set_nologin()
    #             net.do_login()
    #             net._dec_call()
    #             if not net.is_valid():
    #                 # setattr(self._nettls, 'net', None)
    #                 self.curracc = None
    #                 self.net_list.unlock(net)
    #             return self.ensure_login_do(caller, checker)
    #         except Exception:
    #             net._dec_call()
    #             raise
    #     else:
    #         return MRLManager.ensure_login_do(self, caller, checker)






