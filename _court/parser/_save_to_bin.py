#!/usr/bin/env python
# -*- coding:utf8 -*-
import abc
import codecs
import re
import threading

from HTMLParser import HTMLParser

import datetime
import pymongo
import sys

from court.save import CourtStore, LinkSaver
from court.util import extract_flws_ah, Main
from gkutils.parser import CWPParser, CAPParser
from spider.savebin import BinSaver, BinReader


class CourtParser(CWPParser):
    def __init__(self, channel, dist_file, name, parser):
        CWPParser.__init__(self, channel, name)
        self.bin_writer = BinSaver(dist_file)
        self.parser = parser

    def process_child_item(self, item):
        print 'saving', item['name']
        self.bin_writer.append(item['name'], item['value'])

    def parse_item(self, page):
        res = self.parser.parse(page['indexUrl'], page['content'][1])
        if res:
            return [res]
        return []


class CourtCAPParser(CAPParser):
    def __init__(self, channel, dist_file, name, parser):
        CAPParser.__init__(self, channel, name)
        self.bin_writer = BinSaver(dist_file)
        self.parser = parser

    def parse(self, page):
        res = self.parser.parse(page['indexUrl'], page['content'][1])
        if res:
            return [res]
        return []

    def pre_save(self, saver):
        pass

    def on_save(self, items):
        for item in items:
            print 'saving', item['name']
            self.bin_writer.append(item['name'], item['value'])


class ChannelParser:
    def __init__(self, name='failed.txt', mode='a'):
        self.failed_saver = LinkSaver(name, mode)
        pass

    @abc.abstractmethod
    def parse(self, jid, content):
        raise NotImplementedError('virtual function called')

    def on_failed(self, message):
        self.failed_saver.add(message)


class FoshanChannel(ChannelParser):
    def __init__(self, name='failed.fs.txt', mode='a'):
        ChannelParser.__init__(self, name, mode)

    def parse(self, jid, content):
        text = content

        text = re.sub(r'(<[^>]*>)', '',
                      re.sub(r'.*</head>', '', re.sub(r'(<[^>/]*>)|(&nbsp;)', '', text), 0, re.S)).strip()
        # if 'Windows' in text:
        #     text = re.sub(r'^.*?}', '', text).strip()
        ah = extract_flws_ah(text)
        if not ah:
            ah = re.search(
                r'\s.*?((刑)|(民)|(行)|(执)|(赔)|(财)|(商)|(移)|(调)|(协)|(司)|(认)|(保)|(外)|(送)|(请)|(清)|(破)).*?[\d\s×Xx-]+?号', text)
            if ah:
                ah = ah.group().strip()
            else:
                ah = re.search(r'书\n(.*?(号)?)\n', text, re.S)
                if ah:
                    ah = ah.group(1).strip()
                else:
                    print 'cannot find an hao', jid
                    self.on_failed('ah,%s' % jid)
                    return
        return {'name': ah, 'value': '标题:%s\n%s\n' % (ah, text)}


class SzChannel(ChannelParser):
    def __init__(self, name='failed.sz.txt', mode='a'):
        ChannelParser.__init__(self, name, mode)

    def parse(self, jid, content):
        text = content

        text = re.sub(r'(<[^>]*>)', '',
                      re.sub(r'.*</head>', '', re.sub(r'(<[^>/]*>)|(&nbsp;)', '', text), 0, re.S)).strip()
        # if 'Windows' in text:
        #     text = re.sub(r'^.*?}', '', text).strip()
        ah = extract_flws_ah(text)
        if not ah:
            ah = re.search(
                r'\s.*?((刑)|(民)|(行)|(执)|(赔)|(财)|(商)|(移)|(调)|(协)|(司)|(认)|(保)|(外)|(送)|(请)|(清)|(破)).*?[\d\s×Xx-]+?号', text)
            if ah:
                ah = ah.group().strip()
            else:
                print 'cannot find an hao', jid
                self.on_failed('ah,%s' % jid)
                return
        return {'name': ah, 'value': '标题:%s\n%s\n' % (ah, text)}


class HzChannel(ChannelParser):
    def __init__(self, name='failed.hz.txt', mode='a'):
        ChannelParser.__init__(self, name, mode)

    def parse(self, jid, content):
        text = content

        text = re.sub(r'(<[^>]*>)|(&nbsp;)', '', re.sub(r'</p>', '\n', text), 0, re.S).strip()
        # if 'Windows' in text:
        #     text = re.sub(r'^.*?}', '', text).strip()
        ah = extract_flws_ah(text)
        if not ah:
            ah = re.search(r'\s.*?(刑|民|行|执|赔|财|商|移|调|协|司|认|保|外|送|请|清|破|催).*[\d\s×]+?号', text)
            if ah:
                ah = ah.group().strip()
            else:
                ah = re.search(r'(\(|(（))\d{4}(\)|(）))\s*浙\s*\d+.*?(刑|民|行|执|赔|财|商|移|调|协|司|认|保|外|送|请|清|破|催|督).*?(号)?',
                               text)
                if ah:
                    ah = ah.group().strip()
                else:
                    print 'cannot find an hao', jid
                    self.on_failed('ah,%s' % jid)
                    return
        return {'name': ah, 'value': '标题:%s\n%s\n' % (ah, text)}


class BjChannel(ChannelParser):
    def __init__(self, name='failed.txt', mode='a'):
        ChannelParser.__init__(self, name, mode)
        self.parser = HTMLParser()

    def parse(self, jid, content):
        text = re.search(r'unescape\("(.*)"\);', content)
        title = re.search(r'<h3 class="h3_22_m_blue">(.*?)</h3>', content)
        if text:
            text = text.group(1).strip()
            ts = eval('u\"%s\"' % text)
            text = ts
            text = re.sub(r'(<[^>]*>)', '',
                          re.sub(r'.*</head>', '', re.sub(r'(<[^>/]*>)|(&nbsp;)', '', text), 0, re.S)).strip()
            # if 'Windows' in text:
            #     text = re.sub(r'^.*?}', '', text).strip()
            ah = extract_flws_ah(text)
            if not ah:
                ah = re.search(ur'\s.*?(刑|民|行|执|赔|财|商|移|调|协|司|认|保|外|送|请|清|破).*[\d\s×Xx]+?号', text)
                if ah:
                    ah = ah.group().strip()
                else:
                    ah = re.search(ur'(\(|（)\d{4}(\)|）)京[\d\s×]+字第[\d\s×]+号', text)
                    if ah:
                        ah = ah.group().strip()
                    else:
                        print 'cannot find an hao', jid
                        self.on_failed('ah,%s' % jid)
                        return
            return {'name': ah.encode('utf-8'), 'value': '标题:%s\n%s\n' % (title.group(1), text.encode('utf-8'))}


class CqnaChannel(ChannelParser):
    def __init__(self, name='failed.cqna.txt', mode='a'):
        ChannelParser.__init__(self, name, mode)

    def parse(self, jid, content):
        text = re.search(r'</STYLE>.*</div>', content, re.S)
        title = re.search(r'>([^>]*)</h2>', content)
        if text:
            text = text.group().strip()
            text = re.sub(r'(<[^>]*>)', '', text.replace('&nbsp;', ' '), 0, re.S).strip()
            # if 'Windows' in text:
            #     text = re.sub(r'^.*?}', '', text).strip()
            ah = extract_flws_ah(text)
            if not ah:
                ah = re.search(
                    r'\s.*?((刑)|(民)|(行)|(执)|(赔)|(财)|(商)|(移)|(调)|(协)|(司)|(认)|(保)|(外)|(送)|(请)|(清)|(破)).*?[\d\s×Xx-]+?号',
                    text)
                if ah:
                    ah = ah.group().strip()
                else:
                    print 'cannot find an hao', jid
                    self.on_failed('ah,%s' % jid)
                    return
            return {'name': ah, 'value': '标题:%s\n%s\n' % (title.group(1), text)}


class ShChannel(ChannelParser):
    def __init__(self, name='failed.sh.txt', mode='a'):
        ChannelParser.__init__(self, name, mode)

    def parse(self, jid, content):
        text = re.search(r'<div id="wsTable">.*?</table>', content, re.S)
        if not text:
            text = re.search(r'<div class="list_a">.*?</div>', content, re.S)
        ah = re.search(r'var ah="([^"]*)";', content)
        if not ah:
            ah = re.search(r'<td colspan="2" width="80%" align="right">(.*?)</td>', content)
        if text:
            text = text.group().strip()
            text = re.sub(r'(<[^>]*>)|(&nbsp;)', '', text, 0, re.S).strip()
            # if 'Windows' in text:
            #     text = re.sub(r'^.*?}', '', text).strip()
            if ah:
                ah = ah.group(1).strip()
            else:
                ah = extract_flws_ah(text)
                if not ah:
                    ah = re.search(
                        r'\s.*?((刑)|(民)|(行)|(执)|(赔)|(财)|(商)|(移)|(调)|(协)|(司)|(认)|(保)|(外)|(送)|(请)|(清)|(破)).*?[\d\s×Xx-]+?号',
                        text)
                    if ah:
                        ah = ah.group().strip()
                    else:
                        print 'cannot find an hao', jid
                        self.on_failed('ah,%s' % jid)
                        return
            if len(ah) > 50:
                print 'long ah', jid
            return {'name': ah, 'value': '标题:%s\n%s\n' % (ah, text)}
        else:
            print 'cannot find content', jid
            self.on_failed('co,%s' % jid)


class CcChannel(ChannelParser):
    def __init__(self, name='failed.cc.txt', mode='a'):
        ChannelParser.__init__(self, name, mode)

    def parse(self, jid, content):
        text = re.search(r"<div class='doc_area'>.*</tr>", content)
        title = re.search(r"<div class='ws_title'>(.*?)</div>", content)
        ah = re.search(r"<p class='ws_num'>(.*?)</p>", content)
        if text:
            text = text.group().strip()
            text = re.sub(r'(<[^>]*>)', '', text.replace('</p>', '\n'), 0, re.S).strip()
            # if 'Windows' in text:
            #     text = re.sub(r'^.*?}', '', text).strip()
            if not ah:
                ah = extract_flws_ah(text)
                if not ah:
                    ah = re.search(
                        r'\s.*?((刑)|(民)|(行)|(执)|(赔)|(财)|(商)|(移)|(调)|(协)|(司)|(认)|(保)|(外)|(送)|(请)|(清)|(破)).*?[\d\s×Xx-]+?号',
                        text)
                    if ah:
                        ah = ah.group().strip()
                    else:
                        print 'cannot find an hao', jid
                        self.on_failed('ah,%s' % jid)
                        return
            else:
                ah = ah.group(1)
            return {'name': ah, 'value': '标题:%s\n%s\n' % (title.group(1), text)}
        else:
            print 'cannot find content', jid
            self.on_failed('co,%s' % jid)


class DgChannel(ChannelParser):
    def __init__(self, name='failed.dg.txt', mode='a'):
        ChannelParser.__init__(self, name, mode)

    def parse(self, jid, content):
        ah = extract_flws_ah(content)
        if not ah:
            ah = re.search(
                r'\s.*?((刑)|(民)|(行)|(执)|(赔)|(财)|(商)|(移)|(调)|(协)|(司)|(认)|(保)|(外)|(送)|(请)|(清)|(破)).*?[\d\s×Xx-]+?号',
                content)
            if ah:
                ah = ah.group().strip()
            else:

                print 'cannot find an hao', jid
                self.on_failed('ah,%s' % jid)
                return
        return {'name': ah, 'value': '标题:%s\n%s\n' % (ah, content)}


class WlmqChannel(ChannelParser):
    def __init__(self, name='failed.wlmq.txt', mode='a'):
        ChannelParser.__init__(self, name, mode)

    def parse(self, jid, content):
        ah = extract_flws_ah(content)
        if not ah:
            ah = re.search(
                r'\s.*?((刑)|(民)|(行)|(执)|(赔)|(财)|(商)|(移)|(调)|(协)|(司)|(认)|(保)|(外)|(送)|(请)|(清)|(破)).*?[\d\s×Xx-]+?号',
                content)
            if ah:
                ah = ah.group().strip()
            else:
                ls = content.split('\n', 9)
                if len(ls) <= 8:
                    print 'cannot find an hao', jid
                    self.on_failed('ah,%s' % jid)
                    return
                ah = ls[7]
                if ah == '':
                    ah = ls[8]
                    if ah == '':
                        print 'cannot find an hao', jid
                        self.on_failed('ah,%s' % jid)
                        return
        return {'name': ah, 'value': '标题:%s\n%s\n' % (ah, content)}


class SzytChannel(ChannelParser):
    def __init__(self, name='failed.szyt.txt', mode='a'):
        ChannelParser.__init__(self, name, mode)

    def parse(self, jid, content):
        ah = extract_flws_ah(content)
        if not ah:
            ah = re.search(
                r'\s.*?((刑)|(民)|(行)|(执)|(赔)|(财)|(商)|(移)|(调)|(协)|(司)|(认)|(保)|(外)|(送)|(请)|(清)|(破)).*?[\d\s×Xx-]+?号',
                content)
            if ah:
                ah = ah.group().strip()
            else:
                print 'cannot find an hao', jid
                self.on_failed('ah,%s' % jid)
                return
        ah = ah
        return {'name': ah, 'value': '标题:%s\n%s\n' % (ah, content)}


class GxChannel(ChannelParser):
    def __init__(self, name='failed.gx.txt', mode='a'):
        ChannelParser.__init__(self, name, mode)

    def parse(self, jid, content):
        text = eval(content.replace('null', 'None'))
        doc = text['FileContent']
        doc = re.sub(r'<[^>]*>', '', re.sub(r'</\w+>', '\n', doc)).strip()
        ah = extract_flws_ah(doc)
        if not ah:
            ah = re.search(
                r'\s.*?((刑)|(民)|(行)|(执)|(赔)|(财)|(商)|(移)|(调)|(协)|(司)|(认)|(保)|(外)|(送)|(请)|(清)|(破)).*?[\d\s×Xx-]+?号', doc)
            if ah:
                ah = ah.group().strip()
            else:
                ah = re.search(r'书\n(.*?(号)?)\n', doc, re.S)
                if ah:
                    ah = ah.group(1).strip()
                else:
                    print 'cannot find an hao', jid
                    self.on_failed('ah,%s' % jid)
                    return
        # ah = re.search(r'书\n(.*?(号)?)\n', doc, re.S)
        # if ah:
        #     ah = ah.group(1).strip()
        # else:
        #     print 'cannot find an hao', jid
        #     self.on_failed('ah,%s' % jid)
        #     return
        return {'name': ah, 'value': '标题:%s\n%s\n' % (ah, doc)}


def save_bj_word(url, ch):
    m = re.search('^(.*):\/\/(.*)', url)
    channel = m.group(1)
    docid = m.group(2)
    print channel
    dburl = 'mongodb://root:helloipin@localhost/'
    client = pymongo.MongoClient(dburl)
    c = client.admin['page_store_' + channel]
    page = c.find({'indexUrl': url})
    count = 0
    success = False
    for p in page:
        count += 1
        print p['pageContentPath']
        (ft, ofn, pos) = p['pageContentPath'].split('::')
        reader = BinReader(ofn)
        content = reader.readone_at(int(pos))
        print content[0]
        print content[1]
        print datetime.datetime.fromtimestamp(long(p['crawlerUpdateTime']) / 1000)
        res = ch.parse(p['indexUrl'], content[1])
        if res:
            print res['name'], docid
            success = True
            # print res['value']
        else:
            print 'failed', docid
    print 'count:', count
    return success


params = {
    'bj': {'channel': 'bj_court', 'name': 'bj', 'file': 'court.bin', 'parser': BjChannel()},
    'fs': {'channel': 'fs_court', 'name': 'fs', 'file': 'court.fs.bin', 'parser': FoshanChannel()},
    'dg': {'channel': 'dg_court', 'name': 'dg', 'file': 'court.dg.bin', 'parser': DgChannel()},
    'gx': {'channel': 'gx_court', 'name': 'gx', 'file': 'court.gx.bin', 'parser': GxChannel()},
    'sz': {'channel': 'sz_court', 'name': 'sz', 'file': 'court.sz.bin', 'parser': SzChannel()},
    'cc': {'channel': 'cc_court', 'name': 'cc', 'file': 'court.cc.bin', 'parser': CcChannel()},
    'wl': {'channel': 'wlmq_court', 'name': 'wlmq', 'file': 'court.wlmq.bin', 'parser': WlmqChannel()},
    'sh': {'channel': 'sh_court_2', 'name': 'sh', 'file': 'court.sh.bin', 'parser': ShChannel()},
    'hz': {'channel': 'hz_court', 'name': 'hz', 'file': 'court.hz.bin', 'parser': HzChannel()},
    'cq': {'channel': 'cqna_court', 'name': 'cqna', 'file': 'court.cqna.bin', 'parser': CqnaChannel()},
    # 'yt': {'channel': 'sz_yt_court', 'name': 'szyt', 'file': 'court.szyt.bin', 'parser': SzytChannel()},
}


def test_failed_url(index):
    ch = params[index]
    ff = 'failed.%s.txt' % ch['name']
    failed = open(ff, 'r')
    links = []
    for l in failed:
        links.append(l.strip())
    failed.close()
    failed = open(ff, 'w')
    for l in links:
        f = save_bj_word(l.split(',')[1], ch['parser'])
        if not f:
            failed.write(l + '\n')


def _dispatch():
    threads = []
    jobs = []
    for k, p in params.items():
        cp = CourtParser(p['channel'], p['file'], p['name'], p['parser'])
        t = threading.Thread(target=cp.run)
        threads.append(t)
        t.start()
        jobs.append(cp)
    for t in threads:
        t.join()


def run_one(index):
    p = params[index]
    job = CourtParser(p['channel'], p['file'], p['name'], p['parser'])
    job.run()


def run_one_cap(index):
    p = params[index]
    job = CourtCAPParser(p['channel'], p['file'], p['name'], p['parser'])
    job.run()


class MainRun(Main):
    def __init__(self):
        Main.__init__(self)
        self.seeds = 'failed.txt'
        self.mode = 'c'
        self.short_tag = 'm:i:h:o:v:'
        self.index = 1

    def handle(self, opts):
        for o, a in opts:
            if o in ('-h', '--help'):
                self.usage()
                sys.exit(1)
            elif o in ('-v', '--version'):
                self.version()
                sys.exit(0)
            elif o in ('-o', '--output'):
                self.output(a)
                sys.exit(0)
            elif o in ('-m', '--mode'):
                self.mode = a
            elif o in ('-i', '--index'):
                self.index = a
            else:
                print 'unhandled option'
                sys.exit(3)
        if 'a' == self.mode or 'all' == self.mode:
            _dispatch()
        elif 'o' == self.mode or 'one' == self.mode:
            if params.has_key(self.index):
                run_one(self.index)
            else:
                print 'invalid index:', self.index
        elif 'c' == self.mode or 'cap' == self.mode:
            if params.has_key(self.index):
                run_one_cap(self.index)
            else:
                print 'invalid index:', self.index
        elif 'f' == self.mode or 'fail' == self.mode:
            if params.has_key(self.index):
                test_failed_url(self.index)
            else:
                print 'invalid index:', self.index
        else:
            print 'unhandled mode', self.mode


if __name__ == '__main__':
    main = MainRun()
    main.main(sys.argv)
