#! /usr/bin/env python
# encoding:utf-8
import csv
import os
import re
import spider.util
import spider.runtime


class YggkSum(object):
    def __init__(self):
        pass
    def _get_prov_dict(self):
        f = open("prov_list", "rb")
        prov_dict = {}
        line = f.readline()
        while line:
            prov_info = {}
            prov_no, prov_name= line.strip().split(" ")
            prov_dict[str(prov_no)] = prov_name
            line = f.readline()
        return prov_dict
    def sum(self):

        csvfile = file("yggk2015.csv", "w+b")
        cwriter = csv.writer(csvfile)
        cwriter.writerow(["enroll_loc_name", "sch_name", "enroll_major_count", "enroll_major_name", "plan_type", "enroll_diploma",
                          "major_cate", "enroll_plan_count"])
        prov_dict = {}
        prov_dict = self._get_prov_dict()
        emptycnt = 0
        for dir in prov_dict.keys():
            prov_file = open("prov/" + dir + ".txt")
            for line in prov_file.readlines():
                line = line.strip()
                enroll_loc_name = prov_dict.get(dir, None)
                sch_name = line.split(" ")[0]
                enroll_major_count = line.split(" ")[-1]
                enroll_major_name = "-"
                plan_type = "-"
                enroll_diploma = "-"
                major_cate = "-"
                enroll_plan_count = "-"
                for filename in os.listdir("extract/"+dir):
                    if sch_name in filename:
                        planfile = open("extract/%s/%s" % (dir, filename), "rb")
                        for lline in planfile.readlines():
                            lline = lline.strip()
                            if r"此专业在该省无分省招生计划" in lline:
                                spider.runtime.Log.warning(sch_name+" 在 "+ enroll_loc_name +" 无分省招生计划")
                                emptycnt += 1
                            else:
                                enroll_major_name, plan_type, enroll_diploma, major_cate, enroll_plan_count = lline.split(" ")
                            cwriter.writerow([enroll_loc_name, sch_name, enroll_major_count, enroll_major_name, plan_type
                                              , enroll_diploma, major_cate, enroll_plan_count])
                            csvfile.flush()
                        break
        csvfile.close()


if __name__ == "__main__":
    YggkSum().sum()