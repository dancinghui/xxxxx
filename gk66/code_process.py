# -*- coding: utf-8 -*-
import traceback
import time
import requests

CREATE_URL = 'http://bbb4.hyslt.com/api.php?mod=php&act=upload'
REPORTERROR_URL = 'http://bbb4.hyslt.com/api.php?mod=php&act=error'

class DaMaException(Exception):
    pass

class Lianzhong:
    def __init__(self, s, user, pwd, soft_key, image_type = "3040", timeout=60):
        self.timeout = timeout
        self.image_type = image_type
        self.s = s
        self.soft_key = soft_key
        self.pwd = pwd
        self.user = user
        self.login()

    def create(self, img_data):
        data = {
            'user_name': self.user,
            'user_pw': self.pwd,
            'yzm_maxlen':'',
            'yzm_minlen':'',
            'yzmtype_mark':'',
            'zztool_token':self.soft_key
        }

        files = {'upload': ('a.jpg', img_data)}
        try:
            r = self.s.post(CREATE_URL, data=data, files=files)

            if not r.text:
                raise RuntimeError()
            j = r.json()
        except ValueError:
            print "联众返回异常[%s]" % r.text
            time.sleep(1)
            raise RuntimeError()
        except:
            traceback.print_exc()
            time.sleep(1)
            raise RuntimeError()
        try:
            if 'result":true,' in r.text:
                return j["data"]['val'], j["data"]["id"]
            elif "已经损坏或者不是正确的图像格式" in j.get("Error",""):
                time.sleep(1)
                raise RuntimeError()
            else:
                print r.text
                raise DaMaException("联众服务返回异常数据[%s]" % r.text)
        except:
            print r.text
            raise DaMaException("联众服务返回异常数据1[%s]" % r.text)

    #登录帐号
    def login(self):
        errorMsg = {'-1': '参数错误，用户名为空或密码为空', '-2': '用户不存在', '-3': '密码错误', '-4': ' 账户被锁定', '-5': ' 非法登录',
                    '-6': ' 用户点数不足，请及时充值', '-8': ' 系统维护中', '-9': ' 其他'}
        url="http://bbb4.hyslt.com/api.php?mod=php&act=point"
        data = {
            'user_name': self.user,
            'user_pw': self.pwd,
            }
        text=self.s.post(url,data).text

        if u'密码错误' in text:
            raise Exception(errorMsg['-3'])
        elif 'name or pw error' in text:
            raise Exception(errorMsg['-1'])

    #上传验证码
    def report_error(self, id):
        data = {
            'user_name': self.user,
            'user_pw': self.pwd,
            'yzm_id': id,
            }
        r = self.s.post(REPORTERROR_URL, data=data)
        text = r.text
        if 'result":true' in text:
            pass
        else:
            raise DaMaException("联众报告错误异常[%s]" % text)


def get_code(image_content):
    retry=3
    while retry>=0:
        try:
            #联众帐号，密码
            user="brantbzhang"
            pwd="15004622415"

            #软件key 或者作者帐号
            soft_key="fpTof8NxP4FTFOTp6Tfi3ik6TxtfEOkE68nE3foK"
            s=requests.Session()
            lz=Lianzhong(s,user,pwd,soft_key)

            vcode,vid=lz.create(image_content)
            return vcode
        except:
            traceback.print_exc()
            retry-=1
            raise RuntimeError()


if __name__=="__main__":
    content=requests.get("http://gk.sooxue.com/VerifyCode.aspx?")
    # print content.content
    print get_code(content.content)




