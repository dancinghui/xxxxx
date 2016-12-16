#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.ipin.savedb import PageStoreBase
from spider.runtime import Log
from spider.util import TimeHandler
from spider.savebin import FileSaver
import spider
import re
import os
import time
import pymongo
#conn = pymongo.MongoClient("mongodb://crawler:crawler@192.168.1.81,192.168.1.82,192.168.1.83/gaokao_crawler")
conn = pymongo.MongoClient("mongodb://192.168.1.43:27019/jobui")
class PageStoreJobUI(PageStoreBase):

    def __init__(self):
        super(PageStoreJobUI, self).__init__('jd_jobui')
        self.crawlered_ids = set()
        self.log_file = FileSaver("./data/chentao/jobui_log/jobui-"+str(time.strftime('%Y-%m-%d'))+".txt")

    def extract_content(self):
        content = spider.util.htmlfind(self.get_cur_doc().cur_content, 'class="hasVist cfix sbox fs16"', 0)
        try:
            content = content.get_text()
        except:
            Log.errorbin("invalid jd content %s" % self.get_cur_doc().cur_url, self.get_cur_doc().cur_content)
            return None
        return content

    def page_time(self):
        #TODO
        #tag = spider.util.htmlfind(self.get_cur_doc().cur_content, 'class="publish_time"', 0)
        tag = re.search('class="uptime common-icon"></em>(.*?)</dd>',self.get_cur_doc().cur_content)
        try:
            #tag = tag.get_text()
            tag = tag.group(1)
        except:
            Log.errorbin("invalid jd content %s" % self.get_cur_doc().cur_url, self.get_cur_doc().cur_content)
            raise

        return TimeHandler.fmt_time(tag)

    def getopath(self):
        dirs = ['./data/chentao/jobui_data_re']
        for di in dirs:
            if os.path.isdir(di) and os.access(di, os.W_OK):
                return di
        raise RuntimeError("no dir to write files.")


    def save_time_log(self,indexUrl,cur_tm):
        """记录更新时间"""
        #db = conn.gaokao_crawler
        #content = db.page_store_jd_jobui.find_one({"indexUrl": indexUrl})
        db = conn.jobui
        content = db.page_store_jd_jobui.find_one({"indexUrl": indexUrl})
        cur_tm = time.strftime("%Y-%m-%d", time.localtime(cur_tm/1000))
        log = indexUrl+"|0|"+cur_tm
        if content is not None:
            pre_tm = time.strftime("%Y-%m-%d", time.localtime(content['updateTime']/1000))
            if pre_tm == cur_tm:
                print "time is not change , don't recorde !! "
                return
            log = indexUrl+"|"+pre_tm+"|"+cur_tm
        self.log_file.append(log)




if __name__ == '__main__':
    pass
    # db = conn.jobui
    # content = db.indexing.find_one({"indexUrl": "jd_jobui://108841970"})
    # print content