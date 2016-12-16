import requests
import re
from spider.httpreq import ProxyError, BasicRequests
from lxml import html
import urllib
import copy

class BasicReqBak:
    def _do_requests_old(self, url, **kwargs):
        try:
            TOclass = requests.exceptions.ConnectTimeout
        except:
            TOclass = requests.exceptions.Timeout
        try:
            if 'data' in kwargs:
                response = requests.post(url, **kwargs)
            else:
                response = requests.get(url, **kwargs)
            if re.search('Content-Type.*(gbk|gb2312)', response.text, re.M | re.I):
                response.encoding = 'gbk'
            else:
                response.encoding = 'utf-8'
            return response
        except (requests.exceptions.ConnectionError, TOclass,
                    requests.exceptions.ProxyError) as e:
            raise ProxyError(str(e))


class SessionRequests(BasicRequests):
    def __init__(self):
        BasicRequests.__init__(self)
        self.session = requests.Session()

    def reset_session(self):
        self.session = requests.Session()

    def _do_requests(self, url, **kwargs):
        try:
            TOclass = requests.exceptions.ConnectTimeout
        except:
            TOclass = requests.exceptions.Timeout
        try:
            if 'data' in kwargs:
                response = self.session.post(url, **kwargs)
            else:
                response = self.session.get(url, **kwargs)
            if re.search('Content-Type.*(gbk|gb2312)', response.text, re.M | re.I):
                response.encoding = 'gbk'
            else:
                response.encoding = 'utf-8'
            return response
        except (requests.exceptions.ConnectionError, TOclass,
                    requests.exceptions.ProxyError) as e:
            raise ProxyError(str(e))

class _51Parse:
    def extract_content(self):
        self.hdoc = html.fromstring(self.cur_content)
        for i in self.hdoc.xpath("//div[@class='tCompany_text']"):
            return i.text_content().strip()
        return None

class _51CVSearch:
    def do_search2(self, url, **kwargs):
        headers = { 'Referer':self.search_page }
        con = self.request_url(self.search_page)
        condom = html.fromstring(con.text)
        kvs,_ = self.process_form( condom.xpath("//form[@id='form1']") )
        print urllib.urlencode(kvs)
        kvs1 = copy.deepcopy(kvs)
        #self._clean_kvs(kvs1, "pagerBottom", "pagerTop")
        kvs1['pagerTop$FiftyButton']=50
        con = self.request_url(self.search_page, data=kvs1, headers=headers)

        kvs2 = copy.deepcopy(kvs)
        self._clean_kvs(kvs2, "ctrlSerach", "cbxColumns", "chkBox", "radSelactALL")
        xupdate(1, kvs2, """
hidValue=KEYWORDTYPE#0*LASTMODIFYSEL#5*JOBSTATUS#99*WORKYEAR#4|4*SEX#99*TOPDEGREE#|*KEYWORD#多关键字用空格隔开
pagerBottom$lbtnGO=
pagerBottom$txtGO=32
        """)

        con = self.request_url(self.search_page, data=kvs2, headers=headers)

        with open(os.getenv('HOME', '.')+"/hehe.html", "w") as f:
            f.write(con.content)
            print "write file OK"
        return con
