#!/usr/bin/env python
# -*- coding:utf8 -*-

import requests
import json
from lxml import html


city_req_url = "http://www.58.com/changecity.aspx?"
res = requests.get(city_req_url)

urls = ""

doc = html.fromstring(res.text)
els = doc.xpath('//dl[@id="clist"]/dd')
i = 0
for dd in els:
    hrefs = dd.xpath('a/@href')
    for href in hrefs:
        i += 1
        urls += '"' + href + '", '
        if i % 5 == 0:
            urls += '\n'

if urls[-1] == '\n':
    urls = urls[:-1]
else:
    urls = urls[:-2]

urls_result = 'urls=[' + urls + ']'

#########################################
#############  取行业信息  ################
##########################################

els = ["zplvyoujiudian", "jiazhengbaojiexin", "meirongjianshen", "zpjiudian", "zpwentiyingshi",
       "zpanmo", "zpjianshen", "renli", "siji", "zpguanli", "yewu", "kefu", "zpshangwumaoyi",
       "chaoshishangye", "zptaobao", "zpfangchan", "shichang", "zpguanggao", "zpmeishu",
       "zpshengchankaifa", "zpshengchan", "zpwuliucangchu", "xiaofeipin", "zhikonganfang",
       "zpqiche", "tech", "zpjixieyiqi", "zpjixie", "zpfalvzixun", "zhuanye", "fanyizhaopin",
       "zpxiezuochuban", "zpcaiwushenji", "jinrongtouzi", "zpjinrongbaoxian", "zpyiyuanyiliao",
       "zpzhiyao", "zpzhiyao", "huanbao", "zpfangchanjianzhu", "zpwuye", "nonglinmuyu", "zhaopin"]
print len(els)
inds = ""
i=0

for el in els:
    i+=1
    inds += '"' + el + '", '
    if i % 5 == 0:
        inds += '\n'

if inds[-1] == '\n':
    inds = inds[:-1]
else:
    inds = inds[:-2]

inds_result = 'inds=[' + inds + ']'



with open('qdata.py', 'wb') as f:
    f.write('#!/usr/bin/env python \n# -*- coding:utf8 -*- \n')
    f.write(urls_result + '\n\n' + inds_result)



