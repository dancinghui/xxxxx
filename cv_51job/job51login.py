#!/usr/bin/env python
# encoding:utf-8

import qdata
import re
import copy
from spider.spider import MultiRequestsWithLogin, LoginErrors
from spider.httpreq import DbgCurlReq
from urllib2 import urlparse
from lxml import html
import spider.util
import time
from spider.genquery import GQDataHelper
from spider.runtime import StatDict, Log
import copy


class CV51Data(GQDataHelper):
    KEYWORD=""
    LASTMODIFYSEL=[["1", "一周内"], ["2", "两周内"], ["3", "一个月内"], ["4", "两个月内"], ["5", "六个月内"], ["2015", "2015年"], ["2014", "2014年"], ["2013", "2013年"]]

    #["99", "不限"],
    JOBSTATUS=[["0", "目前正在找工作"], ["1", "半年内无换工作的计划"], ["2", "一年内无换工作的计划"], ["3", "观望有好的机会再考虑"], ["4", "我暂时不想找工作"]]

    WORKYEAR = [["0-1", "不限-在读"], ["2-2", "应届"], ["3-3", "一年"], ["4-4", "二年"], ["5-5", "三年"], ["6-6", "五年"],
        ["7-7", "八年"], ["8-99", "十年-不限"]]
    TOPDEGREE =[["1-1", "初中及以下"], ["2-2", "高中"], ["3-3", "中技"], ["4-4", "中专"], ["5-5", "大专"], ["6-6", "本科"], ["7-7", "硕士"], ["10-", "MBA"], ["8-9", "博士"]]
    SEX = [["0", "男"], ["1", "女"]] ##["99", "不限"],
    AGE=[['0-15'], ['60-99'], ]
    for i in range(16,60):
        AGE.append(['%d-%d' % (i,i)])
    AREA=qdata.jobarea
    TOPMAJOR=qdata.mj

    @staticmethod
    def build_hidvalue(args):
        #hvTemp1="KEYWORDTYPE#0*LASTMODIFYSEL#5*JOBSTATUS#0*AGE#3|99*WORKYEAR#2|3*SEX#99*AREA#010000*TOPMAJOR#$经济学类|1000$*TOPDEGREE#2|6*KEYWORD#多关键字用空格隔开"
        hvTemplate="KEYWORDTYPE#0*LASTMODIFYSEL#5*JOBSTATUS#99*AGE#|*WORKYEAR#0|99*SEX#99*AREA#010000*TOPDEGREE#|"
        rs = []
        checked = {}
        for m in re.finditer(r'(\w+)\#([^\*]*)', hvTemplate):
            vname = m.group(1)
            checked[vname] = 1
            if vname in args:
                rs.append(vname + '#' + CV51Data._trans_data(vname, args[vname]))
            else:
                rs.append(m.group())
        for k,v in args.items():
            if k in checked:
                continue
            rs.append(k+'#'+CV51Data._trans_data(k,v))
        return "*".join(rs)

    @staticmethod
    def _trans_data(name, value):
        if name=='WORKYEAR' or name == 'TOPDEGREE' or name == 'AGE':
            return re.sub('-', '|', value)
        return value

    @staticmethod
    def xupdate(doit, kvs, sss):
        if not doit:
            return
        sss = re.sub(r"^\s+|\s+$", '', sss)
        ars = re.split(r"\s*\n\s*", sss, 0, re.S)
        for l in ars:
            if l[0:1] == '#':
                continue
            n,v = re.split(r'=>?', l)
            v = v.strip()
            n = n.strip()
            if v == '<non_exists>':
                if kvs.has_key(n):
                    del kvs[n]
            else:
                kvs[n] = v


class Job51Login(MultiRequestsWithLogin):
    search_index_page = 'http://ehire.51job.com/Candidate/SearchResumeIndex.aspx'
    search_page = 'http://ehire.51job.com/Candidate/SearchResume.aspx'

    # http://ehire.51job.com/CommonPage/RandomNumber.aspx?type=login
    def __init__(self, ac):
        MultiRequestsWithLogin.__init__(self, ac)
        self.ac = ac
        self.cansearch = 0
        self.valid_from = 0
        self.statistics = StatDict()

    def is_valid(self):
        return self.isvalid and int(time.time()) > self.valid_from

    def need_login(self, url, con, hint):
        atext = re.sub(u'<script.*?</script>', u'', con.text, flags=re.S)
        if 'ResumeView.aspx' in url and u'您的操作过于频繁，请注意劳逸结合，休息一会再来' in con.text:
            args = spider.util.utf8str(self.account), self.statistics.get('req'), self.statistics.average_time('req', 'i_use')
            self.statistics.reset()
            Log.error("帐号%s暂时不能看简历 n=%d, av=%s" % args )
            raise LoginErrors.AccountHoldError('too much op')
        if '/SearchResume.aspx' in url and u'您的操作过于频繁，请注意劳逸结合，休息一会再来' in atext:
            args = spider.util.utf8str(self.account), self.statistics.get('req'), self.statistics.average_time('req', 'i_use')
            self.statistics.reset()
            Log.error("帐号%s暂时不能搜索简历 n=%d, av=%s" % args )
            time.sleep(30)
            raise LoginErrors.AccountHoldError('too much op')
        if '/MainLogin.aspx' in con.request.url:
            raise LoginErrors.NeedLoginError('need login')

        if '/Errors.aspx' in con.request.url:
            raise LoginErrors.AccountHoldError('accout exception')

    @staticmethod
    def process_form(domform):
        if isinstance(domform, list) and len(domform) > 0:
            domform = domform[0]
        kvs={}
        submits = {}
        if domform is None:
            return {}
        inps = domform.xpath("//input")
        count = 0
        for i in inps:
            name = i.attrib.get('name', '')
            value = i.attrib.get('value', '')
            type_ = i.attrib.get('type', '').strip().lower()
            if type_ == 'submit':
                submits[name] = value
            elif name != '':
                kvs[name] = value
                count += 1
        return kvs, submits

    def _kick_offline(self, con, condom):
        form = condom.xpath("//form[@id='form1']")[0]
        kvs,_ = self.process_form(form)
        # javascript:__doPostBack('gvOnLineUser','KickOut$0')
        kvs['__EVENTTARGET'] = 'gvOnLineUser'
        kvs['__EVENTARGUMENT'] = 'KickOut$0'
        action = urlparse.urljoin(con.request.url, form.attrib.get('action'))
        con = self.request_url(action, data=kvs, headers={'Referer': con.request.url})
        return 'Navigate.aspx' in con.request.url

    def request_url(self, url, **kwargs):
        self.statistics.inc("req")
        return MultiRequestsWithLogin.request_url(self, url, **kwargs)

    def _real_do_login(self):
        self.statistics.timestart('i_use')
        con0 = self.request_url('http://ehire.51job.com/Navigate.aspx')
        if 'MainLogin.aspx' not in con0.request.url:
            self.cansearch = self.test_search()
            self.statistics.set("req",0)
            return True

        baseurl = 'http://ehire.51job.com/MainLogin.aspx'
        con1 = self.request_url(baseurl)
        hdoc = html.fromstring(con1.text)
        kvs,_ = self.process_form(hdoc.xpath("//form[@id='form1']"))

        MemberName, UserName = tuple(self.account['u'].split(':', 1))
        Password = self.account['p'][0:12]
        chkcode = ''
        if 'txtCheckCodeCN' in kvs:
            chkcode = 'hehe'
        data={'ctmName': MemberName, 'userName': UserName, 'password': Password, 'checkCode': chkcode,
            'oldAccessKey': kvs['hidAccessKey'], 'langtype': kvs['hidLangType'], 'isRememberMe': 'false',
            'sc': kvs['fksc'], 'ec': kvs.get("hidEhireGuid",''), 'returl': kvs.get('returl', '')}
        headers = {'Referer':baseurl}
        con2 = self.request_url("https://ehirelogin.51job.com/Member/UserLogin.aspx", data=data, headers=headers)
        hdoc = html.fromstring(con2.text)
        ei = hdoc.xpath("//form[@id='form1']//span[@id='lblErrorCN']")
        if len(ei)>0:
            xt = ei[0].text_content().strip()
            print spider.util.utf8str(self.account), xt
            if u'会员名、用户名或密码不准确' in xt:
                self.isvalid = False
            if u'您的会员有效期已过' in xt:
                self.isvalid = False
            return False
        if '/useroffline' in con2.request.url.lower():
            if not self._kick_offline(con2, hdoc):
                return False
        elif 'navigate.aspx' not in con2.request.url.lower():
            return False
        self.cansearch = self.test_search()

        if not self.cansearch:
            raise LoginErrors.AccountHoldError('ACCOUT EXCEPTION: %r', self.ac)

        self.statistics.set("req",0)
        return True

    def test_search(self):
        con = self.request_url(self.search_page)
        if con is None or u'您无权操作该页面' in con.text:
            return False

        cansearch = False
        if u'更多可选搜索条件' in con.text:
            cansearch = True
        elif u'点击此处按简历更新时间排序' in con.text:
            cansearch = True
        elif u'/Candidate/ResumeView.aspx?hidUserID=' in con.text:
            cansearch = True
        else:
            return False
        condom = html.fromstring(con.text)
        kvs,_ = self.process_form( condom.xpath("//form[@id='form1']") )
        self._clean_kvs(kvs, "ctrlSerach")
        #kvs['pagerTop$TwentyButton'] = 20
        kvs['pagerTop$FiftyButton']=50
        con = self.request_url(self.search_page, data=kvs, headers={'Referer':self.search_page})
        return True

    def dump_result(self, folist):
        aco = copy.deepcopy(self.account)
        if not self.isvalid:
            aco['status'] = "BROKEN"
        elif self.cansearch == 0:
            aco['status'] = "不能搜索"
        acinfo = spider.util.utf8str(aco)
        for fo in folist:
            fo.write(acinfo + "\n")

    def _clean_kvs(self, kvs, *names):
        ks = kvs.keys()
        for k in ks:
            k1 = re.sub(r'\$.*', '', k)
            if k1 in names:
                del kvs[k]

    def get_search_data(self, qopts):
        con0 = self.request_url(self.search_index_page)
        if not con0:
            return None, None
        con0dom = html.fromstring(con0.text)
        form = con0dom.xpath("//form[@id='form1']")[0]
        kvs,_ = self.process_form(form)
        kvs['hidValue'] = CV51Data.build_hidvalue(qopts)
        kvs['pagerBottom$lbtnGO'] = ' '
        kvs['pagerBottom$txtGO'] = 1
        con1 = self.request_url(self.search_page, data=kvs, headers={'Referer':self.search_index_page})
        if not con1:
            return None, None
        con1dom = html.fromstring(con1.text)
        form1 = con1dom.xpath("//form[@id='form1']")[0]
        kvs1,_ = self.process_form(form1)
        self._clean_kvs(kvs1, "ctrlSerach", "cbxColumns")
        kvs1['hidValue'] = CV51Data.build_hidvalue(qopts)
        kvs1['pagerBottom$lbtnGO'] = ' '
        kvs1['pagerBottom$txtGO'] = 1
        return kvs1, con1

    @staticmethod
    def update_search_data(kvs, page):
        kvs1 = copy.deepcopy(kvs)
        kvs1['pagerBottom$txtGO'] = page
        return kvs1


class Job51LoginDbg(Job51Login):
    def __init__(self, ac, fn):
        Job51Login.__init__(self, ac)
        self._ckfn = fn

    def _new_request_worker(self):
        return DbgCurlReq(self._curlshare, self._ckfn)
