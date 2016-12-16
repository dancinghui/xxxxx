#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.httpreq import BasicRequests
from spider.genquery import GenQueries,GQDataHelper
import time

dqs = [["010","北京","BEIJING"],
["020","上海","SHANGHAI"],
["030","天津","TIANJIN"],
["040","重庆","CHONGQING"],
["050","广东省","GUANGDONG"],
["400","非洲","Africa"],]

compscale = [ [ '010', '1-49人', '1-49' ],
    [ '020', '50-99人', '50-99' ],
    [ '030', '100-499人', '100-499' ],
    [ '080', '10000人以上', 'More than 10000' ] ]

nc = {
'a':{'desc':'apple', 'value':'apple', 'children':{'b':{'value':'a.blue'}, 'r':{'value':'a.red'}} },
'b':{'desc':'pear', 'value':'pear', 'children':{'b':{'value':'p.blue'}, 'r':{'value':'p.red'}, 'B':{'value':'p.Black'}} }
}

class TestQuery(GenQueries):
    def __init__(self, thcnt):
        GenQueries.__init__(self, thcnt)
        self._name = "test_set"
    def init_conditions(self):
        GQDataHelper.add(self, 'nc', nc)
        GQDataHelper.add(self, 'nc2', nc)
        GQDataHelper.add(self, 'dqs', dqs)
        GQDataHelper.add(self, 'compscale', compscale)
    def need_split(self, url, level, last):
        print url,level, last
        if level>1:
            return False
        return True
    def process_failed_url(self, url):
        return True

def test_search():
    a = BasicRequests()
    while True:
        data = {'docids1':"1,2,3,4,5,6,6109234,6110168,11070364", "keywords":"武汉"}
        con = a.request_url("http://localhost:4096/search?hehe=1", data=data)
        if con is not None:
            print con.code, con.text
        time.sleep(10)



if __name__ == "__main__":
    test_search()
    g = TestQuery(1)
    g.run()
