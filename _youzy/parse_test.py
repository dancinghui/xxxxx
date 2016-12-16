#!/usr/bin/env python
# -*- coding:utf8 -*-
from lxml import html
import csv



def get_doc(file_name):
    with open(file_name, 'rb') as f:
        return f.read()

def parse(text):
    #doc = html.fromstring(get_doc("daxue.html"))
    #print "type=========",type(doc)
    doc = html.fromstring(text)
    part1_template ='{}\t\t\t\t\t{}\t\t\t\t\t{}\t\t\t\t\t{}'
    part1_list = []
    els = doc.xpath('//select[@id]/option[@selected]')
    for el in els:
        print el
        part1_list.append(el.text_content().encode('utf-8'))

    print part1_template.format(*part1_list)
    print "================================================================================="


    header_template = '{}\t\t\t\t\t{}\t\t\t\t\t{}\t\t\t\t\t{}\t\t\t\t\t{}'
    header_list = []

    headers = doc.xpath('//table[@class="table table-hover table-bordered table-th-gray"]/thead/tr/th')
    for header in headers:
        style = header.attrib.get('style', None)
        if style:
            continue

        header_list.append(header.text_content().encode('utf-8'))

    print header_template.format(*header_list)

    bodys = doc.xpath('//table[@class="table table-hover table-bordered table-th-gray"]/tbody')

    td_list = []

    for body in bodys:
        style = body.attrib.get('style', None)
        if not style:
            trs = body.xpath('tr')

            for tr in trs:
                tds = tr.xpath('td')
                for td in tds:
                    style = td.attrib.get('style', None)
                    if style:
                        continue
                    td_list.append(td.text_content().encode('utf-8'))
                print header_template.format(*td_list)

fixed = ['学校名称','类型','省份','批次','文理科']
cfcolumn = ['年份','招生批次','选测等级','最高分','最低分','平均分','录取数']
def parseTest():
    doc = html.fromstring(get_doc("cf.html"))
    fixed_line = []
    name = doc.xpath('//div[@class="box"]/h2')
    if len(name) < 1:
        print "---finish---"
        return False
    fixed_line.append(name[0].text_content().encode('utf-8'))
    column_fixed = fixed+cfcolumn
    cf = ''
    for a in column_fixed:
        cf+=a+','
    print "column:",cf
    print "#####################option##########################"
    options = doc.xpath('//select[@id]/option[@selected]')
    for option in options:
        fixed_line.append(option.text_content().encode('utf-8'))
    f = ''
    for i in fixed_line:
       f+=i+","
    print '固定描述:',f

    print "#####################head-column##########################"
    headers = doc.xpath('//table[@class="table table-hover table-bordered table-th-gray"]/thead/tr/th')
    header_column= []
    for header in headers:
        # style = header.attrib.get('style', None)
        # if style:
        #     continue
        header_column.append(header.text_content().encode('utf-8'))
    header_c = ''
    for h in header_column:
        header_c+=h+","
    print "表  头:",header_c

    print "#####################body##########################"
    bodys = doc.xpath('//table[@class="table table-hover table-bordered table-th-gray"]/tbody')
    body_list = []
    for body in bodys:
            style = body.attrib.get('style', None)
            if not style:
                trs = body.xpath('tr')
                for tr in trs:
                    tds = tr.xpath('td')
                    td_list = []
                    for td in tds:
                        #style = td.attrib.get('style', None)
                        #if style:
                        #    continue
                        td_list.append(td.text_content().encode('utf-8'))
                    body_list.append(td_list)

    handle_line(body_list,header_column)
    print body_list
    for tr in body_list:
        s = ''
        for td in tr :
            s+=td+','
        print s
    write_csv(fixed_line,body_list)


def handle_line(body_list,header_column):
    for tr in body_list:
        for h in cfcolumn:
            if not header_column.__contains__(h):
                index = cfcolumn.index(h)
                tr.insert(index,'null')

def write_csv(fixed_line,body_list):
    writer = csv.writer(open('test.csv','wb'))
    writer.writerow(fixed+cfcolumn)
    for tr in body_list:
        line = fixed_line+tr
        writer.writerow(line)

# def testcsv():
#     f = open('test.csv','wb')
#     writer.writerow(['Column1', 'Column2', 'Column3'])
#     lines = [range(3) for i in range(5)]
#     for line in lines:
#         print line
#         writer.writerow(line)

if __name__ == '__main__':
    parseTest()
    #testcsv()
    # line = ['年份1','专业名称1','招生批次1','最高分1','最低分1','录取数1']
    # l =    ['年份','专业名称','招生批次','最高分','最低分','录取数']
    # #pfc   ['年份','专业名称','招生批次','选测等级','最高分','最低分','平均分','录取数']
    # for h in pfcolumn:
    #     if not l.__contains__(h):
    #         index = pfcolumn.index(h)
    #         line.insert(index,'null')
    #
    # s = ''
    # for i in line:
    #     s+=i+','
    # print s

