#!/usr/bin/env python
# -*- coding:utf8 -*-


from service.cv_contact_get.common.downloader_base import DownloaderBase
from spider.spider import MRLManager, Spider
from service.cv_contact_get.common import config, downloader_base
from service.cv_contact_get.store.cv_download_page import CVLPDownloadPageStore
import sys

sys.path.extend(config.CVLpLG_FILE_PATH)
import lp_login
import os


g_index = os.getpid() % 5


def new_LPQYLogin(ac):
    a = lp_login.LPQYLogin(ac)
    a.load_proxy('common/proxy', index=g_index, auto_change=False)
    return a


def new_LPLTLogin(ac):
    a = lp_login.LPLTLogin(ac)
    a.load_proxy('common/proxy', index=g_index, auto_change=False)
    return a


def new_LPLogin(ac):
    _type = ac.get('type', 1)
    if 1 == _type:
        return new_LPQYLogin(ac)
    if 2 == _type:
        return new_LPLTLogin(ac)


class CVLPContactSpider(downloader_base.CVContactSpiderBase):
    def __init__(self, thread_cnt, cvaccs):
        Spider.__init__(self, thread_cnt)

        self.lpm = MRLManager(cvaccs, new_LPLogin)
        self.page_store = CVLPDownloadPageStore()


    def run_job(self, jobid):
        #TODO
        pass

    def prechecker(self, res):
        #TODO
        # 是否还有下载简历数
        pass


class LPDownloader(DownloaderBase):
    def __init__(self, cvaccs=config.CVLP_ACCOUNTS):
        self._cvaccs = cvaccs    # 必须先于 DownloaderBase 初始化
        DownloaderBase.__init__(self, 'cv_liepin')

    def get_cvcontact_spider(self):
        return CVLPContactSpider(1, self._cvaccs)

    def extract_info(self, cv):
        #TODO
        pass
