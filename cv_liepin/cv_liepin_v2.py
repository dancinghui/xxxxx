#!/usr/bin/env python
# -*- coding:utf8 -*-
import sys
sys.path.append(sys.path[0]+"/../")
print sys.path
from page_store import LPCVStore, LPCVConfig
from spider.spider import Spider, MRLManager
from spider.runtime import Log
from spider.genquery import GenQueriesLT, GQDataHelper
from lp_login import LPQYLogin, LPLTLogin
from spider.savebin import FileSaver
import qdata
import spider
import copy
import re
import os
import json
import datetime
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
   "so_translate_flag": "1",
   "cstContent" : {},
   "userStatus" : "",
   "cs_id" : "",
    "yearSalarylow":"",
    "yearSalaryhigh":"",
    }

    headers = {'DNT':1, 'Referer':'http://lpt.liepin.com/resume/soResumeNew/' }
    # accounts = [{'u':'hr20065124', 'p':'zhaopin123'}]
    #
    # accounts = [{'u':'duang2016-2', 'p':'zhaopin1234', 'type': 1},
    #             {'u':'duang2016-1', 'p':'zhaopin1234', 'type': 1},
    #              {'u':'hr20065124', 'p':'zhaopin123', 'type': 1},
    #             {'u': 'lpt20160219', 'p': 'zhaopin1234', 'type': 1},
    #             {'u':'盛阳精诚大区', 'p': 'zhaopin1234', 'type': 1},
    #             ]

    accounts = [

         {'u':'qwer040506', 'p':'zhaopin123', 'type': 1},
         {'u':'xiaoxigua', 'p':'zhaopin123', 'type': 1},
         {'u':'hr20065124', 'p':'zhaopin123', 'type': 1},
          {'u':'盛阳精诚大区', 'p': 'zhaopin1234', 'type': 1},
        {'u':'ymli@wanfeng403.xyz', 'p':'zhaopin123', 'type': 2},
        # {'u':'tmqz@wanfeng403.xyz', 'p':'zhaopin123', 'type': 2},
        {'u':'ymgr@wanfeng403.xyz', 'p':'zhaopin123', 'type': 2},
        # {'u':'asdy@wanfeng403.xyz', 'p':'zhaopin123', 'type': 2},
        # {'u':'lzzm@wanfeng403.xyz', 'p':'zhaopin123', 'type': 2},
        {'u':'jlop@wanfeng403.xyz', 'p':'zhaopin123', 'type': 2},
        # {'u':'hmfw@wanfeng403.xyz', 'p':'zhaopin123', 'type': 2},
        {'u':'86612@wanfeng403.xyz', 'p':'zhaopin123', 'type': 2},

    ]

    # tempfile = spider.racer.TempFileNames()

    # lt_accounts = [{'u':'un98@wanfeng403.xyz', 'p':'zhaopin123'}]
    # lt_accounts = [{'u':'yun8@wanfeng403.xyz', 'p':'zhaopin123'}]
    lt_accounts = [{'u':'evhk@wanfeng403.xyz', 'p':'zhaopin123', 'type': 2}]
    IDS_FILE = "cv_ids.txt"
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
        time.sleep(2)
        data = self.gen_post_data(url, page)

        if self._type == 1:
            url = 'https://lpt.liepin.com/resume/soResumeNew/?forlog=1'
            Cdata.headers.update({'Upgrade-Insecure-Requests':1, 'Referer':'http://lpt.liepin.com/resume/soCondition/'})
        else:
            url = 'https://h.liepin.com/cvsearch/soResume/'
            Cdata.headers.update({'Upgrade-Insecure-Requests':1, 'Referer': 'https://h.liepin.com/cvsearch/soCondition/'})
        con = self.lpm.el_request(url,data=data,headers=Cdata.headers,allow_redirects=True)
        return con


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

        print spider.util.utf8str(url), "|| not need split"
        setattr(self._lts, "_count", count)
        print "|||||||   ", getattr(self._lts, "_count", None)
        return False


    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail(['jianghao@ipin.com'], "CVLPSearch Query Gen", msg)


    def log_url(self, url):
        if isinstance(url, dict):
            url = json.dumps(url)

        count = getattr(self._lts, "_count", None)
        if count:
            url = "%s|| %d" % (url, getattr(self._lts, "_count"))
        tol = spider.util.utf8str(url).strip()
        if tol in self.oldjobs:
            return
        self.fs.append(tol)


class CVLPSearchId(CVLPSearch):

    #type = 1 ==> 企业搜索
    #type = 2 ==> 猎头搜索
    def __init__(self, thread_cnt, ac, type=1, process_num=0, max_process_cnt=1):
        CVLPSearch.__init__(self, thread_cnt, ac, type)

        self._lock = threading.RLock()
        self._ids_num = 0

        # self._name = "CVLPSearchId_process_%d" % process_num
        self._process_num = process_num
        self._max_process_cnt = max_process_cnt

        self._ids_fs = FileSaver(Cdata.IDS_FILE)

    def _inc_num(self):
        with self._lock:
            self._ids_num += 1

    def dispatch(self):
        with open("res.spider.txt", 'rb') as f:
            for index, line in enumerate(f):

                #每个进程处理一部分 数据
                if index % self._max_process_cnt != self._process_num:
                    continue

                line = line.split('}')
                if not line:
                    continue
                url = json.loads(line[0]+"}")

                self.add_main_job({"url": url, "page": "1"})

        self.add_main_job(None)

    def run_job(self, jobd):
        if not isinstance(jobd, dict):
            return

        self.require_time_span(0.5)
        o = self.load_page(jobd.get('url'), jobd.get('page', '1'))
        if o is None:
            self.add_job(jobd)
            return
        if u'抱歉，没有找到符合条件的简历' in o.text:
            print "条件太多， 没找到。。。"

    def load_page(self, condition, page):
        print spider.util.utf8str(condition), "  page: %s" % page
        time.sleep(2)
        data = self.gen_post_data(condition, page)

        if self._type == 1:
            url = 'https://lpt.liepin.com/resume/soResumeNew/?forlog=1'
            Cdata.headers.update({'Upgrade-Insecure-Requests':1, 'Referer':'http://lpt.liepin.com/resume/soCondition/'})
        else:
            url = 'https://h.liepin.com/cvsearch/soResume/'
            Cdata.headers.update({'Upgrade-Insecure-Requests':1, 'Referer': 'https://h.liepin.com/cvsearch/soCondition/'})
        con = self.lpm.el_request(url, data=data, headers=Cdata.headers, allow_redirects=True)
        if not con:
            return None

        time.sleep(2)
        m = re.findall(ur'/resume/showresumedetail/\?res_id_encode=([^& <>"]*)', con.text, re.S)
        m = spider.util.unique_list(m)
        for id_ in m:
            self._inc_num()
            self._ids_fs.append(id_)
            print "found cv_id: %s" % id_

        print "cv id count: %d" % self._ids_num

        #第一次计算分页
        count = 0
        if "1" == str(page):
            if self._type == 1:
                m = re.search(ur'(\d+)[\+]{0,1}\s*<[^<>]*>\s*份简历', con.text)
                if m:
                    count = int(m.group(1))
            elif self._type == 2:
                m = re.search(ur'(\d+)\+\s*<[^<>]*>\s*位人选', con.text, re.S)
                if m:
                    count = int(m.group(1))

            if count > self.split_count:
                print "count : %d > max_count: %d, url: %s" % (count, self.split_count, spider.util.utf8str(url))
                return

            pagecnt = (count+self.pageSize-1) / self.pageSize
            for pn in range(2, pagecnt+1):
                self.add_job({'url': copy.deepcopy(condition), 'page':pn})

        return con

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail(['jianghao@ipin.com'], 'CVLPSearchId process: %d,  DONE' % self._process_num, msg)


class CVLPSpider(Spider):
    def __init__(self, thcnt, acs, type=1, process_num=0, max_process_cnt=1):
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

        self._process_num = process_num
        self._max_process_cnt = max_process_cnt

        self._spider_cnt = 0
        self._start_time = datetime.datetime.today()
        self.url_prefix = 'https://lpt.liepin.com/resume/showresumedetail/?res_id_encode={}&isBatch=0'
        if self._type == 2:
            self.url_prefix = 'https://h.liepin.com/resume/showresumedetail/?res_id_encode={}&isBatch=0'
        self.stat = spider.runtime.StatDict()

        self._limit_cnt=200

    def run_job(self, cvid):

        url = self.url_prefix.format(cvid)
        qstring = "liepincv://"+cvid
        if self.pagestore.check_should_fetch(qstring):
            self.stat.inc('cv')
            o = self.lpm.el_request(url, headers=Cdata.headers, allow_redirects=True)
            if o is None:
                self.add_job(cvid)
                return None
            self.pagestore.save(time.time(), cvid, url, o.text)
            time.sleep(5)
            self._spider_cnt += 1
            self._check_if_stop()
            print "start: %s - now: %s || spider cnt: %d" % (self._start_time, datetime.datetime.today(), self._spider_cnt)
        else:
            print '======%s has downloaded=====' % qstring

    def _check_if_stop(self):
        if self._spider_cnt % self._limit_cnt == 0:
            Log.info("spider %d pages, sleep 60*5s today" % self._spider_cnt)
            time.sleep(60*5)


    def dispatch(self):
        with open(Cdata.IDS_FILE, 'rb') as f:

            for index, line in enumerate(f):
                if index % self._max_process_cnt != self._process_num:
                    continue

                line = line.strip()
                if not line:
                    continue

                if self.pagestore.find_any("%s://%s" % ("cv_liepin", line)):
                    continue
                if not self._is_needed_cv(line):
                    continue

                self.add_main_job(line)

        self.add_main_job(None)

    def _is_needed_cv(self, line):
        if not hasattr(self, 'not_need_cvs'):
            self.not_need_cvs = set()

            if os.path.exists(LPCVConfig.NOT_NEED_CV_FN):
                with open(LPCVConfig.NOT_NEED_CV_FN, 'rb') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        self.not_need_cvs.add(line)

            if os.path.exists(LPCVConfig.NOT_ACCESS_BY_QIYE):
                with open(LPCVConfig.NOT_ACCESS_BY_QIYE, 'rb') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        self.not_need_cvs.add(line)

        if line in self.not_need_cvs:
            return False

        return True

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail(['jianghao@ipin.com'], 'CVLPSpider process %d, DONE' % self._process_num , msg + '\n saved: %d' % self.pagestore.saved_count)


if __name__ == '__main__':
    spider.util.use_utf8()

    if len(sys.argv) < 4:
        print 'Usage: cv_lieping_v2.py [genq | searchId | getCV] process_num max_process_cnt'
        exit(1)

    if int(sys.argv[3]) > len(Cdata.accounts):
        print "not enough accounts, process_cnt: %s > accounts_cnt: %d" % (sys.argv[3], len(Cdata.accounts))
        exit(1)

    process_num = int(sys.argv[2])
    max_proccess_cnt = int(sys.argv[3])
    account = Cdata.accounts[process_num]
    if "genq" in sys.argv[1:]:
        s = CVLPSearch(1, [account], type=account.get("type", 1))
        s.run()
        print "======= gen query complete =========="

    elif "searchId" in sys.argv[1:]:
        sid = CVLPSearchId(1, [account], type=account.get("type", 1), process_num=process_num, max_process_cnt=max_proccess_cnt)
        sid.run()

        print "======= search id complete ==========="

    elif "getCV" in sys.argv[1:]:
        spd = CVLPSpider(1, [account], type=account.get("type", 1), process_num=process_num, max_process_cnt=max_proccess_cnt)
        spd.run()

        print "======= spider page complete =========="
