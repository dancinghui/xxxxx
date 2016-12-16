#!/usr/bin/env python
# -*- coding:utf8 -*-
import datetime
import re

from court.save import CourtStore, LinkDb


class ShanghaiCourtStore(CourtStore):
    def __init__(self, channel='sh_court'):
        CourtStore.__init__(self, channel)

    def extract_content(self):
        m = re.search(r'<div id="wsTable">(.*?</table>)', self.get_cur_doc().cur_content, re.S)
        if m:
            return m.group(1)
        m = re.search(
            r'<table width="600" height="493"  border="0" cellpadding="0" cellspacing="0" class="style3">.*?</table>',
            self.get_cur_doc().cur_content, re.S)
        if m:
            return m.group()
        return self.get_cur_doc().cur_content


class ShanghaiSeedStore(CourtStore):
    def __init__(self):
        CourtStore.__init__(self, 'sh_seeds')


class ShanghaiLinkDb(LinkDb):
    def __init__(self, channel='sh_list'):
        LinkDb.__init__(self, channel)


class DateSpliter():
    @staticmethod
    def split(start, end):
        st = datetime.datetime.strptime(start, '%Y-%m-%d')
        et = datetime.datetime.strptime(end, '%Y-%m-%d')
        delta = et - st
        mid = st + datetime.timedelta(days=delta.days / 2)
        ms = mid.strftime('%Y-%m-%d')
        if delta.days == 1:
            return []
        return [[start, ms], [ms, end]]


if __name__ == '__main__':
    db = ShanghaiLinkDb('sh_link')
    seeds = db.export_seeds()
    for seed in seeds:
        print seed
