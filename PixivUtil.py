import requests
import logging
import re
import demjson
import requests
from DbUtil import DbUtil
from spiderUtil import spiderUtil
import os

class PixivUtil():

    def __init__(self, username, password, logger):
        self.BASE_URL = "https://www.pixiv.net/"
        self.ToGetKeyURL = "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"
        self.postURL = "https://accounts.pixiv.net/api/login?lang=zh"  # 登陆页面

        self.Agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36"
        self.Origin = "https://accounts.pixiv.net"
        self.Referer = "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"
        self.Host = "accounts.pixiv.net"

        self.URL4GET_ILLUST_ID = "https://www.pixiv.net/ajax/user/{userId}/profile/all"
        self.URL_ILLUST_PAGE = "https://www.pixiv.net/member_illust.php?mode=medium&illust_id={illust_id}"  # 插画页面

        self.username = username
        self.password = password
        self.headers = {
            'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
            'User-Agent': 'User-Agent:Mozilla/5.0'
        }
        request_retry = requests.adapters.HTTPAdapter(max_retries=3)  # 尝试三次请求
        self.session = requests.Session()
        self.session.mount('https://', request_retry)
        self.session.mount('http://', request_retry)
        self.spider_util = spiderUtil(logger)
        #  操作数据库
        self.db_util = DbUtil("localhost", "root", "straw@syz", "test", "utf8")
        self.sql_4_insert = 'insert  into illust(title,url,illust_id,illuster_id,page_no,status)values("{title}","{url}","{illust_id}",{illuster_id},"{page_no}",0)'
        self.sql_4_insert_2_done = 'insert  into illust(title,url,illust_id,illuster_id,page_no,status)values("{title}","{url}",{illust_id},{illuster_id},0, 10)'


    def set_logger(self,logger):
        self.logger = logger

    def download_illust_by_illust_id(self, dir,illuster_id,illust_id):
        res = self.db_util.get_one("select * from illust where status = 10 and illust_id = " + illust_id)
        if res:
            self.logger.debug(" 本插画已被下载 illust_id 是 " + illust_id)
            return True
        illust_info = self.get_img_info_by_img_id(illust_id)
        page_count = illust_info["pageCount"]
        img_url = illust_info["urls"]["original"]  # 原图
        temp = img_url.split("_p0")
        res = True
        for i in range(page_count):
            try:
                try:
                    img_url_temp = temp[0] + "_p" + str(i) + temp[1]
                except IndexError as e:
                    img_url_temp = img_url
                    self.logger.error("有可能是动图" + repr(e) + "url是" + img_url, exc_info=True)
                    # 动图的处理
                sql = self.sql_4_insert.format(title=illust_info["illustTitle"], url=img_url_temp,
                                         illust_id=illust_id, illuster_id=illuster_id, page_no=i)
                self.db_util.insert(sql)
                res = res and self.spider_util.download(img_url_temp, dir, header=self.headers)
            except Exception as e:
                res = False
                self.logger.error("下载有问题" + repr(e) + "url是" + img_url_temp, exc_info=True)
        if res:
            self.db_util.update('update illust set status = 10 where illust_id = ' + illust_id)

    # 获取需要post的数据postkey
    def get_post_key(self, url):
        pat = 'name="post_key" value="(.*?)"'
        content = self.session.get(url).text  # 这边，就算不用组装headers也能拿到postKey，但是一定要是get，不能使用post
        res_temp = re.findall(pat, content)
        if len(res_temp) != 1:
            logging.error("无法获得postKey", exc_info=True)
            return None
        postkey = re.findall(pat, content)[0]
        logging.info("your post key is "+postkey)
        return postkey

    #进行模拟登陆
    def login(self):
        postKey = self.get_post_key( self.ToGetKeyURL)
        post_data = \
            {
                "pixiv_id": self.username,
                "password": self.password,
                #"captcha": "",
                #"g_recaptcha_response":"",
                "post_key": postKey,
                #"source":"pc",
                "ref": "wwwtop_accounts_index",
                "return_to": "https://www.pixiv.net/"
             }
        result = self.session.post(self.postURL, data=post_data, headers=self.headers)  # 装个头，能解决一些问题
        temp = result.text
        pat = '"body":{"(.*?)"'
        isLoginFlag = re.findall(pat, temp)[0]
        if isLoginFlag == 'success':
            logging.info("maybe Login Successfully. username id " + self.username)
            return True
        else:
            logging.debug("Login failed")
            return False

    def get_illust_ids(self,illuster_id):
        '''
        根据画师Id获得画师的插画Id
        :param illuster_id:
        :return:
        '''
        illust_id_json = self.session.get(self.URL4GET_ILLUST_ID.format(userId=illuster_id)).text  # 获得所有的图片Id
        illust_id_json = str2json(illust_id_json)
        # 判断是否有新的插画
        ill_ids = illust_id_json["body"]["illusts"]  # 示例：{[illust_id]:[illust_info],[illust_id]:[illust_info],[illust_id]:[illust_info]...}
        return list(ill_ids.keys())

    def get_manga_ids(self, illuster_id):
        '''
        根据画师Id获得画师的漫画Id
        :param illuster_id:
        :return:
        '''
        illust_id_json = self.session.get(self.URL4GET_ILLUST_ID.format(userId=illuster_id)).text  # 获得所有的图片Id
        # print(illust_id_json)
        illust_id_json = str2json(illust_id_json)
        manga_ids = illust_id_json["body"]["manga"]
        return manga_ids.keys()

    def get_img_info_by_img_id(self, img_id):
        '''
        根据插画或漫画的Id获得插画或者漫画的详细信息
        :param img_id:
        :return:
        '''
        try:
            temphtml = self.session.get(self.URL_ILLUST_PAGE.format(illust_id=img_id), timeout=300).text
            illust_info = getjson(temphtml)  # 根据页面信息获得json
            illust_info = str2json(illust_info)  # 解析json
            main_illust_info = illust_info["preload"]["illust"][int(img_id)]
            return main_illust_info
        except Exception as e:
            self.logger.error("获取插画信息失败" + repr(e) + "illust_id是" + img_id, exc_info=True)

    def getjson(self, html):
        '''
        解析作品页面的详细信息
        :param html:
        :return:
        '''
        pat = '}\)\((.*?)\);</script><link rel="apple-touch-icon"'
        data = re.findall(pat, html)
        # print(data)
        if len(data) == 1:
            data = data[0]
        return data


# 判断文件夹是否存在，如果不存在就新建文件夹
def makeDirectory(dicName):
    if not os.path.exists(dicName):
        os.makedirs(dicName, mode=0o777)

#  解析需要的json数据
def getjson(html):
    pat = '}\)\((.*?)\);</script><link rel="apple-touch-icon"'
    data = re.findall(pat, html)
    if len(data) == 1:
        data = data[0]
    return data

def str2json(str):
    return demjson.decode(str)

def getPath(rootPath, illustrator_id):
    return rootPath+illustrator_id+"/";
