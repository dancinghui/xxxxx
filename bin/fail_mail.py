#!/usr/bin/env python
# encoding: utf-8

from spider.util import sendmail
import sys

if __name__ == '__main__':
    mails=['lixungeng@ipin.com', 'jianghao@ipin.com', 'chentao@ipin.com', 'fuwenjie@ipin.com']
    title = "program %s failed" % sys.argv[1]
    msg = "time used : %s\n" % sys.argv[2]
    msg += "exit code: %s\n" % sys.argv[3]
    sendmail(mails, title, msg)
