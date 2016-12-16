#!/usr/bin/env python
# -*- coding:utf8 -*-
import abc
import getopt

import sys

from court.util import Main


class Nacao():
    def __init__(self):
        self.short_tag = ''
        self.tags = []

    def usage(self):
        print 'PyTest.py usage:'
        print '-h,--help: print help message.'
        print '-v, --version: print script version'
        print '-o, --output: input an output verb'
        print '--foo: Test option '
        print '--fre: another test option'

    def version(self):
        print 'PyTest.py 1.0.0.0.1'

    def output(self, args):
        print 'Hello, %s' % args

    @abc.abstractmethod
    def handle(self, opts):
        raise NotImplementedError('virtual function callled')

    def main(self, argv):
        try:
            opts, args = getopt.getopt(argv[1:], self.short_tag, self.tags)
        except getopt.GetoptError, err:
            print str(err)
            self.usage()
            sys.exit(2)
        self.handle(opts)