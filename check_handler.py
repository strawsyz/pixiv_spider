import os
from utils.mysql_util import MysqlUtil
from utils.log_util import Log
from utils.file_util import valid_file
from common.work_status import WorkStatus

"""
检测已下载的文件是否完整
1,从数据库中读取已下载完毕的文件的目录
2.去目录寻找下的文件，检查文件是否完整
3.根据检查结果，修改数据哭中的文件的状态
不处理gif文件
"""


class checker():
    def __init__(self, root_path):
        self.root_path = root_path
        self.SELECT_SQL = "SELECT page_no, loc_url,status FROM illust WHERE illust_id={}"
        self.RESET_ILLUSTER_SQL = "UPDATE illust SET status = 1 WHERE illuster_id = {}"
        self.RESET_ILLUST_SQL = "UPDATE illust SET status = 1 WHERE illuster_id = {} AND illust_id NOT IN ({})"
        self.FILTER_SQL = "SELECT illust_id FROM illust WHERE status = 10 AND illust_id in ({})"
        # 设priority = 6代表已经检查完毕
        self.MAKE_ILLUSTER_STATUS_DONE_SQL = "UPDATE illuster SET priority = 6 WHERE illuster_id = {}"
        self.CHECK_IF_DONE = 'SELECT priority FROM illuster WHERE illuster_id={}'
        self.GET_DONE_ILLUSTER = 'SELECT illuster_id FROM illuster WHERE priority=6'
        self.db_util = MysqlUtil()
        self.logger = Log(__name__, log_cate='checker').get_log()
        self.before_illuster_id = None

    def get_done_illuster(self):
        illuster_ids = self.db_util.get_all(self.GET_DONE_ILLUSTER)
        done_illuster_ids = [i[0] for i in illuster_ids]
        return done_illuster_ids

    def check_empty_dir(self, ignore=[]):
        try:
            ignore = ignore + self.get_done_illuster()
            for file_name in os.listdir(self.root_path):
                if file_name in ignore:
                    continue
                print(file_name)
                # path 即 illuster_id
                if self.before_illuster_id is not None:
                    # 将上一个设为完成
                    self.db_util.update(self.MAKE_ILLUSTER_STATUS_DONE_SQL.format(self.before_illuster_id))
                illuster_id = file_name
                self.before_illuster_id = illuster_id
                # 如果当前的illuster已经处理过了，就跳到下一个
                if self.db_util.get_one(self.CHECK_IF_DONE.format(illuster_id))[0] == 6:
                    continue
                path = os.path.join(self.root_path, file_name)
                if os.path.isdir(path):
                    image_files = os.listdir(path)
                    if len(image_files) == 0:
                        print("no images in {}".format(path))
                        self.db_util.update(self.RESET_ILLUSTER_SQL.format(illuster_id))
                        continue
        except Exception as e:
            self.logger.error('some problem happen', exc_info=1)
            raise e

    def check(self, ignore=[]):
        try:
            ignore = ignore + self.get_done_illuster()
            for file_name in os.listdir(self.root_path):
                if file_name in ignore:
                    continue
                print(file_name)
                # path 即 illuster_id
                if self.before_illuster_id is not None:
                    # 将上一个设为完成
                    self.db_util.update(self.MAKE_ILLUSTER_STATUS_DONE_SQL.format(self.before_illuster_id))
                illuster_id = file_name
                self.before_illuster_id = illuster_id
                if self.db_util.get_one(self.CHECK_IF_DONE.format(illuster_id))[0] == 6:
                    continue
                path = os.path.join(self.root_path, file_name)
                if os.path.isdir(path):
                    image_files = os.listdir(path)
                    if len(image_files) == 0:
                        print("no images in {}".format(path))
                        self.db_util.update(self.RESET_ILLUSTER_SQL.format(illuster_id))
                        continue
                    illust_ids = []
                    for file_ in image_files:
                        if file_.endswith('.zip'):
                            illust_id = file_.replace('.zip', '')
                        elif file_.endswith('.gif'):
                            # todo 暂不处理gif
                            continue
                        else:
                            illust_id = file_.split("_p")[0]
                        if illust_id not in illust_ids:
                            illust_ids.append(illust_id)
                    complete_illust_ids = []
                    # if not illust_ids:
                    #     continue
                    # illust_id_list = self.db_util.get_all(self.FILTER_SQL.format(','.join(illust_ids)))
                    # illust_ids = [i[0] for i in illust_id_list]
                    # if illust_ids:
                    #     continue
                    for illust_id in illust_ids:
                        res = True
                        info = self.db_util.get_one(self.SELECT_SQL.format(illust_id))
                        # 如果是数据库中没有信息
                        if not info:
                            self.logger.info('数据库中没有信息，illust_id为{}'.format(illust_id))
                            print(illust_id)
                            continue
                        (page_no, loc_url, status) = info
                        if status < WorkStatus.done.value:  # 10是下载成功状态，小于10 表示不成功
                            continue
                        loc_url = str(loc_url, encoding='utf-8')
                        if 'gif' in loc_url:
                            # 暂时不处理gif,理论上。gif文件不会进入这里来
                            complete_illust_ids.append(illust_id)
                            continue
                        elif 'ugoira' in loc_url:
                            loc_url = loc_url.replace('_ugoira0.jpg', '.zip')
                            loc_url_temp = loc_url.replace('_ugoira0.png', '.zip')
                            if valid_file(os.path.join(self.root_path, loc_url_temp)):
                                complete_illust_ids.append(illust_id)
                            continue
                        for i in range(page_no):
                            loc_url_temp = loc_url.replace("_p0", "_p{}".format(i))
                            res = res and valid_file(os.path.join(self.root_path, loc_url_temp))
                        # 理论上只有完整的jpg，png到这边来
                        if res:
                            complete_illust_ids.append(illust_id)
                    if not complete_illust_ids:
                        # 全部设为未完成
                        self.db_util.update(self.RESET_ILLUSTER_SQL.format(illuster_id))
                        # self.db_util.update(self.RESET_ILLUST_SQL.format(",".join(incomplete_illust_ids)))
                    else:
                        self.db_util.update(self.RESET_ILLUST_SQL.format(illuster_id, ','.join(complete_illust_ids)))
                    print(complete_illust_ids)
            # 把最后一个illuster_id进行处理
            if self.before_illuster_id is not None:
                self.db_util.update(self.MAKE_ILLUSTER_STATUS_DONE_SQL.format(self.before_illuster_id))
        except Exception as e:
            self.logger.error('some problem happen', exc_info=1)
            raise e


