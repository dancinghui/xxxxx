#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from lxml import html
import json
import openpyxl


url_test = 'http://jiaoyu.baidu.com/CollegeBws/collegeFilter?mode=0&page=%d&cityid=0&city=&sessionID=1459241436843574699&originQuery=&sid=0&subqid=1459241436843574699&srcid=0&qid=1459241436843574699&pvid=1459241436843574699&pssid=0&tn=NONE&zt=self&provinceId=0'
form_data = {
    'mode': 0,
    'page': 1,
    'cityid': 0
}
wb = openpyxl.Workbook()
ws = wb.active
ws.append([u'高校名称', u'所属地', u'院校类型', u'院校属性', u'院校属性', u'院校属性'])
for i in xrange(1, 139):
    url = url_test % i
    res = requests.get(url)
    json_dict = json.loads(res.content.decode("utf-8-sig"))
    content = json_dict['data']['tpl']['college_list']
    doc = html.fromstring(content)
    school_name = doc.xpath('///tbody/tr')
    school_list = doc.xpath('//tbody/tr')
    for each_tr in school_list:
        lis = []
        lis.append(i.xpath('./td[2]/a/text()')[0].strip())
        lis = lis + [j.strip() for j in each_tr.xpath('./td/text()')][3:8]
        ws.append(lis)
wb.save('baidu_edu_result.xlsx')
