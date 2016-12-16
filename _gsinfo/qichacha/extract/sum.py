import time
import os
from spider.savebin import BinReader, BinSaver
from _gsinfo.qichacha.qichacha import QccPageStore
from spider.ipin.savedb import PageStoreBase
import re

class QccPageStoreSum(PageStoreBase):
    def getopath(self):
        dirs = ['/home/peiyuan/data/qichacha/sum', '/opt/_test_store_']
        for di in dirs:
            if os.path.isdir(di) and os.access(di, os.W_OK):
                return di
        raise RuntimeError("no dir to write files.")
    def __init__(self):
        PageStoreBase.__init__(self, "qichacha")

    def page_time(self):
        return 1450346105*1000

    def check_should_fetch(self, cpid):
        indexUrl = "%s://%s" % (self.channel, cpid)
        if self.find_any(indexUrl):
            return False
        return True
    def extract_content(self):
        m = re.search(r'<div class="detail-info">(.*?)<div class="wrap_style mb15  pd5"  id="comment" name="comment">',
                      self.get_cur_doc().cur_content, re.S)
        if m:
            a = re.sub(ur'<[a-zA-Z/!][^<>]*>', '', m.group(1))
            return a.strip()
        Log.error(self.get_cur_doc().cur_url, "no content")
        return None


class QccPageSum(object):
    def __init__(self, dirpath):
        self.pagestore = QccPageStoreSum()
        self.dirpath = dirpath

    def _get_file_path(self):
        filelist = os.listdir(self.dirpath)
        rs = []
        for file in filelist:
            if os.path.isdir(dirpath+file):
                continue
            rs.append(file)
        return rs

    def sum(self):
        filelist = self._get_file_path()
        totalcnt = 0
        rsinfo = []
        for i in range(len(filelist)):
            if os.path.isdir(dirpath+filelist[i]): continue
            binreader = BinReader(dirpath+filelist[i])
            line = binreader.readone()
            endline = 10000000
            cnt = 0
            emptycnt = 0
            skipcnt = 0
            while line[0]:
                print "reading", filelist[i], ",line", cnt+1
                channel, cpid, gettime  = line[0].split(".")
                if self.pagestore.check_should_fetch(cpid):
                    if self.pagestore.save(int(gettime), cpid, "http://qichacha.com/firm_CN_"+cpid, line[1]):
                        print filelist[i], "line", cnt+1, "saved."
                else:
                    print "skip", filelist[i], "line", cnt+1
                    skipcnt += 1
                if line[1] is None:
                    emptycnt += 1
                line = binreader.readone()
                cnt += 1
                totalcnt += 1
                if cnt >= endline:  break
            infostr = ""+str(filelist[i])+" total: "+str(cnt)+" empty: "+ str(emptycnt)+ " skip: "+str(skipcnt)
            print infostr
            rsinfo.append(infostr)
        for info in rsinfo:
            print info
        print len(filelist),"files, total:", totalcnt,"results"
        return totalcnt


if __name__ == '__main__':
    dirpath = "/home/peiyuan/data/qichacha/"
    qccsum = QccPageSum(dirpath)
    qccsum.sum()