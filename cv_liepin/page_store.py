#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import PageStoreBase
from spider.util import htmlfind, TimeHandler
from spider.savebin import FileSaver

class LPCVConfig(object):
    mongdb_url = "mongodb://localhost/cv_crawler"
    NOT_NEED_CV_FN = 'not_need_cvs.txt'
    NOT_ACCESS_BY_QIYE = 'not_access_by_qiye.txt'


class LPCVStore(PageStoreBase):
    def __init__(self):
        PageStoreBase.__init__(self, 'cv_liepin', dburl=LPCVConfig.mongdb_url)
        self.testmode = False
        self._not_need_cv_fs = FileSaver(LPCVConfig.NOT_NEED_CV_FN)
        self._not_access_by_qiye = FileSaver(LPCVConfig.NOT_ACCESS_BY_QIYE)

    def extract_content(self):

        cur_content = self.get_cur_doc().cur_content
        if isinstance(cur_content, unicode):
            cur_content = cur_content.encode('utf-8')

        fields = htmlfind.findTag(cur_content, 'table')

        content = ''
        for field in fields:
            if r'所在行业：' in field:
                content = htmlfind.remove_tag(field, True)
                break
            elif r'Industry:' in field or r'Industry：' in field:
                print "Ignore..... is English page!"
                self._save_not_need_cv(self.get_cur_doc().cur_jdid)
                break

        if r'抱歉，该简历已经设置为对猎头顾问不开放!' in cur_content:
            print "Ignore..... can not access by lietou"
            return None
        if r'该简历人才已经设置了对企业不开放简历，可能该人才已经找到工作，或者暂时没有换工作的意向。' in cur_content:
            print "Ignore..... can not access by qiye"
            self._not_access_by_qiye.append(self.get_cur_doc().cur_jdid)
            return None

        return content

    def _save_not_need_cv(self, cvId):
        self._not_need_cv_fs.append(cvId)

    def page_time(self):
        try:
            t = htmlfind.findTag(self.get_cur_doc().cur_content, 'div', 'class="resume-info"')
            if not t:
                t = htmlfind.findTag(self.get_cur_doc().cur_content, 'div', 'class="tab"')   #猎头页面
                if not t:
                    return None
                return TimeHandler.fmt_time(t[0])
            return TimeHandler.fmt_time(t[0])
        except Exception as e:
            self._save_not_need_cv(self.get_cur_doc().cur_jdid)

    def check_should_fetch(self, jdid):
        indexUrl = "%s://%s" % (self.channel, jdid)
        return not self.find_any(indexUrl)

