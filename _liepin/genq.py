#!/usr/bin/env python
# -*- coding:utf8 -*-

from spider.genquery import GenQueries
import re
import time
from spider.runtime import Log


dqs = [["010","北京","BEIJING"],
["020","上海","SHANGHAI"],
["030","天津","TIANJIN"],
["040","重庆","CHONGQING"],
["050","广东省","GUANGDONG"],
["060","江苏省","JIANGSU"],
["070","浙江省","ZHEJIANG"],
["080","安徽省","ANHUI"],
["090","福建省","FUJIAN"],
["100","甘肃省","GANSU"],
["110","广西","GUANGXI"],
["120","贵州省","GUIZHOU"],
["130","海南省","HAINAN"],
["140","河北省","HEBEI"],
["150","河南省","HENAN"],
["160","黑龙江省","HEILONGJIANG"],
["170","湖北省","HUBEI"],
["180","湖南省","HUNAN"],
["190","吉林省","JILIN"],
["200","江西省","JIANGXI"],
["210","辽宁省","LIAONING"],
["220","内蒙古","NEIMENGGU"],
["230","宁夏","NINGXIA"],
["240","青海省","QINGHAI"],
["250","山东省","SHANDONG"],
["260","山西省","SHANXI"],
["270","陕西省","SHANXI"],
["280","四川省","SICHUAN"],
["290","西藏","XIZANG"],
["300","新疆","XINJIANG"],
["310","云南省","YUNNAN"],
["320","香港","HONGKONG"],
["330","澳门","MACAO"],
["340","台湾","TAIWAN"],
["350","亚洲","Asia"],
["360","北美洲","North America"],
["370","南美洲","South America"],
["380","大洋洲","Oceania"],
["390","欧洲","Europe"],
["400","非洲","Africa"],]

compscale = [ [ '010', '1-49人', '1-49' ],
    [ '020', '50-99人', '50-99' ],
    [ '030', '100-499人', '100-499' ],
    [ '040', '500-999人', '500-999' ],
    [ '050', '1000-2000人', '1000-2000' ],
    [ '060', '2000-5000人', '2000-5000' ],
    [ '070', '5000-10000人', '5000-10000' ],
    [ '080', '10000人以上', 'More than 10000' ] ]

compkind = [ [ '010', '外商独资/外企办事处', 'Foreign-funded/Foreign Office' ],
    [ '020', '中外合营(合资/合作)', 'Joint Venture/Cooperation' ],
    [ '030', '私营/民营企业', 'Private Enterprises' ],
    [ '040', '国有企业', 'State-owned Enterprise' ],
    [ '050', '国内上市公司', 'Domestic Listed Companies' ],
    [ '060', '政府机关／非盈利机构', 'Government Non-profit Organization' ],
    [ '070', '事业单位', 'State-owned Institution' ],
    [ '999', '其他', 'Others' ] ]

jobTitles = [["530","高级管理"],
["531","人力资源"],
["532","财务/审计/税务"],
["533","市场"],
["534","公关/媒介"],
["535","销售管理"],
["536","销售人员"],
["537","销售行政/商务"],
["538","客户服务/技术支持"],
["539","法务"],
["540","行政/后勤/文秘"],
["542","后端开发"],
["543","IT质量管理"],
["545","运营"],
["546","产品"],
["547","UI/UE/平面设计"],
["549","电子/电器/半导体/仪器"],
["550","电信/通信技术"],
["551","硬件开发"],
["553","建筑工程"],
["554","土木/土建规划设计"],
["555","物业管理"],
["556","银行"],
["557","保险"],
["558","业务服务"],
["559","金融产品/行业研究/风控"],
["563","信托/担保/拍卖/典当"],
["564","生产工艺"],
["565","采购/物料/设备管理"],
["566","生产管理/维修"],
["569","百货/连锁/零售服务"],
["571","服装/纺织/皮革"],
["579","汽车销售与服务"],
["585","印刷/包装"],
["589","咨询/调研"],
["591","翻译"],
["592","旅游/出入境服务"],
["593","酒店/餐饮/娱乐/生活服务"],
["594","广告/会展"],
["595","影视/媒体"],
["596","艺术/设计"],
["597","教育/培训"],
["598","实习生/培训生/储备干部"],
["599","交通/运输"],
["600","物流/仓储"],
["602","贸易"],
["603","医学研发/临床试验"],
["610","医院/医疗/护理"],
["611","电力/能源/矿产/地质勘查"],
["613","化工"],
["614","环境科学/环保"],
["615","公务员/公益事业/科研"],
["616","农/林/牧/渔"],
["652","机械设计/制造"],
["653","机械设备/维修"],
["655","医药注册/推广"],
["656","汽车制造"],
["657","前端开发"],
["658","BI"],
["659","配置管理"],
["660","IT管理"],
["661","IT项目管理"],
["662","IT运维/技术支持"],
["663","建筑装潢"],
["664","房地产规划/开发"],
["665","房地产交易/中介"],
["666","质量管理/安全防护"],
["667","项目管理/项目协调"],
["668","写作/采编/出版"],
["669","其他"],
["670","采购"]]

def parseInt(s):
    m = re.match("\s*([0-9]+)", s)
    if m:
        return int(m.group(1))
    raise ValueError("invalid string %s to int" % s)

class GenLPQuery(GenQueries):
    def __init__(self, thcnt=20):
        GenQueries.__init__(self, thcnt)
        self._name = "lp_qiye_queries"

    def init_conditions(self):
        self.baseurl = "http://www.liepin.com/zhaopin/?pubTime=3&salary=*&searchType=1&clean_condition=&jobKind=2&isAnalysis=&init=1&searchField=1&key=&industries=&jobTitles=&dqs=&compscale=000&compkind=000"
        self.cond = ['dqs', 'compscale', 'compkind', 'jobTitles' ]
        self.conddata = [dqs, compscale, compkind, jobTitles]

    def need_split(self, url, level, islast):
        con = self.request_url(url)
        if con is not None:
            m = re.search(ur"共为您找到\s*<strong>([0-9+]*)</strong>\s*职位", con.text)
            if m:
                found = m.group(1)
                count = parseInt(found)
                print "[%d] %s ==> %s %s" % (level, url, found, 'failed' if (count>=4000) else '')
                if parseInt(found) >= 3000:
                    return True
            m1 = re.search(ur'curPage=(\d+)" title="末页"', con.text)
            if m1:
                if int(m1.group(1)) >= 100:
                    print "===failed==="
                    return True
            if m or m1:
                return False
            if re.search(ur"没有找到符合您搜索条件的相关职位", con.text):
                return False
        Log.error("unknown page for", url)
        Log.errorbin(url, con.text)
        time.sleep(1)
        return self.need_split(url, level, islast)

if __name__ == "__main__":
    g = GenLPQuery()
    g.run()
