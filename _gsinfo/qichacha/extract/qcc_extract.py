#! /usr/bin/env python
#encoding:utf-8
from spider.savebin import BinReader
import re
class QccExtract(object):
    def __init__(self):
        self.dsfile = open("/home/peiyuan/workspace/getjd/_gsinfo/qichacha/extract/regNo.txt", "a+b")
        self.fail_file = open("/home/peiyuan/workspace/getjd/_gsinfo/qichacha/extract/fail.txt", "a+b")
    def getRegNo(self, begin, end):
        rs_path = "/home/peiyuan/data/qichacha/sum/qichacha/39/qichacha.9139.bin"
        binReader = BinReader(rs_path)
        i = begin
        k = 0
        while k< i:
            binReader.readone()
            k += 1

        while i < end:
            line = binReader.readone()
            if line[0] == None:
                break
            i += 1
            m = re.search(r"<li><label>注册号：  </label>(.*?)</li>", line[1])
            if m:
                regNo = m.group(1)
                print regNo
                if regNo.strip()!="":
                    self.dsfile.write(regNo.strip()+"\n")
                    self.dsfile.flush()
                else:
                    self.fail_file.write(line[0]+" has no regno!\n")
            else:
                self.fail_file.write(line[0]+" has no regno!\n")

if __name__ == "__main__":
    qccExtract = QccExtract()
    qccExtract.getRegNo(0,2000000)