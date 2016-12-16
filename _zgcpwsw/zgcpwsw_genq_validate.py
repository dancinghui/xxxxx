#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
sys.path.append(sys.path[0]+"/../")
import hashlib
import threading
import json

from zgcpwsw_genq import ZGcpwswQueries
import spider.util


# 为了补全zgcpwsw_genq.py查询条件
class ZGcpwswQueriesValidate(ZGcpwswQueries):

    def __init__(self, thcnt, read_ral=False, need_srl=True):
        ZGcpwswQueries.__init__(self, thcnt, need_srl)
        self.validate_dict = {}
        self.vd_init_signal = threading.Event()
        self.read_ral = read_ral

    def set_md5(self, jobid):
        if isinstance(jobid, dict):
            md5 = hashlib.md5(json.dumps(jobid, ensure_ascii=False)).hexdigest()
            self.validate_dict[md5] = 1

    def dispatch(self):
        with open("court_queries/large_count", "r") as lc_fs:
            for line in lc_fs:
                data = eval(line.strip())
                jobid = data.get("jobid", {})
                self.set_md5(jobid)

        with open("court_queries/medium_count") as mc_fs:
            for line in mc_fs:
                data = eval(line.strip())
                jobid = data.get("jobid", {})
                self.set_md5(jobid)

        with open("court_queries/small_count") as sc_fs:
            for line in sc_fs:
                data = eval(line.strip())
                jobid = data.get("jobid", {})
                self.set_md5(jobid)

        if self.read_ral:
            self.read_re_add_list()
        else:
            self.vd_init_signal.set()
            ZGcpwswQueries.dispatch(self)
        # 释放任务初始化完成的信号

    # 重读失败的任务
    def read_re_add_list(self):
        with open("court_queries/re_add_list", "r") as ral_fs:
            for line in ral_fs:
                jobid = eval(line.strip())
                self.add_job(jobid)
        self.vd_init_signal.set()
        self.wait_q()
        self.add_main_job(None)

    def thread_init(self, tid):
        self.vd_init_signal.wait()
        ZGcpwswQueries.thread_init(self, tid)

    def run_job(self, jobid):
        if self.is_job_exist(jobid):
            print "**********"
        else:
            ZGcpwswQueries.run_job(self, jobid)

    def is_job_exist(self, jobid):
        md5 = hashlib.md5(json.dumps(jobid, ensure_ascii=False)).hexdigest()
        if self.validate_dict.get(md5, 0):
            return True
        else:
            return False

if __name__ == "__main__":
    spider.util.use_utf8()
    # genq = ZGcpwswQueriesValidate(2)
    # genq.set_proxy(['106.75.134.189:18889:ipin:helloipin'], index=0, auto_change=False)
    genq = ZGcpwswQueriesValidate(999, read_ral=True, need_srl=False)
    genq.load_proxy("proxy", True)
    genq.run()
