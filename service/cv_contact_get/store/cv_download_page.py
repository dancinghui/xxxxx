#!/usr/bin/env python
# -*- coding:utf8 -*-

from service.cv_contact_get.common import config, log_util
from service.cv_contact_get.common.download_page_store_base import DownloadPageStoreBase
import pymongo
from lxml import html
from spider.runtime import Log
from spider.util import utf8str
import re
import time
from spider import spider


#################################
# cv 下载页面 存储, (简历下载页面) #
#################################
class CVDownloadPageStore(object):
    def __init__(self, channel):
        self.channel = channel
        self.db_name = config.DOWNLOADED_DB_NAMES.get(self.channel,'')
        self.coll_name = config.DOWNLOADED_COLL_NAMES.get(self.channel,'')
        self.mongodb_url = config.DOWNLOADED_CV_MONGODB_URLS.get(self.channel, '')

        assert self.mongodb_url and self.db_name and self.coll_name

        self.py_mongo_client = pymongo.MongoClient(self.mongodb_url)

    def find_one(self, key):
        return self.py_mongo_client[self.db_name][self.coll_name].find_one(key)


class CVLPDownloadPageStore(DownloadPageStoreBase):
    def __init__(self):
        DownloadPageStoreBase.__init__(self, 'cv_liepin', dburl=config.DOWNLOADED_CV_MONGODB_URLS.get('cv_liepin'))
        self.page_store = CVDownloadPageStore('cv_liepin')

        self.log = log_util.MLog(self.__class__.__name__, config.LOGGING_FILE)


class CVZLDownloadPageStore(DownloadPageStoreBase):
    def __init__(self):
        DownloadPageStoreBase.__init__(self, 'cv_zhilian', dburl=config.DOWNLOADED_CV_MONGODB_URLS.get('cv_zhilian'))
        self.page_store = CVDownloadPageStore('cv_zhilian')

        self.log = log_util.MLog(self.__class__.__name__, config.LOGGING_FILE)

    def extract_content(self):
        doc = self.get_cur_doc()

        hf = spider.util.htmlfind(doc.cur_content, 'id="resumeContentBody"', 0)

        dom = html.fromstring(doc.cur_content)
        contact_info = self.extract_info(dom)

        name = contact_info.get("name", "")
        email = contact_info.get("email","")
        telephone = contact_info.get("telephone", "")

        if not (name and (email or telephone)):
            self.log.info("fail id: %s, extract contact infomation fail" % self.get_cur_doc().cur_jdid)
            return None

        try:
            detail = hf.get_text()
        except:
            Log.errorbin("invalid cv content %s" % doc.cur_url, doc.cur_content)
            return None

        return utf8str(contact_info) + utf8str(detail)

    def page_time(self):

        doc = self.get_cur_doc()
        assert isinstance(doc, DownloadPageStoreBase.CurDoc)
        if isinstance(doc.cur_content, unicode):
            doc.cur_content = doc.cur_content.encode('utf-8')
        m = re.search(r"简历更新时间：.*?(\d+)年(\d+)月(\d+)日", doc.cur_content, re.S)
        if m:
            return self.mktime(m.group(1), m.group(2), m.group(3)) * 1000
        else:
            Log.error("invalid page for %s, url=%s", doc.cur_jdid, doc.cur_url)
            Log.errorbin("invalid cv %s" % doc.cur_url, doc.cur_content)
            return None

    @staticmethod
    def extract_info(dom):
        if isinstance(dom, (str, unicode)):
            dom = html.fromstring(dom)

        user_name = ''
        user_field = dom.xpath('//div[@id="userName"]/@alt')
        if not user_field:
            Log.warning("find zhilian user field exception")
        else:
            user_name = user_field[0]

        contact_info = dom.xpath("//div[@class='feedbackD']//em")
        user_email = ''
        user_telephone = ''
        if not contact_info and len(contact_info) < 2:
            Log.warning("find contact info exception")
        else:
            user_telephone = contact_info[0].text_content()
            user_email = contact_info[1].text_content()

        return {'name': user_name, 'telephone': user_telephone, 'email': user_email}


class CV51DownloadPageStore(DownloadPageStoreBase):
    def __init__(self):
        DownloadPageStoreBase.__init__(self, 'cv_51job', dburl=config.DOWNLOADED_CV_MONGODB_URLS.get('cv_51job'))
        self.page_store = CVDownloadPageStore('cv_51job')

        self.log = log_util.MLog(self.__class__.__name__, config.LOGGING_FILE)

    def extract_content(self):

        dom = html.fromstring(self.get_cur_doc().cur_content)

        xx = dom.xpath("//td[@id='divInfo']")

        contact_info = CV51DownloadPageStore.extract_info(dom)
        name = contact_info.get("name", "")
        email = contact_info.get("email","")
        telephone = contact_info.get("telephone", "")
        if not (name and (email or telephone)):
            self.log.info("fail id: %s, extract contact infomation fail" % self.get_cur_doc().cur_jdid)
            return None

        if xx is not None and len(xx)>0:
            return utf8str(contact_info) + utf8str(xx[0].text_content())

        Log.errorbin(self.get_cur_doc().cur_url, self.get_cur_doc().cur_content)
        Log.error("get cv failed", self.get_cur_doc().cur_url)

        return None

    @staticmethod
    def extract_info(dom):

        if isinstance(dom, (str, unicode)):
            dom = html.fromstring(dom)

        name = ''
        bs = dom.xpath("//span/b")
        if bs is not None and len(bs) > 0:
            name = bs[0].text_content()

        # 电话， email
        tds = dom.xpath('//div[@id="divResume"]//td[@height="20"]')
        telephone_index = -1
        email_index = -1
        for index, td in enumerate(tds):
            if u'电　话：' in td.text_content():
                telephone_index = index + 1
            if u'E-mail：' in td.text_content():
                email_index = index + 1
                break
        telephone = ''
        email = ''
        if telephone_index >=0:
            telephone = tds[telephone_index].text_content()
            telephone = re.search(r'([\d-]*)', telephone).group(1)
        if email_index >=0:
            email = tds[email_index].xpath('a')[0].text_content()

        if isinstance(name, unicode):
            name = name.encode('utf-8')

        return {'name': name, 'email': email, 'telephone': telephone}

    def page_time(self):
        m = re.search(ur'lblResumeUpdateTime.*?(\d+-\d+-\d+)', self.get_cur_doc().cur_content)
        if m:
            t = time.mktime(time.strptime(m.group(1), '%Y-%m-%d'))
            return int(t) * 1000
        return None


if __name__ == '__main__':
    zhilian_store = CVZLDownloadPageStore()

    with open('test_page.html') as f:
        c = f.read()
    print zhilian_store.extract_info(c)

