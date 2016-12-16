#!/usr/bin/env python
# -*- coding:utf8 -*-
import sys
sys.path.append(sys.path[0]+"/../")
print sys.path
from page_store import LPCVStore
from spider.spider import Spider, MRLManager
from spider.genquery import GenQueriesLT, GQDataHelper
from lp_login import LPQYLogin, LPLTLogin
import qdata
import spider
import copy
import re
import os
import json
import time
import spider.runtime
import threading


g_index = os.getpid() % 6

def new_LPQYLogin(ac):
    a = LPQYLogin(ac)
    a.load_proxy('proxy', index=g_index, auto_change=False)
    return a

def new_LPLTLogin(ac):
    a = LPLTLogin(ac)
    a.load_proxy('proxy', index=g_index, auto_change=False)
    return a


class Cdata(GQDataHelper):
    edulevel = [["005","博士后"],["010","博士"],["020","MBA/EMBA"],["030","硕士"],["040","本科"]]
    # edulevel.extend([["050","大专"],["060","中专"],["070","中技"],["080","高中"],["090","初中"]])
    sex = GQDataHelper.qlist('男', '女')
    userStatus=[[0,"在职，看看新机会"],[1,"离职，正在找工作"],[2,"在职，急寻新工作"],[3,"在职，暂无跳槽打算"]]
    agedata = [['0-25'], ['26-30'], ['31-32'], ['33-35'], ['36-40'], ['41-45'], ['46-55'], ['56-999']]

    # workyear = GQDataHelper.qlist('0-2', '3-5', '6-8', '9-999')
    workyear = GQDataHelper.qlist('5-10', '11-999')
    yearSalary = GQDataHelper.qlist('30-80','81-999')
    cst_template = {"keys":"","keysRelation":"","company_name":"","company_name_scope":"0","industrys":"","jobtitles"
:"","dqs":"","wantdqs":"","edulevellow":"","edulevelhigh":"","edulevel_tz":"","school_kind"
:"","agelow":"","agehigh":"","workyearslow":"","workyearshigh":"", "yearSalarylow": "", "yearSalaryhigh":"", "sex":"","userStatus":"","search_level"
:"2"}
    pd_template = {
   "agehigh" : "",
   "search_level" : "1",
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
   "cs_id" : "",
    "yearSalarylow":"",
    "yearSalaryhigh":"",
    }

    headers = {'DNT':1, 'Referer':'http://lpt.liepin.com/resume/soResumeNew/' }
    accounts = [{'u':'hr20065124', 'p':'zhaopin123'}]
    # tempfile = spider.racer.TempFileNames()

    # lt_accounts = [{'u':'un98@wanfeng403.xyz', 'p':'zhaopin123'}]
    # lt_accounts = [{'u':'yun8@wanfeng403.xyz', 'p':'zhaopin123'}]
    lt_accounts = [{'u':'evhk@wanfeng403.xyz', 'p':'zhaopin123'}]

    # lpcvstore = LPCVStore()


class CVLPSearch(GenQueriesLT):
    def __init__(self, thcnt, ac, type=1):
        GenQueriesLT.__init__(self, thcnt)
        self._last_time = 0.0
        self._type = type
        self.lpm = self.getlpm(ac, type)
        self.jobpusher = None
        self.headers = Cdata.headers
        self._lts = threading.local()

        self.pageSize = 20
        self.split_count = 2000
        if self._type == 2:
            self.pageSize = 50
            self.split_count = 5000

    def getlpm(self, ac, tp):
        if tp == 1:
            return MRLManager(ac, new_LPQYLogin)
        elif tp == 2:
            return MRLManager(ac, new_LPLTLogin)

    def require_time_span(self, tm):
        if self._last_time > 0:
            t = time.time() - self._last_time
            if t < tm:
                time.sleep(tm - t)
        self._last_time = time.time()

    def init_conditions(self):
        Cdata.add(self, 'yearSalary', Cdata.yearSalary)
        Cdata.add(self, 'workyear', Cdata.workyear)
        Cdata.add(self, 'edulevel', Cdata.edulevel)
        Cdata.add(self, 'industrys', qdata.industries)
        Cdata.add(self, 'dqs', qdata.cities)
        Cdata.add(self, 'sex', Cdata.sex)
        Cdata.add(self, 'userStatus', Cdata.userStatus)
        Cdata.add(self, 'age', Cdata.agedata)
        print "may max count:", self.get_max_count()

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

        if 'yearSalary' in q:
            m = re.split('-', q['yearSalary'])
            q['yearSalarylow'] = m[0]
            q['yearSalaryhigh'] = m[1]
            del q['yearSalary']

        data = copy.deepcopy(Cdata.pd_template)
        data.update(q)
        cst = copy.deepcopy(Cdata.cst_template)
        cst.update(q)
        data['cstContent'] = json.dumps(cst)
        data['conditionCount'] = len(o1)
        data['curPage'] = page_no
        data['pageSize'] = self.pageSize
        return data

    def load_page(self, url, page):
        print spider.util.utf8str(url)
        data = self.gen_post_data(url, page)

        if self._type == 1:
            url = 'https://lpt.liepin.com/resume/soResumeNew/?forlog=1'
            Cdata.headers.update({'Upgrade-Insecure-Requests':1, 'Referer':'http://lpt.liepin.com/resume/soCondition/'})
        else:
            url = 'https://h.liepin.com/cvsearch/soResume/'
            Cdata.headers.update({'Upgrade-Insecure-Requests':1, 'Referer': 'https://h.liepin.com/cvsearch/soCondition/'})
        con = self.lpm.el_request(url,data=data,headers=Cdata.headers,allow_redirects=True)
        return con

        # time.sleep(5)
        # m = re.findall(ur'/resume/showresumedetail/\?res_id_encode=([^& <>"]*)', con.text, re.S)
        # m = spider.util.unique_list(m)
        # for o in m:
        #     self.jobpusher({'type':'cvurl', 'jobid': o.encode('utf-8')})
        # return con

    def need_split(self, url, level, isLast):
        if level < 1:
            return True
        con = self.load_page(url, 1)
        if u'抱歉，没有找到符合条件的简历' in con.text:
            return False
        if u'您搜索简历操作过于频繁，系统已自动限制您搜索简历操作' in con.text:
            print u"您搜索简历操作过于频繁，系统已自动限制您搜索简历操作"
            return False
        count = 0
        if self._type == 1:
            m = re.search(ur'(\d+)[\+]{0,1}\s*<[^<>]*>\s*份简历', con.text)
            if m:
                count = int(m.group(1))
        elif self._type == 2:
            m = re.search(ur'(\d+)\+\s*<[^<>]*>\s*位人选', con.text, re.S)
            if m:
                count = int(m.group(1))

        if count >= self.split_count:
            return True
        # pagecnt = (count+self.pageSize-1) / self.pageSize
        # for ip in range(1, pagecnt+1):
        #     self.add_job({'url': copy.deepcopy(url), 'type':'search', 'page':ip})

        setattr(self._lts, "_count", count)
        print "|||||||   ", getattr(self._lts, "_count", None)
        return False

    def run_job(self, jobd):
        GenQueriesLT.run_job(self, jobd)
        if not isinstance(jobd, dict):
            return
        tp = self.get_job_type(jobd)
        if tp == 'search':
            self.require_time_span(0.5)
            o = self.load_page(jobd.get('url'), jobd.get('page'))
            if o is None:
                self.add_job(jobd)
                return
            if u'抱歉，没有找到符合条件的简历' in o.text:
                print "条件太多， 没找到。。。"

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            self.jobpusher(None)

    def log_url(self, url):
        if isinstance(url, dict):
            url = json.dumps(url)

        count = getattr(self._lts, "_count", None)
        if count:
            url = "%s\t%d" % (url, getattr(self._lts, "_count"))
        tol = spider.util.utf8str(url).strip()
        if tol in self.oldjobs:
            return
        self.fs.append(tol)


class CVLPSpider(Spider):
    def __init__(self, thcnt, acs, type=1):
        Spider.__init__(self, thcnt)
        self._name = 'cvlpspider'
        self.lpm = MRLManager(acs, new_LPQYLogin)

        if type == 2:
            self.lpm = MRLManager(acs, new_LPLTLogin)
        self.pagestore = LPCVStore()
        self.hasher = spider.util.LocalHashChecker()
        self.lpm.ensure_login_do(None, lambda n:1, None)
        self.lpm.release_obj()
        self.imgcnt = 0
        self._type = type

        self.url_prefix = 'https://lpt.liepin.com/resume/showresumedetail/?res_id_encode={}&isBatch=0'
        if self._type == 2:
            self.url_prefix = 'https://h.liepin.com/resume/showresumedetail/?res_id_encode={}&isBatch=0'
        self.stat = spider.runtime.StatDict()

    def run_job(self, jobd):
        if jobd.get('type') == 'cvurl':
            cvid = jobd.get('jobid')
            url = self.url_prefix.format(cvid)

            qstring = "liepincv://"+cvid
            if self.pagestore.check_should_fetch(qstring):
                self.stat.inc('cv')
                o = self.lpm.el_request(url, headers=Cdata.headers, allow_redirects=True)
                if o is None:
                    self.add_job(jobd)
                    return None
                self.pagestore.save(time.time(), cvid, url, o.text)
                time.sleep(3)
            else:
                print '======%s has downloaded=====' % qstring

    def dispatch(self):
        with open("res.spider.txt", 'rb') as f:
            for line in f:
                line = line.split("\t")
                if not line:
                    continue
                self.add

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail(['lixungeng@ipin.com', 'jianghao@ipin.com'], '%s DONE' % sys.argv[0], msg)


if __name__ == '__main__':
    spider.util.use_utf8()
    # cvget = CVLPSpider(1, Cdata.lt_accounts, type=2)
    # cvget.run(True)
    s = CVLPSearch(1, Cdata.accounts, type=1)
    s.jobpusher = lambda job: None # cvget.add_main_job(job)
    s.run()
    # cvget.wait_run(True)
