#!/usr/bin/env python
# -*- coding:utf8 -*-
import re

from court.save import CourtStore, LinkDb


class WenshuCourtStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'ws_court',dburl='mongodb://localhost/wsw')

    def extract_content(self):
        m = re.search(r'<input type="hidden" id="hidCaseInfo" value=\'([^\']*)\'', self.get_cur_doc().cur_content)
        if m:
            return m.group(1)
        else:
            return self.get_cur_doc().cur_content

    def parse_time(self):
        m = re.search(ur'发布日期：(\d-\d-\d)', self.get_cur_doc().cur_content)
        if m:
            return m.group(1)
        else:
            return None


class WenshuLinkDb(LinkDb):
    def __init__(self, channel='ws_link', db='wsw', dbUrl="mongodb://localhost/wsw"):
        LinkDb.__init__(self, channel, db, dbUrl)
