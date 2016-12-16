#!/bin/usr/env python
#-*- coding: utf-8 -*-
import os
import mongoengine
import sys

#from ipin.gaokao.score.model.score_gxmk import Score_gxmk
from score_gk66 import Score_gk66


mongoengine.connect(None,alias="gk66",host="mongodb://crawler:crawler@192.168.1.81,192.168.1.82,192.168.1.83/gaokao_crawler",socketKeepAlive=True,wtimeout=100000)

def store_score(value):
    print value
    obj=Score_gk66.objects(location=value["location"],year=value["year"],bz=value["bz"],wl=value["wl"],school=value['school'],spec=value['spec'],rank=value['rank'],score=value['score'],batch=value["batch"],score_number=value['score_number'],spec_number=value['spec_number'],high_score=value['high_score'],high_score_rank=value['high_score_rank'],low_score=value['low_score'],low_score_rank=value['low_score_rank'],average_score=value['average_score'],average_score_rank=value['average_score_rank'],level_1=value['level_1'],level_2=value['level_2']).no_cache().timeout(False).first()
    if not obj:
        obj=Score_gk66(location=value["location"],year=value["year"],bz=value["bz"],wl=value["wl"],school=value['school'],spec=value['spec'],rank=value['rank'],score=value['score'],batch=value["batch"],score_number=value['score_number'],spec_number=value['spec_number'],high_score=value['high_score'],high_score_rank=value['high_score_rank'],low_score=value['low_score'],low_score_rank=value['low_score_rank'],average_score=value['average_score'],average_score_rank=value['average_score_rank'],level_1=value['level_1'],level_2=value['level_2'])
        obj.save()
    else:
        print u"数据已存在"

def main(loc):
    datapath=os.path.join(os.path.dirname(__file__),"%s_data.txt"%loc)
    with open(datapath) as f:
        while True:
            line=f.readline()
            print 'line == ' ,line
            if not line:break
            value=eval(line)
            print 'value == ',value
            store_score(value)

if __name__ == '__main__':
    #main(sys.argv[1])
    main('江苏')
