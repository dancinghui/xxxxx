#!/usr/bin/env python
# -*- coding:utf8 -*-


from spider.spider import MRLManager, Spider, LoginErrors
from service.cv_contact_get.common import config, downloader_base, log_util
from service.cv_contact_get.store import cv_download_page
from spider.runtime import Log
from service.cv_contact_get.common.check_download_num import check_download_num
from lxml import html
import threading
import time
import sys
import os
import re

sys.path.extend(config.CV51LG_FILE_PATH)
import job51login

g_index = os.getpid() % 5


def new_51Login(ac):
    class newLg(job51login.Job51Login):
        def __init__(self, acc):
            self.acc = acc
            job51login.Job51Login.__init__(self, acc)

        def need_login(self, url, con, hint):
            super(newLg, self).need_login(url, con, hint)
            if u'对不起，您无权操作该页面！' in con.text:
                Log.warning(u'账号不对, 无权操作')
                raise LoginErrors.AccountHoldError()

            find = re.search(ur"您目前还有.*?<span style='color: red'>(\d+)</span>", con.text, re.S)
            if find:
                remained_download_num = int(find.group(1))
                check_download_num("cv_51job", remained_download_num, self.acc)

    a = newLg(ac)
    # 登录
    # a.load_proxy('common/proxy', index=g_index, auto_change=False)
    a.do_login()
    return a


class CV51ContactSpider(downloader_base.CVContactSpiderBase):

    REAL_URL_TEMPLATE = "http://ehire.51job.com/Candidate/ResumeView.aspx?hidUserID=%s&hidEvents=23&hidKey=303514e18dbc5600b3ecfff9abb76510"

    def __init__(self, thcnt, cvaccs):
        self.cv51nm = MRLManager(cvaccs, new_51Login)
        downloader_base.CVContactSpiderBase.__init__(self, thcnt, 'cv_51job')
        self.page_store = cv_download_page.CV51DownloadPageStore()

        self.log = log_util.MLog(self.__class__.__name__, config.LOGGING_FILE)

    def run_job(self, job):

        realUrl = job.get('realUrl', '')
        cvId = job['cvId']

        indexUrl = "%s://%s" % ("cv_51job", cvId)
        if not realUrl or 'fake' in realUrl:
            realUrl = self.get_real_url(cvId)

        # 设置状态
        self._cv_status.update({indexUrl: config.StatusCode.DOWNLOADING})
        data = {"doType":"SearchToCompanyHr", "userId": cvId, "strWhere": '',}
        content, status = self.with_check_request(self._download_url, data=data, realUrl=realUrl)

        if not content:
            self.log.info('downloaded cv page fail: %s, readd to the queue' % indexUrl)
            self.re_add_job(job)
            return

        status = self.page_store.save(time.time(), cvId, realUrl, content)

        # 失败 重试
        if status == config.StatusCode.AFTER_DOWNLOADING_FAIL:
            self.log.warn("cv %s download fail, readd to the queue" % indexUrl)
            self.re_add_job(job)

        self._cv_status.update({indexUrl: status})

    def with_check_request(self, url, data, realUrl):
        res = self.cv51nm.el_request(url, data=data)

        # if u'简历已在公司人才夹中' in res.text:
        res = self.cv51nm.el_request(realUrl)

        if u"此人简历保密" in res.text:
            return res.text, config.StatusCode.CV_CLOSED

        return res.text, ''

    def get_real_url(self, cvId):

        return CV51ContactSpider.REAL_URL_TEMPLATE % cvId


class CV51jobDownloader(downloader_base.DownloaderBase):
    def __init__(self, cvaccs=config.CV51_ACCOUNTS):
        self._accs = cvaccs
        downloader_base.DownloaderBase.__init__(self, "cv_51job")

    def get_cvcontact_spider(self):
        return CV51ContactSpider(1, self._accs)

    def extract_info(self, cv):
        dom = html.fromstring(cv)
        info = self.download_page_store.extract_info(dom)
        return info

if __name__ == '__main__':
    t = CV51jobDownloader(config.CV51_ACCOUNTS)
    print t.download("26503724")


