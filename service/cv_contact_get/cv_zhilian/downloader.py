#!/usr/bin/env python
# -*- coding:utf8 -*-


from spider.spider import MRLManager
from service.cv_contact_get.common import config, downloader_base,log_util
from service.cv_contact_get.common.check_download_num import check_download_num
from service.cv_contact_get.store import cv_download_page
from service.cv_contact_get.common.load_proxy import PROXIES
from spider.runtime import Log
from lxml import html
import time
import sys
import re
import random
import os

sys.path.extend(config.CVZLLG_FILE_PATH)
import zl_login


def new_ZLLogin(ac):
    g_index = random.randint(0, len(PROXIES)-1)
    class newLg(zl_login.ZLLogin):
        def __init__(self, acc):
            self.acc = acc
            zl_login.ZLLogin.__init__(self, acc)

        def need_login(self, url, con, hint):
            if super(newLg, self).need_login(url, con, hint):
                return True
            find = re.search(ur'还有.*?<span[^<>]*>(\d+)</span>.*?份简历下载余额', con.text, re.S)
            if find:
                remained_download_num = int(find.group(1))
                check_download_num("cv_zhilian", remained_download_num, self.acc)

            return False

        def _real_do_login(self):
            rr = self._real_do_login1()
            return rr

    a = newLg(ac)

    proxy_file_path = os.path.join(os.path.dirname(__file__), '../common/proxy')

    a.load_proxy(proxy_file_path, index=g_index, auto_change=False)
    a.do_login()
    return a


class CVZLContactSpider(downloader_base.CVContactSpiderBase):
    def __init__(self, thcnt, cvaccs):
        self.cvaccs = cvaccs
        self.zlgm = MRLManager(cvaccs, new_ZLLogin)
        downloader_base.CVContactSpiderBase.__init__(self, thcnt, 'cv_zhilian')
        self.page_store = cv_download_page.CVZLDownloadPageStore()

        self.log = log_util.MLog(self.__class__.__name__, config.LOGGING_FILE)

    def run_job(self, job):

        realUrl = job['realUrl']
        cvId = job['cvId']
        indexUrl = "%s://%s" % (self.channel, cvId)

        # 设置状态
        self._cv_status.update({indexUrl: config.StatusCode.DOWNLOADING})

        page_template = config.CV_PAGE_TEMPLATE.get('cv_zhilian')
        cv_page_url = page_template.format(cvId)
        data = self.get_post_data(cvId, cv_page_url)
        content, status = self.with_check_request(self._download_url, data=data, realUrl=cv_page_url)

        if not content:
            self.log.warn('downloaded cv page fail: %s, readd to the queue ' % indexUrl)
            self.re_add_job(job)
            return

        status = self.page_store.save(time.time(), cvId, realUrl, content)

        # 失败 重试
        if status == config.StatusCode.AFTER_DOWNLOADING_FAIL:
            self.log.warn("cv %s download fail, readd to the queue" % indexUrl)
            self.re_add_job(job)
            return

        self._cv_status.update({indexUrl: status})

    def get_post_data(self, cvId, cv_page_url):

        res = self.zlgm.el_request(cv_page_url)
        find = re.search(ur'简历名称.*?<strong[^<>]*>(.*?)</strong>', res.text, re.S)
        if not find:
            Log.errinfo("find zhilian cvname exception")
            return None

        cvname = find.group(1)
        cvname = re.sub(ur'&#160;&#160;','', cvname)
        data = {"extID":cvId, "versionNumber": 1, "favoriteID": "113460230", "resumeName": cvname, "dType": 0}
        return data

    def try_next_proxy(self):
        self.zlgm = MRLManager(self.cvaccs, new_ZLLogin)

    def with_check_request(self, url, data, realUrl):
        res = self.zlgm.el_request(url, data=data)

        if re.search(ur'您的登录IP(.*)存在异常行为，已被暂时冻结', res.text):
            print "trying next proxy ...."
            self.try_next_proxy()
            return self.with_check_request(url,data, realUrl)

        if ur'此应聘者的简历已被下载' in res.text:
            Log.info("already download, url = %s" % realUrl)

        res = self.zlgm.el_request(realUrl)

        return res.text, ''


class CVZLDownloader(downloader_base.DownloaderBase):
    def __init__(self, cvaccs=config.CVZL_ACCOUNTS):
        self._accs = cvaccs
        downloader_base.DownloaderBase.__init__(self, "cv_zhilian")

    def get_cvcontact_spider(self):
        return CVZLContactSpider(1, self._accs)

    def extract_info(self, cv):
        dom = html.fromstring(cv)
        info = self.download_page_store.extract_info(dom)
        return info

if __name__ == '__main__':
    t = CVZLDownloader(config.CVZL_ACCOUNTS)
    print t.download("JM197710394R90250006000")


