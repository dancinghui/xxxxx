#! /usr/bin/env python
# encoding:utf-8

class RegNoGen(object):
    def __init__(self):
        pass

    def check(self, regNo, j=1, p=10):
        regNo = regNo.strip()
        if len(regNo) is not 15:
            print "Invalid regno!!!"
            return False
        s = int(p % 11 + int(regNo[j-1]))
        p = (10 if (s % 10) == 0 else (s % 10)) * 2
        j += 1
        if j > 15:
            return True if (s % 10) == 1 else False
        else:
            return self.check(regNo, j, p)

    def validcode_gen(self, regNo, j=1, p=10):
        regNo = regNo.strip()
        if len(regNo) is not 14:
            print "Invalid regno!!!"
            return -1
        s = int(p % 11 + int(regNo[j-1]))
        p = (10 if (s % 10) == 0 else (s % 10)) * 2
        j += 1
        if j == 15:
            r = p%11
            return 0 if (r==1) else (11-r)
        else:
            return self.validcode_gen(regNo, j, p)

if __name__ == "__main__":
    print RegNoGen().check("110108004044799")
    print RegNoGen().validcode_gen(" 44030110300912")
