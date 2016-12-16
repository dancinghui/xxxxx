#!/usr/bin/env python
# -*- coding:utf8 -*-


#日志配置
LOGGING_FILE="/tmp/cv_contact.log"


DOWNLOAD_NUM_LIMIT_LOW = 10


NOTIFY_EMAILS = [

    "jianghao@ipin.com",
    # "linzelin@ipin.com",

]

#51 登录脚本位置
CV51LG_FILE_PATH = ['../../../cv_51job', '../../cv_51job',]
CVZLLG_FILE_PATH = ['../../cv_zhilian', '../../../cv_zhilian']

#猎聘 登录脚本位置
CVLpLG_FILE_PATH = ['../../../cv_liepin',]

# 下载的简历 mongodb url
DOWNLOADED_CV_MONGODB_URLS = {
    # "cv_51job": "mongodb://hadoop2/cv_download",
    'cv_51job':'mongodb://localhost/cv_download',
    'cv_zhilian':'mongodb://localhost/cv_download',
    # "cv_zhilian": "mongodb://hadoop2/cv_download",
    # "cv_liepin": "mongodb://hadoop2/cv_download",
    'cv_liepin':'mongodb://localhost/cv_download',
}
#====================================
# spider 爬取简历 mongodb url (非下载简历存放位置)
SPIDER_CV_MONGODB_URLS = {

    'cv_51job': 'mongodb://hadoop2/cv_crawler',
    'cv_zhilian': 'mongodb://hadoop2/cv_crawler',
    'cv_liepin': 'mongodb://hadoop2/cv_crawler'
}

SPIDER_DB_NAMES = {

    'cv_51job': 'cv_crawler',
    'cv_zhilian': 'cv_crawler',
    'cv_liepin': 'cv_crawler'
}

SPIDER_COLL_NAMES = {

    'cv_51job': 'page_store_cv_51job',
    'cv_zhilian': 'page_store_cv_zhilian',
    'cv_liepin': 'page_store_cv_liepin',
}

#======================================
# 下载简历存储 数据库名
DOWNLOADED_DB_NAMES = {

    "cv_51job": "cv_download",
    "cv_zhilian": "cv_download",
    "cv_liepin": "cv_download",
}

# 表名
DOWNLOADED_COLL_NAMES = {

    "cv_51job": "page_store_cv_51job",
    "cv_zhilian": "page_store_cv_zhilian",
    "cv_liepin": "page_store_cv_liepin",

}

# 51账号，
CV51_ACCOUNTS = [

    {'p': 'zhaopin123', 'u':'超越石油化工:hr0.1'},
    {'p': 'hr1234', 'u':'威凝电气:hr0.2'},
    {'p': 'hr1234', 'u':'铭泽网苑:hr0.3'},
    {'p': 'zhaopin123', 'u':'众邦物资商贸:hr0.4'},
    {'p': 'zhaopin123', 'u':'adl476:hr0.5'},

]

# liepin账号
CVLP_ACCOUNTS = []

# cv智联账号
CVZL_ACCOUNTS = [

    # {"p": "zhaopin123", "u": "yuqiuyun03"},

    {"p":"zhaopin123","u":"CR-PRO"},

]


# 下载简历 对应url
DOWNLOAD_URLS = {

    "cv_51job": "http://ehire.51job.com/Ajax/Resume/GlobalDownload.aspx",
    "cv_liepin": "https://lpt.liepin.com/resume/downloadResume",
    "cv_zhilian": 'http://rd.zhaopin.com/resumepreview/resume/DownloadResume',

}

# cv详情页面
CV_PAGE_TEMPLATE = {

    "cv_zhilian": "http://rd.zhaopin.com/resumepreview/resume/viewone/1/{}_1_1?searchresume=1",

}


#CODE
class StatusCode(object):
    # 已经在爬虫队列
    ALREADY_IN_DOWNLOAD_QUEUE = 0

    # 刚加入爬取队列，还没开始爬
    BEFORE_DOWNLOADING = 1
    # 正在爬取
    DOWNLOADING = 2
    # 爬取成功
    AFTER_DOWNLOADING_SUCESS = 3

    # 爬取失败
    AFTER_DOWNLOADING_FAIL = 4
    # 重试 失败
    DOWNLOAD_RETRY_FAIL = 5

    # 已经在数据库
    ALREADY_IN_DB = 6

    # 重试中
    DOWNLOAD_RETRYING = 7

    # ========================
    # 下载简历时 各种情况 状态设置

    # 账号不对，不允许下载这个简历
    ACCOUNTS_NO_PERMITION=100

    # 这个简历已经被所用账号下载过
    ALREADY_DOWNLOADED=101

    # # 简历原始页面 下载成功（可能应为简历格式不对 导致 存储失败，）
    # DOWNLOADED_SUCESS=102

    # 请求cv没有被爬取过，获取不到realUrl，下载失败
    NO_REAL_URL = 103

    # CV CLOSED
    CV_CLOSED = 104

    code_msg_map = {

        ALREADY_IN_DOWNLOAD_QUEUE: u'已经在爬虫队列',

        DOWNLOAD_RETRY_FAIL: u'爬虫重试 失败',

        BEFORE_DOWNLOADING: u'刚加入爬取队列，还没开始爬, 或则爬取失败，重试中',
        DOWNLOADING: u'正在爬取',
        AFTER_DOWNLOADING_SUCESS: u'爬取成功',
        AFTER_DOWNLOADING_FAIL: u'爬取失败',

        ALREADY_IN_DB: u'已经在数据库',

        ACCOUNTS_NO_PERMITION: u'账号不对，不允许下载这个简历',
        ALREADY_DOWNLOADED: u'这个简历已经被所用账号下载过',
        # DOWNLOADED_SUCESS: '简历原始页面 下载成功（ 但有可能简历格式不对 导致 存储失败，）',
        NO_REAL_URL: u'请求cv没有被爬取过，获取不到realUrl，下载失败',
        CV_CLOSED: u'简历已经关闭',
        DOWNLOAD_RETRYING: u'重试中',

    }




