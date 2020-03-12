import datetime


def now():
    return datetime.datetime.now()


def get_time(format_='%Y-%m-%d %H:%M:%S'):
    """获得字符串类型的时间"""
    return now().strftime(format_)


def get_datetime(time: str, fmt):
    """将格式化的时间字符串转成datetime类型"""
    return now().strptime(time, fmt)


def year():
    """返回年份"""
    return now().year


def month():
    """返回月份"""
    return now().month


def day():
    """返回月份里的几号"""
    return now().day


def timetuple():
    return now().timetuple()


def timestamp():
    return now().timestamp()


def from_timestamp(x):
    return datetime.datetime.fromtimestamp(x)


def add_day(date_time, day_num):
    """增加或减少天数 day_num可为正数或负数，还可以是小数"""
    return date_time + datetime.timedelta(days=day_num)


def add_week(date_time, week_num):
    return date_time + date_time.timedelta(weeks=week_num)


def add_hour(date_time, hour_num):
    return date_time + date_time.timedelta(hours=hour_num)


def add_minutes(date_time, minute_num):
    return date_time + date_time.timedelta(minutes=minute_num)
