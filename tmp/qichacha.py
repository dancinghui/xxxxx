#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.qq.ptlogin import QQPtLogin
from spider.spider import Spider
from spider.savebin import BinSaver
import re
import time
import sys
from spider.httpreq import CurlReq

reload(sys)
sys.setdefaultencoding("utf-8")

'''
=================================================
corporation info from Qichacha
=================================================
'''


class CorpInfo(object):
    def __init__(self):
        self.name = ""
        self.build_time = ""
        self.legal_person = ""
        self.url = ""
        self.address = ""

    def __init__(self, name, build_time, legal_persion, url, address):
        self.name=name
        self.build_time=build_time
        self.legal_person=legal_persion
        self.url=url
        self.address=address

    def __str__(self):
        str=''
        str+=self.name+","
        str+=self.build_time+","
        str+=self.legal_person+","
        str+=self.url+","
        str+=self.address
        return str

    def __repr__(self):
        return self.__str__()
'''
=================================================
'''

'''
=================================================
qichacha QQ login
=================================================
'''
class QccLogin(QQPtLogin):
    def __init__(self, acc):
        QQPtLogin.__init__(self, acc, 'http://qichacha.com/user_qqlogin')

    def _real_do_login(self):
        self.reset_session()
        rv = self.do_pt_login([])
        if rv:
            con = self.request_url("http://qichacha.com/global_user_qqcallback")
        return rv

    def need_login(self, url, response, hint):
        return False


class QccSpider(Spider):
    def __init__(self, acc, threadcnt):
        self.qcclogin=QccLogin(acc)
        super(QccSpider, self).__init__(threadcnt)

    def do_login(self):
        self.qcclogin.do_login()

    def dispatch(self):
        self.bs = BinSaver("qichacha.bin")
        self.add_job("墨麟")
        self.add_job("爱拼")
        self.wait_q()
        self.add_job(None, True)

    def run_job(self, key):
        print "key is ", key
        for i in range(10):
            url = "http://qichacha.com/search?key=" + str(key) + "&index=name&" + "p=" + str(i+1)
            res = self.qcclogin.request_url(url).text
            # if res is None:
            #     print "%d failed, sleeping 10 secs." % jobid
            #     time.sleep(10)
            #     self.add_job(jobid)
            #     return
            if re.search(u'小查还没找到数据',  res ):
                print key, "match nothing"
                break
            # elif re.search(u'该职位已结束', res.text):
            #     print jobid, "match ending"
            # elif re.search(u'您查看的职位已过期', res.text):
            #     print jobid, "match timeout"
            else:
                print "saving %s ..." % (key+str(i+1))
                fn = 'testresult/qichacha.%s.%d' % ((key+str(i+1)), int(time.time()))
                f = open(fn+".txt", "wb")
                f.write(res)
                # self.bs.append(fn, res.text)


    # def get_html_content(self, key, page):
    #     response = self._do_requests("http://qichacha.com/search?key=" + str(key) + "&index=name&" + "p=" + str(page))
    #     f = open("qichacha.txt", "wb")
    #     f.write(response.text)
    #     return response.text
    #
    # def get_corp_info(self, key, page):
    #     content = self.get_html_content(key, page)
    #     # f = open("qichacha.txt", "rb")
    #     # content=f.read()
    #     corps = []
    #     print content
    #     names = self._match(content, '\"site-list-title\".*?searchbadge', '>(.*?)<')
    #     persons = self._match(content, '<label>法人：</label>(.*?)<label>', '')
    #     dates = self._match(content, '<label>成立日期：</label><span >(.*?)</span>', '')
    #     addresses = self._match(content, '<label> 地址：</label>(.*?)</div>', '')
    #     urls = self._match(content, r'<h3 class="site-list-title"><a href="(.*?)"')
    #     for i in range(len(names)):
    #         corp = CorpInfo(names[i], dates[i], persons[i], urls[i], addresses[i])
    #         corps.append(corp)
    #
    #     return corps
    #
    # def _match(self, content, pattern1, pattern2=''):
    #     list = re.findall(r'' + pattern1, content, re.S)
    #     result_list = []
    #     if (pattern2 != ''):
    #         for i in range(len(list)):
    #             tlist = re.findall(r'' + pattern2, list[i], re.S);
    #             result_list.append(''.join(tlist).strip())
    #         return result_list
    #     else:
    #         for i in range(len(list)):
    #             list[i] = list[i].strip()
    #         return list



if __name__ == '__main__':
    ac = {'qqno': 844656278, 'qqpwd': 'hpy19940102'}
    q = QccSpider(ac,10)
    # q = QccLogin(ac)
    q.qcclogin.do_login()
    q.run()
    # print q.get_corp_info("爱拼", 1)