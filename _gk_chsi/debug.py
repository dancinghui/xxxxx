#!/usr/bin/env python
# -*- coding:utf8 -*-
import logging
import os

from _gk_detail import GkChsiDetailSpider2

if __name__ == '__main__':
    logging.basicConfig(filename=os.path.join(os.getcwd(), 'detail_spider.log.debug'), level=logging.NOTSET,
                        format='%(levelno)s:%(asctime)s:%(threadName)s:%(message)s',
                        datefmt='%m/%d %I:%M:%S %p')

    accounts = {'username': 'hubei102', 'password': 'bobo2016', 'prefix': 'hb', 'proxy': None,
                'kldms': [1, 5]}
    # accounts = {'username': 'jsu2015', 'password': 'AHO001009', 'prefix': 'jsu', 'proxy': '183.239.167.122:8080'}
    # accounts = {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'proxy': '58.211.13.26:55336',
    #             'kldms': [2, 6]}
    # accounts = {'username': 'akg999', 'password': 'AHO001009', 'prefix': 'sh', 'proxy': '58.211.13.26:55336',
    #             'kldms': [1, 5]}
    for kldm in ['5']:
        job = GkChsiDetailSpider2(1, accounts, accounts['prefix'], accounts['proxy'], sleep=0.95, recover=False,
                                  kldm=kldm, bkcc='1')
        # job = GkChsiFsxSpider(1, accounts, accounts['prefix'], accounts['proxy'], 1, kldms=accounts['kldms'],captcha_limit=5000000)
        job.run(async=True)
