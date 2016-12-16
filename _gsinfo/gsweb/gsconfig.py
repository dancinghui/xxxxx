#!/usr/bin/env python
# encoding:utf-8


class ConfigData:
    gsdata = [
    {
        "url": "http://gsxt.saic.gov.cn/zjgs/",
        "prov": "100000",
        "name": "国家工商行政管理总局",
        "pinyin": "Guojia",
        "imgurl": "http://gsxt.saic.gov.cn/zjgs/captcha?preset=&ra=$RND$"
    },
    {
        "url": "http://qyxy.baic.gov.cn/beijing",
        "prov": "110000",
        "name": "北京",
        "pinyin": "Beijing",
        "imgurl": "http://qyxy.baic.gov.cn/CheckCodeCaptcha?currentTimeMillis=$TIME$&num=$RND100000$" #num is random(100000)
    },
    {
        "url": "http://tjcredit.gov.cn/platform/saic/index.ftl",
        "prov": "120000",
        "name": "天津",
        "pinyin": "Tianjin",
        "imgurl": "http://tjcredit.gov.cn/verifycode?date=$TIME$"
    },
    {
        "url": "http://www.hebscztxyxx.gov.cn/notice/",
        "prov": "130000",
        "name": "河北",
        "pinyin": "Hebei",
        "imgurl": "http://www.hebscztxyxx.gov.cn/notice/captcha?preset=&ra=$RND$"
    },
    {
        "url": "http://218.26.1.108/search.jspx",
        "prov": "140000",
        "name": "山西",
        "pinyin": "Shanxi",
        "imgurl": "http://218.26.1.108/validateCode.jspx?type=0&id=$RND$"
    },
    {
        "url": "http://www.nmgs.gov.cn:7001/aiccips/",
        "prov": "150000",
        "name": "内蒙古",
        "pinyin": "Neimenggu",
        "imgurl": "http://www.nmgs.gov.cn:7001/aiccips/verify.html?random=$RND$"
    },
    {
        "url": "http://gsxt.lngs.gov.cn/saicpub/",
        "prov": "210000",
        "name": "辽宁",
        "pinyin": "Liaoning",
        "imgurl": "http://gsxt.lngs.gov.cn/saicpub/commonsSC/loginDC/securityCode.action?tdate=$RND100000$"
    },
    {
        "url": "http://211.141.74.198:8081/aiccips",
        "prov": "220000",
        "name": "吉林",
        "pinyin": "Jilin",
        "imgurl": "http://211.141.74.198:8081/aiccips/securitycode?$RND$"
    },
    {
        "url": "http://gsxt.hljaic.gov.cn/",
        "prov": "230000",
        "name": "黑龙江",
        "pinyin": "Heilongjiang",
        "imgurl": "http://gsxt.hljaic.gov.cn/validateCode.jspx?type=0&id=$RND$"
    },
    {
        "url": "https://www.sgs.gov.cn/notice/home",
        "prov": "310000",
        "name": "上海",
        "pinyin": "Shanghai",
        "imgurl": "https://www.sgs.gov.cn/notice/captcha?preset=&ra=$RND$"
    },
    {
        "url": "http://www.jsgsj.gov.cn:58888/province/",
        "prov": "320000",
        "name": "江苏",
        "pinyin": "Jiangsu",
        "imgurl": "http://www.jsgsj.gov.cn:58888/province/rand_img.jsp?type=7&temp=$RND$"
    },
    {
        "url": "http://gsxt.zjaic.gov.cn/zhejiang.jsp",
        "prov": "330000",
        "name": "浙江",
        "pinyin": "Zhejiang",
        "imgurl": "http://gsxt.zjaic.gov.cn/common/captcha/doReadKaptcha.do" #need cookie to get image.
    },
    {
        "url": "http://www.ahcredit.gov.cn/search.jspx",
        "prov": "340000",
        "name": "安徽",
        "pinyin": "Anhui",
        "imgurl": "http://www.ahcredit.gov.cn/validateCode.jspx?type=0&$RND$"
    },
    {
        "url": "http://wsgs.fjaic.gov.cn/creditpub/home",
        "prov": "350000",
        "name": "福建",
        "pinyin": "Fujian",
        "imgurl": "http://wsgs.fjaic.gov.cn/creditpub/captcha?preset=str-01,math-01&ra=$RND$"
    },
    {
        "url": "http://gsxt.jxaic.gov.cn/",
        "prov": "360000",
        "name": "江西",
        "pinyin": "Jiangxi",
        "imgurl": "http://gsxt.jxaic.gov.cn/ECPS/verificationCode.jsp?_=$TIME$"
    },
    {
        "url": "http://218.57.139.24/",
        "prov": "370000",
        "name": "山东",
        "pinyin": "Shandong",
        "imgurl": "http://218.57.139.24/securitycode?$RND$"
    },
    {
        "url": "http://gsxt.gdgs.gov.cn/",
        "prov": "440000",
        "name": "广东",
        "pinyin": "Guangdong",
        "imgurl": "http://gsxt.gdgs.gov.cn/aiccips/verify.html?random=$RND$"
    },
    {
        "url": "http://gxqyxygs.gov.cn/",
        "prov": "450000",
        "name": "广西",
        "pinyin": "Guangxi",
        "imgurl": "http://gxqyxygs.gov.cn/validateCode.jspx?type=0&id=$RND$"
    },
    {
        "url": "http://aic.hainan.gov.cn:1888/aiccips",
        "prov": "460000",
        "name": "海南",
        "pinyin": "Hainan",
        "imgurl": "http://aic.hainan.gov.cn:1888/aiccips/verify.html?random=$RND$"
    },
    {
        "url": "http://222.143.24.157/",
        "prov": "410000",
        "name": "河南",
        "pinyin": "Henan",
        "imgurl": "http://222.143.24.157/validateCode.jspx?type=0&id=$RND$"
    },
    {
        "url": "http://xyjg.egs.gov.cn/ECPS_HB/index.jsp",
        "prov": "420000",
        "name": "湖北",
        "pinyin": "Hubei",
        "imgurl": "http://xyjg.egs.gov.cn/ECPS_HB/validateCode.jspx?type=1&_=$TIME$"
    },
    {
        "url": "http://gsxt.hnaic.gov.cn/notice/",
        "prov": "430000",
        "name": "湖南",
        "pinyin": "Hunan",
        "imgurl": "http://gsxt.hnaic.gov.cn/notice/captcha?preset=&ra=$RND$"
    },
    {
        "url": "http://gsxt.cqgs.gov.cn/",
        "prov": "500000",
        "name": "重庆",
        "pinyin": "Chongqing",
        "imgurl": "http://gsxt.cqgs.gov.cn/sc.action?width=130&height=40&fs=23&t=$TIME$"
    },
    {
        "url": "http://gsxt.scaic.gov.cn/",
        "prov": "510000",
        "name": "四川",
        "pinyin": "Sichuan",
        "imgurl": "http://gsxt.scaic.gov.cn/ztxy.do?method=createYzm&dt=$TIME$&random=$TIME$"
    },
    {
        "url": "http://gsxt.gzgs.gov.cn/",
        "prov": "520000",
        "name": "贵州",
        "pinyin": "Guizhou",
        "imgurl": "http://gsxt.gzgs.gov.cn/search!generateCode.shtml?validTag=searchImageCode&$TIME$"
    },
    {
        "url": "http://gsxt.ynaic.gov.cn/notice/",
        "prov": "530000",
        "name": "云南",
        "pinyin": "Yunnan",
        "imgurl": "http://gsxt.ynaic.gov.cn/notice/captcha?preset=&ra=$TIME$"
    },
    {
        "url": "http://gsxt.xzaic.gov.cn/",
        "prov": "540000",
        "name": "西藏",
        "pinyin": "Xizang",
        "imgurl": "http://gsxt.xzaic.gov.cn/validateCode.jspx?type=0&id=$RND$"
    },
    {
        "url": "http://xygs.snaic.gov.cn/",
        "prov": "610000",
        "name": "陕西",
        "pinyin": "Shaanxi",
        "imgurl": "http://xygs.snaic.gov.cn/ztxy.do?method=createYzm&dt=$TIME$&random=$TIME$"
    },
    {
        "url": "http://xygs.gsaic.gov.cn/gsxygs/",
        "prov": "620000",
        "name": "甘肃",
        "pinyin": "Gansu",
        "imgurl": "http://xygs.gsaic.gov.cn/gsxygs/securitycode.jpg?v=$TIME$"
    },
    {
        "url": "http://218.95.241.36/",
        "prov": "630000",
        "name": "青海",
        "pinyin": "Qinghai",
        "imgurl": "http://218.95.241.36/validateCode.jspx?type=0&id=$RND$"
    },
    {
        "url": "http://gsxt.ngsh.gov.cn/ECPS/index.jsp",
        "prov": "640000",
        "name": "宁夏",
        "pinyin": "Ningxia",
        "imgurl": "http://gsxt.ngsh.gov.cn/ECPS/verificationCode.jsp?_=$TIME$"
    },
    {
        "url": "http://gsxt.xjaic.gov.cn:7001/",
        "prov": "650000",
        "name": "新疆",
        "pinyin": "Xinjiang",
        "imgurl": "http://gsxt.xjaic.gov.cn:7001/ztxy.do?method=createYzm&dt=$TIME$&random=$TIME$"
    }
]


