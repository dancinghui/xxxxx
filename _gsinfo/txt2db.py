#!/usr/bin/env python
# -*- coding:utf8 -*-

import os
import sys
sys.path.append(sys.path[0]+"/..")
print sys.path

import time
from spider.spider import Spider
import re
from spider.savebin import BinSaver,FileSaver
import spider.util
import json
import pymongo
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
        with open("./gsweb/guangdong/gsinfo_guangdong_QyxyDetail.txt") as f:
            for line in f:
                line = line.strip()
                if line in filter_line or line == "" or line == "{}":
                    print "already...-00000000000000000000000000000000000000000000000000000000000000000"
                    continue
                detail = None
                registID = None
                try:
                    detail = json.loads(line)
                    if "basicInfo" in detail:
                        basic = detail["basicInfo"]
                        if len(basic) != 0 and u"注册号" in basic:
                            registID = basic[u"注册号"]
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
                job = {"detail": detail, "registID": registID}
                self.add_job(job, True)
        self.wait_q_breakable()
        self.add_job(None, True)


    def run_job(self, job):
        detail = job["detail"]
        registID = job["registID"]
        self.parse_shenzhen(registID, detail)

    def parse_shenzhen(self, registID, detail):
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
        investors = []
        if "investorsInfo" in detail:
            investors = detail["investorsInfo"]
            if investors is None:
                investors = []
        staffs = []
        if "staffsInfo" in detail:
            staffs = detail["staffsInfo"]
            if staffs is None:
                staffs = []

        detail_new = {"registID": registID}
        temp_len = len(basic)
        ##################################################基本信息###############################################################
        # key_value = {"incAddress": u"经营场所", "incAddress": u"住所", "incName": u"名称", "establishDate": u"注册日期",  "establishDate": u"成立日期",
        #              "approveDate": u"核准日期", "legalPerson": u"经营者", "legalPerson": u"法定代表人",
        #              "registCapital": u"注册资本", "registOrganization": u"登记机关", "incType": u"类型", "registStatus": u"经营状态"}
        key_value = {u"营业场所":"incAddress", u"经营场所":"incAddress", u"地址": "incAddress", u"住所": "incAddress", u"名称": "incName", u"注册日期": "establishDate",  u"成立日期": "establishDate",
                     u"核准日期": "approveDate", u"投资人":"legalPerson", u"经营者": "legalPerson", u"负责人": "legalPerson", u"法定代表人": "legalPerson",
                     u"注册资本": "registCapital", u"登记机关": "registOrganization", u"类型": "incType", u"经营状态": "registStatus"}
                    #"busnissAllotedTime": "营业期限" businessScope:经营范围 "USCC": u"统一社会信用代码"
        basic_new = {"registID": registID, "oldRegistID": ""}
        for k, v in key_value.items():
            if k in basic:
                content = basic[k]
                basic_new[v] = content

        if "runInfo" in detail and "run_content" in detail["runInfo"]:
            run_content = detail["runInfo"]["run_content"]
            basic_new["businessScope"] = run_content

        if u"统一社会信用代码" in basic:
            USCC = basic[u"统一社会信用代码"]
            if USCC != "" and len(USCC) != 0:
                basic_new["oldRegistID"] = basic_new["registID"]
                basic_new["registID"] = USCC
                registID = USCC
                detail_new["registID"] = registID

        if "registStatus" in basic_new and (u"吊销" in basic_new["registStatus"] or u"注销" in basic_new["registStatus"]):
            basic_new["busnissAllotedTime"] = ""
        else:
            to = None
            fro = None
            froAry = [u"营业期限自", u"经营(驻在)期限自", u"经营期限自", u"经营(驻在)期限自"]
            toAry = [u"营业期限至", u"经营(驻在)期限至", u"经营期限至", u"经营(驻在)期限至"]
            for f in froAry:
                if f in basic:
                    fro = basic[f]
                    break
            for t in toAry:
                if t in basic:
                    to = basic[t]
                    break
            if to is None or fro is None:
                if u"组成形式" in basic and len(basic) == 11:
                    basic_new["busnissAllotedTime"] = ""
                elif len(basic_new) >= len(basic):
                    basic_new["busnissAllotedTime"] = ""
                else:
                    basic_new["busnissAllotedTime"] = ""
                    # print "营业期限获取错误..................................................."
                    # flag = raw_input("是否允许入库?是1否0:")
                    # if flag:
                    #     basic_new["busnissAllotedTime"] = ""
                    # else:
                    #     detail["reason"] = "busnissAllotedTime get error"
                    #     self.fail_file.append(spider.util.utf8str(detail))
                    #     self.recorde_already(detail)
            else:
                basic_new["busnissAllotedTime"] = fro + "-" + to

        #print "基本信息：", spider.util.utf8str(basic_new)
        # if u"组成形式" in basic:
        #     if len(basic) - len(basic_new) != -1:
        #         print "信息不对称...有些基本信息没有取到..."
        # else:
        #     if len(basic) - len(basic_new) != 0:
        #         print "信息不对称...有些基本信息没有取到..."
        registOrganization = basic_new["registOrganization"]
        detail_new["basicInfo"] = basic_new

        ##################################################分支信息###############################################################
        key_value = {"incName": u"名称", "registID": u"注册号", "registOrganization": u"登记机关"}
        branch_new = []
        try:
            for b in branch:
                b_new = {}
                for k, v in key_value.items():
                    if v in b:
                        b_new[k] = b[v]
                branch_new.append(b_new)
        except Exception as e:
            print "发生错误////" ,e
        #print "分支信息：", spider.util.utf8str(branch_new)
        detail_new["branchInfo"] = branch_new

        ##################################################变更信息###############################################################
        key_value = {"altAfter": "changeAfter", "altBefore": "changeBefore", "altDate": "changeDate", "altItem": "changeItem"}
        alt_new = []
        for c in changes:
            c_new = {}
            for k, v in key_value.items():
                if v in c:
                    c_new[k] = c[v]
            alt_new.append(c_new)
        #print "变更信息：", spider.util.utf8str(alt_new)
        detail_new["altInfo"] = alt_new

        #################################################投资信息###############################################################
        key_value = {"investor": u"投资人", "investorType": u"投资人类型", "certType": u"证照类型", "certCode": u"证照号码",
                     "investDetail": u"详情"}
        k_v = {"factInvestWay": u"实缴出资方式", "factInvestDate": u"实缴出资日期", "factInvestAmount": u"实缴出资额（万元）", "factAmount": u"实缴额（万元）",
                "subcribeInvestWay": u"认缴出资方式","subcribeInvestDate": u"认缴出资日期", "subcribeInvestAmount": u"认缴出资额（万元）", "subcribeAmount": u"认缴额（万元）"}
        invest_new = []
        for i in investors:
            i_new = {}
            for k, v in key_value.items():
                if v in i:
                    content = i[v]
                    if isinstance(content, dict):
                        dt = {}
                        for k1, v1 in k_v.items():
                            if v1 in content:
                                dt[k1] = content[v1]
                        i_new[k] = dt
                    else:
                        i_new[k] = i[v]
            invest_new.append(i_new)
        #print "变更信息：", spider.util.utf8str(invest_new)
        detail_new["investInfo"] = invest_new

        ##################################################主要人员信息###############################################################
        key_value = {"name": u"姓名", "job": u"职务"}
        staff_new = []
        for s in staffs:
            s_new = {}
            for k, v in key_value.items():
                if v in s:
                    s_new[k] = s[v]
            staff_new.append(s_new)
        #print "主要人员信息：", spider.util.utf8str(staff_new)
        detail_new["staffInfo"] = staff_new
        #self.sus_file.append(spider.util.utf8str(detail_new))
        #self.save2db_test(registID, detail_new)
        if u"工商行政管理局" in registOrganization:
            self.save2db_gongshang(registID, detail_new)
        elif u"市场监督管理局" in registOrganization:
            self.save2db_shichang(registID, detail_new)
        else:
            self.save2db_test(registID, detail_new)
        #print registID, "解析结果：", spider.util.utf8str(detail_new)


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
    # s.parse_shenzhen("440301102805570", detail)
    #s.init_registID()

