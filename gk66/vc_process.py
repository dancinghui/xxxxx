#coding:utf-8
import os
import json
import re

province_list=["吉林","新疆","宁夏","青海"]

province_list=["青海"]
year_list=[2013]

def process(parm_path,html_path):
    parms=[]

    with open(parm_path) as f:
        while True:
            line=f.readline()
            if not line:break
            parms.append(line.strip())

    with open(html_path) as f:
        while True:
            line=f.readline()
            if not line:break
            if not "vc.aspx" in line:continue
            try:
                js=eval(line)
            except:
                print "error"
                pass
            print json.dumps(js)
            parm=",".join(js["parms"])
            if parm in parms:
                parms.remove(parm)
            print "remove ",parm

def vc_process():
    # dir=os.path.dirname(__file__)
    for province in province_list:
        for year in year_list:
            # if not os.path.exists(os.path.join(dir,"%s_%s_have_get_parm.txt"%(province,year))):continue
            process("%s_%s_have_get_parm.txt"%(province,year),"%s_%s_html_content.txt"%(province,year))


if __name__=="__main__":
    vc_process()
