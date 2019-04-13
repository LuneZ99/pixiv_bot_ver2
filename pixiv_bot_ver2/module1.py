import json
import os

'''
jl = []
nm = open('names.txt', encoding='utf-8')
st0 = nm.read()
st1 = st0.split('\n')
for s in st1:
    ls = s.split(' / ')
    p0 = ls[2].split(' ')
    p1 = '_'.join(p0)
    jl.append((ls[1]+' 東方', p1))
with open('characters.json', 'w', encoding="utf8") as fi:
    json.dump(jl, fi, ensure_ascii=False, indent=4)
nm.close()
'''

os.makedirs('E:/LuneZ99/python/pixiv_bot_ver2/pixiv_bot_ver2/img/aaa')