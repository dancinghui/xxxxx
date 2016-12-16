#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys

sys.path.append("..")
from ipin.crawler.mock import MockEnv
from ipin.rpc.client_factory.client_config import ClientConfig
from ipin.rpc.client_factory.client_factory import ClientFactory
from ipin.crawler.common import CommonConfig
from spider.httpreq import BasicRequests
import re

class IpinFactory:
    def _config(self):
        config = ClientConfig()
        cls = CommonConfig
        urlIndexAddr = os.getenv(cls.URL_INDEX_KEY)
        if not urlIndexAddr:
            raise ValueError("miss env {}".format(cls.URL_INDEX_KEY))
        config.urlIndexConfig.addrList = urlIndexAddr.split(",")

        pageStoreAddr = os.getenv(cls.PAGE_STORE_KEY)
        if not pageStoreAddr:
            raise ValueError("miss env {}".format(cls.PAGE_STORE_KEY))
        config.pageStoreConfig.addrList = pageStoreAddr.split(",")

        proxyMgrAddr = os.getenv(cls.PROXY_MGR_KEY)
        if not proxyMgrAddr:
            raise ValueError("miss env {}".format(cls.PROXY_MGR_KEY))
        config.proxyMgrConfig.addrList = proxyMgrAddr.split(",")

        crawlerMgrAddr = os.getenv(cls.CRAWLER_MGR_KEY)
        if not crawlerMgrAddr:
            raise ValueError("miss env {}".format(cls.CRAWLER_MGR_KEY))
        config.crawlerMgrConfig.addrList = crawlerMgrAddr.split(",")

        querySetAddr = os.getenv(cls.QUERY_SET_KEY)
        if not querySetAddr:
            raise ValueError("miss env {}".format(cls.QUERY_SET_KEY))
        config.querySetConfig.addrList = querySetAddr.split(",")

        eventCollectAddr = os.getenv(cls.EVENT_COLLECT_KEY)
        if not eventCollectAddr:
            raise ValueError("miss env {}".format(cls.EVENT_COLLECT_KEY))
        config.eventCollectConfig.addrList = eventCollectAddr.split(",")
        return config

    def __init__(self):
        MockEnv.setUrlIndexAddr("192.168.1.81:9988")
        MockEnv.setPageStoreAddr("192.168.1.81:9989")
        MockEnv.setProxyMgrAddr("183.56.160.174:9931")
        MockEnv.setCrawlerMgrAddr("192.168.1.81:9934")
        MockEnv.setQuerySetAddr("192.168.1.81:9997")
        MockEnv.setEventCollectAddr("192.168.1.81:9984")
        config = self._config()
        factory = ClientFactory(config)
        self._urlIndexClient = factory.getUrlIndexClient()
        self._pageStoreClient = factory.getPageStoreClient()
        self._proxyMgrClient = factory.getProxyMgrClient()
        self._crawlerMgrClient = factory.getCrawlerMgrClient()
        self._querySetClient = factory.getQuerySetClient()
        self._eventCollectClient = factory.getEventCollectClient()
    def getProxyList(self):
        prs = self._proxyMgrClient.listAllProxy()
        oprs = []
        for p in prs:
            oprs.append({'host':p.host, 'port':p.port, 'password':p.password})
        return oprs
    def genRequestsParam(self,proxy):
        auth = None
        if proxy.get('password'):
            auth = ('PROXY_PASSWORD', proxy.get('password'))
        hostport = "%s:%s" % (proxy.get('host') , proxy.get('port'))
        proxies = {'http':'http://'+hostport, 'https':'https://'+hostport }
        return (auth, proxies)
    def genTinyProxy(self, proxy):
        hostport = "%s:%s" % (proxy.get('host') , 18888)
        proxies = {'http':'http://ipin:ipin1234@'+hostport+"/", 'https':'https://ipin:ipin1234@'+hostport+"/" }
        return (hostport+":ipin:ipin1234", proxies)

def find_ipin_proxy():
    ff = IpinFactory()
    prs =  ff.getProxyList()
    s = BasicRequests()
    #print json.dumps(prs, ensure_ascii=0).encode('utf-8')
    res = {}
    for p in prs:
        print "trying", p
        auth,proxies = ff.genRequestsParam(p)
        con = s.request_url("http://ip.cn/", auth=auth, proxies=proxies, timeout=6)
        if con is None:
            continue
        m = re.search("<code>(.*?)</code>", con.text)
        if m:
            sys.stderr.write("%s %s\n" % ( p['host'], m.group(1) ))
            res[m.group(1)] = "%s:%s:%s" % (p.get('host'), p.get('port'), p.get('password'))
        p2, proxies = ff.genTinyProxy(p)
        print proxies
        con = s.request_url("http://ip.cn/", proxies=proxies, timeout=5)
        if con is None:
            continue
        m = re.search("<code>(.*?)</code>", con.text)
        if m:
            sys.stderr.write("%s %s\n" % ( p['host'], m.group(1) ))
            res[m.group(1)] = p2
    print "\n".join(res.values())

if __name__ == "__main__":
    find_ipin_proxy()
