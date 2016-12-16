#!/usr/bin/env python
# -*- coding:utf8 -*-
import abc


class SpiderSeeds():
    @abc.abstractmethod
    def load_list_seeds(self):
        raise NotImplementedError('virtual method called')

    @abc.abstractmethod
    def load_paper_seeds(self):
        raise NotImplementedError('virtual method called')
