#!/usr/bin/python
# -*- encoding:utf8 -*-

from mongoengine import Document
from mongoengine.fields import StringField, IntField, FloatField

class Score_gk66(Document):
    """
    各省份录取分数线
    TODO(专业名称需要替换掉)
    """
    location            = StringField(help_text = "省份")
    year                = StringField(help_text= "年份")
    bz                  = StringField(help_text = "b: 本科, z: 专科")
    wl                  = StringField(help_text = "w: 文科, l: 理科")

    school              = StringField(help_text = "学校")
    spec                = StringField(help_text = "专业")
    rank                = StringField(help_text = "名次")
    score               = StringField(help_text = "分数")
    batch               = StringField(help_text= "批次")
    score_number        = StringField(help_text = "本分录取人数")
    spec_number         = StringField(help_text = "本专业录取人数")
    high_score          = StringField(help_text = "最高分")
    high_score_rank     = StringField(help_text = "最高分名次")
    low_score           = StringField(help_text = "最低分")
    low_score_rank      = StringField(help_text = "最低分名词")
    average_score       = StringField(help_text = "学校投档分")
    average_score_rank  = StringField(help_text = "学校投档分")

    level_1             = StringField(help_text = "选测科目等级1")
    level_2             = StringField(help_text = "选测科目等级2")

    meta = {"db_alias":"gk66", "collection":"gk66_score"}


