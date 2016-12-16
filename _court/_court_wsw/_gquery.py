#!/usr/bin/env python
# -*- coding:utf8 -*-
from spider.genquery import GenQueries


class GenWSWQueries(GenQueries):
    def __init__(self, thcnt=8):
        GenQueries.__init__(self, thcnt)
        self._name = 'WenshuwangGenQueries'

    def init_conditions(self):
        pass
