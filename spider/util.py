#!/usr/bin/env python
# -*- coding:utf8 -*-

import re
import smtplib
import socket
import sys
import os
import time
from email.header import Header
from email.mime.text import MIMEText
import hashlib
import threading
import json
import cutil
import getopt
import subprocess
import json.encoder
from runtime import utf8str, use_utf8

assert cutil.version() >= 102


class LocalHashChecker:
    def __init__(self):
        self.hashlist = {}
        self.locker = threading.RLock()

    @staticmethod
    def get_md5(string):
        return hashlib.md5(string).hexdigest()

    def query(self, string):
        h = LocalHashChecker.get_md5(string)
        with self.locker:
            return self.hashlist.get(h, 0)

    def add(self, string):
        h = LocalHashChecker.get_md5(string)
        with self.locker:
            old = self.hashlist.get(h, 0)
            self.hashlist[h] = old+1
            return old+1


class HashChecker:
    TCP_HOST = ('127.0.0.1', 11011)
    def _query(self, cmd, string):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data = None
        try:
            s.connect(self.TCP_HOST)
            s.send(cmd + string + "\r\n")
            data = s.recv(10).strip()
        except Exception as e:
            sys.stderr.write("===HASH ERROR:===" + str(e)+"\n")
        s.close()
        return data
    def query(self, string):
        o = self._query('Q', string)
        if o is not None:
            return int(o)
        return o
    def add(self, string):
        o = self._query('A', string)
        if o is not None:
            return int(o)
        return o


class FSSaver:
    @staticmethod
    def getopath():
        dirs = ['/data/crawler/_files_', '/opt/_test_store_']
        for di in dirs:
            if os.path.isdir(di) and os.access(di, os.W_OK):
                return di
        raise RuntimeError("no dirs for write files.")

    def __init__(self):
        self.fdir = FSSaver.getopath()
        if not self.fdir:
            raise RuntimeError('no dir for writing files.')

    def save(self, key1, key2, content):
        if isinstance(key2, int) or isinstance(key2, long):
            key2 = str(key2)

        d1 = '%s/%s' % (self.fdir, key1)
        d2 = '%s/%s' % (d1, key2[0:3])
        d3 = '%s/%s' % (d2, key2[3:6] or '_')
        d4 = '%s/%s' % (d3, key2)
        if isinstance(content, unicode):
            content = content.encode('utf-8')

        try:
            os.mkdir(d1, 0755)
        except:
            pass
        try:
            os.mkdir(d2, 0755)
        except:
            pass
        try:
            os.mkdir(d3, 0755)
        except:
            pass

        with open(d4, 'wb') as f:
            f.write(content)
        return d4


class FS(object):
    @staticmethod
    def dbg_save_file(filename, content):
        try:
            with open(filename, 'wb') as fo:
                fo.write(utf8str(content))
            return True
        except:
            return False
    @staticmethod
    def dbg_append_file(filename, content):
        with open(filename, 'a+b') as fo:
            fo.write(utf8str(content) + "\n")


class htmlfind:
    def __init__(self, html, reg, which):
        self.s = ''
        self.start = 0
        self.which = 0
        self._begin(html, reg, which)

    def _begin(self, s, reg, which):
        if isinstance(s, unicode):
            s = s.encode('utf-8')
        regtype = type(re.compile(''))
        if isinstance(reg, unicode) or isinstance(reg, str) or isinstance(reg, regtype):
            reg = [reg]
        if not isinstance(reg, list):
            raise RuntimeError("unknown type")
        start=0
        for r in reg:
            if isinstance(r, unicode):
                r = r.encode('utf-8')
            if isinstance(r, str):
                m = re.search(r, s, start)
            elif isinstance(r, regtype):
                m = r.search(s, start)
            else:
                raise RuntimeError("unknown type")
            if m is not None:
                start = m.end(0)
            else:
                start = len(s)
                break
        self.s = s
        self.start = start
        self.which = which

    def process_form(self):
        return cutil.process_form(self.s, self.start, self.which)

    def get_node(self):
        return cutil.get_html_node(self.s, self.start, self.which)

    def get_text(self):
        return cutil.get_html_text(self.s, self.start, self.which)

    def get_text_hash(self):
        return cutil.get_html_text_hash(self.s, self.start, self.which)

    @staticmethod
    def findTag(doc, tag, attr=None, text_pattern=None):
        pat = None
        if not attr and not text_pattern:
            pat = ur'<{}[^<>]*>(.*?)</{}>'.format(tag, tag)
        elif not attr and text_pattern:
            pat = ur'<{}[^>]*?>{}</{}>'.format(tag, text_pattern, tag)
        elif attr and not text_pattern:
            pat = ur'<{}[^>]*{}[^>]*>(.*?)</{}>'.format(tag, attr, tag)
        elif attr and text_pattern:
            pat = ur'<{}[^>]*{}[^>]*>{}</{}>'.format(tag, attr, text_pattern, tag)

        els = re.findall(pat, doc, re.S)
        return els

    @staticmethod
    def remove_tag(s, fmt=False):
        if fmt:
            r = re.sub(r'<br>|<p>|<BR>','\n', s)
            r = re.sub(r'(<[^>]*>)','',r)
            r = re.sub(r'&nbsp;', ' ', r)
            r = re.sub(r'[\t\r ]+', ' ', r)
            r = re.sub(r'\s+\n+\s+', '\n', r)
            r = re.sub(r'^\s+|\s+$', '', r)
        else:
            r = re.sub(r'(<[^>]*>)','',s)
            r = re.sub(r'&nbsp;', ' ', r)
        return r


class GetOptions:
    def __init__(self, opts='', longopts='default'):
        if longopts is 'default':
            longopts = ['page=', 'singlethread', 'mjparellel']
        opts_, args_ = getopt.getopt(sys.argv[1:], opts, longopts)
        self.opts = opts_
        self.args = args_
    def get(self, name, defv=None):
        for k,v in self.opts:
            if k == name:
                return v
        return defv


def sendmail(email, title, message):
    username = 'notify@ipin.com'
    password = '4c4b5e4dfF'
    smtphost = 'smtp.exmail.qq.com'
    smtpport = 465
    """username: postmaster
    password: suChe$huP6ar
    mail_server: smtp.service.ipin.com"""
    if isinstance(message, unicode):
        message = message.encode('utf-8')
    if isinstance(title, unicode):
        title = message.encode('utf-8')
    msg = MIMEText(message, 'plain', 'utf-8')
    msg['Subject'] = Header(title, 'utf-8')
    msg['From'] = username
    if isinstance(email, list):
        msg['To'] = '; '.join(email)
        tolist = email
    else:
        msg['To'] = email
        tolist = [email]
    for i in range(0, len(tolist)):
        m = re.search('<([a-z0-9_@\-.]*)>\s*$', tolist[i], re.I)
        if m:
            tolist[i] = m.group(1)
    print "sending mail to", tolist
    print msg.as_string()
    s = smtplib.SMTP_SSL(smtphost, smtpport)
    s.login(username, password)
    s.sendmail(username, tolist, msg.as_string())
    s.quit()

def unique_list(arr):
    if not isinstance(arr, list):
        return arr
    oarr = []
    for i in arr:
        if i not in oarr:
            oarr.append(i)
    return oarr


def chained_regex(s, *regex):
    inp = [s]
    outarr = []
    retype = type(re.compile(''))
    for ri in regex:
        for ss in inp:
            if isinstance(ri, str) or isinstance(ri, unicode):
                m = re.findall(ri, ss)
            elif isinstance(ri, retype): #assume ri is a compiled pattern
                m = ri.findall(ss)
            else:
                raise RuntimeError('invalid arg')
            if m:
                outarr.extend(m)
        if len(outarr) == 0:
            return []
        inp = outarr
        outarr = []
    return inp


def wait_god():
    try:
        l = 'pywait.%d' % os.getpid()
        with open('/proc/sys/kernel/random/uuid') as f:
            l = f.read().strip()
        sys.stderr.write("enable <key.%s> and wait up to 30sec to continue...\n" % l)
        h = HashChecker()
        while True:
            v = h.query("key." + l)
            if v:
                return True
            time.sleep(30)
    except Exception as e:
        print e
        sys.stderr.write("God is angry!\n")
        time.sleep(99999999)


def get_hostname():
    try:
        with open('/etc/hostname') as f:
            return f.readline().strip()
    except:
        pass
    try:
        a = os.popen("hostname")
        return a.read().strip()
    except:
        pass
    return None


class TimeHandler(object):
    @staticmethod
    def isBeforeNDay(t, day):
        if isinstance(t, str) or isinstance(t, unicode):
            m = re.search('(\d+)-(\d+)-(\d+).*?(\d+):(\d+):(\d+)', t)
            if m:
                arr = [int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5)), int(m.group(6)), 0, 0, 0]
                t = time.mktime(arr)
                if time.time() - t > 3600 * 24 * day:
                    return True

        if isinstance(t, int):
            if int(time.time()) - t/1000 > 3600 * 24 * day:
                return True
        return False

    @staticmethod
    def getTimeOfNDayBefore(day):
        day = int(day)
        one_day = 24 * 3600
        nday_before = time.time() - day * one_day
        return int(nday_before * 1000)

    @staticmethod
    def fmt_time(tag):
        if isinstance(tag, unicode):
            tag = tag.encode('utf-8')

        now_time = list(time.localtime())

        t = re.search(r'(\d+):(\d+)', tag)
        if t:
            now_time[3] = int(t.group(1))
            now_time[4] = int(t.group(2))
            return int(time.mktime(now_time) * 1000)

        t = re.search(r'(\d+)-(\d+)-(\d+)', tag)
        if t:
            now_time[0] = int(t.group(1))
            now_time[1] = int(t.group(2))
            now_time[2] = int(t.group(3))
            return int(time.mktime(now_time) * 1000)

        t = re.search(r'(\d+)-(\d+)', tag)
        if t:
            now_time[1] = int(t.group(1))
            now_time[2] = int(t.group(2))
            return int(time.mktime(now_time) * 1000)


        t = re.search(r'(\d+)/(\d+)/(\d+)', tag)
        if t:
            now_time[0] = int(t.group(1))
            now_time[1] = int(t.group(2))
            now_time[2] = int(t.group(3))
            return int(time.mktime(now_time) * 1000)

        t = re.search(r'(\d+)小时', tag)
        if t:
            hour = int(t.group(1))
            return int(time.time() - hour * 3600) * 1000

        t = re.search(r'(\d+)分钟', tag)
        if t:
            minute = int(t.group(1))
            return int(time.time() - minute * 60) * 1000

        t = re.search(r'(\d+).*?天', tag)
        if t:
            day = t.group(1)
            return TimeHandler.getTimeOfNDayBefore(day)

        t = re.search(r'前天', tag)
        if t:
            return TimeHandler.getTimeOfNDayBefore(2)
        t = re.search(r'昨天', tag)
        if t:
            return TimeHandler.getTimeOfNDayBefore(1)

        t = re.search(r'今天', tag)
        if t:
            return TimeHandler.getTimeOfNDayBefore(0)

        t = re.search(r'刚刚', tag)
        if t:
            return int(time.time()) * 1000

        t = re.search(r'(\d+)月内', tag)
        if t:
            day = int(t.group(1)) * 30
            return TimeHandler.getTimeOfNDayBefore(day)

        t = re.search(r'(\d+)周内', tag)
        if t:
            day = int(t.group(1)) * 7
            return TimeHandler.getTimeOfNDayBefore(day)

        t = re.search(r'(\d+).*?day', tag)
        if t:
            day = t.group(1)
            return TimeHandler.getTimeOfNDayBefore(day)

        t = re.search(r'(\d+).*?hour', tag)
        if t:
            hour = int(t.group(1))
            return int(time.time() - hour * 3600) * 1000

        t = re.search(r'(\d+).*?minute', tag)
        if t:
            minute = int(t.group(1))
            return int(time.time() - minute * 60) * 1000

        raise Exception("not copy time pattern: {}".format(tag))


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        print os.environ["PATH"]
        for path in os.environ["PATH"].split(os.pathsep):

            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


def runjs(jscode):
    jscode = utf8str(jscode)
    nodeapp = which("node")
    if nodeapp is None:
        nodeapp = which("nodejs")
    if nodeapp is None:
        raise RuntimeError("nodejs is NOT found!")
    node = subprocess.Popen(nodeapp, stdin=subprocess.PIPE, stdout=subprocess.PIPE, close_fds=True, bufsize=len(jscode)+1)
    node.stdin.write(jscode)
    node.stdin.close()
    ooo = ''
    while True:
        oo1 = node.stdout.read(1024)
        if not oo1:
            break
        ooo += oo1
    node.wait()

    if node.returncode == 0:
        return ooo
    else:
        raise RuntimeError("excute js failed.", node.returncode, ooo)


class Pager(object):
    @staticmethod
    def select_by_pager(lst, pageno, pagenum):
        """本函数把lst里的内容分页,总页数为pagenum, 分出页为第pageno页.
        注意:pageno以1而不是0起始"""
        assert pagenum>0
        assert pageno>0 and pageno<=pagenum
        assert isinstance(lst, list)
        lstsz = len(lst)
        if lstsz == 0:
            return lst
        pagesize = (lstsz + pagenum - 1) / pagenum
        pgstart = (pageno-1)*pagesize
        pgend = pageno * pagesize
        return lst[pgstart:pgend]


class StateMachine(object):
    def __init__(self, states):
        self.state = 0
        self.states = states

    def in_state(self, c):
        pass

    def chg_state(self, sc):
        pass

    def out_value(self):
        return None

    def process(self, s):
        self.state = 0
        for c in s:
            found = 0
            for sc in self.states:
                if c == sc[0] and self.state == sc[1]:
                    self.state = sc[2]
                    self.chg_state(sc)
                    found = 1
                    break
            if found == 0:
                self.in_state(c)
        return self.out_value()


class CJSONEncoder(object):
    """customizable json encoder"""
    INFINITY = float('inf')
    FLOAT_REPR = repr

    def __init__(self, indent=None, addspace=1, encoding="utf-8"):
        self.indent = indent
        self.encoding = encoding
        self.level = 0
        self.addspace = ' ' if addspace else ''

    def floatstr(self, o, _repr=FLOAT_REPR, _inf=INFINITY, _neginf=-INFINITY):
        if o != o:
            text = 'NaN'
        elif o == _inf:
            text = 'Infinity'
        elif o == _neginf:
            text = '-Infinity'
        else:
            return _repr(o)
        return text

    def _newline(self, reason):
        if self.indent is None:
            return self.addspace
        else:
            return "\n"

    def _indent(self, level):
        if self.indent is None:
            return ""
        return " " * self.indent * level

    def _add_comma(self, s):
        return s + ","

    def _inclevel(self, dct):
        self.level += 1

    def _declevel(self, dct):
        self.level -= 1

    def encode(self, js):
        if isinstance(js, dict):
            vlen = len(js)
            vi = 0
            if vlen==0:
                return "{}"
            o = "{" + self._newline('dict.begin')
            for k, v in sorted(js.items(), key=lambda kv: kv[0]):
                vi += 1
                if isinstance(k, unicode):
                    k = k.encode(self.encoding)
                else:
                    k = str(k)
                o += self._indent(self.level+1)
                o += json.encoder.encode_basestring(k)
                o += ":"
                if isinstance(v, list) or isinstance(v, dict):
                    o += self._newline('dict.subobj') + self._indent(self.level+1)
                    tr = {}
                    self._inclevel(tr)
                    o += self.encode(v)
                    self._declevel(tr)
                else:
                    oldlevel = self.level
                    self.level = -1
                    o += self.addspace
                    o += self.encode(v)
                    self.level = oldlevel
                if vi != vlen:
                    o = self._add_comma(o)
                    o += self._newline('dict.nextchild')
            o += self._newline('dict.end')
            o += self._indent(self.level) + "}"
            return o
        elif isinstance(js, list):
            vlen = len(js)
            vi = 0
            if vlen == 0:
                return "[]"
            o = "[" + self._newline('list.begin')
            for v in js:
                vi += 1
                o += self._indent(self.level+1)
                tr={}
                self._inclevel(tr)
                o += self.encode(v)
                self._declevel(tr)
                if vi != vlen:
                    o = self._add_comma(o)
                    o += self._newline('list.nextchild')
            o += self._newline('list.end')
            o += self._indent(self.level) + "]"
            return o
        elif isinstance(js, unicode):
            js = js.encode(self.encoding)
            return self._indent(self.level) + json.encoder.encode_basestring(js)
        elif isinstance(js, str):
            return self._indent(self.level) + json.encoder.encode_basestring(js)
        elif isinstance(js, float):
            js = self.floatstr(js)
            return self._indent(self.level) + js
        elif js is True:
            return 'true'
        elif js is False:
            return 'false'
        elif js is None:
            return 'null'
        elif isinstance(js, (int, long)):
            return str(js)
        else:
            js = str(js)
            return self._indent(self.level) + json.encoder.encode_basestring(js)


def transform(lst, c):
    assert isinstance(lst, list)
    i = 0
    while i < len(lst):
        lst[i] = c(lst[i])
        i += 1

def compose_url_param(url, query):
    assert isinstance(query, dict)

    q = []
    for key in query:
        q.append("%s=%s" % (key, query[key]))

    if '?' not in url:
        url += '?'
    elif not url.index('?') == len(url) - 1:
        if url[-1] != '&':
            url += '&'

    return utf8str(url + '&'.join(q))


