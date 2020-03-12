import enum


class WorkStatus(enum.Enum):
    """作品的下载状态"""
    waiting = 0  # 进入下载队列等待下载开始
    failure = 1  # 下载失败的
    done = 10  # 下载完成
    complete = 11  # 经验证文件完整
    unfound = 444  # 这是动图
