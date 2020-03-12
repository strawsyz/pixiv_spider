# import imageio
import os
import zipfile
import json
import demjson
import re
from utils.file_util import make_directory


def re_findone(pat, html):
    data = re.findall(pat, html)
    if len(data) == 1:
        data = data[0]
    return data


def complie_re_findone(pat, html):
    """找到第一个符合条件的数据，然后返回"""
    data = pat.findall(html)
    # if len(data) == 1:
    #     data = data[0]
    return data[0]


def re_get_num(pat, html):
    """获得匹配的数量"""
    content = re.findall(pat, html)
    return len(content)


def complie_re_get_num(pat, html):
    """获得匹配的数量"""
    content = pat.findall(html)
    return len(content)


def str2json(str):
    return demjson.decode(str)


def zip2gif(zip_path, dest, illust_id, delays):
    file_path = os.path.join(dest, illust_id)
    make_directory(file_path)
    # with open(zip_path, "wb+") as fp:
    #     fp.write(gif_data)
    temp_file_list = []
    zipo = zipfile.ZipFile(zip_path, "r")
    for file in zipo.namelist():
        temp_file_list.append(os.path.join(file_path, file))
        zipo.extract(file, file_path)
    zipo.close()
    # 读取所有静态图片，合成gif
    image_data = []
    #  for file in temp_file_list:
    #       image_data.append(imageio.imread(file))
    # 第一种报错    ValueError: Image is not numeric, but
    # Array.
    # 第二种报错    ValueError: quantization error
    #  imageio.mimsave(os.path.join(file_path, illust_id + ".gif"), image_data, "GIF", duration=delays)
    # 清除所有中间文件。
    for file in temp_file_list:
        os.remove(file)


def remove_punctuations(text, punctuation=None, replace='', pat=None):
    """
    去掉标点符号
    :param text: 文本
    :param punctuation: 要去掉符号
    :param replace: 代替的文字
    :param pat: 如果有特定的符号要去掉，需要有特定找到符号的模式
    :return:
    """
    if punctuation is not None:
        # pattern = re.compile(r'[{}]+'.format(punctuation))
        return re.sub(r'[{}]+'.format(punctuation), replace, text)
    else:
        return pat.sub(replace, text)
