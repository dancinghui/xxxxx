#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
# os.environ['PAGESTORE_DB'] = 'mongodb://localhost/page'
os.environ['PATH'] += ":/usr/local/bin"
from spider.genquery import GQDataHelper, GenQueriesLT
from spider.ipin.savedb import PageStoreBase
from spider.spider import Spider, MRLManager
from hr_login import HrLogin, HrConfig
from spider.util import TimeHandler, htmlfind
import qdata
import copy
import spider
import re
import threading
import json
import time



g_index = os.getpid() % 5


def new_ChinaHrLogin(ac):
    a = HrLogin(ac)
    a.load_proxy('checked_proxy', index=g_index, auto_change=True)
    return a


class CData(GQDataHelper):
    degree_data = [["2", "高中/中专/中技及以下"], ["3", "大专及同等学历"], ["4", "本科/学士及同等学历"], ["5", "硕士及同等学历"], ["6", "博士及以上"], ["6", "其他"]]
    age_data = [['15-20'], ['21-22'],['23-24'], ['25-26'], ['27-28'], ['29-30'], ['31-34'], ['34-37'], ['38-40'], ['41-99'],]
    workStatus = [['1', '在职'], ['2', '离职']]
    # reFreshTime=[['6', "1年内"]]
    reFreshTime = [['3', '一个月'],]
    jobType = [['1', '全职'], ['2', '兼职'], ['3', '实习']]
    hasPhoto = [['0', '无照片'], ['1', '有照片']]
    gender_data = [['1'], ['2']]

    salary = [['0-2000'], ['2001-3000'],['3001-4000'],['4001-5000'],
              ['5001-6000'], ['6001-7000'], ['7001-8000'], ['8001-9000'],
              ['9001-10000'], ['10001-20000'], ['20001-30000'], ['30001-40000'],
              ['40001-50000'], ['50001-99999']]

    SEARCH_URL = 'http://qy.chinahr.com/cv/sou?'
    CV_PAGE_URL_TMPLATE = 'http://qy.chinahr.com/cvm/preview?cvid={}&from=sou'


class CVChinahrStore(PageStoreBase):
    def __init__(self):
        PageStoreBase.__init__(self, 'cv_chinahr', dburl='mongodb://hadoop2/cv_crawler')

    def extract_content(self):

        cur_content = self.get_cur_doc().cur_content
        if isinstance(cur_content, unicode):
            cur_content = cur_content.encode('utf-8')

        find = htmlfind(cur_content, '<div class="inforBase">', 0)

        try:
            info = htmlfind.remove_tag(find.get_text(), True)
            return info
        except Exception, e:
            print "cv_id: %s, exception: %r" % (self.get_cur_doc().cur_jdid, e)
            return None

    def page_time(self):
        cur_content = self.get_cur_doc().cur_content
        if isinstance(cur_content, unicode):
            cur_content = cur_content.encode('utf-8')

        find = re.search(r'<em>更新时间：(.*)</em>', cur_content, re.S)
        if find:
            return TimeHandler.fmt_time(find.group(1))

        return None


class GenQ(GenQueriesLT):
    def __init__(self, thcnt):
        GenQueriesLT.__init__(self, thcnt)
        self.m_db = CVChinahrStore()
        self._name = 'cv_chinahr'
        self.lgm = MRLManager(HrConfig.ac, new_ChinaHrLogin)

        self._tls = threading.local()

    def init_conditions(self):
        CData.add(self, 'live', qdata.city_data) # 必须作为第一条件，否则会有和直接查看url时显示不一样
        CData.add(self, 'reFreshTime', CData.reFreshTime)
        CData.add(self, 'degree', CData.degree_data)
        CData.add(self, 'sex', CData.gender_data)
        CData.add(self, 'age', CData.age_data)
        CData.add(self, 'workStatus', CData.workStatus)
        CData.add(self, 'salary', CData.salary)
        #简历详细度

        CData.add(self, 'jobType', CData.jobType)
        CData.add(self, 'hasPhoto', CData.hasPhoto)
        CData.add(self, 'workPlace', qdata.city_data)
        CData.add(self, 'jobs', qdata.job_data)

        self.select_user_agent('firefox')

    def translate_data(self, o):
        url = {}
        if 'age' in o:
            m = re.split('-', o['age'])
            url.update({'minAge': m[0]})
            url.update({'maxAge': m[1]})

        if 'salary' in o:
            m = re.split('-', o['salary'])
            url.update({'minSalary': m[0]})
            url.update({'maxSalary': m[1]})

        for key in ['degree', 'jobs', 'sex','workPlace', 'reFreshTime', 'live', 'jobType', 'workStatus', 'hasPhoto']:
            if key in o:
                url.update({key : o[key]})
        return url

    def need_split(self, url, level, isLast):
        params = self.translate_data(url)

        real_url = spider.util.compose_url_param(CData.SEARCH_URL, params)

        res = self.lgm.el_request(real_url)
        count = 0
        find = re.search(u'搜索到.*?<span>(\d+).*?</span>', res.text, re.S)
        if find:
            count = int(find.group(1))
            if count > 2999:
                return True

            if count:
                setattr(self._tls, '_count', count)

            print "real_url: %s || count: %d" % (real_url, count)

        return False

    def log_url(self, url):

        if isinstance(url, dict):
            url = self.translate_data(url)
            url = json.dumps(url)

        count = getattr(self._tls, "_count", None)
        if count:
            url = " %s|| %d" % (url, getattr(self._tls, "_count"))
            self.fs.append(url)


class ChinaHrCVGet(Spider):
    def __init__(self, thread_cnt):
        Spider.__init__(self, thread_cnt)
        self._name = 'chinahr_cv_get'
        self.lgm = MRLManager(HrConfig.ac, new_ChinaHrLogin)
        self.page_store = CVChinahrStore()

    def dispatch(self):
        with open('res.cv_chinahr.txt') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                line = line.split("||")[0]
                self.add_main_job({"url": json.loads(line), "type": 'search', 'page': '1'})

        self.wait_q()
        self.add_main_job(None)

    def run_job(self, jobid):

        type_ = jobid.get("type", "")
        if not type_:
            return

        if "search" == type_:
            params = jobid.get('url')
            params.update({"page": jobid.get('page')})
            real_url = spider.util.compose_url_param(CData.SEARCH_URL, params)
            res = self.lgm.el_request(real_url)
            find = re.findall(r'cvId="(.*?)"', res.text, re.S)
            for cvid in find:
                self.add_job({"cvid": cvid, 'type': 'cvpage'})

            if jobid.get('page') == '1':
                self.parse_next(res.text, params)

        if "cvpage" == type_:
            real_url = CData.CV_PAGE_URL_TMPLATE.format(jobid.get('cvid'))
            res = self.lgm.el_request(real_url)
            self.page_store.save(time.time(), jobid.get('cvid'), real_url, res.text)

    def parse_next(self, content, params):
        p = copy.deepcopy(params)
        del p['page']
        find = re.search(u'搜索到.*?<span>(\d+).*?</span>', content, re.S)
        if find:
            totalpage = (int(find.group(1)) + 20) / 20
            for page in range(2, totalpage):
                self.add_job({'url': p, 'type': 'search', 'page': str(page)})

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            spider.util.sendmail(['jianghao@ipin.com'], 'cv_chinahr done', msg)


if __name__ == '__main__':

    # t = GenQ(3)
    t = ChinaHrCVGet(20)
    # t.load_proxy('checked_proxy')
    t.run()