import configparser
import requests
import re
import ssl
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
import urllib.error
import time
import logging
import json
import demjson
from spiderUtil import spiderUtil
from DbUtil import DbUtil
from PixivUtil import PixivUtil
import threading

# 判断文件夹是否存在，如果不存在就新建文件夹
def makeDirectory(dicName):
    if not os.path.exists(dicName):
        os.makedirs(dicName, mode=0o777)

#  解析需要的json数据
def getjson(html):
    pat = '}\)\((.*?)\);</script><link rel="apple-touch-icon"'
    data = re.findall(pat, html)
    # print(data)
    if len(data) == 1:
        data = data[0]
    return data

def getPath(rootPath, illustrator_id):
    return rootPath+illustrator_id+"/";


#  新版的爬取pixiv的插画
if __name__ == '__main__':

    # 第一步，创建一个logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Log等级总开关
    # 第二步，创建一个handler，用于写入日志文件
    rq = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    log_path = os.path.dirname(os.getcwd()) + '/Logs/'
    log_name = log_path + rq + '.log'
    logfile = log_name
    fh = logging.FileHandler(logfile, mode='w')
    fh.setLevel(logging.DEBUG)  # 输出到file的log等级的开关
    # 第三步，定义handler的输出格式
    formatter = logging.Formatter("%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    fh.setFormatter(formatter)
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    console.setFormatter(formatter)
    # 第四步，将logger添加到handler里面
    logger.addHandler(fh)
    logger.addHandler(console)

    try:
        conf = configparser.ConfigParser()
        conf.read("config.conf")
        ids = conf.items("ids")
        rootPath = conf.get("path","path")  # 下载图片存储的根目录
        host = conf.get("mysql","host")
        dbusername = conf.get("mysql","username")
        dbpassword = conf.get("mysql","password")
        dbname = conf.get("mysql","dbname")
        charset = conf.get("mysql","charset")
        username = conf.get("pixivaccount", "username")
        password = conf.get("pixivaccount", "password")
    except Exception as e:
        logger.error("请检查你配置的下载路径====》"+repr(e), exc_info=True)  # Python中的traceback模块被用于跟踪异常返回信息，可以在logging中记录下traceback
        raise e

    #  操作数据库
    db_util = DbUtil(host, dbusername, dbpassword, dbname, charset)
    sql_4_insert = 'insert  into illust(title,url,illust_id,illuster_id,page_no)values("{title}","{url}","{illust_id}",{illuster_id},"{page_no}")'
    sql_4_insert_2_done = 'insert  into illust(title,url,illust_id,illuster_id,page_no,status)values("{title}","{url}",{illust_id},{illuster_id},0, 10)'

    ssl._create_default_https_context = ssl._create_unverified_context
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    #  测试。用来解决, 'ssl3_read_bytes', 'sslv3 alert bad record mac')
    requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL'
    x = 1

   
    pixiv_util = PixivUtil(username, password, logger)
    pixiv_util.set_logger(logger)
    if pixiv_util.login():
        session = pixiv_util.session  # 获得登陆后的会话
        headers = {
            'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
        }

        for id in ids:  # 循环画师Id
            illuster_id = id[1]
            logger.info("正在下载的是" + illuster_id + "的作品")
            res =db_util.get_one("select * from illuster where illuster_id = " + illuster_id)
            if res:
                logger.debug("该画师已存在"+illuster_id)
            else:
                now = int(time.time())
                time_struct = time.localtime(now)
                strTime = time.strftime("%Y-%m-%d %H:%M:%S", time_struct)
                db_util.insert("insert into illuster(illuster_id,create_time,modify_time) value("+illuster_id+",'"+strTime+"','"+strTime+"')")
            dir = getPath(rootPath, illuster_id)  # 根据画师Id获得保存的图片的地址
            makeDirectory(dir)  # 创建目录
            illust_ids = pixiv_util.get_illust_ids(illuster_id)
            print("共有插图%d个"%(len(illust_ids)))
            logger.info("共有插图%d个"%(len(illust_ids)))
            # threads = []
            for illust_id in illust_ids:  # 循环的到的illust_id
                pixiv_util.download_illust_by_illust_id(dir, id[1], illust_id)
            logger.info(id[1]+"的作品下载完成")
        logger.info("所有的作品下载完成")
        session.close()
    else:
        logger.error("登陆失败")

