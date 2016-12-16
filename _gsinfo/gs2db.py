#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
sys.path.append(sys.path[0]+"/..")
print sys.path

import time
from spider.spider import Spider
import re
from spider.savebin import BinSaver, FileSaver
import spider.util
import json
import pymongo
import random
from lxml import html
filter_line = set()
filter_code = set()
conn = pymongo.MongoClient("mongodb://192.168.1.44:27019/gsinfo")

class GSinfo2DB(Spider):
    """工商数据入库"""
    def __init__(self, thcnt):
        Spider.__init__(self, thcnt)
        self.success_count = 0
        self.fail_count = 0
        self.fail_file = FileSaver("fail2db.txt")
        self.sus_file = FileSaver("SZ2DB.txt")
        self.init_filter()
        self.proxies = {'http': 'http://ipin:helloipin@haohr.com:50001', 'https': 'https://ipin:helloipin@haohr.com:50001'}
            #{'http': 'http://ipin:helloipin@192.168.1.39:3428', 'https': 'https://ipin:helloipin@192.168.1.39:3428'}
        self.select_user_agent("=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/49.0.2623.108 Chrome/49.0.2623.108 Safari/537.36")

    def init_filter(self):
        with open("SZ2DB.txt") as f:
            cnt = 0
            for line in f:
                line = line.strip()
                filter_line.add(line)
                cnt += 1
        print "初始化完毕＞＞＞＞＞＞ ", cnt

    def wait_q_breakable(self):
        lt = 0
        while True:
            if not self.job_queue.empty() or not self.job_queue2.empty() or not self.job_queue3.empty():
                time.sleep(5)
            if time.time() < lt + 1 and self._running_count==0:
                return True
            time.sleep(2)
            lt = time.time()
            if self._worker_count == 0:
                return False



    def recorde_already(self, detail):
        if isinstance(detail, dict):
            detail = spider.util.utf8str(detail)
        self.sus_file.append(detail)
        filter_line.add(detail)

    def dispatch(self):
        #gsinfo_guangdong_guangzhou  gsinfo_guangdong_QyxyDetail   gsinfo_guangdong_entityShow  gsinfo_guangdong_GSpublicityList
        #"./gsweb/guangdong/gsinfo_guangdong_GSpublicityList.txt"
        #"./gsweb/hunan/gsinfo_hunan.txt"
        #"./gsweb/sichuan/gsinfo_sichuan.txt"
        fl = "./gsweb/guangdong/gsinfo_guangdong_GSpublicityList.txt"
        with open(fl) as f:
            for line in f:
                line = line.strip()
                if line in filter_line or line == "" or line == "{}":
                    print "already......", line
                    continue
                detail = None
                try:
                    detail = json.loads(line)
                    if "basicInfo" in detail:
                        basic = detail["basicInfo"]
                        if len(basic) != 0:
                            pass
                        else:
                            detail["reason"] = "len(basic)=0 or rigistID not exist"
                            self.fail_file.append(spider.util.utf8str(detail))
                            continue
                    else:
                        detail["reason"] = "basicInfo is not exist"
                        self.fail_file.append(spider.util.utf8str(detail))
                        continue
                except Exception as e:
                    print e, "json转换出错", line
                    continue
                job = {"detail": detail}
                self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)


    def run_job(self, job):
        detail = job["detail"]
        self.parse(detail)

    def parse(self, detail):
        basic = detail["basicInfo"]
        branch = []
        if "branchInfo" in detail:
            branch = detail["branchInfo"]
            if branch is None:
                branch = []

        changes = []
        if "changesInfo" in detail:
            changes = detail["changesInfo"]
            if changes is None:
                changes = []
            if "list" in changes:
                changes = changes["list"]

        invest = []
        if "investorsInfo" in detail:
            invest = detail["investorsInfo"]
            if invest is None:
                invest = []

        staffs = []
        if "staffsInfo" in detail:
            staffs = detail["staffsInfo"]
            if staffs is None:
                staffs = []

        detail_new = {}
        regOrg = self.parse_basic(basic, detail, detail_new)

        # if len(branch) != 0:
        #    self.parse_branch(branch, detail, detail_new)
        invest_detail = []
        if len(changes) != 0:
            invest_detail = self.parse_change(changes, detail_new, regOrg=regOrg)

        if len(staffs) != 0:
            invest_detail = self.parse_staff(staffs, detail_new, regOrg=regOrg)

        #解析投资信息一定要放在最后
        if len(invest) != 0:
            self.parse_invest(invest, detail_new, invest_detail=invest_detail)

        # if "registIDnone" in detail_new["registID"]:
        #     pass
            #这个要入到另外一个库

    def parse_invest(self, invest, detail_new, invest_detail=[]):
        key_value = {u"投资人": "investor", u"股东": "investor", u"股东类型": "investorType",u"投资人类型": "investorType",
                     u"证照类型": "certType", u"证照/证件类型": "certType",
                     u"证照号码": "certCode", u"证照/证件号码": "certCode",
                     u"详情":"investDetail", u"投资详情":"investDetail"}

        k_v = {u"实缴出资方式": "factInvestWay", u"实缴出资日期": "factInvestDate", u"实缴出资时间": "factInvestDate",
               u"实缴出资额（万元）": "factInvestAmount",u"实缴出资额": "factInvestAmount",
               u"实缴额（万元）": "factAmount",
               u"认缴出资方式": "subcribeInvestWay", u"认缴出资日期": "subcribeInvestDate", u"认缴出资时间": "subcribeInvestDate",
               u"认缴出资额（万元）": "subcribeInvestAmount", u"认缴出资额": "subcribeInvestAmount",
               u"认缴额（万元）":"subcribeAmount" }

        invest_new = []
        for i in invest:
            i_new = {}
            for k, v in key_value.items():
                if k in i:
                    content = i[k]
                    if isinstance(content, dict):
                        dt = {}
                        if len(content) == 0:
                            i_new[v] = dt
                            continue
                        for k1, v1 in k_v.items():
                            if k1 in content:
                                dt[v1] = content[k1]
                        i_new[v] = dt
                    else:
                        i_new[v] = i[k]
            if i_new["investDetail"] is None or len(i_new["investDetail"]):
                if len(invest_detail) != 0:
                    for d in invest_detail:
                        if d["investor"] == i_new["investor"] and d["investorType"] == i_new["investorType"]:
                            del d["investor"]
                            del d["investorType"]
                            i_new["investDetail"] = d
            invest_new.append(i_new)
        print "投资信息：", spider.util.utf8str(invest_new)
        detail_new["investInfo"] = invest_new


    def parse_staff(self, staffs, detail_new, regOrg=None):
        key_value = {u"姓名": "name", u"职务": "job", "name": "name", "position": "job"}
        staff_new = []
        invest_detail = []
        for s in staffs:
            s_new = {}
            for k, v in key_value.items():
                if k in s:
                    s_new[v] = s[k]
            staff_new.append(s_new)
            detail_i = self.get_invest_detail_guangdong(s, regOrg=regOrg)
            if detail_i is not None:
                invest_detail.append(detail_i)
        detail_new["staffInfo"] = staff_new
        print "主要人员信息：", spider.util.utf8str(s_new)
        return invest_detail

    def get_invest_detail_guangdong(self, staff, regOrg):
        #http://gsxt.gdgs.gov.cn/aiccips/GSpublicity/invInfoDetails.html?invNo=f508af48-0151-1000-e000-812fc0a8de0b&entNo=ee5085df-ca37-4d37-9ab5-32471850b056&regOrg=440882
        url = "http://gsxt.gdgs.gov.cn/aiccips/GSpublicity/invInfoDetails.html?"
        if "entNO" in staff and "vipNO" in staff:
            url += "entNo="+staff["entNO"] + "&invNo="+staff["vipNO"] + "&regOrg="+regOrg
            retry = 0
            while True:
                res = self.request_url(url)#, proxies=self.proxies)
                if res is None or res.code != 200:
                    retry += 1
                    print "广东　变更信息中拉取投资详情出现错误...retry=%d" % retry , "res is None" if res is None else "res.code = %d" % res.code
                    time.sleep(1)
                    continue
                else:
                    return self.parse_invest_detail_page(res.text)
        return None

    def parse_invest_detail_page(self, page):
        doc = html.fromstring(page)
        trs = doc.xpath("//div[@id='jibenxinxi']//table[@class='detailsList']/tr")
        detail = {}
        #header = [u"股东", u"股东类型", u"认缴出资额", u"认缴出资方式", u"认缴出资日期", u"实缴出资额", u"实缴出资方式", u"实缴出资时间"]
        header = ["investor", "investorType", "subcribeInvestAmount", "subcribeInvestWay",
                  "subcribeInvestDate", "factInvestAmount", "factInvestWay", "factInvestDate"]
        for tr in trs:
            tds = tr.xpath("td")
            if len(tds) == 0 or len(tds) == 1:
                continue
            i = 0
            for td in tds:
                c = td.text_content().strip()
                if i == 0 and c == "":
                    return None
                detail[header[i]] = c
                i += 1
        detail["subcribeAmount"] = ""
        detail["factAmount"] = ""
        return detail


    def parse_change(self, changes, detail_new, regOrg=None):
        #http://gsxt.gzaic.gov.cn/aiccips/GSpublicity/invInfoDetails.html?invNo=3BDA8054-68A8-BD88-1336-A6E6C1B9930F&entNo=440115115022009121500033&regOrg=440111 广州
        key_value = {"changeAfter": "altAfter", "changeBefore": "altBefore", "changeDate": "altDate", "changeItem": "altItem",
                     "altAf": "altAfter", "altBe": "altBefore", "altDate": "altDate", "altFiled": "altItem"}
        alt_new = []
        invest_detail = []
        for c in changes:
            c_new = {}
            for k, v in key_value.items():
                if k in c:
                    c_new[v] = c[k]
            alt_new.append(c_new)
            detail_i = self.get_invest_detail_guangzhou(c, regOrg=regOrg)
            if detail_i is not None:
                invest_detail.append(detail_i)
        print "变更信息：", spider.util.utf8str(alt_new)
        detail_new["altInfo"] = alt_new
        return invest_detail


    def get_invest_detail_guangzhou(self, change, regOrg=None):
        #针对广州系统未拉取的投资详情页面　　－－　根据变更信息里面的一些参数提取出来组合成链接访问  regOrg可以随便
        url = "http: // gsxt.gzaic.gov.cn / aiccips / GSpublicity / invInfoDetails.html?"
        if "entNo" in change and "entChaNo" in change:
            url += "entNo="+change["entNo"] + "&entChaNo="+change["entChaNo"] + "&regOrg="+regOrg
            retry = 0
            while True:
                res = self.request_url(url, proxies=self.proxies)
                if res is None or res.code != 200:
                    retry += 1
                    print "广州　变更信息中拉取投资详情出现错误...retry=%d" % retry , "res is None" if res is None else "res.code = %d" % res.code
                    time.sleep(1)
                    continue
                else:
                    return self.parse_invest_detail_page(res.text)
        return None


    def parse_basic(self, basic, detail, detail_new):
        #标准的key-value　至少这12个字段要保证有，其他的多则存少则略
        stantard_key = ["incAddress", "incName", "establishDate", "approveDate", "legalPerson", "registID", "oldRegistID",
                        "registOrganization", "incType", "registStatus", "busnissAllotedTime", "businessScope"]

        key_value = {u"营业场所": "incAddress", u"经营场所": "incAddress", u"地址": "incAddress", u"住所": "incAddress",
                     u"名称": "incName", u"注册日期": "establishDate", u"成立日期": "establishDate",u"核准日期": "approveDate",
                     u"投资人": "legalPerson", u"经营者": "legalPerson", u"负责人": "legalPerson",u"法定代表人": "legalPerson",
                     u"注册资本": "registCapital", u"注册资金": "registCapital",
                     u"登记机关": "registOrganization", u"类型": "incType", u"登记状态": "registStatus",u"经营状态": "registStatus",
                     u"注册号": "oldRegistID", u"统一社会信用代码": "registID", u"注册号/统一社会信用代码": "registID",
                     u"营业期限自":"fro", u"经营(驻在)期限自":"fro", u"经营期限自":"fro",
                     u"营业期限至":"to", u"经营(驻在)期限至":"to", u"经营期限至":"to",
                     u"经营范围": "businessScope"
                     }

        basic_new = {}
        for k, v in key_value.items():
            if k in basic:
                content = basic[k]
                basic_new[v] = content

        registID = basic_new["registID"] if "registID" in basic_new else ""
        oldRegistID = basic_new["oldRegistID"] if "oldRegistID" in basic_new else ""

        #如果有注册号且不为"",则判断信用代码是否"",如果是,则registID = oldRegistID
        #如果统一社会信用代码为空，用注册号作key，如果不为空，继续使用统一社会信用代码作key
        if oldRegistID != "":
            if registID == "":
                registID = oldRegistID
                basic_new["registID"] = registID
                basic_new["oldRegistID"] = ""
        else:
            if registID == "":
                print "信息出现错误..."
                registID = "registIDnone" + str(random.randrange(1, 99999999, 1))
                basic_new["registID"] = registID

        detail_new["registID"] = registID

        to = basic_new["to"] if "to" in basic_new else ""
        fro = basic_new["fro"] if "fro" in basic_new else ""
        if fro != "":
            basic_new["busnissAllotedTime"] = fro + "-" +to
            del basic_new["to"]
            del basic_new["fro"]
        else:
            basic_new["busnissAllotedTime"] = ""

        #针对深圳系统
        if "runInfo" in detail and "run_content" in detail["runInfo"]:
            run_content = detail["runInfo"]["run_content"]
            basic_new["businessScope"] = run_content

        for key in stantard_key:
            if key in basic_new:
                continue
            else:
                print "警告！！！！！！     %s 　不包含在基本信息内．．．．．．"% key
                basic_new[key] = ""
        detail_new["basicInfo"] = basic_new
        print "RESULT:", spider.util.utf8str(detail_new)

        if "registIDnone" not in registID:
            if len(registID) == 18:
                return registID[2:8]
            else:
                return registID[0:6]



    def parse_branch(self, branch, detail, detail_new):
        key_value = {u"名称": "incName", u"注册号": "registID", u"注册号/统一社会信用代码": "registID",  u"登记机关": "registOrganization"}
        branch_new = []
        try:
            for b in branch:
                b_new = {}
                for k, v in key_value.items():
                    if k in b:
                        b_new[v] = b[k]
                branch_new.append(b_new)
        except Exception as e:
            print "发生错误////" ,e
        detail_new["branchInfo"] = branch_new
        print "分支信息：", spider.util.utf8str(detail_new)


    # def parse_shenzhen(self, registID, detail):
    #
    #
    #     ##################################################分支信息###############################################################

    #
    #     ##################################################变更信息###############################################################

    #
    #     #################################################投资信息###############################################################

    #
    #     ##################################################主要人员信息###############################################################
    #     key_value = {"name": u"姓名", "job": u"职务"}
    #     staff_new = []
    #     for s in staffs:
    #         s_new = {}
    #         for k, v in key_value.items():
    #             if v in s:
    #                 s_new[k] = s[v]
    #         staff_new.append(s_new)
    #     #print "主要人员信息：", spider.util.utf8str(staff_new)
    #     detail_new["staffInfo"] = staff_new
    #     #self.sus_file.append(spider.util.utf8str(detail_new))
    #     #self.save2db_test(registID, detail_new)
    #     if u"工商行政管理局" in registOrganization:
    #         self.save2db_gongshang(registID, detail_new)
    #     elif u"市场监督管理局" in registOrganization:
    #         self.save2db_shichang(registID, detail_new)
    #     else:
    #         self.save2db_test(registID, detail_new)
    #     #print registID, "解析结果：", spider.util.utf8str(detail_new)


    def save2db_gongshang(self, registID, detail):
        """入库 --工商行政管理局"""
        db = conn.gsinfo
        key = {"registID": registID}
        result = db.gongshang_info.update(key, detail, upsert=True)
        if isinstance(result, dict):
            #self.recorde_already(spider.util.utf8str(detail))
            print registID, "入库成功：", result
        else:
            print "入库失败＞．．．", result

    def save2db_shichang(self, registID, detail):
        """入库 --市场监督管理局"""
        db = conn.gsinfo
        key = {"registID": registID}
        result = db.shichang_info.update(key, detail, upsert=True)
        if isinstance(result, dict):
            #self.recorde_already(spider.util.utf8str(detail))
            print registID, "入库成功：", result
        else:
            print "入库失败＞．．．", result

    def save2db_test(self, registID, detail):
        """入库 -- 测试库"""
        db = conn.gsinfo
        key = {"registID": registID}
        result = db.test_info.update(key, detail, upsert=True)
        if isinstance(result, dict):
            #self.recorde_already(spider.util.utf8str(detail))
            print registID, "入库成功：", result
        else:
            print "入库失败＞>>>>>>>>．．．", result




    def event_handler(self, evt, msg, **kwargs):
        if evt == 'DONE':
            msg += "GSinfo to db finish..."
            spider.util.sendmail('chentao@ipin.com', '%s DONE' % sys.argv[0], msg)


if __name__ == "__main__":
    # start = time.time()
    s = GSinfo2DB(1)
    s.run()
    # end = time.time()
    # print "time : {} , count : {} ,speed : {}t/s".format((end-start), s.num_count, s.num_count/(end - start))
    # line = '{"basicInfo": {"地区":"深圳","住所": "深圳市南山区侨香路香年广场[南区]主楼（A 座）403", "名称": "深圳市永利竹实业发展有限公司", "成立日期": "1997年12月19日", "核准日期": "2014年04月18日", "法定代表人": "邹振惠", "注册号": "440301102805570", "注册资本": "3000万元人民币", "登记机关": "深圳市市场监督管理局南山局", "类型": "有限责任公司", "经营状态": "登记成立", "统一社会信用代码": "", "营业期限自": "1997年12月19日", "营业期限至": "2017年12月19日"}, "branchInfo": [{"名称": "深圳市永利竹实业发展有限公司松岗空调专卖店", "序号": "1", "注册号": "4403012063479", "登记机关": "深圳市市场监督管理局"}, {"名称": "深圳市永利竹实业发展有限公司沙头电器商场", "序号": "2", "注册号": "4403012019775", "登记机关": "深圳市市场监督管理局福田局"}, {"名称": "深圳市永利竹实业发展有限公司平南分公司", "序号": "3", "注册号": "440307104787771", "登记机关": "深圳市市场监督管理局龙岗局"}, {"名称": "深圳市永利竹实业发展有限公司西乡空调专卖店", "序号": "4", "注册号": "440306104732417", "登记机关": "深圳市市场监督管理局宝安局"}, {"名称": "深圳市永利竹实业发展有限公司空调专卖店", "序号": "5", "注册号": "4403012061678", "登记机关": "深圳市市场监督管理局市注册局"}, {"名称": "深圳市永利竹实业发展有限公司龙华支架厂", "序号": "6", "注册号": "440301107385223", "登记机关": "深圳市市场监督管理局龙华局"}, {"名称": "深圳市永利竹实业发展有限公司百花电器商场", "序号": "7", "注册号": "4403012033774", "登记机关": "深圳市市场监督管理局福田局"}, {"名称": "深圳市永利竹实业发展有限公司龙岗空调专卖店", "序号": "8", "注册号": "440307105418571", "登记机关": "深圳市市场监督管理局龙岗局"}, {"名称": "深圳市永利竹实业发展有限公司南油电器商场", "序号": "9", "注册号": "4403012042145", "登记机关": "深圳市市场监督管理局南山局"}, {"名称": "深圳市永利竹实业发展有限公司汽车修理厂", "序号": "10", "注册号": "4403012003132", "登记机关": "深圳市市场监督管理局罗湖局"}, {"名称": "深圳市永利竹实业发展有限公司福田电器商场", "序号": "11", "注册号": "4403012105373", "登记机关": "深圳市市场监督管理局福田局"}], "changesInfo": [{"changeAfter": "人民币3000.0000 万元", "changeBefore": "人民币1000.0000 万元", "changeDate": "2014年04月18日", "changeItem": "注册资本", "sequence": "1"}, {"changeAfter": "刘凤娇  1398.0000(万元)  46.6000%  邹振惠  1602.0000(万元)  53.4000%", "changeBefore": "邹振惠  534.0000(万元)  53.4000%   刘凤娇  466.0000(万元)  46.6000%", "changeDate": "2014年04月18日", "changeItem": "股东（投资人）", "sequence": "2"}], "investorsInfo": [{"投资人": "刘凤娇", "投资人类型": "自然人", "证照号码": "", "证照类型": "", "详情": {"实缴出资方式": "", "实缴出资日期": "", "实缴出资额（万元）": "", "实缴额（万元）": "", "股东": "刘凤娇", "认缴出资方式": "", "认缴出资日期": "", "认缴出资额（万元）": "", "认缴额（万元）": "1398.0000万元人民币"}}, {"投资人": "邹振惠", "投资人类型": "自然人", "证照号码": "", "证照类型": "", "详情": {"实缴出资方式": "", "实缴出资日期": "", "实缴出资额（万元）": "", "实缴额（万元）": "", "股东": "邹振惠", "认缴出资方式": "", "认缴出资日期": "", "认缴出资额（万元）": "", "认缴额（万元）": "1602.0000万元人民币"}}], "runInfo": {"run_content": "兴办实业（具体项目另行申报）；国内贸易（不含专营、专控、专卖商品）；中央空调、冷气设备的安装、维修（提供上门维修服务）；经营进出口业务；普通货运（凭粤交运管许可深字440300046551号道路运输经营许可证经营，有效期至2015年07月10日），空气能、太阳能设备的销售、安装、维修（限上门安装、维修），房屋租赁，不锈钢架、铁架的生产和销售（生产限分支机构经营）。（以上法律、行政法规、国务院决定禁止的项目除外，限制的项目须取得许可后方可经营）^", "run_scope": "章程记载的经营范围"}, "staffsInfo": [{"姓名": "于洪", "序号": "1", "职务": "监事"}, {"姓名": "邹振惠", "序号": "2", "职务": "执行（常务）董事"}, {"姓名": "邹振惠", "序号": "3", "职务": "总经理"}]}'
    # detail = json.loads(line)
    # s.parse(detail)
    # s.parse_shenzhen("440301102805570", detail)
    #s.init_registID()

