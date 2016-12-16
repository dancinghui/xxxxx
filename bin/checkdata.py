#!/usr/bin/env python
# encoding: utf-8

import getopt
import struct
import sys
import threading

from spider.savebin import BinReader, BinSaver


class BinReader1:
    def __init__(self, fn):
        self.fd = open(fn, 'rb')
        self.lock = threading.Lock()

    def __del__(self):
        self.fd.close()

    def readone_i(self):
        sz0 = self.fd.read(4)
        if len(sz0) == 0:
            return (None, None)
        if len(sz0) != 4:
            raise IOError('invalid file')
        (sz,) = struct.unpack("I", sz0)
        fn = self.fd.read(sz)
        if len(fn) != sz:
            raise IOError('invalid file')

        sz0 = self.fd.read(4)
        if len(sz0) != 4:
            raise IOError('invalid file')
        (sz,) = struct.unpack("I", sz0)
        gzconn = self.fd.read(sz)
        if len(gzconn) != sz:
            raise IOError('invalid file')
        return (fn, gzconn)

    def readone(self):
        with self.lock:
            (a, b) = self.readone_i()
        return (a, b)


def showusage():
    print """usage:
    checkdata.py [-p] [-i index] binfile
      -p : also print values
OR:
    checkdata.py -o outfile -m string binfile [binfile...]
    """


def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'o:m:pi:')
    except getopt.GetoptError as e:
        showusage()
        return 1

    outfile = None
    matchstr = ''
    printout = False
    index = -1
    for (n, v) in opts:
        if n == '-o':
            outfile = v
        if n == '-m':
            matchstr = v
        if n == '-p':
            printout = True
        if n == '-i':
            index = int(v)

    if len(args) == 0:
        showusage()
        return 1

    if outfile:
        fo = BinSaver(outfile)
        for fn in args:
            r = BinReader(fn)
            while True:
                (n, v) = r.readone()
                if n is None:
                    break
                if matchstr in v:
                    fo.append(n, v)
    else:
        for fn in args:
            if printout or index!=-1:
                r = BinReader(fn)
            else:
                r = BinReader1(fn)
            findex = 0
            while True:
                (n, v) = r.readone()
                if n is None:
                    break
                if index!=-1:
                    if findex==index:
                        if printout:
                            print v
                        else:
                            print n
                    elif findex>index:
                        break
                elif printout:
                    print n, v
                else:
                    print n
                findex += 1


if __name__ == "__main__":
    main()
