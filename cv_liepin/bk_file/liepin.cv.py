#!/usr/bin/env python
# -*- coding:utf8 -*-

import StringIO
import copy
import hashlib
import json
import random
import re
import sys
import time

import pymongo
import requests

import cv_liepin.qdata
import spider.racer
import spider.util
from spider.genquery import GenQueries, GQDataHelper
from spider.spider import MultiRequestsWithLogin, MRLManager


class LPCVStore:
    MONGO_URL = "mongodb://page_store:page_store@hadoop3/page_store"
    CHANNEL = 'cv_liepin'
    def __init__(self):
        page_store_client = pymongo.MongoClient(self.MONGO_URL)
        self.col = page_store_client["page_store"]["page_store_" + self.CHANNEL]
    def save(self, url, cvid, page):
        doc = { "indexUrl" : self.CHANNEL + "://" + cvid,
            "contentSign" : "xxxxx",
            "realUrl" : url,
            "crawlerUpdateTime" : long(time.time()*1000),
            "owner" : self.CHANNEL,
            "pageContent" : page.encode('utf-8') }
        dockey = {"indexUrl" : self.CHANNEL + "://" + cvid}
        self.col.update(dockey, doc, True)


class FakeCVStore:
    def __init__(self):
        pass

    def save(self, url, cvid, page):
        print cvid


class Cdata(GQDataHelper):
    edulevel = [["005","博士后"],
["010","博士"],
["020","MBA/EMBA"],
["030","硕士"],
["040","本科"],
["050","大专"],
["060","中专"],
["070","中技"],
["080","高中"],
["090","初中"],]
    sex = GQDataHelper.qlist('男', '女')
    userStatus=[[0,"在职，看看新机会"],[1,"离职，正在找工作"],[2,"在职，急寻新工作"],[3,"在职，暂无跳槽打算"]]
    agedata = [['0-25'], ['26-30'], ['31-35'], ['36-40'], ['41-45'], ['46-55'], ['56-999']]
    workyear = GQDataHelper.qlist('0-2', '3-5', '5-8', '9-999')
    cst_template = {"keys":"","keysRelation":"","company_name":"","company_name_scope":"0","industrys":"","jobtitles"
:"","dqs":"","wantdqs":"","edulevellow":"","edulevelhigh":"","edulevel_tz":"","school_kind"
:"","agelow":"","agehigh":"","workyearslow":"","workyearshigh":"","sex":"","userStatus":"","search_level"
:"2"}
    pd_template = {
   "agehigh" : "",
   "search_level" : "2",
   "jobtitles" : "",
   "company_name" : "",
   "keys" : "",
   "workyearslow" : "",
   "search_scope" : "",
   "dqs" : "",
   "conditionCount" : "",
   "company_name_scope" : "0",
   "wantdqs" : "",
   "edulevellow" : "",
   "industrys" : "",
   "cs_createtime" : "",
   "sex" : "",
   "edulevelhigh" : "",
   "agelow" : "",
   "workyearshigh" : "",
   "so_translate_flag" : "1",
   "cstContent" : {},
   "userStatus" : "",
   "cs_id" : ""
    }
    headers = {'DNT':1, 'Referer':'http://lpt.liepin.com/resume/soResumeNew/' }
    accounts = [{'u':'深圳市晶伯川科技有限公司', 'p':'zhaopin123'}]
    tempfile = spider.racer.TempFileNames()
    try:
        lpcvstore = LPCVStore()
    except:
        print '===== using fake store ======'
        lpcvstore = FakeCVStore()


class LPRequest(MultiRequestsWithLogin):
    def get_image_code(self, url, fc=None):
        while True:
            imgcon = self.request_url(url)
            f = StringIO.StringIO()
            f.write(imgcon.content)
            f.seek(0)
            response = requests.post('http://www.haohaogame.com:8099/codeocr', files={'file':f})
            imgcode = response.text.strip()
            if re.match(ur'^\d+$', imgcode):
                if isinstance(fc,dict):
                    fc['content'] = imgcon.content
                    fc['code'] = imgcode
                return imgcode

    def _real_do_login(self):
        print "===========login========="
        self.reset_session()
        mainpage = 'http://www.liepin.com/user/lpt/'
        headers = {'Referer':mainpage}
        con = self.request_url(mainpage)
        imgcode = self.get_image_code('http://www.liepin.com/image/randomcode4Login/?' + str(random.random()))
        data = {'rand':imgcode, 'user_kind':1, 'user_login':self.account['u'],
                'user_pwd': hashlib.md5(self.account['p']).hexdigest() }
        con = self.request_url('http://www.liepin.com//webUser/ajaxLogin4BH', data=data, headers=headers)
        try:
            jo = json.loads(con.text)
            if jo.get('flag') == 1:
                return 1
        except:
            pass
        return 0

    def need_login(self, url, con, hint):
        if con.is_permanent_redirect or con.is_redirect:
            location = con.headers.get('location')
            if 'validat' in location.lower():
                print location
                spider.util.sendmail('lixungeng@ipin.com', 'need validate code', location)
                while not self.validate_user(location):
                    time.sleep(10)
                return 'retry'
            return True
        return False

    def validate_user(self, url):
        self.request_url(url)
        code = self.get_image_code('http://www.liepin.com/image/randomcode4ValidationUser/')
        postdata = {'object_type': 1, 'rand_validationuser':code}
        con = self.request_url('http://www.liepin.com/validation/verifyIllegalUser/', data=postdata)
        if con is not None:
            j = json.loads(con.text)
            if int(j.get('flag')) == 0:
                print j.get('msg').encode('utf-8')
            else:
                return True
        return False


class LiepinCV(GenQueries, MRLManager):
    MAX_VIEW = 200
    MAX_PAGE = 10
    PAGE_CNT = 20

    def __init__(self, thcnt):
        GenQueries.__init__(self, thcnt)
        MRLManager.__init__(self, Cdata.accounts, LPRequest)
        self._name = 'lp_queries'
        self.baseurl = {}

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail('lixungeng@ipin.com', '%s DONE' % sys.argv[0], msg)

    def init_conditions(self):
        Cdata.add(self, 'industrys', cv_liepin.qdata.industries)
        Cdata.add(self, 'dqs', cv_liepin.qdata.cities)
        Cdata.add(self, 'edulevel', Cdata.edulevel)
        Cdata.add(self, 'sex', Cdata.sex)
        Cdata.add(self, 'userStatus', Cdata.userStatus)
        Cdata.add(self, 'age', Cdata.agedata)
        Cdata.add(self, 'workyear', Cdata.workyear)

    def gen_post_data(self, o1, page_no=1):
        q = copy.deepcopy(o1)
        if 'edulevel' in q:
            q['edulevellow'] = q['edulevel']
            q['edulevelhigh'] = q['edulevel']
            del q['edulevel']
        if 'age' in q:
            m = re.split('-', q['age'])
            q['agelow'] = m[0]
            q['agehigh'] = m[1]
            del q['age']
        if 'workyear' in q:
            m = re.split('-', q['workyear'])
            q['workyearslow'] = m[0]
            q['workyearshigh'] = m[1]
            del q['workyear']
        data = copy.deepcopy(Cdata.pd_template)
        data.update(q)
        cst = copy.deepcopy(Cdata.cst_template)
        cst.update(q)
        data['cstContent'] = json.dumps(cst)
        data['conditionCount'] = len(o1)
        data['curPage'] = page_no
        data['pageSize'] = 20
        return data

    def load_page(self, url, page):
        data = self.gen_post_data(url, page)
        con = self.request_url('http://lpt.liepin.com/resume/soResumeNew/?forlog=1', data=data, headers=Cdata.headers,
                               allow_redirects=False)
        if con is None:
            return None
        time.sleep(2)
        #process con.text
        m = spider.util.chained_regex(con.text,
            re.compile(ur'table-resume-list.*table-resume-list(.*)</table>', re.S),
            re.compile(ur'"(/resume/showresumedetail[^" ]*)') )
        m = spider.util.unique_list(m)
        for o in m:
            self.add_job({'type':'cvurl', 'url':"http://lpt.liepin.com" + o.encode('utf-8')})
        return con

    def run_job(self, jobd):
        self.dump_jobid(jobd)
        GenQueries.run_job(self, jobd)
        if not isinstance(jobd, dict):
            return
        if jobd.get('type') == 'loadpage':
            o = self.load_page(jobd.get('url'), jobd.get('page'))
            if o is None:
                self.add_job(jobd)
        if jobd.get('type') == 'cvurl':
            url = jobd.get('url')
            m = re.search(r'res_id_encode=([a-z0-9A-Z]+)', url)
            if m:
                cvid = m.group(1)
                qstring = "liepincv://"+cvid
                cnt = spider.util.HashChecker().query(qstring)
                if cnt is not None and int(cnt) != 0:
                    print '======%s hash downloaded=====' % qstring
                    return
                o = self.al_request(jobd.get('url'), headers=Cdata.headers, allow_redirects=False)
                if o is None:
                    return None
                print '==========saveing======'
                spider.util.HashChecker().add(qstring)
                time.sleep(5)
                Cdata.lpcvstore.save(url, cvid, o.text)
                print '==========save done===='

    def need_split(self, url, level, isLast):
        if level<1:
            return True
        con = self.load_page(url, 1)

        if u'抱歉，没有找到符合条件的简历' in con.text:
            return False
        count = 0
        m = re.search(ur'共有\s*<[^<>]*>\s*(\d+)\s*<[^<>]*> 份简历', con.text)
        if m:
            count = int(m.group(1))
        pagecnt = (count+self.PAGE_CNT-1) / self.PAGE_CNT

        if pagecnt >= 2 and (isLast or pagecnt <= self.MAX_PAGE):
            for ip in range(2, pagecnt+1):
                self.add_job({'url':copy.deepcopy(url), 'type':'loadpage', 'page':ip})
        if pagecnt <= self.MAX_PAGE:
            return False
        return True


def test():
    l = LPRequest({'u':'username', 'p':'password'})
    for i in range(0, 100):
        tk = {}
        code = l.get_image_code('http://www.liepin.com/image/randomcode4ValidationUser/', tk)
        with open('%03d_%s.jpg' % (i, code), 'wb') as f:
            f.write(tk['content'])

if __name__ == '__main__':
    if len(sys.argv)>=2 and sys.argv[1] == 'test':
        test()
    else:
        l = LiepinCV(1)
        l.run()
