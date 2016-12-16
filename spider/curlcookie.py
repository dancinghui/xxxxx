#!/usr/bin/env python
# -*- coding:utf8 -*-
from cookielib import CookieJar, Cookie, DefaultCookiePolicy

class MyCookiePolicy(DefaultCookiePolicy):
    def __init__(self):
        DefaultCookiePolicy.__init__(self)
    def return_ok_expires(self, cookie, request):
        if cookie.expires == 0:
            return True
        if cookie.is_expired(0):
            return False
        return True

class CurlCookieJar(CookieJar):
    class FakeReq(object):
        def __init__(self, domain, path):
            self._domain = domain
            self._path = path
        def get_full_url(self):
            return "https://%s%s" % (self._domain, self._path)
        def is_unverifiable(self):
            return False
        def get_header(self, name, defv=''):
            if name.lower() == 'host':
                return self._domain
            return defv
        def get_type(self):
            return 'https'

    def __init__(self, ignore_expires=True, ignore_discard=True ):
        CookieJar.__init__(self, policy=MyCookiePolicy())
        self._ignore_expires = ignore_expires
        self._ignore_discard = ignore_discard

    def add_list(self, cks):
        if len(cks) is 0:
            return
        for ck in cks:
            if isinstance(ck, str):
                self.add_line(ck)
            elif isinstance(ck, unicode):
                self.add_line(ck.encode('utf-8'))
            elif isinstance(ck, Cookie):
                self.set_cookie(ck)
            else:
                raise RuntimeError("type error, support string list and cookie list.")
        return

    def add_line(self, line):
        domain, domain_specified, path, secure, expires, name, value = line.split('\t')
        return self._add_cookie(domain, name, value, domain_specified, path, secure, expires)

    def _add_cookie(self, domain, name, value, domain_specified="FALSE", path="/", secure="FALSE", expires=0):
        secure = (secure == "TRUE")
        domain_specified = (domain_specified == "TRUE")
        if name == "":
            # cookies.txt regards 'Set-Cookie: foo' as a cookie
            # with no name, whereas cookielib regards it as a
            # cookie with no value.
            name = value
            value = None

        initial_dot = domain.startswith(".")
        # assert domain_specified == initial_dot
        discard = False
        if expires == "":
            expires = None
            discard = True

        # assume path_specified is false
        c = Cookie(0, name, value,
                   None, False,
                   domain, domain_specified, initial_dot,
                   path, False,
                   secure,
                   expires,
                   discard,
                   None,
                   None,
                   {})
        if not self._ignore_discard and c.discard:
            #a session cookie
            #TODO deal with a session cookie
            pass
        if not self._ignore_expires and c.is_expired():
            #end of life, do not add it
            raise RuntimeError("the cookie's life ended, try add it in ignore_expires mod.")

        self.set_cookie(c)
        return

    def get_cookie(self, domain, path, cookie_name):
        rq = CurlCookieJar.FakeReq(domain, path)
        if len(domain) > 0:
            cookies = self._cookies_for_request(rq)
            for ck in cookies:
                if ck.name == cookie_name:
                    return ck
        else:
            #when there is no domain, also ignores path.
            for k1, v1 in self._cookies.items():
                for k2, v2 in v1.items():
                    if v2.has_key(cookie_name):
                        return v2[cookie_name]
        return None

    def get_value(self, cookie_domain, cookie_path, cookie_name):
        ck = self.get_cookie(cookie_domain, cookie_path, cookie_name)
        return ck.value

    def get_all_value(self, cookie_name):
        reslist=[]
        for k1, v1 in self._cookies.items():
            if v1 is not None:
                for k2, v2 in v1.items():
                    r = v2.get(cookie_name, None)
                    if r is not None:
                        reslist.append(r.value)

        if len(reslist) is 0:
            raise RuntimeError("No such cookie named '%s'" % cookie_name)
        if len(reslist) is 1:
            return reslist[0]
        return reslist

    def __str__(self):
        return self._cookies.__str__()


if __name__ == '__main__':
    ckjar = CurlCookieJar()
    ckjar.add_line(r'qichacha.com\tFALSE\t/\tFALSE\t0\tPHPSESSID\tqem1b4d95083nun7rjpbcrhod1')
    ckjar.add_list(r'qichacha.com\tFALSE\t/\tFevalALSE\t0\tPHPSESSID\tqem1b4d95083nun7rjpbcrhod1,qichacha.com\tFALSE\t/\tFALSE\t0\tSERVERID\ta66d7d08fa1c8b2e37dbdc6ffff82d9e|1450144620|1450144620'.split(","))
    print ckjar.get_value("qichacha.com", "/", "PHPSESSID")