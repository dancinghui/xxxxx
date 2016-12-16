#!/usr/bin/env python
# -*- coding:utf8 -*-


from spider.ipin.savedb import PageStoreBase
from service.cv_contact_get.common import config, log_util
import os
import time


class DownloadPageStoreBase(PageStoreBase):
    def __init__(self, channel, dburl):
        PageStoreBase.__init__(self, channel, dburl)

        # 子类需要覆盖
        self.log = None

    def getopath(self):
        dirs = ['/data/cv_download', '/opt/_test_store_']
        for di in dirs:
            if os.path.isdir(di) and os.access(di, os.W_OK):
                return di
        raise RuntimeError("no dir to write files.")

    def save(self, getime, jdid, real_url, content, fnpath=None, offset=None):

        if isinstance(content, unicode):
            content = content.encode('utf-8')
        super(DownloadPageStoreBase, self).save(getime, jdid, real_url, content, fnpath, offset)

        # 等待存完
        time.sleep(1)
        indexUrl = "%s://%s" % (self.channel, jdid)
        if self.find_any(indexUrl):
            self.log.info(" cvId: %s, download success " % indexUrl)
            return config.StatusCode.AFTER_DOWNLOADING_SUCESS
        else:
            return config.StatusCode.AFTER_DOWNLOADING_FAIL