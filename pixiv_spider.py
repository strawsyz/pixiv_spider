import threadpool
import requests
import ssl
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
from utils.mysql_util import MysqlUtil as DbUtil
from utils.pixiv_util import PixivUtil
from utils.file_util import make_directory
from utils.conf_util import ConfigureUtil
from utils.log_util import Log
from common.work_status import WorkStatus
import time
from utils.time_util import get_time


class PixivSpider():
    def load_config(self):
        # 加载配置文件
        self.config = ConfigureUtil('config/config.conf')
        try:
            self.thread_num = self.config.get("app", "thread_num", type_="int")
            # 下载图片存储的根目录
            self.root_path = self.config.get("download", "path")
            # 下载循环等待的时间
            self.waiting_time = self.config.get("download", "waiting_time", type_="int")
        except Exception as e:
            self.logger.error("请检查你配置的下载路径====》{}".format(repr(e)), exc_info=True)
            raise e

    def load_logger(self):
        self.logger = Log(__name__).get_log()

    def __init__(self):
        # 加载配置文件
        self.sql_4_update = 'update illuster set priority = 0,  modify_time = "{}" WHERE illuster_id  = {}'
        self.load_logger()
        self.load_config()
        self.pixiv_util = PixivUtil()
        self.db_util = DbUtil()
        self.pool = threadpool.ThreadPool(self.thread_num)
        self.WAITING_SQL = 'select illuster_id from illuster WHERE priority > 0 ' \
                           ' AND illuster_id!=11 ORDER BY priority DESC LIMIT {} '
        ssl._create_default_https_context = ssl._create_unverified_context
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        #  测试。用来解决, 'ssl3_read_bytes', 'sslv3 alert bad record mac')
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL'

    def login(self):
        is_login = self.pixiv_util.login()
        if not is_login:
            self.logger.info("登陆失败,请检查账号密码是否正确和网络是否连通")
            return False
        else:
            return True

    def save_concerned_illuster_info(self, type_: str):
        """
        根据用户id找到用户关注的画师，保存到数据库
        :param type_: hide或者show hide表示未公开，show表示已公开
        :return:
        """
        if not self.login():
            return
        page_num = self.pixiv_util.get_concerned_illusters_pagenum(type_)
        for current_page_num in range(1, page_num + 1):
            ids_, profiles, usernames = self.pixiv_util.get_concerned_illuster_info(type_, current_page_num)
            for illuster_id, profile, username in zip(ids_, profiles, usernames):
                res = self.db_util.get_one("select id from illuster where illuster_id = " + illuster_id)
                str_time = get_time()
                if res:
                    self.logger.debug("该画师已存在" + illuster_id)
                    self.db_util.update('UPDATE illuster SET name=%s, image_url=%s, modify_time=%s, priority=%s '
                                        'WHERE illuster_id =%s',
                                        (username, profile, str_time, 0, illuster_id))
                else:
                    self.db_util.insert(
                        "insert into illuster(illuster_id,name,image_url,create_time,modify_time,priority) "
                        "value(" + illuster_id + ",'" + username + "','" + profile + "','" + str_time + "','" + str_time + "',5)")
        self.logger.info("信息保存完毕")

    def get_illuster_ids(self, num, use_data_base=False):
        """
        获得num个未爬取的画家id
        优先使用配置文件中的画家id，然后是数据库中待爬取的
        """
        ids = self.config.get("download", "illuster_ids")
        ids = [] if ids is None else ids.split()
        if len(ids) > num - 1:
            return ids[:10]
        elif use_data_base:
            illuster_ids = self.db_util.get_all(self.WAITING_SQL.format(10))
            for illuster_id in illuster_ids:
                ids.append(str(illuster_id[0]))
            temp = list(set(ids))[:10]
            temp.sort(key=ids.index)
            return temp
        else:
            return ids[:10]

    def main(self, batch_size=10, use_database=False):
        """
        自动读取配置文件或者数据库，获得需要爬取的作家的id
        配置文件要更加优先
        找到画家id爬取画家的作品
        """
        while True:
            illuster_ids = self.get_illuster_ids(batch_size, use_database)
            if len(illuster_ids) == 0:
                time.sleep(60 * 60 * 4)
            for illuster_id in illuster_ids:
                self.logger.info("正在下载的是" + illuster_id + "的作品")
                if use_database:
                    res = self.db_util.get_one("select id from illuster where illuster_id = %s", illuster_id)
                    # 爬取画师有关信息
                    str_time = get_time()
                    # 先判断画师是否存在于pixiv网站
                    # is_exist = self.pixiv_util.is_illuster_exist(illuster_id)
                    info = self.pixiv_util.get_illuster_info(illuster_id)
                    if info is None:
                        self.db_util.insert("update illuster set priority = -1 WHERE illuster_id = %s", illuster_id)
                        continue
                    else:
                        name, img_url = info
                    if res:
                        self.logger.debug("该画师已存在数据库中" + illuster_id)
                        self.db_util.update(
                            "update illuster set name = %s, image_url = %s, modify_time = %s where illuster_id = %s",
                            (name, img_url, str_time, illuster_id))
                    else:
                        self.db_util.insert(
                            "insert into illuster(illuster_id, name, image_url, create_time,modify_time,priority)"
                            " value(%s, %s, %s, %s, %s,5)",
                            (illuster_id, name, img_url, str_time, str_time))
                dir_ = os.path.join(self.root_path, illuster_id)
                make_directory(dir_)
                illust_ids = self.pixiv_util.get_illust_ids(illuster_id)
                if illuster_ids is None:
                    self.logger.error('获得插画列表失败，画师id为{}, 开始下一个画师的信息爬取'.format(illuster_id))
                    continue
                illust_num = len(illust_ids)
                self.logger.info("共有插图%d个" % (illust_num))
                if use_database:
                    if res:
                        self.logger.debug("该画师已存在数据库中" + illuster_id)
                        self.db_util.update(
                            "update illuster set name = %s, image_url = %s, modify_time = %s, illust_num = %s where illuster_id = %s",
                            (name, img_url, str_time, illust_num, illuster_id))
                    else:
                        self.db_util.insert(
                            "insert into illuster(illuster_id, name, image_url, create_time,modify_time,illust_num, priority)"
                            " value(%s, %s, %s, %s, %s, %s, 5)",
                            (illuster_id, name, img_url, str_time, str_time, illust_num))
                if illust_num > 0:
                    if use_database:
                        illust_ids = self.pixiv_util.filter_4_downloaded_work(illust_ids)
                    # 准备循环的数据
                    var_list = []
                    for illust_id in illust_ids:  # 循环的到的illust_id
                        var_list.append(([dir_, illust_id], None))
                    if self.pool is None:
                        self.pool = threadpool.ThreadPool(self.thread_num)
                    tasks = threadpool.makeRequests(self.pixiv_util.download_work_by_illust_id, var_list)
                    [self.pool.putRequest(task) for task in tasks]
                    self.pool.wait()

                # 直接删除第一个id，因为第一个id最先下载
                il_ids = self.config.get("download", "illuster_ids")
                if il_ids is not None:
                    self.config.update("download", "illuster_ids", " ".join(il_ids.split()[1:]))
                if use_database:
                    self.db_util.update(self.sql_4_update.format(get_time(), illuster_id))
                self.logger.info("{}的作品下载完成".format(illuster_id))
            self.logger.info('one batch is over')
            time.sleep(self.waiting_time)
        self.logger.info("所有的作品下载完成")
        session.close()


if __name__ == '__main__':
    spider = PixivSpider()
    spider.main()
