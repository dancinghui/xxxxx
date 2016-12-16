#coding=utf-8

from requests import sessions
from lxml import html
import urlparse
import random
import re
import time
import copy

class Config(object):
    TOTAL_COUNT = 100
    ID_LOW = 0
    ID_MAX = 5000000
    TIMERANGE = 3600 * 24 * 30 * 6

    PAGE_URL_TEMPLATE = "http://ehire.51job.com/Candidate/ResumeView.aspx?hidUserID={}"
    LOGIN_URL = 'http://ehire.51job.com/MainLogin.aspx'
    SEARCH_URL_TEMPLATE = "http://ehire.51job.com/Candidate/SearchResume.aspx"

    SEARCH_KEY_WORDS = ["工程师", "销售", "会计"]

    ac = {"p": "0491418666lcf", "u": "15678111:187602"}

    DATE_TEMPLATE = {

        "__EVENTTARGET": "trlSerach$btnConditionQuery",
        "__EVENTARGUMENT": "",
        "__LASTFOCUS": "",
        "__VIEWSTATE": "", #
        "MainMenuNew1$CurMenuID":"MainMenuNew1_imgResume|sub4",
        "ctrlSerach$hidTab":"",
        "ctrlSerach$hidFlag":"",
        "ctrlSerach$ddlSearchName":"",
        "ctrlSerach$hidSearchID":"",
        "ctrlSerach$hidChkedExpectJobArea":"",
        "ctrlSerach$KEYWORD":"",
        "ctrlSerach$KEYWORDTYPE":"",
        "ctrlSerach$AREA$Text":"选择/修改",
        "ctrlSerach$AREA$Value":"",
        "ctrlSerach$TopDegreeFrom":"",
        "ctrlSerach$TopDegreeTo":"",
        "ctrlSerach$LASTMODIFYSEL":5, #最近6个month
        "ctrlSerach$WorkYearFrom": 0,
        "ctrlSerach$WorkYearTo":99,
        "ctrlSerach$WORKFUN1$Text":"选择/修改",
        "ctrlSerach$WORKFUN1$Value":"",
        "ctrlSerach$WORKINDUSTRY1$Text": "选择/修改",
        "ctrlSerach$WORKINDUSTRY1$Value":"",
        "ctrlSerach$SEX":99,
        "ctrlSerach$JOBSTATUS":99,
        "ctrlSerach$txtUserID": "-多个简历ID用空格隔开-",
        "ctrlSerach$txtSearchName":"",
        "pagerBottom$btnNum4":1, #
        "pagerBottom$txtGO":0, #
        "cbxColumns$0":"AGE",
        "cbxColumns$1":"WORKYEAR",
        "cbxColumns$2":"SEX",
        "cbxColumns$4":"AREA",
        "cbxColumns$8":"TOPMAJOR",
        "cbxColumns$9":"TOPDEGREE",
        "cbxColumns$14": "LASTUPDATE",
        "hidSearchHidden":"",
        "hidUserID":"",
        "hidCheckUserIds":"",
        "hidCheckKey":"", #
        "hidEvents": "",
        "hidBtnType":"",
        "hidDisplayType":0,
        "hidJobID":"",
        "hidValue":"KEYWORDTYPE#0*LASTMODIFYSEL#5*JOBSTATUS#99*WORKYEAR#0|99*SEX#99*TOPDEGREE#|*KEYWORD#", #,
        "hidWhere":"00#0#0#0|99|20150722|20160122|99|99|99|99|99|000000|000000|99|99|99|0000|99|99|99|00|0000|99|99|99|0000|99|99|00|99|99|99|99|99|99|99|99|99|000000|0|0|0000|99#%BeginPage%#%EndPage%#", #
        "hidSearchNameID":"",
        "hidEhireDemo":"",
        "hidNoSearch":"",
        "hidYellowTip":"",





    }


class CV51TestGet(object):
    def __init__(self):
        self.sess = sessions.Session()
        self.account = Config.ac
        self.count = 0

    def do_login(self):

        res = self.sess.get(Config.LOGIN_URL)
        hdoc = html.fromstring(res.text)
        kvs,_ = self.process_form(hdoc.xpath("//form[@id='form1']"))

        MemberName, UserName = tuple(self.account['u'].split(':', 1))
        Password = self.account['p'][0:12]

        chkcode = ''
        if 'txtCheckCodeCN' in kvs:
            chkcode = 'hehe'
        data={'ctmName': MemberName, 'userName': UserName, 'password': Password, 'checkCode': chkcode,
            'oldAccessKey': kvs['hidAccessKey'], 'langtype': kvs['hidLangType'], 'isRememberMe': 'false',
            'sc': kvs['fksc'], 'ec': kvs.get("hidEhireGuid",''), 'returl': kvs.get('returl', '')}
        headers = {'Referer':Config.LOGIN_URL}

        con2 = self.sess.post("https://ehirelogin.51job.com/Member/UserLogin.aspx", data=data, headers=headers)
        hdoc = html.fromstring(con2.text)

        ei = hdoc.xpath("//form[@id='form1']//span[@id='lblErrorCN']")
        if len(ei)>0:
            xt = ei[0].text_content().strip()
            if u'会员名、用户名或密码不准确' in xt:
                self.isvalid = False
            return False
        if '/useroffline' in con2.request.url.lower():
            if not self._kick_offline(con2, hdoc):
                return False
        elif 'navigate.aspx' not in con2.request.url.lower():
            return False

        print self.sess.cookies.items()
        return True

    def _kick_offline(self, con, condom):
        form = condom.xpath("//form[@id='form1']")[0]
        kvs,_ = self.process_form(form)
        # javascript:__doPostBack('gvOnLineUser','KickOut$0')
        kvs['__EVENTTARGET'] = 'gvOnLineUser'
        kvs['__EVENTARGUMENT'] = 'KickOut$0'
        action = urlparse.urljoin(con.request.url, form.attrib.get('action'))
        con = self.sess.post(action, data=kvs, headers={'Referer': con.request.url})
        return 'Navigate.aspx' in con.request.url

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


    def get_one_case(self, i):
        # i = 2603127
        url = Config.PAGE_URL_TEMPLATE.format(i)
        res = self.sess.get(url)

        hdoc = html.fromstring(res.text)
        textDate = hdoc.xpath('//span[@id="lblResumeUpdateTime"]')
        textDate = textDate[0].text_content() if textDate else ''

        if textDate:
            find = re.search(r'(\d+)-(\d+)-(\d+)', textDate)
            if find:
                ls = list(time.localtime())
                ls[0] = int(find.group(1))
                ls[1] = int(find.group(2))
                ls[2] = int(find.group(3))

                pubstamp = time.mktime(ls)
                if time.time() - pubstamp < Config.TIMERANGE:
                    return i
                else:
                    return None

        return None

    def _clean_kvs(self, kvs, *names):
        ks = kvs.keys()
        for k in ks:
            k1 = re.sub(r'\$.*', '', k)
            if k1 in names:
                del kvs[k]

    def get_real_cases(self):

        hidValue = "KEYWORDTYPE#0*LASTMODIFYSEL#5*JOBSTATUS#99*AGE#|*WORKYEAR#0|99*SEX#99*AREA#010000*TOPDEGREE#|"
        ctrlSerachKEYWORD = Config.SEARCH_KEY_WORDS[random.randint(0, len(Config.SEARCH_KEY_WORDS) - 1)]
        hidValue += ctrlSerachKEYWORD

        con = self.sess.get("http://ehire.51job.com/Candidate/SearchResumeIndex.aspx")
        condom = html.fromstring(con.text)
        kvs,_ = self.process_form( condom.xpath("//form[@id='form1']") )
        # self._clean_kvs(kvs, "ctrlSerach")
        kvs['pagerTop$FiftyButton']=50
        kvs["LASTMODIFYSEL"] = 5
        kvs["hidValue"] = hidValue

        rad = random.randint(1, 59)
        total = []
        for i in [rad, rad+1]:
            kvs.update({
                "pagerBottom$btnNum4": i,
                "pagerBottom$txtGO":i-1,
            })


            con = self.sess.post(Config.SEARCH_URL_TEMPLATE, data=kvs, headers={'Referer':Config.SEARCH_URL_TEMPLATE})
            find = re.findall(r'/Candidate/ResumeView.aspx\?hidUserID=(\d+)', con.text, re.S)
            if find:
                total.extend(find)

        return set(total)



    def get_cases(self):
        with open('idx', 'wb') as f:
            while(self.count < Config.TOTAL_COUNT):
                # i = random.randint(Config.ID_LOW, Config.ID_MAX)
                # if self.get_one_case(i):
                find = self.get_real_cases()
                for i in find:
                    if self.count >= Config.TOTAL_COUNT:
                        break
                    print "SECUSS, id: ", i
                    self.count += 1
                    f.write('%s\n'%i)


if __name__ == '__main__':
    ts = CV51TestGet()
    count = 0
    while not ts.do_login():
        count += 1
        if count > 10:
            break
        continue

    ts.get_cases()