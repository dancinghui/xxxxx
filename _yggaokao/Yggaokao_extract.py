#! /usr/bin/evn python
#encoding:utf-8

import re
import os
import spider.util
import spider.runtime
class YggkExtract(object):
    def __init__(self):
        pass
    def extract_major(self):
        folders = os.listdir("detail")
        for folder in folders:
            files = os.listdir("detail/"+folder)
            for file in files:
                f = open ("detail/"+folder+"/"+file, "r+b")
                if not os.path.exists("extract/" + folder):
                    os.makedirs("extract/" + folder)

                content = ""
                for line in f.readlines():
                    content += line
                t = re.findall(r"<h2>(.*?)</h2>", content, re.S)
                schoolname = ""
                if len(t) is 0:
                    spider.runtime.Log.error("detail/"+folder+"/"+file+"No school name!!!!\n")
                else:
                    schoolname = t[0].strip()

                fw = open ("extract/" + folder + "/" + file.split(".")[0] + "_" + schoolname + ".txt", "w+b")
                province_data_list = re.findall(r">分省招生的专业<(.*?)>不分省招生的专业<", content, re.S)
                if len(province_data_list) is 0:
                    spider.runtime.Log.error(folder+"/"+file+",无法截取分省招生专业信息\n")
                    continue
                province_data = province_data_list[0]
                if r"此专业在该省无分省招生计划" in province_data:
                    spider.runtime.Log.error(folder+"/"+file+",没有分省招生专业信息\n")
                major_list = re.findall(r"<tbody.*?>(.*?)</tbody>", province_data, re.S)
                if len(major_list) is 0 and r"此专业在该省无分省招生计划" in province_data:
                    spider.runtime.Log.error(folder+"/"+file+",没有分省招生专业信息\n")
                    fw.write("此专业在该省无分省招生计划\n")
                    continue
                elif len(major_list) is 0:
                    spider.runtime.Log.error(folder+"/"+file+",无法截取专业招生专业信息\n")
                    continue
                else:
                    for major_content in major_list:
                        type_list = re.findall(r"<tr.*?>(.*?)</tr>", major_content, re.S)
                        if len(type_list) is 0:
                            spider.runtime.Log.error(folder+"/"+file+"/" + major_name + ",没有信息\n")
                            continue
                        major_name = ""
                        for i in range(len(type_list)):
                            type_content = type_list[i]
                            tds = re.findall(r"<td.*?>(.*?)</td>", type_content, re.S)
                            if len(tds) is 0:
                                spider.runtime.Log.error(type_content+"--------------No tds!!!\n")
                                continue

                            if i is 0:
                                l = re.findall(r">(.*?)<", tds[0], re.S)
                                if len(l) is not 0:
                                    major_name = l[0].strip()
                                elif len(l) is 0 and tds[0].strip() is not "":
                                    major_name = tds[0].strip()
                                else:
                                    spider.runtime.Log.error(tds[0]+"----------------No major name!\n")

                            enroll_plan_count = tds[-1].strip()
                            major_cate = tds[-3].strip()
                            enroll_diploma = tds[-4].strip()
                            plan_type = tds[-5].strip()

                            print major_name+" "+plan_type + " "\
                                     + enroll_diploma + " " + major_cate + " "\
                                     + enroll_plan_count +"\n"
                            fw.write(major_name+" "+plan_type + " "
                                     + enroll_diploma + " " + major_cate + " "
                                     + enroll_plan_count +"\n")
                            fw.flush()
                fw.close()
                f.close()







if __name__ == "__main__":
    y = YggkExtract()
    y.extract_major()
    exit()