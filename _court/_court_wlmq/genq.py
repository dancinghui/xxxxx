#!/usr/bin/env python
# -*- coding:utf8 -*-
import json
import re

from court.genq import PageGenQueries


class WLMQGenQuery(PageGenQueries):
    def __init__(self,saver='jobs'):
        super(WLMQGenQuery, self).__init__(saver)
        self.page_pattern = ur'<a id="([^"]*?)" title="最后一页" [^>]*javascript:__doPostBack[^>]*>(\d+)<\/a>'
        self.page_index = 2
        self.target_index = 1

        self.form_pattern = r'<form[^>]*id="form1">.*<\/form>'
        self.input_pattern = r'<input[^>]*>'
        self.base_urls = [
            'http://222.82.211.38:8002/publiclist.aspx?fymc=&ajlb=9715918889E6905BB9AD59B88AA07AC2&type=4F813CCBFE6A7793',
            'http://221.181.38.141:8002/publiclist.aspx?fymc=&ajlb=9715918889E6905BB9AD59B88AA07AC2&type=4F813CCBFE6A7793',
            'http://211.138.34.59:8002/publiclist.aspx?fymc=&ajlb=9715918889E6905BB9AD59B88AA07AC2&type=4F813CCBFE6A7793',
            'http://www.wlmqgxqcourt.org:8002/publiclist.aspx?fymc=&ajlb=9715918889E6905BB9AD59B88AA07AC2&type=4F813CCBFE6A7793']
        self.ignore_inputs = [u'tbGoPage']

if __name__ == '__main__':
    job = WLMQGenQuery()
    job.run()
