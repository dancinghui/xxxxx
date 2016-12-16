#!/usr/bin/env python
# -*- coding:utf8 -*-
import threading

from _gk_chsi import GkChsiFsxSpider


class JobRunner:
    def __init__(self, recover=False):
        self.accounts = [
            {'username': 'jsu2015', 'password': 'AHO001009', 'prefix': 'jsu', 'proxy': '183.239.167.122:8080','maxscore':480},
            {'username': 'akg999', 'password': 'AHO001009', 'prefix': 'shh', 'proxy': '203.195.160.14:8080','maxscore':750},
            {'username': 'huoguo', 'password': 'AHO001009', 'prefix': 'sc', 'proxy': '218.106.96.201:80','maxscore':750},
            {'username': 'doing222', 'password': 'AHO001009', 'prefix': 'tj', 'proxy': '218.106.96.201:80','maxscore':750},
            {'username': 'none098', 'password': 'AHO001009', 'prefix': 'sx.ty', 'proxy': '218.106.96.201:80','maxscore':750},
            {'username': 'tsingtao2015', 'password': 'AHO001009', 'prefix': 'sd', 'proxy': '218.106.96.201:80','maxscore':750},
            {'username': 'star0945', 'password': 'AHO001009', 'prefix': 'nm', 'proxy': '218.106.96.201:80','maxscore':750},
            {'username': 'mint123', 'password': 'AHO001009', 'prefix': 'ln', 'proxy': '218.106.96.201:80','maxscore':750},
            {'username': 'pinkpink', 'password': 'AHO001009', 'prefix': 'jl', 'proxy': '218.106.96.201:80','maxscore':750},
            {'username': 'hero001', 'password': 'AHO001009', 'prefix': 'henan', 'proxy': '218.106.96.201:80','maxscore':750},
            {'username': 'canton2015', 'password': 'AHO001009', 'prefix': 'gd', 'proxy': '218.106.96.201:80','maxscore':750},
            {'username': 'homo123', 'password': 'AHO001009', 'prefix': 'bj', 'proxy': '218.106.96.201:80','maxscore':750},
            {'username': 'hefei111', 'password': 'AHO001009', 'prefix': 'ah', 'proxy': '218.106.96.201:80','maxscore':750},
            {'username': 'aho120709', 'password': 'ipin2015', 'prefix': 'nx', 'proxy': '221.7.169.124:8000','maxscore':750},
            {'username': 'coconut007', 'password': 'AHO001009', 'prefix': 'hain', 'proxy': '221.7.169.124:8000','maxscore':900}
        ]
        self.recover = recover

    def run(self):
        threads = []
        for i in range(0, len(self.accounts)):
            thread = threading.Thread(target=self.run_job, args=(i,))
            threads.append(thread)
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def run_job(self, jid):
        job = GkChsiFsxSpider(1, self.accounts[jid], self.accounts[jid]['prefix'], self.accounts[jid]['proxy'], 1,
                              captcha_limit=5000000, recover=self.recover)
        job.run()


if __name__ == '__main__':
    job = JobRunner()
    job.run()
