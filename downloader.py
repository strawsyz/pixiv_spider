import os
from utils.header_util import get_header
from utils.mysql_util import MysqlUtil
from common.illust_type import IllustType
from utils.spider_util import SpiderUtil
from utils.file_util import make_directory, valid_file, file_extension
from common.work_status import WorkStatus
import time
import threadpool
import requests
from utils.log_util import Log

"""
可以作为下载器使用 
需要有数据库！！！！
1。读取数据库中需要下载的图片url信息
2。从pixiv下载图片到本地
"""


class Downloader:
    def __init__(self, path):
        self.db_util = MysqlUtil()
        self.spdier_util = SpiderUtil()
        self.root_path = path
        self.logger = Log(__name__).get_log()

    def get_info(self, select_sql):
        """
        根据sql查询要爬取的数据
        """
        res = self.db_util.get_all(select_sql)
        infos = []
        for info in res:
            type_ = info[3]
            if type_ == IllustType.ugoira.value:
                # todo 只下载zip文件，之后再处理缩略图
                url = Downloader.handle_url_4_ugoira(info[0])
            else:
                url = str(info[0], encoding='utf-8')
                if '.gif' in url:
                    # 暂不处理gif类型
                    continue
                if '.jpg' in url or '.png' in url:
                    pass
                else:
                    self.logger.warning('不支持的类型！illust_id为{}'.format(info[1]))
            infos.append((url, self.get_path(url, str(info[2])), info[4], info[1]))
        return infos

    def get_path(self, url: str, illuster_id: str):
        path = os.path.join(self.root_path, illuster_id)
        make_directory(path)
        return os.path.join(path, url.split("/")[-1])

    @staticmethod
    def handle_url_4_ugoira(url):
        url = str(url, encoding="utf-8")
        i = url.replace('img-original', 'img-zip-ugoira')
        i = i.replace('0.jpg', '1920x1080.zip')
        i = i.replace('0.png', '1920x1080.zip')
        return i

    def download_file(self, url, save_path, headers):
        res = self.spdier_util.download_file(url, save_path, headers)
        if res == 404:
            self.logger.error('无法找到文件，url为{}'.format(url))
            return 404
        if res and valid_file(save_path, file_extension(save_path)):
            return True
        else:
            return False

    def download_file_list(self, url, save_path, headers, page_num: int, illust_id):
        """当一个illust_id下的所有插画都下载完成才更新状态"""
        res = True
        for i in range(page_num):
            url_temp = url.replace('_p0', '_p{}'.format(i))
            save_path_temp = save_path.replace('_p0', '_p{}'.format(i))
            res = res and self.download_file(url_temp, save_path_temp, headers)
            if res == 404:
                self.db_util.update(
                    'UPDATE illust SET status = {} WHERE illust_id = {}'.format(WorkStatus.unfound.value, illust_id))
                return
        if res:
            self.db_util.update(
                'UPDATE illust SET status = {} WHERE illust_id = {}'.format(WorkStatus.complete.value, illust_id))

    def main(self, select_sql, headers, thread_num, interval):
        """
        查询url数据，然后自动下载
        :param select_sql:  查询数据的sql语句
        :param headers:  请求头设置
        :param thread_num:  下载线程数
        :param interval:  循环查询数据库的时间间隔
        :return:
        """
        pool = None
        while True:
            infos = self.get_info(select_sql)
            print('get info from database')
            if infos:
                param_list = [([i[0], i[1], headers, i[2], i[3]], None) for i in infos]
                if pool is None:
                    pool = threadpool.ThreadPool(thread_num)
                tasks = threadpool.makeRequests(self.download_file_list, param_list)
                [pool.putRequest(task) for task in tasks]
                pool.wait()
            self.logger.info('one batch is over')
            print('one batch is over')
            time.sleep(interval)
