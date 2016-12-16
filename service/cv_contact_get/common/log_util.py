#!/usr/bin/env python
# -*- coding:utf8 -*-

import logging


class MLog(object):
    def __init__(self, log_name, log_file):
        self._log_file = log_file
        self._log_name = log_name

        self._logger = logging.getLogger(self._log_name)

        # 创建一个handler，用于写入日志文件
        self.fh = logging.FileHandler(self._log_file)

        # 再创建一个handler，用于输出到控制台
        self.ch = logging.StreamHandler()

        self._init()

    def _init(self):
        self.setLevel()
        self.setFormat()

        # 给logger添加handler
        self._logger.addHandler(self.fh)
        self._logger.addHandler(self.ch)

    def setLevel(self, level=logging.INFO):
        self._logger.setLevel(level)

    def setFormat(self, fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"):
        fmt = logging.Formatter(fmt)
        self.fh.setFormatter(fmt)
        self.ch.setFormatter(fmt)

    def __getattr__(self, item):
        return getattr(self._logger, item)


if  __name__ == "__main__":
    t = MLog(__name__, "tt.log")

    t.info("123")
    t.setLevel(logging.WARNING)
    t.info('123')