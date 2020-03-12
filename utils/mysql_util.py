import pymysql
from utils.db_util import get_connection


class MysqlUtil(object):
    mysql = None

    def __init__(self):
        # self.connect()
        self.db = get_connection()

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, 'inst'):
            cls.inst = super(MysqlUtil, cls).__new__(cls, *args, **kwargs)
        return cls.inst

    def get_one(self, sql, param=()):
        """
        返回元组的格式
        如果没有找到数据就会返回None
        """
        try:
            cursor, conn = self.execute(sql, param)
            res = cursor.fetchone()
            return res
        except Exception as e:
            print(sql)
            raise e
        finally:
            self.close(cursor, conn)

    def get_all(self, sql='', param=()):
        # 判断是否连接,并设置重连机制
        # self.connected()
        try:
            cursor, conn = self.execute(sql, param)
            res = cursor.fetchall()
            return res
        except Exception as e:
            print(sql)
            raise e
        finally:
            self.close(cursor, conn)

    def insert(self, sql='', param=()):
        # self.connected()
        try:
            # self.db.getconn().execute(sql, param)
            cursor, conn = self.execute(sql, param)
            # _id=self.db.conn.insert_id()
            _id = cursor.lastrowid
            conn.commit()
            # 防止表中没有id返回0
            if _id == 0:
                return True
            return _id
        except Exception as e:
            print(sql)
            print('insert except   ', e.args)
            conn.rollback()
            raise e
        finally:
            self.close(cursor, conn)

    def insert_mul(self, sql='', param=()):
        # self.connected()
        cursor, conn = self.db.getconn()
        try:
            cursor.executemany(sql, param)
            # self.execute(sql,param)
            conn.commit()
            self.close(cursor, conn)
            return True
        except Exception as e:
            print(sql)
            print('insert many except   ', e.args)
            conn.rollback()
            self.close(cursor, conn)
            # self.conn.rollback()
            raise e
            return False

    def delete(self, sql='', param=()):
        # self.connected()
        try:
            # cur = self.conn.cursor()
            # self.db.getconn().execute(sql, param)
            cursor, conn = self.execute(sql, param)
            # self.db.conn.commit()
            self.close(cursor, conn)
            return True
        except Exception as e:
            print(sql)
            print('delete except   ', e.args)
            conn.rollback()
            self.close(cursor, conn)
            # self.conn.rollback()
            raise e
            return False

    def update(self, sql='', param=()):
        # self.connected()
        try:
            # cur = self.conn.cursor()
            # self.db.getconn().execute(sql, param)
            cursor, conn = self.execute(sql, param)
            # self.db.conn.commit()
            self.close(cursor, conn)
            return True
        except Exception as e:
            print(sql)
            print('update except. sql is ' + sql + 'param is ')
            print(e.args)
            print(param)
            conn.rollback()
            self.close(cursor, conn)
            # self.conn.rollback()
            raise e

    @classmethod
    def get_instance(self):
        if MysqlUtil.mysql is None:
            MysqlUtil.mysql = MysqlUtil()
        return MysqlUtil.mysql

    # 执行命令
    def execute(self, sql='', param=(), autoclose=False):
        cursor, conn = self.db.getconn()
        try:
            if param:
                cursor.execute(sql, param)
            else:
                cursor.execute(sql)
            conn.commit()
            if autoclose:
                self.close(cursor, conn)
        except Exception as e:
            print(sql)
            print(param)
            print(e.args)
            raise e
        return cursor, conn

    # 执行多条命令
    # '[{"sql":"xxx","param":"xx"}....]'
    def executemany(self, list=[]):
        cursor, conn = self.db.getconn()
        try:
            for order in list:
                sql = order['sql']
                param = order['param']
                if param:
                    cursor.execute(sql, param)
                else:
                    cursor.execute(sql)
            conn.commit()
            self.close(cursor, conn)
            return True
        except Exception as e:
            print('execute failed========', e.args)
            print(list)
            conn.rollback()
            self.close(cursor, conn)
            raise e

    # def connect(self):
    #     self.conn = pymysql.connect(user='root', db='asterisk', passwd='kalamodo', host='192.168.88.6')

    def close(self, cursor, conn):
        cursor.close()
        conn.close()
        # print
        # u"PT连接池释放con和cursor";


def get_info_from_sql():
    mysql = MysqlUtil()
    res = mysql.get_all('select url from illust WHERE  status = 444')
    for url in res:
        url = str(url[0])
        i = url.replace('img-original', 'img-zip-ugoira')
        i = i.replace('0.jpg', '1920x1080.zip')
        i = i.replace('0.png', '1920x1080.zip')
        yield i
        if '.zip' not in i:
            print('url替换失败， url is ' + url)
        else:
            pass

