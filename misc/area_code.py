#!/usr/bin/env python
# encoding: utf-8

from spider.httpreq import BasicRequests
import re
import spider.util
from spider.util import utf8str

def sv(m):
    if m.group(0) == '</p>':
        return "\n"
    return ''

def get_short_name(name):
    postfix = "特别行政区|新区|地区|自治区|区|省|自治县|县|市|自治州|自治旗|旗".split('|')
    mz = ['各族', '汉族', '蒙古族', '回族', '藏族', '维吾尔族', '苗族', '彝族', '壮族', '布依族', '朝鲜族', '满族',
'侗族', '瑶族', '白族', '土家族', '哈尼族', '哈萨克族', '傣族', '黎族', '傈僳族', '佤族', '畲族',
'拉祜族', '水族', '东乡族', '纳西族', '景颇族', '柯尔克孜族', '土族', '达斡尔族', '仫佬族', '羌族',
'布朗族', '撒拉族', '毛南族', '仡佬族', '锡伯族', '阿昌族', '普米族', '塔吉克族', '怒族', '乌兹别克族',
'俄罗斯族', '鄂温克族', '德昂族', '保安族', '裕固族', '京族', '塔塔尔族', '独龙族', '鄂伦春族',
'赫哲族', '门巴族', '珞巴族', '基诺族', '高山族']
    az = []
    az.extend(postfix)
    az.extend(mz)
    az.extend(["维吾尔","哈萨克"])
    oname = name
    while True:
        oname1 = oname
        for o in az:
            exp = (o+'$').decode('utf-8')
            name1 = re.sub(exp, '', oname)
            if name1 != oname:
                oname = name1
                break
        if oname == oname1:
            break
    if oname == u'':
        return None
    return oname

def get_area_code():
    nr = BasicRequests()
    nr.select_user_agent('firefox')
    con = nr.request_url('http://www.stats.gov.cn/tjsj/tjbz/xzqhdm/201504/t20150415_712722.html')
    xx = spider.util.htmlfind(con.text, '<div class="TRS_PreAppend"', 0)
    shtml = xx.get_node()
    stext = re.sub('<.*?>', lambda m: sv(m), shtml)
    stext = re.sub('&nbsp;', ' ', stext)

    outmap = {}
    cclist = {}
    fulloutmap = {}

    for line in re.split("\n", stext):
        cns = re.split(r'\s+', line)
        if len(cns) <= 1:
            continue
        code, name = cns
        name = name.decode('utf-8').strip()

        if u'直辖县级行政区划' in name:
            continue
        if name in [u'市辖区', u'区', u'县', u'矿区', u'郊区', u'城区']:
            continue
        if name not in fulloutmap:
            fulloutmap[name] = []
        fulloutmap[name].append(code[0:4])

        name1 = get_short_name(name)
        if name1 is None or name1 == name:
            continue
        if name1 not in cclist:
            cclist[name1] = {}
        if code[0:4] not in cclist[name1]:
            cclist[name1][code[0:4]] = []
        cclist[name1][code[0:4]].append([code, name])

    for key in cclist.keys():
        if key == u'吉林':
            outmap[key] = "2202"
        elif key == u"海南":
            outmap[key] = "4600"
        elif len(cclist[key]) == 1:
            thekey = cclist[key].keys()[0]
            outmap[key] = thekey
        else:
            preflist = []
            for thekey, v in cclist[key].items():
                for code, name in v:
                    if code[-2:] == '00':
                        preflist.append(code)
            if len(preflist) == 0:
                pass
            elif len(preflist) == 1:
                outmap[key] = preflist[0][0:4]
            else:
                assert not "nani?"

    fout = {}
    for k,v in outmap.items():
        fout[k] = v
    for k,v in fulloutmap.items():
        if len(v)==1:
            fout[k] = v[0]
    return fout


spider.util.use_utf8()
allmap = get_area_code()
print utf8str(allmap)

