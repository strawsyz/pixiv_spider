import configparser


class ConfigureUtil():
    """
    配置文件工具
    有读取、修改、增加、删除、保存功能
    增删改需要保存才会修改文件
    """

    def __init__(self, path=None, encoding='utf-8'):
        self.config = configparser.ConfigParser()
        if not path:
            self.path = 'config/config.conf'
        else:
            self.path = path
        self.config.read(self.path, encoding=encoding)

    def get(self, section, option, type_=None, is_error=False, default=None):
        """ 获得个某个section下的option的内容
        :param section:
        :param option:
        :param type_:
        :param is_error: 作为是否容错的标志
        :param default:
        :return:
        """
        res = self.get_option(section, option, is_error)
        if res is None:
            return default
        # if type is None:
        #     return res
        if type_ == 'int':
            return int(res)
        if type_ == 'float':
            return float(res)
        return res

    def get_option(self, section, option, is_error=True):
        """
        获得某个option
        :param section:
        :param option:
        :param is_error: 是否允许没找到option
        如果为True，没有找到option返回None，
        如果为False，没找到就报错
        :return:
        """
        try:
            res = self.config.get(section, option)  # 自动去掉空字符
            if res == '' or res.isspace():
                return None
            return res
        except configparser.NoOptionError as e:
            if is_error:
                return None
            else:
                print(e.message)
                raise e

    def get_section(self, section):
        return self.config.items(section)

    def add(self, section, key: str = None, value: str = None):
        """
        key 和 value都不为None才会增加key-value对
        否则 只增加section
        :param section:
        :param key:
        :param value:
        :return:
        """
        if key is None or value is None:
            self.config.add_section(section)
        else:
            try:
                self.config.set(section, key, value)
            except configparser.NoSectionError as e:
                self.config.add_section(section)
                self.config.set(section, key, value)
        self.save()

    def get_sections(self):
        # 获得配置文件中的对应的section
        return self.config.sections()

    def remove(self, section, option=None):
        if option is None:
            self.config.remove_section(section)
        else:
            self.config.remove_option(section, option)
        self.save()

    def save(self, mode='w'):
        """
        保存对配置文件的增删改，默认重写模式
        :param mode:  a->追加模式 w->重新写入模式
        最好不用追加模式，会导致配置文件出现相同的section
        !!!  w 会把注释也删除，慎用
        :return:
        """
        with open(self.path, mode) as file:
            self.config.write(file)

    def update(self, section, option, new_value):
        self.config.set(section, option, new_value)
        self.save()
