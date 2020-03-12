import logging
import time
import os
from utils.file_util import make_directory


class Log:
    def __init__(self, logger_name=None, log_cate='main'):
        """
            指定保存日志的文件路径，日志级别，以及调用文件
            将日志存入到指定的文件中
        """
        # 创建一个logger
        self.logger = logging.getLogger(logger_name)
        # 设置日志级别
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '[%(levelname)s]<%(asctime)s> %(filename)s->%(funcName)s line:%(lineno)d %(message)s')

        # 保存日志的文件
        file_dir = os.getcwd() + '/Logs'
        make_directory(file_dir)
        self.log_path = file_dir
        self.log_name = self.log_path + "/" + log_cate + "." + time.strftime("%Y_%m_%d") + '.log'
        # fh = logging.FileHandler(self.log_name, 'a')  # 追加模式  这个是python2的
        fh = logging.FileHandler(self.log_name, 'a', encoding='utf-8')  # 这个是python3的
        fh.setLevel(logging.DEBUG)
        # 定义handler的输出格式
        fh.setFormatter(formatter)
        # 给logger添加handler
        self.logger.addHandler(fh)

        # 再创建一个handler，用于输出到控制台
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
        self.logger.addHandler(console)

        # logging自带的保存文本日志文件的handler
        # th = logging.handlers.TimedRotatingFileHandler(filename=filename, when=when, backupCount=backCount,
        #                                        encoding='utf-8')  # 往文件里写入#指定间隔时间自动生成文件的处理器
        # # 实例化TimedRotatingFileHandler
        # # interval是时间间隔，backupCount是备份文件的个数，如果超过这个个数，就会自动删除，
        # # when是间隔的时间单位，单位有以下几种：
        # # S 秒
        # # M 分
        # # H 小时、
        # # D 天、
        # # W 每星期（interval==0时代表星期一）
        # # midnight 每天凌晨
        # th.setFormatter(formatter)  # 设置文件里写入的格式
        # self.logger.addHandler(th)


        #  添加下面一句，在记录日志之后移除句柄
        # self.logger.removeHandler(ch)
        # self.logger.removeHandler(fh)
        # 关闭打开的文件
        fh.close()
        console.close()

    def get_log(self):
        return self.logger
