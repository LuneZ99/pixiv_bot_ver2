import pixivpy3 as p
import os
import re
import random as r
import time
import threading
import json
import sys


# tag热图搜索 会员限定
def search_by_tag_popular(word, duration=None, num=1, p_num=2):
    img_list = []
    for pi in range(p_num):
        json_result = api.search_illust(word, duration=duration, sort='popular_desc')
        # print(len(json_result))
        img_list.extend(json_result.illusts)
        # print(len(img_list))
    print(img_list[0])
    print(img_list[30])
    try:
        for n in range(num):
            i = r.randint(0, len(img_list) - 1)
            illust = img_list[i]
            # print(illust['total_bookmarks'])
            api.download(illust.image_urls['large'], path='img/', name=word+'_'+str(n)+'.jpg')
            img_list_out.append('img/'+word+'_'+str(n)+'.jpg')
        return img_list_out, ''
    except ValueError:
        return [], '没有这个tag相关的图片！'

def main():

    # 获得输入 可接受输入：来份色图/来n份色图/来份图/来n份图/tag... 其他输入会输出'你在做什么我不太懂呀~'
    text = input()
    # text = ' '.join(sys.argv[1:])
    # 初始化输出
    tags_file = open('tags_list.json', 'r', encoding="utf8")
    tags_list = json.load(tags_file)
    output = {
        'text': '',         # 回复的消息内容
        'qq': None,         # @某qq回复
        'img_list': [],     # 要发送的图片列表
    }
    try:
        # time_limit(1)

        # 寻找当天r18色图
        if text.startswith('来') and text.endswith('份色图'):
            if text == '来份色图':
                # output['img_list'], output['text'] = search_by_tag_popular(word='r18', p_num=2)
                output['img_list'], output['text'] = rank_by_time(mode='week_r18')
            else:
                num = re.search('\d+', text).group()
                if num:
                    # output['img_list'], output['text'] = search_by_tag_popular(word='r18', num=int(num), p_num=2)
                    output['img_list'], output['text'] = rank_by_time(mode='week_r18', num=int(num))
                else:
                    output['text'] = '输入有误！'

        # 当天热门榜随机
        elif text.startswith('来') and text.endswith('份图'):
            if text == '来份图':
                output['img_list'], output['text'] = rank_by_time(mode='day_male')
            else:
                num = re.search('\d+', text).group()
                if num:
                    output['img_list'], output['text'] = rank_by_time(mode='day_male', num=int(num))
                else:
                    output['text'] = '输入有误！'

        # 按tag搜寻:
        elif text.startswith('tag'):
            # tag搜寻帮助
            if text == 'tag':
                output['text'] += '用法：\n1 “tag 标签1 标签2 ……”\n2 tag查询后按序号检索'
            # 列出推荐tag列表
            elif text == 'tag查询' or text == 'tag查找':
                tags_list = get_tags()
                for i in range(len(tags_list)):
                    output['text'] += str(i + 1) + ' ' + tags_list[i] + '\n'
                output['text'] = output['text'][:-1]
            # 直接搜寻tag
            elif text.startswith('tag '):
                word = text[4:]
                output['img_list'], output['text'] = search_by_tag_popular(word=word)

        # 按tag列表索引
            else:
                if not tags_list:
                    output['text'] = '你还没查询过tag，不能使用tag索引！使用"tag查询"来获取tag'
                else:
                    output['img_list'], output['text'] = search_by_tag_popular(word=tags_list[int(text[3:])-1])

        elif text == '帮助':
            output['text'] = '可接受指令：\n来份色图\n来n份色图\n来份图\n来n份图\ntag'
        # 未知输入
        else:
            output['text'] = '你在做什么我不太懂呀~'

    # 报错
    # except RuntimeError():
    #     output['text'] = '超时了，网络似乎不好呢'
    except:
        output['text'] = '人偶出现bug，请联系开发者进行维护'

    # tag输出为json文件
    with open('tags_list.json', 'w', encoding="utf8") as fi:
        json.dump(tags_list, fi, ensure_ascii=False, indent=4)

    # 打印json
    print(json.dumps(output, ensure_ascii=False))


def test():
    search_by_tag_popular(word='百合')
# 全局变量
# _tags_list = []                         # tag列表
# 账号密码
_USERNAME = "corgiclub@yeah.net"
_PASSWORD = "corgiclubADMIN"

# 登录api
api = p.AppPixivAPI()
api.login(_USERNAME, _PASSWORD)

