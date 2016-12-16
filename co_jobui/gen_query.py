#!/usr/bin/env python
# -*- coding:utf8 -*-

from lxml import html
import requests
import json
import codecs
import re

def getCity():

    rs = []
    url = "http://www.jobui.com/changecity/?from=http://www.jobui.com/cmp?"
    con = requests.get(url)

    doc = html.fromstring(con.text)
    cities = doc.xpath("//div[@class='moreCity box']//dd//a")

    for city in cities:
        data_city = city.attrib.get('data_city','')
        if not data_city:
            continue

        rs.append(data_city)
    return json.dumps(rs, ensure_ascii=False, indent=4)


def getIndustry():
    rs = []

    url = 'http://www.jobui.com/cmp?'
    con = requests.get(url)
    doc = html.fromstring(con.text)

    elems = doc.xpath("//dd[@class='debor-line auto']//a")

    for elem in elems:
        href = elem.attrib.get('href','')
        if not href or "industry" not in href:
            continue

        ind = elem.text
        rs.append(ind)

    return json.dumps(rs, ensure_ascii=False, indent=4)


def getCoType():
    rs = []
    url = 'http://www.jobui.com/cmp?'
    con = requests.get(url)
    doc = html.fromstring(con.text)

    elems = doc.xpath("//dd/a")
    for elem in elems:
        href = elem.attrib.get('href','')
        if not href or "type" not in href:
            continue

        _type = elem.text
        if not _type:
            continue
        rs.append(_type)

    rs = rs[:-2]

    return json.dumps(rs, ensure_ascii=False)

def getIncScale():

    rs = []
    url = 'http://www.jobui.com/cmp?'
    con = requests.get(url)
    doc = html.fromstring(con.text)

    elems = doc.xpath("//dd/a")
    for elem in elems:
        href = elem.attrib.get('href','')
        if not href or "worker" not in href:
            continue

        _type = elem.text
        if not _type:
            continue
        rs.append(_type)

    return json.dumps(rs, ensure_ascii=False)

def getAreaCode(cities):
    rs = {}
    if isinstance(cities, basestring):
        cities = json.loads(cities)

    for city in cities:

        areaCodes = []

        url = "http://www.jobui.com/cmp?area=%s" % city
        con = requests.get(url)
        doc = html.fromstring(con.text)

        elems = doc.xpath('//dd/a')
        for elem in elems:
            href = elem.attrib.get('href','')
            if not href or 'areaCode' not in href:
                continue
            find = re.search(r'areaCode=(\d+)', href)
            if not find:
                print "href : %s do not contains areaCode" % href
                continue

            text = elem.text
            areaCode = find.group(1)

            areaCodes.append((text, areaCode))

        rs[city] = areaCodes
        print "city %s areaCode get complete" % city


    return json.dumps(rs, ensure_ascii=False, indent=4)







def genQ():
    cities = getCity()
    inds = getIndustry()
    co_type = getCoType()
    co_scale = getIncScale()

    area_code = getAreaCode(cities)

    with codecs.open('query.py', 'wb', encoding='utf-8') as f:
        f.write("""#!/usr/bin/env python\n# -*- coding:utf8 -*-\n""")

        f.write("\n\n\ncities = %s\n" % cities)
        f.write("\n\n\ninds = %s\n" % inds)
        f.write('\n\n\nco_types = %s\n' % co_type)
        f.write('\n\n\nco_scale = %s\n' % co_scale)
        f.write('\n\n\nareaCodes = %s\n' % area_code)


if __name__ == '__main__':
    genQ()