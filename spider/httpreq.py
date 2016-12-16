#!/usr/bin/env python
# -*- encoding:utf-8 -*-

import urllib
import pycurl
from StringIO import StringIO
import copy
import time
import re
import threading
import traceback
from curlcookie import CurlCookieJar
import signal
import os
from runtime import Log
from collections import OrderedDict
import sys

if os.name != 'nt':
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)


class ProxyError(Exception):
    def __init__(self, r):
        Exception.__init__(self)
        self.reason = r

    def __str__(self):
        return "ProxyError:%s" % self.reason


class DNSError(Exception):
    def __init__(self, r):
        Exception.__init__(self)
        self.hostname = r

    def __str__(self):
        return "Dns failed:" + self.hostname


class CurlReq(object):
    DEBUGREQ = 1

    class Request(object):
        def __init__(self):
            self.headers = None
            self.url = None

    class Response(object):
        def __init__(self):
            self.content = None
            self.text = None
            self.encoding = None
            self.code = 0
            self.request = CurlReq.Request()
            self.cookies = None
            self.headers = None

    def __init__(self, curlshare):
        self.curl = None
        self.cur_response = None
        self._curlshare = curlshare
        self.reset()
        self.otherinfo = {}
        self._proxy = ''
        self._buffer = None
        self._user_agent = 'curl/7.20.1'

    def __del__(self):
        if self.curl:
            self.curl.close()

    def _debug_func(self, _type, text):
        r = self.cur_response
        if r:
            if _type == pycurl.INFOTYPE_HEADER_OUT:
                r.request.headers = text
            elif _type == pycurl.INFOTYPE_HEADER_IN:
                r.headers = (r.headers or '') + text
            else:
                # print text.strip()
                pass

    def reset(self):
        if self.curl:
            self.curl.close()
        self.curl = pycurl.Curl()
        if self._curlshare:
            self.curl.setopt(pycurl.SHARE, self._curlshare)

    def _gen_kv_info(self, params):
        if isinstance(params, unicode):
            return params.encode('utf-8')
        if isinstance(params, str):
            return params
        if params:
            qstr = ''
            for k, v in params.items():
                if isinstance(k, unicode):
                    k = k.encode('utf8')
                if isinstance(v, unicode):
                    v = v.encode('utf8')
                qstr += '&' + urllib.quote(str(k)) + '=' + urllib.quote(str(v))
            return qstr[1:]
        else:
            return ''

    def _inner_reset(self):
        c = self.curl
        c.reset()
        c.setopt(pycurl.FOLLOWLOCATION, 1)
        c.setopt(pycurl.MAXREDIRS, 7)
        c.setopt(pycurl.NOSIGNAL, 1)
        c.setopt(pycurl.VERBOSE, 1)
        c.setopt(pycurl.DEBUGFUNCTION, self._debug_func)
        c.setopt(pycurl.ENCODING, "gzip, deflate")
        c.setopt(pycurl.SSL_VERIFYPEER, 0)
        c.setopt(pycurl.SSL_VERIFYHOST, 0)
        c.setopt(pycurl.IPRESOLVE, pycurl.IPRESOLVE_V4)
        return c

    def select_user_agent(self, ua):
        if ua == 'baidu':
            self._user_agent = 'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)'
        elif ua == 'firefox':
            self._user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:42.0) Gecko/20100101 Firefox/42.0'
        elif ua[0:1] == '=':
            self._user_agent = ua[1:]
        else:
            raise RuntimeError("unknown user agent")

    def prepare_req(self, url, **kwargs):
        c = self._inner_reset()
        c.setopt(pycurl.TIMEOUT, int(kwargs.get('timeout', 30)))
        rv = CurlReq.Response()
        self.cur_response = rv
        self._buffer = StringIO()
        c.setopt(c.WRITEDATA, self._buffer)

        headers = kwargs.get('headers', {})
        if not 'User-Agent' in headers.keys():
            headers['User-Agent'] = self._user_agent
        header_tuples = [str('%s: %s' % x) for x in headers.items()]
        c.setopt(pycurl.HTTPHEADER, header_tuples)

        allow_redirect = kwargs.get("allow_redirects", None)
        if allow_redirect is not None:
            if not allow_redirect:
                c.setopt(pycurl.FOLLOWLOCATION, 0)

        params = kwargs.get('params')
        if params:
            qstr = self._gen_kv_info(params)
            # TODO: FIXME what if # in url???
            if '?' in url:
                url += '&' + qstr
            else:
                url += '?' + qstr
        c.setopt(c.URL, url)

        files = kwargs.get('files')
        if files:
            ifile = 0
            file_fields = []
            for name, v_ in files.items():
                if isinstance(v_, tuple):
                    filename, fileobj = v_
                else:
                    fileobj = v_
                    if ifile > 0:
                        filename = 'file%d' % ifile
                    else:
                        filename = 'file'
                ifile += 1
                if isinstance(fileobj, str):
                    value = pycurl.FORM_BUFFER, filename, pycurl.FORM_BUFFERPTR, fileobj  # pycurl.FORM_CONTENTTYPE, "image/jpeg"
                else:
                    fileobj.seek(0)
                    value = pycurl.FORM_BUFFER, filename, pycurl.FORM_BUFFERPTR, fileobj.read()  # pycurl.FORM_CONTENTTYPE, "image/jpeg"
                    fileobj.seek(0)
                file_fields.append((name, value))
            for name, v_ in kwargs.get('data', {}).items():
                file_fields.append((name, str(v_)))
            c.setopt(c.HTTPPOST, file_fields)
        else:
            data = kwargs.get('data', None)
            if data is not None:
                c.setopt(c.POSTFIELDS, self._gen_kv_info(data))

        auth = kwargs.get('auth')
        if auth:
            c.setopt(c.HTTPAUTH, c.HTTPAUTH_BASIC)
            c.setopt(c.USERNAME, auth[0])
            c.setopt(c.PASSWORD, auth[1])
        pr = kwargs.get('proxies', None)
        setproxy = None
        if pr:
            setproxy = pr.get('https')
            c.setopt(c.PROXY, setproxy)
        self._proxy = setproxy
        return c

    def doreq(self, url, **kwargs):
        c = self.prepare_req(url, **kwargs)
        try:
            if CurlReq.DEBUGREQ:
                sys.stderr.write("req.url: " + url + " proxy: " + str(self._proxy) + "\n")
            c.perform()
        except pycurl.error as e:
            code, msg = e.args
            errorobj = self._error_obj(code, msg)
            if errorobj:
                raise errorobj
            else:
                raise
        rv = self._build_result()
        c.reset()
        return rv

    def _error_obj(self, code, msg):
        setproxy = self._proxy
        rv = self.cur_response
        m = re.search("Couldn't resolve host '(.*?)'", msg)
        if m:
            return DNSError(m.group(1))

        if setproxy:
            # 检查哪些是由代理服务器导致的问题.
            m = re.search(r'(\d+\.\d+\.\d+\.\d+)', setproxy)
            prhost = m.group(1) if m else '1111.1111.2222.3333'
            if code == pycurl.E_COULDNT_CONNECT and prhost in msg:
                return ProxyError(msg)
            elif code == pycurl.E_OPERATION_TIMEDOUT:
                if 'connection timed out' in msg.lower():
                    return ProxyError(msg)
                if re.search(r'Operation timed out .* with 0 bytes received', msg, re.I):
                    return ProxyError(msg)
            elif code == pycurl.E_RECV_ERROR:
                if not rv.headers:
                    return ProxyError(msg)
        return None

    def _build_result(self):
        c = self.curl
        rv = self.cur_response
        rv.content = self._buffer.getvalue()
        if re.search('Content-Type:.*charset=utf-8', rv.headers, re.M | re.I):
            rv.encoding = 'utf-8'
        elif re.search('Content-Type.*(gbk|gb2312)', rv.content, re.M | re.I):
            rv.encoding = 'gb18030'
        else:
            rv.encoding = 'utf-8'
        rv.text = rv.content.decode(rv.encoding, 'replace')
        rv.code = c.getinfo(c.RESPONSE_CODE)
        rv.cookies = c.getinfo(c.INFO_COOKIELIST)
        rv.request.url = c.getinfo(c.EFFECTIVE_URL)
        return rv


class DbgCurlReq(CurlReq):
    def __init__(self, s, ckfn):
        CurlReq.__init__(self, s)
        self._ckfn = ckfn
        self.curl.setopt(pycurl.COOKIEFILE, self._ckfn)
        self.curl.setopt(pycurl.COOKIEJAR, self._ckfn)

    def doreq(self, url, **kwargs):
        r = CurlReq.doreq(self, url, **kwargs)
        self.curl.setopt(pycurl.COOKIEJAR, self._ckfn)
        self.curl.setopt(pycurl.COOKIELIST, "FLUSH")
        return r


class BasicRequests(object):
    def __init__(self):
        self.locker = threading.RLock()
        self.sp_proxies = OrderedDict()
        self._auto_change_proxy = False
        self._cur_proxy_index = -1
        self.default_headers = {}
        self._curltls = threading.local()
        self._user_agent = 'curl/7.45.0'
        self.select_user_agent('baidu')

    def select_user_agent(self, ua):
        if ua == 'baidu':
            self._user_agent = 'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)'
        elif ua == 'firefox':
            self._user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:42.0) Gecko/20100101 Firefox/42.0'
        elif ua[0:1] == '=':
            self._user_agent = ua[1:]
        else:
            raise RuntimeError("unknown user agent")

    def compose_url(self, url, name, value):
        assert isinstance(url, unicode) or isinstance(url, str)
        if isinstance(url, unicode):
            url = url.encode('utf-8')
        m = re.search("[?&]%s=([^&]*)" % name, url)
        if m:
            return url[0:m.start(1)] + value + url[m.end(1):]
        else:
            return "%s&%s=%s" % (url, name, value)

    def set_proxy(self, prs, index=-1, auto_change=True):
        self._cur_proxy_index = index
        self._auto_change_proxy = auto_change
        if isinstance(prs, list):
            for p in prs:
                self.sp_proxies[p] = 0
        elif isinstance(prs, str) or isinstance(prs, unicode):
            self.sp_proxies[prs] = 0
        else:
            raise RuntimeError('invalid argument')

    def load_proxy(self, fn, index=-1, auto_change=True):
        with open(fn, 'r') as f:
            for line in f:
                line = line.strip()
                line = re.sub('\s*#.*', '', line)
                if line == '':
                    continue
                self.sp_proxies[line] = 0
        self._cur_proxy_index = index
        self._auto_change_proxy = auto_change
        print "==== %d proxies loaded ====" % len(self.sp_proxies.keys())

    def _on_req_success(self, kwargs, memo, response):
        if isinstance(self.sp_proxies, dict) and len(self.sp_proxies.keys()) > 0:
            oldproxy = memo.get('proxy')
            if oldproxy is not None and oldproxy in self.sp_proxies:
                self.sp_proxies[oldproxy] = 0

    def _set_proxy(self, kwargs, selproxy):
        # check proxy type.
        m = re.match('([0-9.]+):(\d+):([a-z0-9]+):([a-z0-9._-]+)$', selproxy, re.I)
        m1 = re.match('([0-9.]+):(\d+):([a-z0-9]+)$', selproxy, re.I)
        if m:
            prstr = '%s:%s@%s:%s' % (m.group(3), m.group(4), m.group(1), m.group(2))
            proxies = {'http': 'http://' + prstr, 'https': 'https://' + prstr}
            kwargs['proxies'] = proxies
        elif m1:
            prstr = '%s:%s' % (m1.group(1), m1.group(2))
            proxies = {'http': 'http://' + prstr, 'https': 'https://' + prstr}
            kwargs['auth'] = ('PROXY_PASSWORD', m1.group(3))
            kwargs['proxies'] = proxies
        else:
            proxies = {'http': 'http://' + selproxy, 'https': 'https://' + selproxy}
            kwargs['proxies'] = proxies

    def _replace_proxy(self, kwargs, memo):
        with self.locker:
            if not isinstance(self.sp_proxies, dict) or len(self.sp_proxies.keys()) == 0:
                return False
            if self._auto_change_proxy:
                oldproxy = memo.get('proxy')
                if oldproxy in self.sp_proxies:
                    self.sp_proxies[oldproxy] += 1
                prs = self.sp_proxies.keys()
                for i in range(0, len(prs)):
                    self._cur_proxy_index = (self._cur_proxy_index + 1) % len(prs)
                    selproxy = prs[self._cur_proxy_index]
                    if self.sp_proxies.get(selproxy, 0) <= 10:
                        memo['proxy'] = selproxy
                        self._set_proxy(kwargs, selproxy)
                        return True
            elif self._cur_proxy_index < 0:
                # don't auto change proxy, and the index < 0, no proxy is used.
                # but don't report an error.
                return True
            else:
                prs = self.sp_proxies.keys()
                selproxy = prs[self._cur_proxy_index % len(prs)]
                self._set_proxy(kwargs, selproxy)
                return True
        return False

    def req_content_check(self, url, resp):
        return True

    def is_proxy_error(self):
        return getattr(self._curltls, 'is_proxy_error', False)

    def request_url(self, url, **kwargs):
        headers1 = copy.deepcopy(self.default_headers)
        headers1.update({"User-Agent": self._user_agent})
        if 'headers' in kwargs:
            headers1.update(kwargs['headers'])
        kwargs['headers'] = headers1
        kwargs.setdefault('timeout', 30.0)
        memo = {}
        setattr(self._curltls, 'is_proxy_error', False)

        if len(self.sp_proxies) > 0:
            if not self._replace_proxy(kwargs, memo):
                raise RuntimeError("no proxy")

        i = 0
        while i < 3:
            i += 1
            try:
                response = self._do_requests(url, **kwargs)
                if self.req_content_check(url, response):
                    self._on_req_success(kwargs, memo, response)
                    return response
            except (KeyboardInterrupt, SystemExit):
                raise
            except ProxyError as e:
                setattr(self._curltls, 'is_proxy_error', True)
                print "proxy failed %s" % url, e.reason
                if i >= 2 and self._auto_change_proxy and self._replace_proxy(kwargs, memo):
                    i = 0
                    print "retry using proxy ", kwargs.get('proxies', '')
            except DNSError as e:
                Log.warning("dns for %s error!" % e.hostname)
                time.sleep(3)
                i -= 1
            except Exception as e:
                if not self.on_other_http_exception(e):
                    hpr = kwargs.get('proxies', {}).get('http', '')
                    Log.error("FAIL: req %s proxy=%s, err=" % (url, hpr), str(type(e)), str(e))
                    traceback.print_exc()
            time.sleep(1)
        return None

    def on_other_http_exception(self, exception):
        """
        other exception handler
        :return True if exception is handled,False otherwise
        """
        return False

    def _do_requests(self, url, **kwargs):
        curl = getattr(self._curltls, 'curl', None)
        if curl is None:
            curl = self._new_request_worker()
            setattr(self._curltls, 'curl', curl)
        return curl.doreq(url, **kwargs)

    def _new_request_worker(self):
        return CurlReq(None)


class SpeedControlRequests(BasicRequests):
    def __init__(self):
        BasicRequests.__init__(self)

    def with_sleep_requests(self, url, sleep=0, **kwargs):
        time.sleep(sleep)
        return self.request_url(url, **kwargs)


class SessionRequests(BasicRequests):
    def __init__(self):
        BasicRequests.__init__(self)
        self._curlshare = pycurl.CurlShare()
        self._curlshare.setopt(pycurl.SH_SHARE, pycurl.LOCK_DATA_DNS)
        self._curlshare.setopt(pycurl.SH_SHARE, pycurl.LOCK_DATA_COOKIE)

    def _new_request_worker(self):
        return CurlReq(self._curlshare)

    def _do_requests(self, url, **kwargs):
        rv = BasicRequests._do_requests(self, url, **kwargs)
        # TODO: replace SimpleCookie with someone better.
        if rv is not None:
            curlckjar = getattr(self._curltls, 'cookies', None)
            if curlckjar is None:
                curlckjar = CurlCookieJar()
            curlckjar.add_list(rv.cookies)
            setattr(self._curltls, 'cookies', curlckjar)
        return rv

    def reset_session(self):
        cs = pycurl.CurlShare()
        cs.setopt(pycurl.SH_SHARE, pycurl.LOCK_DATA_DNS)
        cs.setopt(pycurl.SH_SHARE, pycurl.LOCK_DATA_COOKIE)
        self._curlshare = cs
        curl = self._new_request_worker()
        setattr(self._curltls, 'curl', curl)

    def get_cookie(self, cookiename, defaultv='', domain='', path='/'):
        curlckjar = getattr(self._curltls, 'cookies', None)
        if curlckjar is None:
            raise RuntimeError("No cookies in curltls")
        ck = curlckjar.get_cookie(domain, path, cookiename)
        if ck is None:
            return defaultv
        else:
            return ck.value

    def _boolv_(self, v):
        if v is False or v is None or v is 0:
            return "FALSE"
        return "TRUE"

    def add_cookie(self, domain, name, value, domain_specified="?", path="/", secure="FALSE", expires=0):
        if domain_specified == '?':
            if domain[0:1] == '.':
                domain_specified = "TRUE"
            else:
                domain_specified = "FALSE"
        domain_specified = self._boolv_(domain_specified)
        secure = self._boolv_(secure)
        if expires is None:
            expires = 0

        curl = getattr(self._curltls, 'curl', None)
        if curl is None:
            curl = self._new_request_worker()
            setattr(self._curltls, 'curl', curl)
        ck_ = [domain, domain_specified, path, secure, str(expires), name, value]
        curl.curl.setopt(pycurl.COOKIELIST, "\t".join(ck_))

        curlckjar = getattr(self._curltls, 'cookies', None)
        if curlckjar is not None:
            curlckjar._add_cookie(domain, name, value, domain_specified, path, secure, expires)

    def add_cookie_line(self, domain, cookie_line):
        curl = getattr(self._curltls, 'curl', None)
        if curl is None:
            curl = self._new_request_worker()
            setattr(self._curltls, 'curl', curl)
        if re.search(r';\s*domain\s*=', cookie_line, re.I):
            # ignore the domain argument.
            pass
        else:
            assert isinstance(domain, str) or isinstance(domain, unicode)
            domain = re.sub(r'.*?@', '', domain)
            domain = re.sub(r':.*', '', domain)
            assert domain != ''
            if re.search(r';', cookie_line):
                cookie_line = re.sub(';', '; domain=%s;' % domain, cookie_line)
            else:
                cookie_line = cookie_line + ('; domain=%s;' % domain)

        if cookie_line[0:11] == "Set-Cookie:":
            curl.curl.setopt(pycurl.COOKIELIST, cookie_line)
        else:
            curl.curl.setopt(pycurl.COOKIELIST, "Set-Cookie: " + cookie_line)

        curlckjar = CurlCookieJar()
        setattr(self._curltls, 'cookies', curlckjar)
        curlckjar.add_list(curl.curl.getinfo(pycurl.INFO_COOKIELIST))
