#coding:utf-8
import requests
#import ipdb
import sys
import os
import traceback
import time
import random
import re
from code_process import get_code
from proxy import get_proxy_and_confirm
import socket
import json
from requests.exceptions import ReadTimeout
socket.setdefaulttimeout(0)

from bs4 import BeautifulSoup

# mongoengine.connect(None,alias="gaokao_score",host="mongodb://crawler:crawler@192.168.1.81,192.168.1.82,192.168.1.83/gaokao_crawler",socketKeepAlive=True,wtimeout=100000)

province_code_map={ "安徽":34, "北京":11, "重庆":50, "福建":35, "广东":44, "甘肃":62, "广西":45, "贵州":52, "河北":13, "湖北":42, "黑龙江":23, "河南":41, "湖南":43, "海南":46, "吉林":22, "江苏":32, "江西":36,
                    "辽宁":21, "内蒙古":15, "宁夏":64, "青海":63, "山西":14, "上海":31, "山东":37, "四川":51, "陕西":61, "天津":12, "新疆":65, "西藏":54, "云南":53}
wenli_code_map={"文科":1,"理科":5}

account_list=[
    # ["999177273","242442"], # ["999234123","785245"], # ["999666566","135643"],
    # ["999217244","783147"], # ["999412112","784767"], # ["999326518","672715"],
    # # ["999631631","617661"],
    # ["999314648","511265"], ["999658265","422318"],
    # ["999516865","875853"], ["999422556","587486"],
    # ["999484846","836473"], ["999112241","484816"],
    # ["999612823","682533"], ["999558374","256757"],
    # ["999532665","685835"], ["999768383","763773"],
    # ["999172818","451185"], ["999221814","286743"],
    # ["999218144","773846"], ["999486341","537641"],
    # ["999186124","176634"], ["999844475","311682"],
    # ["999578138","543318"], ["999535168","386182"],
    # ["999167524","446511"], ["999172114","158144"],
    # ["999852625","553158"], ["999675528","753457"],
    # ["999254843","837745"], ["999788256","731656"],
    # ["999242824","888366"], ["999461751","726266"],
    # ["999458881","654436"], ["999837875","588127"],
    # ["999346862","615857"], ["999518434","575364"],
    # ["999662513","446485"], ["999156558","347325"],
    # ["999427325","317836"], ["999333816","821461"],
    # ["999711331","764581"], ["999137157","141447"],
    # ["999687382","166377"], ["999613882","678832"],
    # ["999815377","671272"], ["999383575","665332"],
    # ["999364734","354544"], ["999832417","377624"],
    # ["999784336","455458"], ["999223322","573487"],
    # ["999161663","147613"], ["999382171","165864"],
    # ["999833154","225711"], ["999774275","532547"],
    ["999438718","735335"], ["999313241","874263"],
    ["999822813","271881"], ["999768265","746214"],
    ["999743655","275282"], ["999136522","428368"],
    ["999883413","873123"], ["999847613","812773"],
    ["999546662","558152"], ["999248775","528762"],
    ["999187146","164176"], ["999175276","651171"],
    ["999768427","811826"], ["999235765","572172"],
    ["999455363","428432"], ["999683881","354123"],
    ["999516828","875115"], ["999454371","432321"],
    ["999436662","112554"]
]


class ScoreSooxue:

    def __init__(self,account_list):
        self.account_list=account_list
        self.account_should_config=None
        self.current_balance=-1
        self.__VIEWSTATE=None
        self.__EVENTVALIDATION=None
        self.current_account=None

    def func_retry(self,func,**kwargs):
        retry=3
        while retry>=0:
            try:
                return func(**kwargs)
            except ReadTimeout,e:
                retry-=1
                traceback.print_exc()
                print "timeout sleep:%ss\n"%((3-retry)*30)
                time.sleep((3-retry)*30)
            except Exception,e:
                traceback.print_exc()
                retry-=1
                time.sleep((3-retry)*3)
        raise RuntimeError("重复3次超时")

    def do_get(self,session,url,timeout=10):
        resp=self.func_retry(session.get,url=url,timeout=timeout)
        if "window.location" in resp.content:
            url="http://%s/%s"%("gk.sooxue.com",re.search('location="(\S*)"',resp.content).group(1))
            print "js跳转",url
            resp=self.do_get(session,url)
        return resp

    def do_post(self,session,url,data,timeout=10):
        resp=self.func_retry(session.post,url=url,data=data,timeout=timeout)
        if "window.location" in resp.content:
            url="http://%s/%s"%("gk.sooxue.com",re.search('location="(\S*)"',resp.content).group(1))
            resp=self.do_post(session,url,data)
            print "js跳转",url
        return resp

    def get_have_get_parm(self,have_get_parm_path):
        have_get_parm=set()
        if not os.path.exists(have_get_parm_path):
            return set()
        with open(have_get_parm_path) as f:
            while True:
                line=f.readline()
                if not line:break
                have_get_parm.add(line.strip())
        return have_get_parm

    def logout(self):
        try:
            self.do_get(self.session,"http://gk.sooxue.com/login.aspx?action=logout",timeout=2)
            print "登出账号:%s"%self.current_account[0]
        except:
            traceback.print_exc()
            print "登出账号异常:%s"%self.current_account[0]
        self.current_account=None
        self.current_balance=-1
        self.session=None

    def account_base_config_ifneed(self):
        content=self.do_get(self.session,"http://gk.sooxue.com/query.aspx").content
        if "请先设置考生所在省市和科类!" not in content:
            return
        url="http://gk.sooxue.com/myconfig.aspx"
        content=self.do_get(self.session,url).content
        soup=BeautifulSoup(content)
        __VIEWSTATE=soup.find(id="__VIEWSTATE")["value"]
        __EVENTVALIDATION=soup.find(id="__EVENTVALIDATION")["value"]
        data={
            "__EVENTTARGET":"",
            "__EVENTARGUMENT":"",
            "__VIEWSTATE":__VIEWSTATE,
            "__EVENTVALIDATION":__EVENTVALIDATION,
            "ctl00$PageContent$ssdm":"11",
            "ctl00$PageContent$kldm":"5",
            "ctl00$PageContent$truename":"贾丽丽",
            "ctl00$PageContent$txtSchoolName":"尚志中学",
            "ctl00$PageContent$txtClassName":"物理学",
            "ctl00$PageContent$tel":"15004655342",
            "ctl00$PageContent$address":"黑龙江省齐齐哈尔滨市",
            "ctl00$PageContent$sfz":"23018318800845552X",
            "ctl00$PageContent$set_ssdm_kldm":"确定信息并提交"
        }
        self.do_post(self.session,url,data)

    def login(self,username,pawword):
        login_url="http://gk.sooxue.com/login.aspx"
        data={
            "username":username,
            "password":pawword,
            "x":49,
            "y":40
        }

        self.session=requests.Session()
        content=self.do_post(self.session,login_url,data).content
        self.current_account=[username,pawword]
        print "登录账号:%s"%username

    def switch_proxy(self,session):
        ip=get_proxy_and_confirm()
        print "设置代理:%s"%ip
        proxy = {'http':ip}
        session.proxies=proxy

    def init_session(self):
        session=requests.Session()
        session.headers.update({
           "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36",
           "Accept-Language":"zh-CN,zh;q=0.8,en;q=0.6",
           "Cache-Control":"max-age=0",
           "Accept":"*/*"
        })
        self.switch_proxy(session)
        return session

    def switch_account(self,switch=True):
        if not switch:
            username,pawword=self.current_account
        if self.current_account:
            self.logout()
        while self.account_list:
            self.session=self.init_session()
            if switch:
                username,pawword=self.account_list.pop(0)
            else:
                switch=True
            try:
                self.login(username,pawword)
                self.account_base_config_ifneed()
                if self.account_should_config:
                    self.account_config(self.account_should_config[0],self.account_should_config[1])
                self.__VIEWSTATE,self.__EVENTVALIDATION=self.get_viewstate_for_query()
                print "账号余额:%s"%self.current_balance
                if self.current_balance>20:
                    return
            except:
                traceback.print_exc()
                print "账号异常,选用下一个"
        print "账号已经全部用完！"
        raise RuntimeError("账号已经全部用完！")

    def account_config(self,province,wenli):
        province_code=province_code_map.get(province,None)
        if not province_code:
            raise RuntimeError("没有找到对应的省份")
        wenli_code=wenli_code_map.get(wenli,None)
        if not wenli_code:
            raise RuntimeError("没有找到对应的科类")
        config_url="http://gk.sooxue.com/myConfig.aspx"
        content=self.do_get(self.session,config_url).content
        #print content
        if "请先登录！" in content:
            raise RuntimeError(u"没有登录!")
        # print content
        soup=BeautifulSoup(content)
        viewstat=soup.find(id="__VIEWSTATE")["value"]
        eventvalidation=soup.find(id="__EVENTVALIDATION")["value"]
        data={
            "__EVENTTARGET":"",
            "__EVENTARGUMENT":"",
            "__VIEWSTATE":viewstat,
            "__EVENTVALIDATION":eventvalidation,
            "ctl00$PageContent$ssdm1":province_code,
            "ctl00$PageContent$kldm1":wenli_code,
            "ctl00$PageContent$Button1":"提交"
        }
        self.do_post(self.session,config_url,data)

    def get_viewstate_for_query(self):
        url="http://gk.sooxue.com/query.aspx"
        content=self.do_get(self.session,url).content
        soup=BeautifulSoup(content)
        # print content
        __VIEWSTATE=soup.find(id="__VIEWSTATE")["value"]
        __EVENTVALIDATION=soup.find(id="__EVENTVALIDATION")["value"]
        self.current_balance=int(soup.find(id="ctl00_lb_point").get_text())
        return __VIEWSTATE,__EVENTVALIDATION

    def code_processer(self,content):
        # code_path=os.path.join(os.path.dirname(__file__),"code.png")
        code_url="http://gk.sooxue.com/VerifyCode.aspx?"
        image_content=self.do_get(self.session,code_url).content
        print u"获取验证码"
        vcode=get_code(image_content)
        print u"验证码：%s"%vcode
        soup=BeautifulSoup(content)
        data={
            "__VIEWSTATE":soup.find(id="__VIEWSTATE")["value"],
            "__EVENTVALIDATION":soup.find(id="__EVENTVALIDATION")["value"],
            "TextBox1":vcode,
            "Button1":"验证码校验"
        }
        url="http://gk.sooxue.com/%s"%soup.find(id="form1")["action"]
        content=self.do_post(self.session,url,data).text
        print "sleep 10秒"
        return content

    def get_page(self,year,benzhuan,score,province,wenli,params_path):
        url="http://gk.sooxue.com/query.aspx"
        data={
                "__VIEWSTATE":self.__VIEWSTATE,
                "__EVENTVALIDATION":self.__EVENTVALIDATION,
                "ctl00$PageContent$cengci_6":benzhuan,
                "ctl00$PageContent$year_2":year,
                "ctl00$PageContent$queryType_2":"fs",
                "ctl00$PageContent$inputValue_2":score,
                "ctl00$PageContent$btnTfswcKsqx":"查看考生去向（20搜学币）"
            }
        content=self.do_post(self.session,url,data).text
        while "VerifyCode.aspx" in content:
            print u"出现验证码：识别中..."
            content=self.code_processer(content)
        content_dict={
            "parms":params_path.split(','),
            "content":content
        }
        print json.dumps(content_dict)
        if u"没有找到您查询分数或位次的录取信息" in content:
            self.html_content_file.write(json.dumps(content_dict)+"\n")
            return
        soup=BeautifulSoup(content)
        tables=soup.find_all("table","border4")
        if not tables:
            print "没有数据,异常，重新爬取"
            raise RuntimeError()
        score_rank=-1
        if benzhuan!=u"专科":
            rank_content=soup.find("title").get_text()
            score_rank=re.search("\((\d*)",rank_content.encode("utf-8")).group(1)
        self.html_content_file.write(json.dumps(content_dict)+"\n")
        self.current_balance=int(soup.find(id="ctl00_lb_point").get_text())
        for table in tables:
            batch=table.get_text()
            content=table.find_next("table")
            rows=content.find_all("tr")[1:]
            for row in rows:
                items=row.find_all("td")
                school_name=items[0].get_text()
                major_name=items[1].get_text()
                score_number=items[2].get_text()
                spec_number=items[3].get_text()
                print year,benzhuan,score,province,wenli,school_name,major_name,score_number,spec_number
                row={
                    "score":score,
                    "batch":batch,
                    "location":province,
                    "bz":benzhuan,
                    "school":school_name,
                    "score_number":score_number,
                    "spec":major_name,
                    "spec_number":spec_number,
                    "wl":wenli,
                    "year":year,
                    "score_rank":score_rank
                }
                self.data_file.write(str(row)+"\n")

    def builder_parameter(self,province_list,year_list):
        for province in province_list:
            for year in year_list:
                for wenli in ["文科","理科"]:
                    for benzhuan in ["本科","专科"]:
                        yield province,year,wenli,benzhuan

    def flush(self):
        self.have_get_parm_file.flush()
        self.html_content_file.flush()
        self.data_file.flush()

    def process(self,year,benzhuan,province,wenli):
        score=0
        error_num=0
        while score<=750:
            try:
                params_path="%s,%s,%s,%s,%s"%(province,year,wenli,benzhuan,score)
                if params_path in self.have_get_parm:
                    print "已经爬取，pass!%s"%params_path
                    score+=1
                    continue
                self.get_page(year,benzhuan,score,province,wenli,params_path)
                self.have_get_parm_file.write(params_path+"\n")
                score+=1
                time.sleep(random.randint(5,10))
                if self.current_balance<20:
                    print "账号:%s已经使用完,切换账号"%self.current_account[0]
                    self.switch_account()
                error_num=0
                self.flush()
            except:
                error_num+=1
                traceback.print_exc()
                if error_num==1:
                    self.switch_account(switch=False)
                elif error_num>=2:
                    self.switch_account()

    def init__file(self,province,year):
        have_get_parm_path=os.path.join(os.path.dirname(__file__),"%s_%s_have_get_parm.txt"%(province,year))
        self.html_content_file=open(os.path.join(os.path.dirname(__file__),"%s_%s_html_content.txt"%(province,year)),'a')
        self.have_get_parm=self.get_have_get_parm(have_get_parm_path)
        self.data_file=open(os.path.join(os.path.dirname(__file__),"%s_%s_sooxue_data.txt"%(province,year)),'a')
        self.have_get_parm_file=open(have_get_parm_path,'a')

    def run(self,province_list,year_list):
        for province,year,wenli,benzhuan in self.builder_parameter(province_list,year_list):
            self.init__file(province,year)
            self.account_should_config=[province,wenli]
            if not self.current_account or self.current_balance <20:
                self.switch_account()
            self.process(year,benzhuan,province,wenli)

    def get_bath_info(self):
        self.switch_account()
        for province in province_code_map.keys()[-1:]:
            batch_info_file=open(os.path.join(os.path.dirname(__file__),"bath_info_%s.csv"%province),"w")
            for wenli in wenli_code_map.keys()[-1:]:
                self.account_config(province,wenli)
                bkcontent=self.do_get(self.session,"http://gk.sooxue.com/js/js2014_1/s37k5.js").content
                # zkcontent=self.do_get(self.session,"http://gk.sooxue.com/js/js2013_3/s37k5.js").content;
                bk_data_dict=self.get_bath_info_from_js(bkcontent)
                # zk_data_dict=self.get_bath_info_from_js(zkcontent)
                # self.oupute(batch_info_file,province,wenli,True,bk_data_dict)
                # self.oupute(batch_info_file,province,wenli,False,zk_data_dict)
            batch_info_file.close()

    def oupute(self,ofile,province,wenli,is_benke,data_dict):
        for batch_info in data_dict.values():
            for major in batch_info["major_list"]:
                row=[province,wenli,"本科" if is_benke else "专科",batch_info["batch"],batch_info["sch_name"],major]
                #print " ".join(row)
                row=[item for item in row]
                ofile.write(",".join(row)+"\n")

    def get_bath_info_from_js(self,content):
        data_dict={}
        for line in content.split(";")[1:]:
            if (line.startswith("yx[") or line.startswith("yx_zk[")) and not line.startswith("yx_zk['']"):
                batch_name=None
                list_content=line.split("Array")[1].replace("(","[").replace(")","]")
                sch_list=eval(list_content)
                for item in sch_list:
                    if re.findall("p\d",item[0]):
                        batch_name=item[1]
                    elif re.findall("\d+_\d",item[0]):
                        sch_name=item[1]
                        sch_id=item[0]
                        data_dict.setdefault(sch_id,{})
                        data_dict[sch_id]["sch_name"]=sch_name
                        data_dict[sch_id]["batch"]=batch_name
                    else:
                        raise RuntimeError()
            elif (line.startswith("zy[") or line.startswith("zy_zk[")) and not line.startswith("zy_zk['_"):
                sch_id=re.search("\['(\d*_\d)'\]=",line).group(1)
                list_content=line.split("Array")[1].replace("(","[").replace(")","]")
                major_list=[major[1] for major in eval(list_content)]
                data_dict[sch_id]["major_list"]=major_list
        return data_dict

def get_score_info():
    work_list=[
        # ["吉林",2012],
        # ["新疆",2012],
        # ["宁夏",2012],
        # ["青海",2012],
        # ["青海",2013],
        ["云南",2014]
    ]
    # province_list=["黑龙江"]
    def run(province,year,account_list):
        soonxue=ScoreSooxue(account_list)
        soonxue.run([province],[year])
    index=0
    from concurrent import futures
    with futures.ProcessPoolExecutor(max_workers=5) as e:
        for province,year in work_list:
            accounts=[account_list[idx] for idx in range(len(account_list)) if idx%len(work_list)==index]
            e.submit(run,province,year,accounts)
            index+=1

if __name__ == '__main__':

    import logging
    try:
        import http.client as http_client
    except ImportError:
        import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1
    # You must initialize logging, otherwise you'll not see debug output.
    logging.basicConfig()
    logging.getLogger().setLevel(logging.WARN)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.WARN)
    requests_log.propagate = True
    #def info(type,value,tb):
    #    traceback.print_exception(type,value,tb)
    #    ipdb.pm()
    #sys.excepthook=info
    #ipdb.launch_ipdb_on_exception()
    #ScoreSooxue(account_list[-1:]).get_bath_info()
    get_score_info()
