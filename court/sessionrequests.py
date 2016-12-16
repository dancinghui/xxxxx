#!/usr/bin/env python
# -*- coding:utf8 -*-
import abc
import pycurl
import re
import threading

from spider.curlcookie import CurlCookieJar
from spider.httpreq import BasicRequests, CurlReq


class AbstractSessionRequests(BasicRequests):
    def __init__(self):
        BasicRequests.__init__(self)

    @abc.abstractmethod
    def _new_request_worker(self):
        raise NotImplementedError()

    @staticmethod
    def _new_curl_share():
        curlshare = pycurl.CurlShare()
        curlshare.setopt(pycurl.SH_SHARE, pycurl.LOCK_DATA_DNS)
        curlshare.setopt(pycurl.SH_SHARE, pycurl.LOCK_DATA_COOKIE)
        return curlshare

    @abc.abstractmethod
    def _reset_curl_share(self):
        raise NotImplementedError()

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
        self._reset_curl_share()
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


class ETOSSessionRequests(AbstractSessionRequests):
    '''
    each thread use one session
    session do not share between threads
    '''

    def __init__(self):
        super(ETOSSessionRequests, self).__init__()
        self.__curlshare = threading.local()

    def _new_request_worker(self):
        curlshare = getattr(self.__curlshare, 'curl', None)
        if curlshare is None:
            curlshare = AbstractSessionRequests._new_curl_share()
            setattr(self.__curlshare, 'curl', curlshare)
        return CurlReq(curlshare)

    def _reset_curl_share(self):
        curlshare = AbstractSessionRequests._new_curl_share()
        setattr(self.__curlshare, 'curl', curlshare)


class RedirectCurlReq(CurlReq):
    def _inner_reset(self):
        c = super(RedirectCurlReq, self)._inner_reset()

        c.setopt(pycurl.MAXREDIRS, 20)

        return c


class ATOSSessionRequests(AbstractSessionRequests):
    """threads share one session """

    def __init__(self):
        super(ATOSSessionRequests, self).__init__()
        self.__curlshare = AbstractSessionRequests._new_curl_share()

    def _new_request_worker(self):
        return RedirectCurlReq(self.__curlshare)

    def _reset_curl_share(self):
        self.__curlshare = AbstractSessionRequests._new_curl_share()


class ComplexSessionRequests(AbstractSessionRequests):
    '''
    multiple threads use multiple sessions
    '''
    pass
