#!/usr/bin/env python
# -*- coding:utf8 -*-

from lxml import html
import requests
import json
import codecs




def getCity():

    rs = []

    URL = "http://company.zhaopin.com/"
    con = requests.get(URL)
    doc = html.fromstring(con.text)

    cities = doc.xpath('//div[@class="city_nav"]//li/strong/a')

    for city in cities:
        href = city.attrib.get('href','')
        if not href:
            continue

        text = getattr(city, 'text', '')
        print "%s: %s" % (text, href)
        rs.append((text, href))

    return json.dumps(rs, ensure_ascii=False)


def getIndustry():
    rs = []
    URL = "http://company.zhaopin.com/beijing/"
    con = requests.get(URL)
    doc = html.fromstring(con.text)

    inds = doc.xpath("//div[@id='industry']//a")
    for ind in inds:
        _id = ind.attrib.get('id','')
        if not _id:
            continue

        text = getattr(ind, "text", '')
        print "%s: %s" % (text, _id)
        rs.append((text, _id))

    return json.dumps(rs, ensure_ascii=False)

def genQ():
    with codecs.open('query.py', 'wb', encoding='utf-8') as f:
        cities = getCity()
        inds = getIndustry()

        f.write("""#!/usr/bin/env python\n# -*- coding:utf8 -*-\n""")

        f.write("\n\n\ncities = %s\n" % cities)
        f.write("\n\n\ninds = %s\n" % inds)

    print "gen query complete"

if __name__ == '__main__':
    # getCity()
    # getIndustry()
    genQ()