#! /usr/bin/env python
# encoding:utf-8
import spider.spider
from spider.spider import  BasicRequests, SessionRequests, Spider
import spider.util
import hashlib
import threading
import chardet
import urllib
import base64
class codeimgSpider(BasicRequests):
    def __init__(self, threadcnt):
        BasicRequests.__init__(self)
        self.thread_count = threadcnt
        self.ths = []
        self.img_catch = {}

    def run(self):
        for i in range(self.thread_count):
            thd = threading.Thread(target=self.get_code_img)
            thd.start()
            self.ths.append(thd)

    def get_code_img(self):
        count = 0
        dupcnt = 0
        while(True):
            url = "http://qiye.qianzhan.com/account/varifyimage?date=90"
            res = urllib.urlopen(url).read()
            if res is None or res.strip() =="":
                print "Bad connect!!!!"
            print chardet.detect(res)
            f = open("img_code.gif", "w+b")
            f.write(res)
            f.close()
            print res
            md5str = hashlib.md5(res.strip()).hexdigest()
            with self.locker:
                if self.img_catch.get(md5str,None) is not None:
                    self.img_catch[md5str]+=1
                    print "dup!!!!!!!!!!!!!!!"+str(self.img_catch[md5str])+" times."
                    print "%d images, dup %d." %(count, dupcnt)
                    dupcnt+=1
                else:
                    self.img_catch[md5str]=0
                    count+=1

            if count>1:
                break

        # f = open("img_code.gif", "w+b")
        # f.write(con.text.strip())
        # f.close()

if __name__ == "__main__":
    spider.util.use_utf8()
    cd = codeimgSpider(1)
    cd.run()