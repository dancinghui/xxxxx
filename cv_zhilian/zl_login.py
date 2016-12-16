#!/usr/bin/env python
# encoding: utf8

import spider.util
from spider.spider import SessionRequests, MultiRequestsWithLogin, LoginErrors
from lxml import html
from spider.captcha.onlineocr import OnlineOCR
from collections import OrderedDict
import re
import copy


class ZLImager(object):
    def __init__(self):
        self.sr = SessionRequests()
        self.state = 0
        self.code = ''
        self.lastimg = None
        self.pccv = None

    def _get_image_con(self, osr):
        headers={'Referer':'http://rd2.zhaopin.com/portal/myrd/regnew.asp?za=2'}
        con = osr.request_url('https://passport.zhaopin.com/checkcode/imgrd', headers=headers)
        if con is not None:
            self.lastimg = con.content
            self.pccv = osr.get_cookie('pcc', '')
            return con.content
        else:
            return 'net bad'

    def _get_code(self, osr):
        #g = GetImageCode(lambda : self._get_image_con())
        g = OnlineOCR('zhilian')
        self.code = g.resolve(lambda dbgdata=None: self._get_image_con(osr))
        if self.code is not None and self.code != '':
            self.state = 1
        return self.code

    def get_code(self, osr):
        if self.state == 0:
            return self._get_code(osr)
        else:
            osr.add_cookie('.zhaopin.com', 'pcc', self.pccv)
            return self.code

    def image_timeout(self):
        self.state = 0


class GlobalData(object):
    zlimg = ZLImager()
    login_proxy = None


class ZLLogin(MultiRequestsWithLogin):
    def __init__(self, ac):
        MultiRequestsWithLogin.__init__(self,ac)
        assert isinstance(ac, dict)
        self.cansearch = 0
        self.isvalid = True

    def _test_search(self):
        testsearch_url = 'http://rdsearch.zhaopin.com/Home/ResultForCustom?SF_1_1_7=7,9&orderBy=DATE_MODIFIED,1&pageSize=60&SF_1_1_27=0&exclude=1'
        con1 = self.request_url(testsearch_url, headers={'Referer':'http://rdsearch.zhaopin.com/Home/ResultForCustom'})
        if re.search(ur'\d+</span>份简历', con1.text):
            self.cansearch = 1
        else:
            self.cansearch = 0

    def _real_do_login(self):
        # a,b,c = self._cur_proxy_index, self._auto_change_proxy, self.sp_proxies
        # self.sp_proxies = OrderedDict()
        # self.set_proxy(GlobalData.login_proxy, 0, 0)
        rr = self._real_do_login1()
        return rr

    def _real_do_login1(self):
        self.request_url('http://rd2.zhaopin.com/portal/myrd/regnew.asp?za=2')
        imgcode = GlobalData.zlimg.get_code(self)
        data = {'CheckCode':imgcode, 'LoginName':self.account['u'], 'Password':self.account['p'], 'Submit':''}
        con = self.request_url('https://passport.zhaopin.com/org/login', data=data)
        if con is None:
            return False
        if u'>正在跳转<' in con.text:
            con = self.request_url('http://rd2.zhaopin.com/s/loginmgr/loginproc_new.asp')
            self._test_search()
            return True
        elif u'请选择你要登入的系统' in con.text:
            con = self.request_url('http://rd2.zhaopin.com/s/loginmgr/loginproc_new.asp')
            self._test_search()
            return True
        else:
            cdoc = html.fromstring(con.text)
            t = cdoc.xpath("//form[@id='form1']//div[@class='msg_error']")
            if t is not None:
                xt = t[0].text_content().strip()
                # print xt
                if u'验证码错误' in xt:
                    GlobalData.zlimg.image_timeout()
                elif u'用户名或密码错误' in xt:
                    self.isvalid = False
                elif u'存在异常行为，已被暂时冻结' in xt:
                    self.isvalid = False
            return False

    def is_valid(self):
        return self.isvalid

    def need_login(self, url, response, hint):
        if hint == 'search':
            if not self.cansearch:
                self.isvalid = False
                raise LoginErrors.AccountHoldError('expired')
            if u'贵公司合同已到期，请您联系销售续约' in response.text:
                self.isvalid = False
                raise LoginErrors.AccountHoldError('expired')
        if '/loginmgr/login.asp' in response.request.url:
            raise LoginErrors.NeedLoginError()
        if u'<title>智联招聘网--HR服务--登录' in response.text:
            raise LoginErrors.NeedLoginError()

    def dump_result(self, folist):
        aco = copy.deepcopy(self.account)
        if not self.isvalid:
            aco["status"] = "BROKEN"
        elif self.cansearch == 0:
            aco["status"] = "不能搜索"

        acinfo = spider.util.utf8str(aco)
        for fo in folist:
            fo.write(acinfo + "\n")

if __name__ == '__main__':
    osr = SessionRequests()
    code = GlobalData.zlimg.get_code(osr)
    print code
    spider.util.FS.dbg_save_file('xx.jpg', GlobalData.zlimg.lastimg)
    pass
