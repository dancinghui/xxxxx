#!/usr/bin/env python
# -*- coding:utf8 -*-

from service.cv_contact_get.common import config
from spider.spider import MRLManager, Spider
from spider.ipin.savedb import BinReader
from spider.runtime import Log
from service.cv_contact_get.store import cv_download_page, cv_page
import threading
import requests
import time

class CVContactSpiderBase(Spider):
    def __init__(self, thcnt, channel):

        # 子类需要覆盖
        self.log = None

        Spider.__init__(self, thcnt)
        self.channel = channel
        self._name = "%s_download" % channel

        self._download_url = config.DOWNLOAD_URLS.get(channel, '')
        self._retry_times = 3

        assert self._download_url

        # cv status
        self._cv_status = {}

        # test search
        test_search = threading.Thread(target=self.test_search)
        test_search.start()

    def test_search(self):

        time.sleep(60*5)

        while True:
            url_51job = "http://127.0.0.1:9527/cvDownload?channel=cv_51job&cvId=333848830"
            url_zhilian = "http://127.0.0.1:9527/cvDownload?channel=cv_zhilian&cvId=JM623034232R90250000000"
            url_liepin = "http://127.0.0.1:9527/cvDownload?channel=cv_liepin&cvId=4689556020O2963248056"
            requests.get(url_51job)
            requests.get(url_zhilian)
            requests.get(url_liepin)

            time.sleep(60*10)

    def dispatch(self):
        pass

    def _get_a_job(self):

        jobid = self.job_queue.get(True)
        self.job_queue.task_done()
        if jobid is not None:
            self._mjob_count += 1
        return jobid, 1

    def push_job(self, j):

        if not j:
            self.log.warn("pushed a empty job")
            return

        if "realUrl" not in j or "cvId" not in j:
            self.log.warn("job need realUrl and cvId")
            return

        indexUrl = "%s://%s" % (self.channel, j['cvId'])

        if not self.check_need_add_to_main(j, indexUrl):
            status = self._cv_status.get(indexUrl)
            self.log.info(u"cvId: %s, current status: %s, not need add to main queue" % (indexUrl, status))
            return

        self.add_main_job(j)
        self.log.info(" ===============   start fetching cvId: %s ==============" % indexUrl)

    def check_need_add_to_main(self, j, indexUrl):
        if j.get('time', 0) > self._retry_times:
            self.cv_status.update({indexUrl: config.StatusCode.DOWNLOAD_RETRY_FAIL})
            self.log.warn('retry times: %d > %d' % (j.get('time', 0), self._retry_times))
            return False
        else:
            # 表示重试
            if 'time' in j:
                return True

        current_status = self._cv_status.get(indexUrl, '')

        if config.StatusCode.CV_CLOSED == current_status:
            self.log.warn("cv closed: %s" % indexUrl)
            return False

        if current_status in [config.StatusCode.BEFORE_DOWNLOADING, config.StatusCode.DOWNLOADING,
                              config.StatusCode.AFTER_DOWNLOADING_SUCESS, config.StatusCode.AFTER_DOWNLOADING_FAIL]:

            return False

        return True

    @property
    def cv_status(self):
        return self._cv_status

    def re_add_job(self, job):
        tm = job.get('time', 0) + 1
        job['time'] = tm
        self.push_job(job)


class DownloaderBase(object):
    def __init__(self, channel):

        self._channel = channel

        self.download_page_store = self.get_download_page_store(channel)  # 下载简历 存储库
        self.page_store = cv_page.CVPageStore(channel)  # 爬虫库
        self._contact_spider = self.get_cvcontact_spider()
        self._contact_spider.run(True, report=False)  # 异步

    def get_download_page_store(self, channel):
        if 'cv_51job' == channel:
            return cv_download_page.CV51DownloadPageStore()
        elif 'cv_liepin' == channel:
            return cv_download_page.CVLPDownloadPageStore()
        elif 'cv_zhilian' == channel:
            return cv_download_page.CVZLDownloadPageStore()
        else:
            raise Exception("unknown channel ")

    def get_cvcontact_spider(self):
        raise NotImplementedError('virual function called, need contact spider')

    def do_download(self, cvId, indexUrl, check_db):

        # 查询数据库
        if check_db:
            cv = self.download_page_store.page_store.find_one({'indexUrl': indexUrl})
            if cv:
                pagePath = cv.get("pageContentPath", '')
                if not pagePath:
                    raise Exception("pagePath valid")
                pagecontent = self.getPageContent(pagePath)
                return config.StatusCode.ALREADY_IN_DB, self.extract_info(pagecontent)

        # 从爬虫库中 直接获取realUrl
        # realUrl = self.page_store.get_real_url({'indexUrl':indexUrl})
        realUrl = "http://ehire.51job.com/Candidate/ResumeView.aspx?hidUserID=26503724&hidEvents=23&hidKey=ea7c41e8e6caa41f9ace8ae756d8ae4d"

        self._contact_spider.push_job({"cvId": cvId, "realUrl": realUrl})

        status = self._contact_spider.cv_status.get(indexUrl)
        return status, ''

    def extract_info(self, cv):
        raise NotImplementedError('virtual function called')

    def download(self, cvId, check_db=False):
        # 做预处理： indexUrl包括渠道， cvId只有id
        if self._channel not in cvId:
            indexUrl = "%s://%s" % (self._channel, cvId)
        else:
            indexUrl = cvId
            cvId = cvId.split('://')[1]

        return self.do_download(cvId, indexUrl, check_db)

    def getPageContent(self, filename):
        parts = filename.split("::")
        if len(parts) == 3:
            binReader = BinReader(parts[1])
            _, content = binReader.readone_at(int(parts[2]))
            if len(content) == 0:
                raise Exception("file name:{} , content error".format(filename))
            return content

        if len(parts) == 1:
            with open(filename) as f:
                content = f.read()
                if len(content) == 0:
                    raise Exception("file name:{} , content error".format(filename))
                return content
