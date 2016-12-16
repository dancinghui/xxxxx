#!/usr/bin/env python
# -*- coding:utf8 -*-
import os


class SpeedReport():
    def __init__(self, file_name):
        self.source = file_name
        self.results = {}

    def read_source(self):
        with open(self.source, 'r') as f:
            for l in f:
                p = l.strip().split(':', 3)
                if not self.results.has_key(p[0]):
                    self.results[p[0]] = {}
                if not self.results[p[0]].has_key(p[1]):
                    self.results[p[0]][p[1]] = []
                self.results[p[0]][p[1]].append(p[2])

    def output_speed(self, outf):
        out = open(outf, 'w')
        for ac, timedict in self.results.items():
            for t, ids in timedict.items():
                print ac, t, len(ids)
                out.write('%s,%s,%d\n' % (ac, t, len(ids)))
        out.flush()
        out.close()


if __name__ == '__main__':
    sr = SpeedReport('account.log')
    sr.read_source()
    sr.output_speed('speed.spec.jl.csv')
