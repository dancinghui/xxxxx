#!/usr/bin/env python
# encoding: utf8

#note: 工作年限的计算有问题.
import spider.util
from zl_login import ZLLogin, GlobalData
from spider.runtime import Log
from spider.spider import MRLManager, LoginErrors
from spider.genquery import GQDataHelper, GenQueries
from spider.spider2 import Spider2
from spider.ipin.savedb import PageStoreBase
import time
import qdata
import json
import re
import sys
import os
from spider.captcha.onlineocr import OnlineOCR
from spider.httpreq import BasicRequests

mongo_cvdb_url = os.getenv('PAGESTORE_DB', "mongodb://localhost/cv_crawler")
g_proxy_index = -1


def new_ZLLogin(ac):
    a = ZLLogin(ac)
    if isinstance(g_proxy_index,str):
        a.set_proxy(g_proxy_index, 0, 0)
    elif isinstance(g_proxy_index, int) and  g_proxy_index >= 0:
        a.load_proxy('curproxy1', index=g_proxy_index, auto_change=False)

    a.load_proxy('proxy')
    return a


class CVZLPageStore(PageStoreBase):
    def __init__(self):
        PageStoreBase.__init__(self, 'cv_zhilian', mongo_cvdb_url)

    def extract_content(self):
        doc = self.get_cur_doc()
        assert isinstance(doc, PageStoreBase.CurDoc)
        hf = spider.util.htmlfind(doc.cur_content, 'id="resumeContentBody"', 0)
        try:
            return hf.get_text()
        except:
            Log.errorbin("invalid cv content %s" % doc.cur_url, doc.cur_content)
            raise

    def page_time(self):
        doc = self.get_cur_doc()
        cur_content = doc.cur_content
        assert isinstance(doc, PageStoreBase.CurDoc)
        if isinstance(cur_content, unicode):
            cur_content = cur_content.encode('utf-8')
        m = re.search(r"简历更新时间：.*?(\d+)年(\d+)月(\d+)日", cur_content)
        if m:
            return self.mktime(m.group(1), m.group(2), m.group(3)) * 1000
        else:
            Log.error("invalid page for %s, url=%s", doc.cur_jdid, doc.cur_url)
            Log.errorbin("invalid cv %s" % doc.cur_url, doc.cur_content)
            return None

    def check_should_fetch(self, jdid):
        indexUrl = "%s://%s" % (self.channel, jdid)
        return not self.find_new(indexUrl)


class CVZhilianGetCV(Spider2):
    def __init__(self, thcnt, cfgname, acs):
        Spider2.__init__(self, thcnt)
        self._name = 'cvzlgetcv_%s' % cfgname
        self.zlm = MRLManager(acs, new_ZLLogin)
        self.pagestore = CVZLPageStore()
        self.hasher = spider.util.LocalHashChecker()
        self.zlm.ensure_login_do(None, lambda n:1, None)
        self.zlm.release_obj()
        self.imgcnt = 0

    def init_jobs(self):
        return

    def wait_job(self):
        return self.wait_job_by_condition()

    def push_job(self, j):
        if j is None:
            self._no_more_wait_job = True
        else:
            self.add_job(j)

    def _get_image(self, refurl):
        imgurl = "http://rd2.zhaopin.com/s/loginmgr/monitorvalidatingcode.asp?t=" + str(int(time.time())*1000)
        con = self.zlm.el_request(imgurl, headers={'Referer':refurl})
        if con is None:
            Log.warning("fetch image failed, sleep 1s")
            time.sleep(1)
            return self._get_image(refurl)
        return con.content

    def get_cv(self, url):
        #http://rd.zhaopin.com/resumepreview/resume/viewone/2/JM622670859R90250000000_1_1?searchresume=1
        con = self.zlm.el_request(url)
        if con is None:
            return None

        if u"您需要输入验证码才能继续后续的操作" in con.text:
            self.imgcnt += 1
            if self.imgcnt > 10:
                self.imgcnt = 0
                self.zlm.set_nologin()
                return None

            for i in range(0,5):
                code = OnlineOCR('zhilian2').resolve(lambda dbgdata=None: self._get_image(url))
                purl = "http://rd.zhaopin.com/resumePreview/resume/_CheackValidatingCode?validatingCode=" + code
                con = self.zlm.el_request(purl, data={'validatingCode':code}, headers={'Referer':url})
                if con is not None:
                    if re.search('true', con.text, re.I):
                        time.sleep(5)
                        return None
                Log.warning('验证码输入失败')
                time.sleep(2)
            #连续失败了5次, 换帐号!!
            self.zlm.set_nologin()
            self.imgcnt = 0
            return None

        return con

    def run_job(self, jobid):
        # {'type':'cv', 'url':'http://rd.zhaopin.com/resumepreview/resume/viewone/2/JM321509749R90250002000_1_1?searchresume=1'}
        if self.get_job_type(jobid) == 'cv':
            url = jobid['url']
            m = re.search(ur'/([0-9A-Z]+)_\d+_\d+', url)
            if m is None:
                Log.error('invalid cv url', url)
                return
            jdid = m.group(1)
            if self.pagestore.check_should_fetch(jdid):
                con = self.get_cv(url)
                if con is None:
                    self.add_job(jobid)
                    return
                if u"该简历已被求职者删除" in con.text:
                    return
                if u"抱歉，该简历已被删除" in con.text:
                    return
                if u"由于系统繁忙，一会再来看一下吧" in con.text:
                    Log.warning("url %s 繁忙不可获得" % url)
                    return
                getime = int(time.time())
                self.pagestore.save(getime, jdid, url, con.text)
            else:
                Log.errinfo("跳过拉取简历%s" % jdid)

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            title = ' '.join(sys.argv) + ' DONE'
            msg += "saved: %d\n" % self.pagestore.saved_count
            spider.util.sendmail(['lixungeng@ipin.com', 'jianghao@ipin.com'], title, msg)


class CVZhilianUtil(object):
    @staticmethod
    def get_count(url, con):
        if u'请修改或适当减少搜索项再进行搜索' in con.text:
            return 0
        hf = spider.util.htmlfind(con.text, 'class="rd-resumelist-span"', 1)
        try:
            count = int(hf.get_text())
            return count
        except:
            Log.error("invalid search content", url)
            Log.errorbin(url, con.text)
            time.sleep(99)
            raise

    @staticmethod
    def sub_pages(url, con):
        count = CVZhilianUtil.get_count(url, con)
        if count > 4000:
            count = 4000
        npages = (count+60-1) / 60
        if npages >= 2:
            b = BasicRequests()
            for p in range(2, npages+1):
                url1 = b.compose_url(url, 'pageIndex', p)
                yield url1

    @staticmethod
    def get_search_url(opts):
        # SF_1_1_27=0为中文简历 SF_1_1_27=1为英文简历, 但是从js看并不能搜英文的.
        b = BasicRequests()
        # surl = 'http://rdsearch.zhaopin.com/Home/ResultForCustom?SF_1_1_7=7,9&orderBy=DATE_MODIFIED,1&pageSize=60&SF_1_1_27=0&exclude=1'
        surl = 'http://rdsearch.zhaopin.com/Home/ResultForCustom?SF_1_1_7=8,9&orderBy=DATE_MODIFIED,1&pageSize=60&SF_1_1_27=0&exclude=1'
        for name, value in opts.items():
            surl = b.compose_url(surl, name, value)
        return surl


class CVZhilianSearch(Spider2):

    PAGE_TEMPLATE="http://rd.zhaopin.com/resumepreview/resume/viewone/1/%s_1_1"
    CRAWLER_RANGE_MAP = {

        '3d': '1,9', #最近三天
        '1w': '2,9', #最近一周
        '2w': '3,9', #最近两周
        '1m': '4,9', #最近一个月
        '2m': '5,9', #最近2个月
        '3m': '6,9', #最近3个月
        '6m': '7,9', #最近6个月
        '1y': '8,9', #最近1年

    }

    def __init__(self, thcnt, acs):
        Spider2.__init__(self, thcnt)
        self._name = 'cv_zhilian'
        self.jobpusher = None
        self.zlm = MRLManager(acs, new_ZLLogin)
        self.headers = {'Referer': 'http://rdsearch.zhaopin.com/Home/ResultForCustom'}
        self.search_cnt = 0

        self.crawler_range = None

    def init_jobs(self):
        # fn = 'cv_zhilian.queries.txt'
        # fn = 'split1y.txt'
        fn = "one_month_splitly.txt"
        self.add_main_job_file({'type':'main'}, fn)

    def search_cnt_checker(self, net):
        # 当搜索次数到达一定数量时, 必须换帐号登录, 否则可能被封.
        self.search_cnt += 1
        if self.search_cnt > 500:
            self.search_cnt = 0
            raise LoginErrors.AccountHoldError()

    def run_job(self, job):
        jt = self.get_job_type(job)
        if jt == 'main':
            joburl = CVZhilianUtil.get_search_url(json.loads(job['line']))
            # if this account can't search, then giveup.
            con = self.zlm.el_request(joburl, headers=self.headers, hint='search', prechecker=self.search_cnt_checker)
            if con.code == 404:
                con = None
            if con is None:
                Log.warning('请求搜索页失败', joburl)
                self.add_job(job)
                return
            for su in CVZhilianUtil.sub_pages(joburl, con):
                self.add_job({'type':'search', 'url': su})
            self.parse_page(joburl, con)
        elif jt == 'search':
            joburl = job['url']
            # if self.crawler_range:
            #     joburl = CVZhilianUtil.get_count()
            con = self.zlm.el_request(joburl, headers=self.headers, hint='search')
            if con.code == 404:
                con = None
            if con is None:
                Log.warning('请求搜索页失败', joburl)
                self.add_job(job)
                return
            self.parse_page(joburl, con)

    def parse_page(self, url, con):
        if u"请修改或适当减少搜索项再进行搜索" in con.text:
            if not self.zlm.cur_worker().cansearch:
                # Account BLOCKED ??
                self.zlm.cur_worker().isvalid = False
                raise RuntimeError("AccountBlocked")
            Log.error("NO_RESULT_OR_BLOCK", url)
            return
        try:
            hf = spider.util.htmlfind(con.text, 'div class="resumes-list"', 0)
            node = hf.get_node()
            a = re.findall(ur'''tag="([a-zA-Z0-9]+)_1"''', node)
            a = spider.util.unique_list(a)
            for i in a:
                # print "found_cv", i
                self.jobpusher({'type':'cv', 'url':CVZhilianSearch.PAGE_TEMPLATE % i})
        except:
            msg = "unknown search result %s" % url
            Log.error(msg, "sleep 5s.")
            Log.errorbin(msg, con.text)
            time.sleep(5)

    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            self.jobpusher(None)
        elif evt == 'STARTED':
            #spider.misc.stacktracer.trace_start('res.trace.html')
            pass


class CVZhilianData(GQDataHelper):
    agelist = []
    for i in range(16, 60):
        agelist.append(["%d,%d" % (i,i)])
    agelist.append(["61,65"])
    agelist.append(["66,99"])

    gender=[['1', '男'],['2', '女']]
    edugr=[["1,1", "初中"], ["2,2", "中技"], ["3,3", "高中"], ["4,4", "中专"], ["5,5", "大专"], ["7,7", "本科"],
           ["9,9", "硕士"], ["11,11", "MBA"], ["13,13", "EMBA"], ["15,15", "博士"], ["0,0", "其它"]]
    workstate=[["1", "离职"], ["2", "在职，可一个月内到岗"], ["3", "在职，不想换工作"], ["4", "在职考虑换工作"], ["5", "应届毕业生"]]
    corp_type=[["1", "国企"], ["5", "民营"], ["4", "合资"], ["2", "外商独资"], ["8", "股份制企业"], ["9", "上市公司"], ["3", "代表处"], ["6", "国家机关"], ["10", "事业单位"], ["7", "其它"]]
    corp_size=[["1", "20人以下"], ["2", "20-99人"], ["3", "100-499人"], ["4", "500-999人"], ["5", "1000-9999人"], ["6", "10000人以上"]]

class CVZhilianSplit(GenQueries):
    def __init__(self, thcnt, ac):
        GenQueries.__init__(self, thcnt)
        self._last_time = 0.0
        self.zlm = MRLManager(ac, new_ZLLogin)
        self.headers = {'Referer': 'http://rdsearch.zhaopin.com/Home/ResultForCustom'}
        self.search_cnt = 0

    def init_conditions(self):
        # 更新日期 固定为6个月
        # 年龄，性别，学历，户口所在地，当前工作状态，现居住地，企业性质，企业规模
        CVZhilianData.add(self, 'SF_1_1_7', [['4,9', '最近一个月']])
        CVZhilianData.add(self, 'SF_1_1_8', CVZhilianData.agelist)
        CVZhilianData.add(self, 'SF_1_1_9', CVZhilianData.gender)
        CVZhilianData.add(self, 'SF_1_1_6',  qdata.provs)  #现居住地
        CVZhilianData.add(self, 'SF_1_1_5', CVZhilianData.edugr)
        CVZhilianData.add(self, 'SF_1_1_10', qdata.provs)  #户口所在地
        CVZhilianData.add(self, 'SF_1_1_29', CVZhilianData.workstate)
        CVZhilianData.add(self, 'SF_1_1_31', CVZhilianData.corp_type)
        CVZhilianData.add(self, 'SF_1_1_30', CVZhilianData.corp_size)
        self.zlm.ensure_login_do(None, lambda n: 1, None)
        cansearch = self.zlm.cur_worker().cansearch
        self.zlm.release_obj()
        if not cansearch:
            raise RuntimeError("this account can't search!")

    def search_cnt_checker(self, net):
        self.search_cnt += 1
        if self.search_cnt > 380:
            self.search_cnt = 0
            raise LoginErrors.AccountHoldError()

    def need_split(self, opts, level, isLast):
        url = CVZhilianUtil.get_search_url(opts)
        con = self.zlm.el_request(url, headers=self.headers, prechecker=self.search_cnt_checker)
        if con.code == 404:
            con = None
        if con is None:
            Log.warning('请求搜索页失败', url)
            time.sleep(5)
            return self.need_split(opts, level, isLast)
        cnt = CVZhilianUtil.get_count(url, con)
        if cnt == 0:
            return 0
        return cnt >= 4000


def do_split():
    l = open("acc4").read()
    jl = json.loads(l)
    sp = CVZhilianSplit(1, jl['main'])
    GlobalData.login_proxy = '106.75.134.190:18888:ipin:ipin1234'
    sp.run()


def main():
    opts = spider.util.GetOptions('c:p:l:t:')
    cfg = opts.get('-c')
    if not cfg:
        print "没有帐号不能运行"
        return
    proxyidx = opts.get('-p')
    global g_proxy_index
    if not proxyidx:
        g_proxy_index = -1
    elif re.search(r'\..*:', proxyidx):
        g_proxy_index = proxyidx
    else:
        g_proxy_index = int(proxyidx)

    GlobalData.login_proxy = opts.get('-l')

    #load accounts.
    jcfg = json.loads(open(cfg).read())
    cfgname = re.sub(".*/", "", cfg)
    gcv = CVZhilianGetCV(1, cfgname, jcfg['gcv'])
    gcv.run(True)
    a = CVZhilianSearch(1, jcfg['main'])

    a.jobpusher = lambda job : gcv.push_job(job)
    a.bindopts(opts)
    a.run()
    gcv.wait_run(True)


if __name__ == '__main__':
    spider.util.use_utf8()
    if len(sys.argv)>=2 and sys.argv[1] == "split":
        do_split()
    else:
        main()
