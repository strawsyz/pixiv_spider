import re
import requests
from utils.mysql_util import MysqlUtil as DbUtil
from utils.spider_util import SpiderUtil
import os
from utils.conf_util import ConfigureUtil
from utils.data_clean_util import str2json
from common.work_status import WorkStatus
from common.illust_type import IllustType
from utils.log_util import Log


class PixivUtil:
    def __init__(self):
        self.init_pattern()
        self.load_config()

        self.logger = Log(__name__).get_log()
        self.GET_KEY_PAGE = "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"
        self.LOGIN_PAGE = "https://accounts.pixiv.net/api/login?lang=zh"  # 登陆页面

        self.UGOIRA_URL = 'https://www.pixiv.net/ajax/illust/{illust_id}/ugoira_meta'  # 动图url,0填写动图的id
        self.URL_4_GET_ALL_WORK_ID = "https://www.pixiv.net/ajax/user/{userId}/profile/all"  # 画师的所有作品信息
        self.URL_4_ILLUSTER_MAIN_PAGE = "https://www.pixiv.net/ajax/user/{}/profile/top"  # 画师主页24个作品信息,少量画师信息
        self.URL_4_GET_ILLUSTER_INFO = "https://www.pixiv.net/ajax/user/{}?full=1"  # 用于获得画师信息
        self.URL_ILLUST_PAGE = "https://www.pixiv.net/member_illust.php?mode=medium&illust_id={illust_id}"  # 插画页面
        self.URL_ILLUST_PAGE = "https://www.pixiv.net/ajax/illust/{illust_id}"  # 插画页面

        self.REFERER = "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"
        self.USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36"

        self.headers = {
            'Referer': self.REFERER,
            'User-Agent': self.USER_AGENT
        }
        # 方法二：设置请求失败之后重复请求次数
        # requests.adapters.DEFAULT_RETRIES = self.max_retries

        self.session = requests.Session()
        if self.cookie is not None:
            self.session.cookies.set("authentication", self.cookie)
        if self.proxies['http'] is not None or self.proxies['https'] is not None:
            self.session.proxies = self.proxies  # 设置session默认代理

        # 方法1：设置请求失败之后重复请求次数
        request_retry = requests.adapters.HTTPAdapter(max_retries=self.max_retries)
        self.session.mount('https://', request_retry)
        self.session.mount('http://', request_retry)

        # self.session.keep_alive = False

        self.spider_util = SpiderUtil()
        #  操作数据库
        self.db_util = DbUtil()
        self.sql_4_insert = 'insert into illust(title,url,illust_id,illuster_id,page_no,status,`restrict`,x_restrict)' \
                            'values ( %s, %s, %s, %s, %s, 0, %s, %s)'
        self.sql_4_insert_4_ugoira = 'insert  into illust(title,url,illust_id,illuster_id,page_no,status)values( %s, %s, %s, %s, %s,444)'
        self.sql_4_insert_2_done = 'insert  into illust(title,url,illust_id,illuster_id,page_no,status)values( %s, %s, %s, %s, 0, 10)'

    def get_session(self):
        if self.login():
            return self.session
        else:
            self.logger.error("登陆失败,请检查账号密码是否正确和网络是否连通")
            return 'error'

    def load_config(self):
        config = ConfigureUtil('config/config.conf')
        http_proxy = config.get('proxy', 'http', is_error=True)
        https_proxy = config.get('proxy', 'https', is_error=True)
        self.proxies = {'http': http_proxy, 'https': https_proxy}
        # 重试次数必须是数值类型
        self.max_retries = config.get('app', 'max_retries', 'int')
        #  超时时间， 单位是秒
        self.timeout = config.get('app', 'time_out', type_="int", is_error=True, default=20)
        self.username = config.get('account', 'username')
        self.password = config.get('account', 'password')
        # self.cookie = "p_ab_id=0; p_ab_id_2=3; login_ever=yes; a_type=0; b_type=1; first_visit_datetime_pc=2018-06-06+10%3A53%3A26; _ga=GA1.2.1555034815.1497772914; p_ab_d_id=1974173592; yuid_b=NXcmaYM; module_orders_mypage=%5B%7B%22name%22%3A%22sketch_live%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22following_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22tag_follow%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22recommended_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22everyone_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22mypixiv_new_illusts%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22fanbox%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22featured_tags%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22contests%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22user_events%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22sensei_courses%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22spotlight%22%2C%22visible%22%3Atrue%7D%2C%7B%22name%22%3A%22booth_follow_items%22%2C%22visible%22%3Atrue%7D%5D; ki_r=; __utmc=235335808; OX_plg=pm; c_type=26; __utmv=235335808.|2=login%20ever=yes=1^3=plan=normal=1^5=gender=male=1^6=user_id=27971320=1^9=p_ab_id=0=1^10=p_ab_id_2=3=1^11=lang=zh=1; gsScrollPos-422=; _td=5e2a3ce8-e5ca-4e1c-9bc5-4188deff8d9d; ki_s=197685%3A0.0.0.0.0; gsScrollPos-73=; gsScrollPos-74=0; __utmz=235335808.1558931621.48.3.utmcsr=accounts.pixiv.net|utmccn=(referral)|utmcmd=referral|utmcct=/login; limited_ads=%7B%22responsive%22%3A%22%22%7D; PHPSESSID=27971320_a3ba646dd6d6fe402a566008ca109afe; privacy_policy_agreement=1; ki_t=1539786814040%3B1564299004430%3B1564299004430%3B7%3B11; categorized_tags=0Gd_u69FDa~0VZuk18GJB~0roTzTKxJy~7cMRrOPRjW~BU9SQkS-zU~EQHKvBDRBz~IVwLyT8B6k~Ig5OcZugU6~OEXgaiEbRa~OT-C6ubi9i~RcahSSzeRf~RkTaP3d-E6~_-agXPKuAQ~b8b4-hqot7~cpt_Nk5mjc~jYnWl04aAC~l2rugVKl6u~r70NVOGJ5H~xlfjJKgpwx~y8GNntYHsi; __utmt=1; __utma=235335808.1555034815.1497772914.1564650150.1564650214.63; tag_view_ranking=0xsDLqCEW6~Ie2c51_4Sp~BU9SQkS-zU~y8GNntYHsi~RTJMXD26Ak~AI_aJCDFn0~RcahSSzeRf~i83OPEGrYw~8HRshblb4Q~4-_9de7LBH~cpt_Nk5mjc~q3eUobDMJW~skx_-I2o4Y~faHcYIP1U0~404yEt28rv~fFjokb4ZCF~-YeeMY1Yjs~FqVQndhufZ~tgP8r-gOe_~0HA6x-6rNd~Ow9mLSvmxK~KN7uxuR89w~5oPIfUbtd6~NpsIVvS-GF~gooMLQqB9a~Lt-oEicbBr~gpglyfLkWs~jYnWl04aAC~VIOKa7rioU~HBlflqJjBZ~zyKU3Q5L4C~TWrozby2UO~BB4jge2y2O~nyZIqZI1jx~MM6RXH_rlN~3gc3uGrU1V~LJo91uBPz4~laE3IylUE6~_hSAdpN9rx~n7YxiukgPF~l2rugVKl6u~A0c1GtjhvT~KhVXu5CuKx~WlKkwEuUi0~VbPCYJXdEP~2-RXlHt092~M2vKPRxAge~ehP5NJ0cy5~RokSaRBUGr~eVxus64GZU~vFXX3OXCCb~p2LP_MNOlh~pSgdr8bSLW~lhJLvPIIlV~RybylJRnhJ~T4PSuIdiwS~T53qL7THLZ~vSWEvTeZc6~iVTmZJMGJj~4i9bTBXFoE~rOnsP2Q5UN~r70NVOGJ5H~P5glpXg6VU~ie0shhAARr~JmNHQca4Km~ouiK2OKQ-A~K_WSdFXjg4~nrFOQYIh7z~7cMRrOPRjW~EWR7JDW6jH~tw8Zob-Izr~sAwDH104z0~Sbp1gmMeRy~JXmGXDx4tL~j3leh4reoN~C9_ZtBtMWU~pnCQRVigpy~dx7ljrJnxj~0roTzTKxJy~trfda46Fk8~yIg4ditfn_~XEuS3TPyCa~v3nOtgG77A~2XSW7Dtt5E~2EpPrOnc5S~QnLUXjsTk6~o2vM33GyaO~o3o9P--kXx~JL8rvDh62i~hQUvXSyZW-~LBMc5qP5TM~xlfjJKgpwx~zIv0cf5VVk~Z9XB6vYxvi~mIBxNOpKNs~B_OtVkMSZT~gmYaY_jsM2~CiSfl_AE0h~QEgdaUlAgu~JVA9YTPBgb; __utmb=235335808.3.10.1564650214"
        self.cookie = config.get('account', 'cookie', is_error=True)

    def init_pattern(self):
        self.illuster_id_from_user = re.compile('<input name="id\[\]" value="(.*?)" type="checkbox"')
        self.illuster_profile_from_user = re.compile('data-profile_img="(.*?)"')
        self.illuster_username_from_user = re.compile('"data-user_name="(.*?)"></a>')
        self.pagenum_4_show = re.compile('<a href="\?type=user&amp;rest=show&amp;p=(.*?)">')
        self.pagenum_4_hide = re.compile('<a href="\?type=user&amp;rest=hide&amp;p=(.*?)">')
        # 用于获得作品详情
        self.get_illust_detail = re.compile('}\)\((.*?)\);</script><link rel="apple-touch-icon"')

    def set_logger(self, logger):
        self.logger = logger

    def download_work_by_illust_id(self, save_dir, illust_id: str, use_databse=False):
        if use_databse:
            res = self.db_util.get_one(
                "select status from illust where illust_id = " + illust_id)
            if res is not None:
                if res[0] == WorkStatus.done.value:  # 已被下载好
                    self.logger.info(" 本插画已被下载 illust_id 是 " + illust_id)
                    return True
        # 获得插画信息
        illust_info = self.get_img_info_by_img_id(illust_id)
        if illust_info is None:
            return
        (title, img_url, page_count, restrict, x_restrict, illust_type, illuster_id) = illust_info
        # 判断文件类型
        if illust_type == IllustType.illust.value:
            self.download_illust(save_dir, illust_id, illuster_id, title, img_url, page_count, restrict, x_restrict)
        elif illust_type == IllustType.ugoira.value:  # 新遇到的动图
            self.logger.warning("遇到ugoira插画，id为{}".format(illust_id))
            # return
            self.download_ugoira(save_dir, illust_id, illuster_id, title, img_url, restrict, x_restrict)
        elif illust_type == IllustType.manga.value:
            self.download_manga(illust_id, illuster_id, title, img_url, page_count, restrict, x_restrict)
        else:
            self.logger.info("暂不支持该类型的下载")

    def download_illust(self, save_dir, illust_id, illuster_id, title, img_url, page_count, restrict, x_restrict,
                        use_database=False):
        res = True
        for i in range(page_count):
            try:
                temp = img_url.replace('_p0', '_p' + str(i))
                # self.insert_illust(illust_id, IllustType.illust.value, title, img_url,
                #                    illuster_id, page_count, restrict, x_restrict)
                res = res and self.spider_util.download_img(temp, save_dir, header=self.headers)
            except Exception as e:
                res = False
                self.logger.error("下载失败" + repr(e) + "url是" + temp, exc_info=True)
                break
        if use_database:
            if res:
                self.insert_illust(illust_id, title, img_url,
                                   illuster_id, page_count, restrict, x_restrict, WorkStatus.done.value)
            else:
                # 数据库中保存下载失败的记录
                self.insert_illust(illust_id, title, img_url,
                                   illuster_id, page_count, restrict, x_restrict, WorkStatus.failure.value)

    def download_illust_o(self, save_dir, illust_id, illuster_id, title, img_url, page_count, restrict, x_restrict):
        # temp = img_url.split("_p0")
        res = True
        for i in range(page_count):
            # img_url = ""
            try:
                img_url = img_url.replace('_p0', '_p' + str(i))
                # img_url = temp[0] + "_p" + str(i) + temp[1]
                self.insert_illust(illust_id, IllustType.illust.value, title, img_url,
                                   illuster_id, page_count, restrict, x_restrict)
                res = res and self.spider_util.download_img(img_url, save_dir, header=self.headers)
            except Exception as e:
                res = False
                self.logger.error("下载失败" + repr(e) + "url是" + img_url, exc_info=True)
                break
        if res:
            self.db_util.update('update illust set status = %s where illust_id = %s',
                                (WorkStatus.done.value, illust_id))

    def filter_4_downloaded_work(self, illust_id_list):
        """查询数据库，看是否有对应的作品已经被下载完成了"""
        str_illust_id = ",".join(str(illust_id) for illust_id in illust_id_list)
        illust_sql = 'select illust_id from illust WHERE status = {} AND illust_id in ({})' \
            .format(WorkStatus.done.value, str_illust_id)
        # ugoira_sql = 'select ugoira_id from ugoira WHERE status = {} AND ugoira_id in ({})' \
        #     .format(WorkStatus.done.value, str_illust_id)
        res_in_illust = self.db_util.get_all(illust_sql)
        # res_in_ugoira = self.db_util.get_all(ugoira_sql)
        downloaded_illust_ids = [i[0] for i in res_in_illust]
        # res_in_work.append([i[0] for i in res_in_ugoira])
        for illust_id in downloaded_illust_ids:
            if str(illust_id) in illust_id_list:
                illust_id_list.remove(str(illust_id))
        return illust_id_list
        # not_downloaded_work_ids = []
        # for i in illust_id_list:
        #     if int(i) not in downloaded_illust_ids:
        #         not_downloaded_work_ids.append(i)
        # return not_downloaded_work_ids

    def get_postkey(self, url):
        """获取需要post的数据postkey"""
        pat = 'name="post_key" value="(.*?)"'
        # 不用组装headers也能拿到postKey，但是一定要是get，不能使用post
        content = self.session.get(url, timeout=15).text
        res_temp = re.findall(pat, content)
        if len(res_temp) != 1:
            self.logger.error("无法获得postKey", exc_info=True)
            return None
        postkey = re.findall(pat, content)[0]
        self.logger.info("your post key is " + postkey)
        return postkey

    def login(self):
        """模拟登陆"""
        try:
            postkey = self.get_postkey(self.GET_KEY_PAGE)
            if not postkey:
                return False
            post_data = \
                {
                    "pixiv_id": self.username,
                    "password": self.password,
                    # "captcha": "",
                    # "g_recaptcha_response":"",
                    "post_key": postkey,
                    # "source":"pc",
                    "ref": "wwwtop_accounts_index",
                    "return_to": "https://www.pixiv.net/"
                }
            # 装个头，能解决一些问题
            result = self.session.post(self.LOGIN_PAGE, data=post_data, headers=self.headers,
                                       cookies={"cookies": self.cookie})
            pat = '"body":{"(.*?)"'
            is_login_flag = re.findall(pat, result.text)[0]
            if is_login_flag == 'success':
                self.logger.info("Log in successfully.Your username is " + self.username)
                return self.session
            else:
                self.logger.info("Login failed")
                return False
        except Exception as e:
            self.logger.error('连接无响应', exc_info=True)
            return False

    def get_illust_ids(self, illuster_id):
        """
        根据画师Id获得画师的插画IdList
        插画包括动图和静态图
        :param illuster_id: 画师id
        :return:
        """
        try:
            # 获得所有的图片Id
            illust_id_json = self.get(self.URL_4_GET_ALL_WORK_ID.format(userId=illuster_id)).text
            illust_id_json = str2json(illust_id_json)
            ill_ids = illust_id_json["body"]["illusts"]
            # 示例：{[illust_id]:[illust_info],[illust_id]:[illust_info],[illust_id]:[illust_info]...}
            if ill_ids != []:
                return list(ill_ids.keys())
            else:
                return []
        except Exception as e:
            self.logger.error("搜索画师失败！" + repr(e) + "illuster_id是" + illuster_id,
                              exc_info=True)
            return None

    def get_manga_ids(self, illuster_id):
        """
        根据画师Id获得画师的漫画Id
        :param illuster_id:
        :return:
        """
        illust_id_json = self.get(self.URL_4_GET_ALL_WORK_ID.format(userId=illuster_id)).text  # 获得所有的图片Id
        illust_id_json = str2json(illust_id_json)
        manga_ids = illust_id_json["body"]["manga"]
        return list(manga_ids.keys())

    def get_img_info_by_img_id(self, illust_id):
        """
        根据插画或漫画的Id获得插画或者漫画的详细信息
        :param img_id:
        :return:
        """
        try:
            # info = self.session.get(self.URL_ILLUST_PAGE.format(illust_id=illust_id), timeout=self.timeout,
            #                         cookies={"cookies": self.cookie}).text
            info = self.get(self.URL_ILLUST_PAGE.format(illust_id=illust_id)).text
            illust_info_json = str2json(info)
            if self.isError(illust_info_json):
                self.logger.error(
                    "找不到illust信息，illust_id is {},error message is {}".format(illust_id, illust_info_json['message']),
                    exc_info=True)
                return None
            body = illust_info_json['body']
            illust_type = body['illustType']
            page_count = body['pageCount']
            restrict = body['restrict']
            x_restrict = body['xRestrict']
            title = body['title']
            url = body['urls']['original']
            illuster_id = body['userId']
            return title, url, page_count, restrict, x_restrict, illust_type, illuster_id
        except Exception as e:
            self.logger.error("获取插画信息失败" + repr(e) + "illust_id是" + illust_id, exc_info=True)
            return None

    # def is_illuster_exist(self, illuster_id):
    #     try:
    #         illust_id_json = self.get(self.URL_4_GET_ALL_WORK_ID.format(userId=illuster_id)).text  # 获得所有的图片Id
    #         illust_id_json = str2json(illust_id_json)
    #         if self.isError(illust_id_json):
    #             self.logger.error("画师不存在！illuster_id是{}".format(illuster_id), exc_info=True)
    #             return False
    #         else:
    #             return True
    #     except Exception as e:
    #         self.logger.error("无法判断画师是否存在！illuster_id是{}".format(illuster_id), exc_info=True)
    #         return None

    def get_concerned_illuster_info(self, type_, current_page_num):
        url = 'https://www.pixiv.net/bookmark.php?type=user&rest={}&p={}'.format(type_, current_page_num)
        html = self.get(url).text
        ids = self.illuster_id_from_user.findall(html)
        profiles = self.illuster_profile_from_user.findall(html)
        usernames = self.illuster_username_from_user.findall(html)
        return ids, profiles, usernames

    def get_show_pagenum(self, html):
        page = self.pagenum_4_show.findall(html)
        return len(page)

    def get_hide_pagenum(self, html):
        page = self.pagenum_4_hide.findall(html)
        return len(page)

    def get_concerned_illusters_pagenum(self, type_: str):
        """获得关注的画家的大致信息
        type 为 hide或者show"""
        content = self.session.get('https://www.pixiv.net/bookmark.php?type=user&rest={}'.format(type_),
                                   cookies={"cookies": self.cookie}).text
        page_num = 0
        if type_ == 'hide':
            page_num = self.get_hide_pagenum(content)
        elif type_ == 'show':
            page_num = self.get_show_pagenum(content)
        return page_num

    def get_pagenum_hide(self, html):
        page = self.pagenum_4_hide.findall(html)
        return len(page)

    def get_ugoira_info(self, illust_id):
        #  插画id 下载illust信息
        gif_info = str2json(
            self.session.get(self.UGOIRA_URL.format(illust_id=illust_id), cookies={"cookies": self.cookie}).text)
        # print(gif_info)
        delays = [item["delay"] for item in gif_info["body"]["frames"]]
        frames = {f['file']: f['delay'] for f in gif_info["body"]['frames']}
        page_num = len(delays)
        zip_url = gif_info["body"]["originalSrc"]
        return frames, page_num, zip_url, delays

    def download_ugoira(self, save_dir, illust_id, illuster_id, title, url, restrict, x_restrict):
        try:
            frames, page_num, zip_url, delays = self.get_ugoira_info(illust_id)
            # self.insert_ugoira(illust_id, title, url, illuster_id, page_num=None,
            #                    restrict=restrict, x_restrict=x_restrict, status=WorkStatus.done.value)
            # page_num = self.spider_util.download_ugoira(illust_id,  dest, self.session)
            gif_path = os.path.join(save_dir, illust_id + ".gif")
            zip_path = os.path.join(save_dir, illust_id + ".zip")
            res = self.spider_util.download_ugoira(zip_url, zip_path, self.headers)
            delays = [str(i) for i in delays]
            delays = ",".join(delays)
            if res:
                # 下载成功
                self.insert_ugoira(illust_id, title, url, illuster_id, page_num=page_num,
                                   restrict=restrict, x_restrict=x_restrict, status=WorkStatus.done.value,
                                   delays=delays)
            else:
                self.insert_ugoira(illust_id, title, url, illuster_id, page_num=page_num,
                                   restrict=restrict, x_restrict=x_restrict, status=WorkStatus.failure.value,
                                   delays=delays)
        except Exception:
            self.logger.error('下载动图时，遇到问题', exc_info=True)

    def insert_illust(self, illust_id, title=None, url=None, illuster_id=None, page_num=None,
                      restrict=None, x_restrict=None, status=None):
        select_sql = 'SELECT id  FROM illust WHERE illust_id = %s '
        res = self.db_util.get_one(select_sql, illust_id)
        loc_url = str(illuster_id) + "/" + url.split('/')[-1]
        if not res:  # 数据库里没找到相关信息
            insert_sql = 'INSERT INTO illust(title, url, illust_id, illuster_id, page_no, `type`, status,`restrict`,' \
                         'x_restrict, loc_url)  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
            self.db_util.insert(insert_sql, (title, url, illust_id, illuster_id, page_num, IllustType.illust.value,
                                             status, restrict, x_restrict, loc_url))
        else:
            update_sql = 'UPDATE illust SET status = %s, page_no=%s, `restrict`=%s, x_restrict=%s, title=%s, ' \
                         'loc_url=%s, type=%s WHERE illust_id=%s'
            self.db_util.update(update_sql,
                                (status, page_num, restrict, x_restrict, title, loc_url,
                                 IllustType.illust.value, illust_id))

    def insert_ugoira(self, illust_id, title, url, illuster_id, page_num,
                      restrict=None, x_restrict=None, status=None, delays=None):
        select_sql = 'SELECT id  FROM illust WHERE illust_id = %s AND type = {}'.format(IllustType.ugoira.value)
        res = self.db_util.get_one(select_sql, illust_id)
        loc_url = str(illuster_id) + "/" + url.split('/')[-1]
        if not res:  # 数据库里没找到相关信息
            insert_sql = "INSERT INTO ugoira( ugoira_id, delays) VALUES (%s, %s)"
            self.db_util.insert(insert_sql, (illust_id, delays))
            insert_sql = 'INSERT INTO illust(title, url, illust_id, illuster_id, page_no, `type`, status,`restrict`,' \
                         'x_restrict, loc_url)  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
            self.db_util.insert(insert_sql, (title, url, illust_id, illuster_id, page_num, IllustType.ugoira.value,
                                             status, restrict, x_restrict, loc_url))
        else:
            update_sql = 'UPDATE illust SET status = %s, page_no=%s, `restrict`=%s, x_restrict=%s, title=%s, ' \
                         'loc_url=%s, type=%s WHERE illust_id=%s'
            self.db_util.update(update_sql,
                                (WorkStatus.done.value, page_num, restrict, x_restrict, title, loc_url,
                                 status, illust_id))

    def update_illust(self, illust_id, page_num, illust_status=WorkStatus.done.value):
        # select_sql = 'SELECT status  FROM illust WHERE illust_id = %s '
        update_sql = 'UPDATE illust SET status = %s , page_no=%s WHERE illust_id = %s'
        self.db_util.update(update_sql, (illust_status, page_num, illust_id))
        # if self.db_util.get_one(select_sql, (illust_id)):
        #     update_sql = 'UPDATE illust SET status = %s, page_no = %s WHERE illust_id = %s'
        #     self.db_util.update(update_sql, (WorkStatus.done.value, page_num, illust_id))
        # else:
        #     self.logger.error("")
        # insert_sql = 'INSERT INTO illust(title, url, illust_id, illuster_id, page_no, `type`, status,`restrict`,' \
        #              'x_restrict)  VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
        # self.db_util.insert(insert_sql, (title, url, illust_id, illuster_id, page_num, illust_type,
        #                                      WorkStatus.waiting.value, restrict, x_restrict))

    def isError(self, json):
        return json['error']

    def download_manga(self, illust_id, illuster_id, title, img_url, page_count, restrict, x_restrict):
        raise NotImplementedError
        pass

    def get(self, url):
        return self.session.get(url, cookies={"cookies": self.cookie}, timeout=self.timeout)

    def get_illuster_info(self, illuster_id):
        # content = self.get(self.URL_4_GET_ILLUST_ID.format(userId=illuster_id)).text
        try:
            content = self.get(self.URL_4_GET_ILLUSTER_INFO.format(illuster_id)).text
            content_json = str2json(content)
            if self.isError(content_json):
                self.logger.error("画师不存在！illuster_id是{}".format(illuster_id), exc_info=True)
                return None
            name = content_json['body']['name']
            img_url = content_json['body']['imageBig']
            # print(content_json['extraData']['meta']['title'])
            # pat = re.compile('「(.*)」的个人资料 - pixiv')
            # # pat.search(content_json['extraData']['meta']['title'])
            # # pat = re.compile('「(.*)」的个人资料 - pixiv')
            # name = pat.findall(content_json['extraData']['meta']['title'])[0]
            return name, img_url
        except Exception:
            self.logger.error("无法判断画师是否存在！illuster_id是{}".format(illuster_id), exc_info=True)
            return None
