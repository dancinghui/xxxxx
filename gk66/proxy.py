#coding:utf-8
import json
import traceback
import requests

def get_ip_list():
    url='http://svip.kuaidaili.com/api/getproxy?'
    data={
        "orderid":"953383017901599",
        "num":"1",
        "quality":"1,2",
        "area_ex":"广东,香港,湖南,湖北,福建,江西,贵州,湖北",
        "method":"1,2",
        "browser":"2",
        "an_ha":"1",
        "an_an":"1",
        "format":"json",
        "f_sp":1
    }
    for key,value in data.items():
        url+="&%s=%s"%(key,value)
    content=requests.get(url).text
    print content
    try:
        jscontent=json.loads(content)
    except:
        traceback.print_exc()
        return []
    if jscontent["code"]!=0:
        print jscontent["msg"]
        return []
    return jscontent["data"]["proxy_list"]

def confirm(ip):
    proxy = {'http':ip}
    print "测试IP:%s"%ip
    try:
        url="http://gk.sooxue.com/image/grey.gif"
        requests.get(url,proxies=proxy,timeout=3)
        return True
    except:
        print "ip:%s失效！"%ip
        return False

def get_proxy_and_confirm():
    while True:
        ip_list=get_ip_list()
        if  len(ip_list)>0:
            ip,delay=str(ip_list[0]).split(',')
            print ip,delay
            if float(delay)<2 and confirm(ip):
                return ip

if __name__ == '__main__':
    print get_proxy_and_confirm()
    # confirm("183.222.164.23")
