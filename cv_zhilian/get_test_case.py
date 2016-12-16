#!/usr/bin/env python
# encoding: utf8

from requests import sessions
import requests

import StringIO
import re
import random

class OnlineOCR(object):
    def __init__(self, type_):
        self.server = 'http://www.haohaogame.com:8099/codeocr'
        self._type = type_

    def resolve(self, getimg):
        while True:
            imgcon = getimg()
            f = StringIO.StringIO()
            f.write(imgcon)
            f.seek(0)
            url = "%s?type=%s" % (self.server, self._type)
            response = requests.post(url, files={'file': f})
            imgcode = response.text.strip()
            if imgcode == '<fail>' or imgcode == 'not found':
                continue
            return imgcode


class Config(object):
    ac = [{"p": "zhilian123", "u": "faeu8582"},
{"p": "zhilian123", "u": "ajoe7324"},
{"p": "zhilian123", "u": "suey8380"},
{"p": "zhilian123", "u": "bsee7820"},
{"p": "zhilian123", "u": "puyt7832"},
{"p": "zhilian123", "u": "ytyd1583"},
{"p": "zhilian123", "u": "hset9427"},
{"p": "zhilian123", "u": "hdes9426"},
{"p": "zhilian123", "u": "gaie8392"},
{"p": "zhilian123", "u": "bsoe7328"},
{"p": "zhilian123", "u": "ndpy7846"},
{"p": "zhilian123", "u": "heyt7225"},
{"p": "zhilian123", "u": "gady8427"},
{"p": "zhilian123", "u": "hsnb3275"},
{"p": "zhilian123", "u": "dsrw8437"},
{"p": "zhilian123", "u": "tyws8342"},
{"p": "zhilian123", "u": "teyd7462"},
{"p": "zhilian123", "u": "gvae7327"},
{"p": "zhilian123", "u": "bxcd6236"},
{"p": "zhilian123", "u": "hedt8436"},
{"p": "zhilian123", "u": "sdsa7898"},
{"p": "zhilian123", "u": "faey7328"},
{"p": "zhilian123", "u": "gbse7903"},
{"p": "zhilian123", "u": "snye8328"},
{"p": "zhilian123", "u": "gsey8046"},
{"p": "zhilian123", "u": "dsda7893"},
{"p": "zhilian123", "u": "jetw6783"},
{"p": "zhilian1234", "u": "eqkt3275"},
{"p": "zhilian1234", "u": "lkbu4132"},
{"p": "zhilian1234", "u": "ymlx4545"},
{"p": "zhilian1234", "u": "tdsp7866"},
{"p": "zhilian1234", "u": "jfbg5436"},
{"p": "zhilian1234", "u": "yatv7864"},
{"p": "zhilian1234", "u": "lfbl8797"},
{"p": "zhilian1234", "u": "wmoi4563"},
{"p": "zhilian1234", "u": "ilks8766"},
{"p": "zhilian1234", "u": "tpsh5165"},
{"p": "zhilian1234", "u": "xcng6841"},
{"p": "zhilian1234", "u": "szea9849"},
{"p": "zhilian1234", "u": "effg3060"},
{"p": "zhilian1234", "u": "yoam9480"},
{"p": "zhilian1234", "u": "hqnn9844"},
{"p": "zhilian1234", "u": "myta6209"},
{"p": "zhilian1234", "u": "xoow9498"},
{"p": "zhilian1234", "u": "ztbe9889"},
{"p": "zhilian1234", "u": "nyzb9849"},
{"p": "zhilian1234", "u": "uleg8794"},
{"p": "zhilian1234", "u": "gtpd9884"},
{"p": "zhilian1234", "u": "gbrf8978"},
{"p": "zhilian1234", "u": "vxlt8948"},
{"p": "zhilian1234", "u": "hrhe9879"},
{"p": "zhilian1234", "u": "hijs9651"},
{"p": "zhilian1234", "u": "wyih3654"},
{"p": "zhilian1234", "u": "vzes6854"},
{"p": "zhilian1234", "u": "bsra9410"},
{"p": "zhilian1234", "u": "glwo2355"},
{"p": "zhilian1234", "u": "xvqp9858"},
{"p": "zhaopin1234", "u": "wez30748708t"},
{"p": "zhaopin123", "u": "13A614"},
{"p": "zhaopin123", "u": "rch123"},
{"p": "zhaopin123", "u": "zhmt1234"},
{"p": "zhaopin123", "u": "wldx123"},
{"p": "zhaopin123", "u": "cxm2015"},
{"p": "zhaopin123", "u": "eyxt2015"},
{"p": "zhaopin123", "u": "hfyt2015"},
{"p": "zhaopin123", "u": "htdy2015"},
{"p": "ms123456", "u": "szmusen"},
]
    URL_TEMPLATE = "http://rdsearch.zhaopin.com/Home/ResultForCustom?SF_1_1_31={}&SF_1_1_27=0&orderBy=DATE_MODIFIED,1&exclude=1&pageIndex={}"
    TOTAL_COUNT = 100


class CVZLTestGet(object):
    def __init__(self):
        self.sess = sessions.Session()
        self.sess.proxies = {'http':'http://ipin:ipin1234@114.119.39.130:18888/', 'https':'https://ipin:ipin1234@114.119.39.130:18888/'}
        self.headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:42.0) Gecko/20100101 Firefox/42.0'}
        # self.pauth = ("ipin", "ipin1234")
        self.sess.get("https://passport.zhaopin.com/org/login")
        self.ocr = OnlineOCR("zhilian")
        self.cansearch = 0
        self.index = 0
        self.count = 0

    def get_code(self):
        g = OnlineOCR('zhilian')
        self.code = g.resolve(lambda : self._get_image_con())
        if self.code is not None and self.code != '':
            self.state = 1
        return self.code

    def _get_image_con(self):
        self.headers.update({'Referer':'http://rd2.zhaopin.com/portal/myrd/regnew.asp?za=2'})
        res = self.sess.get('https://passport.zhaopin.com/checkcode/imgrd')

        return res.content

    def _test_search(self):
        testsearch_url = 'http://rdsearch.zhaopin.com/Home/ResultForCustom?SF_1_1_7=7%2C9&orderBy=DATE_MODIFIED,1&pageSize=60&SF_1_1_27=0&exclude=1'
        con1 = self.sess.get(testsearch_url, headers={'Referer':'http://rdsearch.zhaopin.com/Home/ResultForCustom'})
        if re.search(ur'\d+</span>份简历', con1.text):
            self.cansearch = 1
        else:
            self.cansearch = 0

    def do_login(self):
        imgcode = self.get_code()
        data = {'CheckCode':imgcode, 'LoginName':Config.ac[self.index]['u'], 'Password':Config.ac[self.index]['p'], 'Submit':''}
        con = self.sess.post('https://passport.zhaopin.com/org/login', data)
        if u'>正在跳转<' in con.text:
            con = self.sess.get('http://rd2.zhaopin.com/s/loginmgr/loginproc_new.asp')
            self._test_search()
            return True
        elif u'请选择你要登入的系统' in con.text:
            con = self.sess.get('http://rd2.zhaopin.com/s/loginmgr/loginproc_new.asp')
            self._test_search()
            return True
        elif u'贵公司合同已到期，请您联系销售续约，续约后开通' or u'您的登录过于频繁' in con.text:
            self.index += 1
            self.index %= len(Config.ac)


        return False


    def try_next_account(self):
        self.index += 1
        self.index %= len(Config.ac)
        self.ac = Config.ac[self.index]

    def get_one(self):
        i = 0
        # self._test_search()
        while not self.cansearch:
            i += 1
            if i > 10:
                i = 0
                self.try_next_account()
            self.do_login()

        if not self.cansearch:
            return False

        incType = random.randint(1,10)
        pageIndex = random.randint(1,100)
        url = Config.URL_TEMPLATE.format(incType, pageIndex)

        self.headers.update({'Referer':'http://rdsearch.zhaopin.com/home/SearchByCustom'})
        res = self.sess.get(url, headers=self.headers)
        find = re.findall(r'http://rd.zhaopin.com/resumepreview/resume/viewone/2/([^_]*)_\d_\d?', res.text, re.S)
        if find:
            i = random.randint(0, len(find)-1)
            return find[i]

        return False

    def get_ids(self):
        with open('idx', 'wb') as f:
            while(self.count < Config.TOTAL_COUNT):
                jlid = self.get_one()
                if jlid:
                    print "SUCESS, count:{}".format(self.count)
                    f.write('%s\n' % jlid)
                    self.count += 1
                else:
                    print "FAIL"


if __name__ == '__main__':
    zl = CVZLTestGet()
    zl.get_ids()
