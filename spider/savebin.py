#!/usr/bin/env python
import StringIO
import gzip
import os
import struct
import threading
import csv
import cutil
#from os.path import join, getsize

class FileSaver:
    def __init__(self, fn):
        self.fd = open(fn, 'a+b')
        self.lock = threading.Lock()

    def __del__(self):
        self.fd.close()

    def append(self, value):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        with self.lock:
            self.fd.write(value+"\n")
            self.fd.flush()

class CsvSaver:
    def __init__(self, fn, head):
        self.writer = csv.writer(open(fn,'wb'))
        self.writer.writerow(head)
        self.lock = threading.Lock()

    def __del__(self):
        self.writer.close()

    def writerline(self, line):
        if isinstance(line, unicode):
            value = line.encode('utf-8')
        with self.lock:
            print "wirte csv:%s"%line
            self.writer.writerow(line)

class BinSaver:
    @staticmethod
    def compress_item(name, value):
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        if isinstance(name, unicode):
            name = name.encode('utf-8')
        fo = StringIO.StringIO()
        f = gzip.GzipFile(fileobj=fo, mode='wb')
        f.write(value)
        f.close()
        r = fo.getvalue()
        fo.close()
        return struct.pack("I", len(name)) + name + struct.pack("I", len(r)) + r

    def __init__(self, fn):
        self._fn = fn

    def append(self, name, value):
        a = BinSaver.compress_item(name, value)
        pos = cutil.mp_append_log(self._fn, a)
        if pos < 0:
            raise IOError("unable to write bin file.")
        return pos

    def filename(self):
        return self._fn

    def getsize(self):
        filename = os.path.abspath(self.filename())
        size = os.path.getsize(filename)
        return size


class BinReader:
    def __init__(self, fn):
        self._fsz = float(os.path.getsize(fn))
        self._nread = 0
        self.fn = fn
        self.fd = open(fn, 'rb')
        self.lock = threading.Lock()
    def __del__(self):
        self.fd.close()
    def _readone_i(self):
        sz0 = self.fd.read(4)
        if len(sz0) == 0:
            return (None,None)
        if len(sz0) != 4:
            raise IOError('invalid file')
        (sz,) = struct.unpack("I", sz0)
        fn = self.fd.read(sz)
        if len(fn) != sz:
            raise IOError('invalid file')
        self._nread += sz+4

        sz0 = self.fd.read(4)
        if len(sz0) != 4:
            raise IOError('invalid file')
        (sz,) = struct.unpack("I", sz0)
        gzconn = self.fd.read(sz)
        if len(gzconn) != sz:
            raise IOError('invalid file')
        self._nread += sz+4

        fin = StringIO.StringIO(gzconn)
        with gzip.GzipFile(fileobj=fin, mode='rb') as f:
            conn = f.read()
        fin.close()
        return (fn, conn)

    def progress(self):
        if self._fsz == 0.0:
            return 1.0
        return float(self._nread) / self._fsz

    def readone(self):
        with self.lock:
            return self._readone_i()

    def readone_at(self, pos):
        with self.lock:
            self.fd.seek(pos)
            return self._readone_i()


if __name__ == "__main__":
    t = BinReader('../_jobui/data/jobui_job.bin')
    count = 0
    while True:
        (a,b) = t.readone()
        if a is None:
            break
        count+=1
        if count % 10000 == 0:
             #print "count==%d,a==[%s],b==[%s]"%(count,a,b)
            print "count==%d,"%(count)
    print "the last count=[%d]" % count
        #print "count==%d"%count
