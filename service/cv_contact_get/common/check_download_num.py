#!/usr/bin/env python
# -*- coding:utf8 -*-


from spider.spider import LoginErrors
import config
from log_util import MLog
from spider.util import sendmail

common_log = MLog("common_log", config.LOGGING_FILE)


def check_download_num(channel, remain_num, acc):
    if remain_num == 0:
        common_log.warn(r'账号可下载简历为0')
        raise LoginErrors.AccountHoldError()

    elif remain_num < config.DOWNLOAD_NUM_LIMIT_LOW:

        sendmail(config.NOTIFY_EMAILS, "%s 简历下载数通知" % channel,
                 """\n\n账号: %r, 剩余简历下载数：%d""" % (acc, remain_num))




if  __name__ == '__main__':
    check_download_num("cv_zhilian", 1, {'p':'zhaopin123', 'u':'test'})