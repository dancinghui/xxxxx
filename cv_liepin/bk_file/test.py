#coding=UTF-8
m = ''
with open('qy_page.html', 'rb') as f:
    m = f.read()

print type(m)
# print m

import re
# find = re.findall(r'/resume/showresumedetail/\?(res_id_encode=[^" ]*)', m, re.S)
'共\s*<[^<>]*>\s*(\d+)\s*<[^<>]*>\s*人选'
find = re.findall(r'<table[^<>]*>(.*?)</table>', m, re.S)

for u in find:
    print u
# m = re.search(r'(\d+)\+\s*<[^<>]*>\s*份简历', m, re.S)
print find
