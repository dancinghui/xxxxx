#!/usr/bin/env python
# -*- coding:utf8 -*-
import re
import threading
import sys
import spider
from spider.spider import LoginErrors, MRLManager,MultiRequestsWithLogin
from spider.httpreq import SessionRequests
import time
import spider.util
import random
from spider.runtime import Log

'''
=================================================
Youzy login
=================================================
'''
class YouzyLogin(SessionRequests):
    def do_login(self,i):
        url = "http://www.youzy.cn/ajaxpro/Zero.Web.Pc.AjaxServices.Users.Auth,Zero.Web.Pc.ashx"
        user = [{"input":{"Username":"13826537792","Password":"woaitao0320"}},
                {"input":{"Username":"13047212138","Password":"woaitao0320"}},
                {"input":{"Username":"13272336540","Password":"woaitao0320"}},
                {"input":{"Username":"13923454061","Password":"woaitao0320"}},
                {"input":{"Username":"13686860704","Password":"woaitao0320"}},
                {"input":{"Username":"15116434571","Password":"woaitao0320"}},
                {"input":{"Username":"18397705838","Password":"woaitao0320"}},
                {"input":{"Username":"13047219012","Password":"woaitao0320"}}
                ]

        #param = {"input":{"Username":"13826537792","Password":"woaitao0320"}}
        #param = {"input":{"Username":"13143436016","Password":"woaitao0320"}}
        #param = {"input":{"Username":"13047212138","Password":"woaitao0320"}}
        #param = {"input":{"Username":"13272336540","Password":"woaitao0320"}}
        #param = {"input":{"Username":"13923454061","Password":"woaitao0320"}}
        #param = {"input":{"Username":"13686860704","Password":"woaitao0320"}}
        headers={'Content-Type': 'text/plain; charset=UTF-8', 'X-AjaxPro-Method': 'Login', "Referer": "http://www.youzy.cn/hunan"}
        param = user[i]
        print "this login param is :",param
        con = self.request_url(url, data=spider.util.utf8str(param), headers=headers)
        print con.text

# if __name__ == '__main__':
#     user = [{"input":{"Username":"13826537792","Password":"woaitao0320"}},
#                 {"input":{"Username":"13826537792","Password":"woaitao0320"}},
#                 {"input":{"Username":"13047212138","Password":"woaitao0320"}},
#                 {"input":{"Username":"13272336540","Password":"woaitao0320"}},
#                 {"input":{"Username":"13923454061","Password":"woaitao0320"}},
#                 {"input":{"Username":"13686860704","Password":"woaitao0320"}},
#                 {"input":{"Username":"15116434571","Password":"woaitao0320"}}
#                 ]
#     i = 0
#     while i<10:
#         print user[random.randint(0,6)]
#         #print random.randint(0,6)
#         i+=1